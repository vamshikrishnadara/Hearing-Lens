"""Export fictional source categories and pipeline results for a separate formula check.

The workbook's counts/formulas are calculated independently from these categories.
This creates review material, not a claim that a human has checked it.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from pipeline.gaps import analyze_gaps
from pipeline.ingest import map_columns
from scripts.validate_gaps import REFERENCES


def prepare(sample_path):
    sample_path = Path(sample_path)
    sample = pd.read_csv(sample_path, dtype=str, keep_default_na=False)
    mapped = map_columns(sample, comment_column='comment_text', respondent_id_column='respondent_id',
                         subgroup_columns=['role', 'housing_tenure']).frame
    # The fixed sample must need no cleaning; this workbook checks gap arithmetic,
    # not ingest. Refuse a changed fixture that needs additional source bookkeeping.
    if len(mapped) != len(sample) or sample[['role', 'housing_tenure']].eq('').any().any():
        raise ValueError('The fixed workbook fixture requires nonmissing groups and no dropped rows.')
    result = analyze_gaps(mapped, references=REFERENCES)
    if any(row['suppressed'] for row in result['rows']):
        raise ValueError('The fixed workbook fixture must have no suppressed groups.')
    return {'source': 'data/samples/' + sample_path.name,
            'source_sha256': hashlib.sha256(sample_path.read_bytes()).hexdigest(),
            'notice': 'Fictional data and reference shares. Formula verification is not human signoff.',
            'source_rows': sample[['role', 'housing_tenure']].values.tolist(),
            'references': REFERENCES, 'pipeline_rows': result['rows']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / 'data/samples/synthetic_theme_benchmark.csv'
    result = prepare(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as handle:
        handle.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'source_rows': len(result['source_rows']), 'comparison_rows': len(result['pipeline_rows'])}))


if __name__ == '__main__':
    main()
