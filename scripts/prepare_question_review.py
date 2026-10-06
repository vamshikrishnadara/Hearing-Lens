"""Prepare a reproducible blind 200-sentence local review; never invent labels."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

import pandas as pd

from pipeline.questions import analyze_questions, DETECTOR_VERSION
from scripts.validate_cfpb_themes import load_sample
from scripts.validate_core import load_federal


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def make_packet(corpora, *, size=200, seed=20261006):
    if type(size) is not int or size < 1:
        raise ValueError('Sample size must be a positive integer.')
    pool, corpus_hashes = [], {}
    for name, frame in sorted(corpora.items()):
        result = analyze_questions(frame)
        corpus_hashes[name] = fingerprint(result['sentences'])
        pool.extend(dict(row, corpus=name) for row in result['sentences'])
    if len(pool) < size:
        raise ValueError('Not enough nonempty sentences for the requested review sample.')
    # Sample all sentences, not just predicted questions: false negatives must
    # remain eligible. Repeated occurrences are retained, as in the source corpus.
    selected = random.Random(seed).sample(pool, size)
    manifest_rows, blind_rows = [], []
    for i, row in enumerate(selected, 1):
        immutable = {key: row[key] for key in ['corpus', 'row_position', 'sentence_index',
                                               'source_start', 'source_end', 'text', 'text_sha256']}
        immutable['review_id'] = f'question-{i:03d}'
        manifest_rows.append(dict(immutable, predicted_question=row['is_question']))
        blind_rows.append(dict(immutable, human_question='', reviewer='', notes=''))
    payload = {'schema_version': 1, 'detector_version': DETECTOR_VERSION, 'seed': seed,
               'sampling': 'Uniform without replacement over pooled sentence occurrences; no filtering by predictions.',
               'pool_sentences': len(pool), 'sample_size': size, 'corpus_fingerprints': corpus_hashes,
               'sample_by_corpus': dict(sorted(Counter(r['corpus'] for r in selected).items())),
               'rows': manifest_rows}
    manifest = dict(payload, sample_id=fingerprint(payload))
    review = {'schema_version': 1, 'sample_id': manifest['sample_id'], 'rows': blind_rows}
    return manifest, review


def review_html(review):
    template = (Path(__file__).parent / 'templates/question_review.html').read_text()
    # JSON in a script element needs HTML-sensitive characters escaped even when
    # rendered via textContent; uploaded comments are untrusted plain text.
    encoded = json.dumps(review, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return template.replace('__REVIEW_DATA__', encoded)


def write_packet(destination, manifest, review):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    files = {'question-review-manifest.json': json.dumps(manifest, indent=2, ensure_ascii=False),
             'question-review.json': json.dumps(review, indent=2, ensure_ascii=False),
             'Hearing_Lens_Question_Review.html': review_html(review)}
    if any((destination / name).exists() for name in files):
        raise ValueError('Review files already exist; choose a new folder to preserve human work.')
    for name, content in files.items():
        with (destination / name).open('x') as handle:
            handle.write(content + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--synthetic', type=Path, required=True)
    parser.add_argument('--cfpb-dir', type=Path, required=True)
    parser.add_argument('--federal-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    corpora = {'synthetic': pd.read_csv(args.synthetic, dtype=str, keep_default_na=False),
               'cfpb': load_sample(args.cfpb_dir)[0], 'federal': load_federal(args.federal_dir)[0]}
    manifest, review = make_packet(corpora)
    write_packet(args.output_dir, manifest, review)
    print(json.dumps({k: manifest[k] for k in ['sample_id', 'pool_sentences', 'sample_size', 'sample_by_corpus']}, indent=2))


if __name__ == '__main__':
    main()
