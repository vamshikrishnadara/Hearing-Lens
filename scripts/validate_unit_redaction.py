"""Check unit patterns on fictional cases and optionally a prepared public sample.

Print aggregate public-data results only; no source narratives or IDs are emitted.
"""

import argparse
from collections import Counter
import json
from pathlib import Path

import pandas as pd

from pipeline.redact import _PATTERNS, redact_frame
from scripts.validate_cfpb_themes import load_sample


# Observed ordinary-word errors; evaluation only, never used as a runtime allowlist.
KNOWN_ORDINARY = {
    'step', 'steps', 'steal', 'stealing', 'step-mother', 'steep', 'stem', 'united',
    'steady', 'stellar', 'apartment clean',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample-dir', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / 'data/samples/unit_redaction_cases.json').read_text())
    pattern = dict(_PATTERNS)['UNIT_NUMBER']
    full = redact_frame(pd.DataFrame({'comment_text': [case['text'] for case in cases]}))
    checks = []
    for case, output in zip(cases, full.frame['redacted_comment_text']):
        pattern_output = pattern.sub('[UNIT_NUMBER]', case['text'])
        checks.append({**case, 'pattern_output': pattern_output,
                       'pattern_matches_expected': pattern_output == case['expected_pattern_output'],
                       'full_pipeline_output': output})
    report = {'notice': 'Fictional pattern cases and optional public development sample; not privacy certification.',
              'unit_pattern': pattern.pattern,
              'fictional_cases': {'count': len(cases), 'pattern_matches_expected': sum(c['pattern_matches_expected'] for c in checks), 'cases': checks}}
    if args.sample_dir:
        sample, manifest = load_sample(args.sample_dir)
        ordinary = Counter()
        affected = []
        total = 0
        for position, text in enumerate(sample.comment_text):
            matches = [m.group().casefold() for m in pattern.finditer(text)]
            total += len(matches)
            bad = [value for value in matches if value in KNOWN_ORDINARY]
            ordinary.update(bad)
            if bad:
                affected.append(position)
        result = redact_frame(sample[['comment_text']])
        report['public_sample'] = {
            'rows': len(sample), 'sample_sha256': manifest['sample_sha256'],
            'pattern_unit_matches': total, 'known_ordinary_word_matches': dict(ordinary),
            'known_ordinary_word_total': sum(ordinary.values()),
            'affected_row_positions': affected, 'full_pipeline_entity_counts': result.entity_counts,
        }
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
