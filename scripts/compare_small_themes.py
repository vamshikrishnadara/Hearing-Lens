"""Compare opt-in small-theme merging; print aggregates without public text or IDs.

Run: python -m scripts.compare_small_themes --sample-dir PATH
Optional --baseline-report PATH verifies the previous manual-six result.
"""
import argparse
from collections import Counter
import importlib.metadata
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import adjusted_rand_score

from pipeline.redact import build_safe_display_frame
from pipeline.themes import MODEL_PATH, analyze_themes
from scripts.compare_theme_grouping import new_fixture
from scripts.validate_cfpb_themes import load_sample


def summarize(result, safe_texts):
    themes, assignments = result['themes'], result['assignments']
    by_row = {a['row_position']: a['theme_id'] for a in assignments}
    counts = Counter(a['theme_id'] for a in assignments)
    quotes = [(theme['theme_id'], q) for theme in themes for q in theme['quotes']]
    return {
        'initial_count': result['theme_selection']['selected_count'],
        'final_count': len(themes),
        'group_sizes': [t['count'] for t in themes],
        'small_group_count': sum(t['count'] < 3 for t in themes),
        'candidate_quote_count': len(quotes),
        'themes_with_three_quotes': sum(len(t['quotes']) == 3 for t in themes),
        'merging': result['theme_merging'],
        'checks': {
            'each_analyzed_row_assigned_once': len(by_row) == len(assignments) == result['analyzed_comments'],
            'counts_match_assignments': dict(counts) == {t['theme_id']: t['count'] for t in themes},
            'shares_match_counts': all(np.isclose(t['share'], t['count'] / result['analyzed_comments']) for t in themes),
            'quote_membership_valid': all(by_row.get(q['row_position']) == theme_id for theme_id, q in quotes),
            'quotes_match_redacted_originals': all(0 <= q['row_position'] < len(safe_texts) and q['text'] == safe_texts[q['row_position']] for _, q in quotes),
            'quote_lengths_valid': all(12 <= len(q['text'].split()) <= 60 for _, q in quotes),
        },
    }


def compare(frame, count):
    safe_texts = build_safe_display_frame(frame[['comment_text']]).frame.comment_text.tolist()
    results = {mode: analyze_themes(frame[['comment_text']], theme_count=count, merge_small_themes=enabled)
               for mode, enabled in [('disabled', False), ('enabled', True)]}
    summary = {mode: summarize(result, safe_texts) for mode, result in results.items()}
    summary['same_analyzed_positions'] = (
        [a['row_position'] for a in results['disabled']['assignments']] ==
        [a['row_position'] for a in results['enabled']['assignments']])
    summary['themes_and_assignments_unchanged'] = all(
        results['disabled'][key] == results['enabled'][key] for key in ['themes', 'assignments'])
    if 'validation_theme' in frame:
        for mode, result in results.items():
            truth = [frame.iloc[a['row_position']]['validation_theme'] for a in result['assignments']]
            actual = [a['theme_id'] for a in result['assignments']]
            summary[mode]['adjusted_rand_index'] = float(adjusted_rand_score(truth, actual))
    return summary, results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample-dir', required=True, type=Path)
    parser.add_argument('--baseline-report', type=Path)
    args = parser.parse_args()
    frame, manifest = load_sample(args.sample_dir)
    public, results = compare(frame, 'auto')
    manual, manual_results = compare(frame, 6)
    if args.baseline_report:
        old = json.loads(args.baseline_report.read_text())
        if old['sample_provenance']['sample_sha256'] != manifest['sample_sha256']:
            raise ValueError('Baseline uses a different sample.')
        previous = old['validation']['result']
        manual['previous_baseline_unchanged'] = {key: manual_results['disabled'][key] == previous[key]
            for key in ['themes', 'assignments', 'warnings', 'theme_selection', 'analyzed_comments', 'empty_comments_removed', 'excluded_row_positions'] if key in previous}
    fictional_auto, _ = compare(new_fixture(), 'auto')
    fictional_manual, _ = compare(new_fixture(), 3)
    source = MODEL_PATH / 'hearing_lens_source.json'
    print(json.dumps({
        'notice': 'Experimental fixed size <3 and cosine threshold 0.75, chosen before this comparison. No public theme ground truth or semantic accuracy claim. Reports omit public text and IDs.',
        'sample_sha256': manifest['sample_sha256'],
        'model_source': json.loads(source.read_text()) if source.exists() else {},
        'versions': {p: importlib.metadata.version(p) for p in ['sentence-transformers', 'scikit-learn', 'torch', 'spacy']},
        'cfpb_100_auto': public, 'cfpb_100_manual6': manual,
        'fictional_24_auto': fictional_auto, 'fictional_24_manual3': fictional_manual,
    }, indent=2))


if __name__ == '__main__':
    main()
