"""Reproduce development-only gap checks on fictional data; never infer a baseline."""
import argparse
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path

import pandas as pd

from pipeline.gaps import analyze_gaps
from pipeline.ingest import map_columns

# Explicit fictional development assumptions, not Census/Chicago demographics.
REFERENCES = {
    'subgroup__role': {'Parent': '40%', 'Teacher': '20%', 'Resident': '20%', 'Student': '10%', 'Community organizer': '10%'},
    'subgroup__housing_tenure': {'Renter': '60%', 'Owner': '35%', 'Other': '5%'},
}


def run(sample):
    mapped = map_columns(sample, comment_column='comment_text', respondent_id_column='respondent_id',
                         subgroup_columns=['role', 'housing_tenure'])
    result = analyze_gaps(mapped.frame, references=REFERENCES)
    # Independent arithmetic: original Python row dictionaries, integer counts and
    # exact rational shares. This is a code check, not a human spreadsheet review.
    raw = sample.to_dict('records')
    seen, cleaned = set(), []
    for row in raw:
        if not str(row['comment_text']).strip(): continue
        respondent = str(row['respondent_id']).strip()
        if respondent and respondent in seen: continue
        if respondent: seen.add(respondent)
        cleaned.append(row)
    checks = []
    for field, baseline in REFERENCES.items():
        original = field.removeprefix('subgroup__')
        counts = Counter(str(row[original]).strip().casefold() for row in cleaned
                         if pd.notna(row[original]) and str(row[original]).strip())
        n = sum(counts.values())
        for row in [r for r in result['rows'] if r['field'] == field]:
            key = row['group'].casefold()
            if row['suppressed']:
                raise AssertionError('This fixed development fixture should have no small groups.')
            share = Fraction(counts[key], n)
            reference = Fraction(baseline[row['group']].rstrip('%')) / 100
            expected = {'count': counts[key], 'participation_share': float(share),
                        'reference_share': float(reference),
                        'gap_percentage_points': float(100 * (share - reference)),
                        'representation_ratio': float(share / reference)}
            passed = all(row[k] == value for k, value in expected.items())
            checks.append({'field': field, 'group': row['group'], 'passed': passed})
    return {'notice': 'Fictional baselines only. Independent rational-arithmetic code check, not a human hand-computed spreadsheet or real population comparison.',
            'input_rows': len(sample), 'eligible_rows': len(mapped.frame),
            'references': REFERENCES, 'result': result, 'checks': checks,
            'all_checks_passed': all(c['passed'] for c in checks)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sample = pd.read_csv(root / 'data/samples/synthetic_theme_benchmark.csv', dtype=str)
    report = run(sample)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'gap-validation.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    pd.DataFrame(report['result']['rows']).to_csv(args.output_dir / 'gap-table.csv', index=False)
    print(json.dumps({'input_rows': report['input_rows'], 'group_checks': len(report['checks']),
                      'all_checks_passed': report['all_checks_passed']}, indent=2))
    if not report['all_checks_passed']: raise SystemExit(1)


if __name__ == '__main__': main()
