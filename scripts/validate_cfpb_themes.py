"""Validate themes on an explicitly prepared local public CFPB sample; print JSON.

Does not download anything or write files. Full redacted review text is intended
for local review only; publish aggregate findings instead of this JSON.
"""

import argparse
from collections import Counter
import importlib.metadata
import json
from pathlib import Path
import re
from time import perf_counter

import pandas as pd

from pipeline.redact import build_safe_display_frame
from pipeline.themes import MODEL_PATH, analyze_themes
from scripts.prepare_cfpb_sample import sha256_file


def load_sample(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'cfpb_manifest.json').read_text())
    sample = directory / 'cfpb_sample.csv'
    if sha256_file(sample) != manifest['sample_sha256']:
        raise ValueError('Sample checksum does not match its manifest.')
    frame = pd.read_csv(sample, dtype=str, keep_default_na=False)
    if not {'comment_text', 'complaint_id', 'product', 'issue', 'date_received'} <= set(frame.columns):
        raise ValueError('Sample is missing required columns.')
    if len(frame) != manifest['sample_rows'] or frame.complaint_id.tolist() != manifest['selected_complaint_ids']:
        raise ValueError('Sample rows do not match the manifest.')
    if frame.comment_text.str.strip().eq('').any() or frame.complaint_id.duplicated().any():
        raise ValueError('Sample has empty narratives or repeated complaint identifiers.')
    return frame, manifest


def evaluate(frame):
    start = perf_counter()
    # Product/issue fields are contextual metadata, not theme truth or model input.
    result = analyze_themes(frame[['comment_text']], theme_count=6)
    elapsed = perf_counter() - start
    safe = build_safe_display_frame(frame[['comment_text']]).frame.comment_text.tolist()
    sizes = [len(text.split()) for text in safe]
    product_counts, review = {}, []
    for theme in result['themes']:
        positions = [a['row_position'] for a in result['assignments'] if a['theme_id'] == theme['theme_id']]
        product_counts[str(theme['theme_id'])] = dict(Counter(frame.iloc[positions]['product']))
        if len(review) < 3:
            # Fixed first five input positions, not a claim of representative review.
            review.append({'theme_id': theme['theme_id'], 'label': theme['label'],
                           'members': [{'row_position': i, 'text': safe[i]} for i in positions[:5]]})
    quotes = [q for theme in result['themes'] for q in theme['quotes']]
    return {
        'elapsed_seconds_including_model_load': round(elapsed, 3),
        'timing_scope': 'Theme analysis only; excludes CSV loading, imports, setup downloads, and preparation of the review packet.',
        'redacted_word_counts': {'minimum': min(sizes), 'median': float(pd.Series(sizes).median()),
                                 'maximum': max(sizes), 'within_12_to_60': sum(12 <= n <= 60 for n in sizes)},
        'product_composition_context_only': product_counts,
        'candidate_quote_count': len(quotes),
        'quote_checks': [{'row_position': q['row_position'], 'word_count': len(q['text'].split()),
                          'raw_email_pattern': bool(re.search(r'\S+@\S+', q['text']))} for q in quotes],
        'themes_with_three_quotes': sum(len(t['quotes']) == 3 for t in result['themes']),
        'themes_with_source_placeholder_keywords': sum(any(re.fullmatch(r'[xX]{2,}', w) for w in t['keywords']) for t in result['themes']),
        'manual_review_packet': review,
        'result': result,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        frame, manifest = load_sample(args.sample_dir)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f'Sample validation failed ({type(exc).__name__}); check the sample and manifest.\n')
    source = MODEL_PATH / 'hearing_lens_source.json'
    report = {
        'notice': 'Public-data development check. No hand-coded theme truth, accuracy score, or privacy certification. Keep review text local.',
        'sample_provenance': {k: manifest[k] for k in ['source_page', 'source_url', 'archive_sha256', 'sample_sha256', 'seed', 'sample_rows']},
        'model_source': json.loads(source.read_text()) if source.exists() else {},
        'versions': {p: importlib.metadata.version(p) for p in ['sentence-transformers', 'scikit-learn', 'torch', 'spacy']},
        'validation': evaluate(frame),
    }
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
