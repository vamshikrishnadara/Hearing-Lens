"""Validate the complete export path on fixed local development samples.

Detailed outputs stay in a new explicitly selected local folder. No human
quality review, accuracy labels or real population references are fabricated.
"""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

from pipeline.ingest import load_table, map_columns
from pipeline.quotes import valid_source_quote
from pipeline.redact import build_safe_display_frame
import run_all
from scripts.validate_cfpb_themes import load_sample
from scripts.validate_core import load_federal
from scripts.validate_gaps import REFERENCES, run as validate_gap_fixture
from scripts.validate_questions import validate_result as validate_questions


def check_result(result, frame):
    """Cross-module alignment and source integrity, not semantic acceptance."""
    assignments = result['themes']['assignments']
    by_position = {a['row_position']: a['theme_id'] for a in assignments}
    safe = build_safe_display_frame(frame[['comment_text']]).frame.comment_text.tolist()
    themes = result['themes']
    checks = {
        'input_rows_match': result['input_rows'] == result['questions']['input_rows'] == len(frame),
        'affect_rows_in_order': [r['row_position'] for r in result['affect']['rows']] == list(range(len(frame))),
        'unique_theme_assignments': len(by_position) == len(assignments) == themes['analyzed_comments'],
        'valid_theme_positions': all(0 <= i < len(frame) for i in by_position),
        'theme_totals': sum(t['count'] for t in themes['themes']) + themes['outlier_count'] == len(assignments),
        'timeline_theme_totals': sum(r['count'] for r in result['timeline']['theme_volumes']) == len(assignments),
        'timeline_affect_totals': sum(r['total_comments'] for r in result['timeline']['periods']) == len(frame),
        'theme_affect_totals': sum(r['total_comments'] for r in result['affect_by_theme']) == len(assignments),
        'canonical_date_used': result['timeline']['period_column'] == ('date_or_hearing' if 'date_or_hearing' in frame else None),
        'quotes_trace_to_theme_source': all(by_position.get(q['row_position']) == t['theme_id']
            and valid_source_quote(q, safe[q['row_position']])
            for t in themes['themes'] for q in t['quotes'] + t.get('quote_alternatives', [])),
        'suppressed_metrics_hidden': all(all(r[k] is None for k in
            ['count', 'participation_share', 'gap_percentage_points', 'representation_ratio'])
            for r in result['gaps']['rows'] if r['suppressed']),
    }
    checks.update({f'questions_{k}': v for k, v in validate_questions(result['questions'], frame).items()})
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cfpb-dir', type=Path, required=True)
    parser.add_argument('--federal-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error('Choose a new output folder; previous results must be preserved.')
    # Check existing public sample provenance before running analysis.
    load_sample(args.cfpb_dir)
    load_federal(args.federal_dir)
    root = Path(__file__).resolve().parents[1]
    args.output_dir.mkdir(parents=True, mode=0o700)
    response = args.output_dir / 'fictional-response.txt'
    response.write_text(json.loads((root / 'data/samples/synthetic_agency_responses.json').read_text())['response_text'])
    references = args.output_dir / 'fictional-references.json'
    references.write_text(json.dumps({k.removeprefix('subgroup__'): v for k, v in REFERENCES.items()}))
    inputs = {
        'synthetic': (root / 'data/samples/synthetic_theme_benchmark.csv', 'hearing_date', 'respondent_id',
                      ['role', 'housing_tenure']),
        'cfpb': (args.cfpb_dir / 'cfpb_sample.csv', 'date_received', 'complaint_id', []),
        'federal': (args.federal_dir / 'federal_sample.csv', 'hearing_date', 'source_id', []),
    }
    report = {'notice': 'Automated development validation only. Human theme/affect, spreadsheet, '
              '200-sentence question and top-three reviews remain pending. First analysis includes model '
              'load only for the first corpus; repeat runs reuse model weights but recompute outputs. '
              'Command-body timing includes loading/mapping, analysis, chart serialization and disk writes; '
              'it excludes process startup and imports already performed by this validator. '
              'The 30-second warm core benchmark is reported separately from the expanded full pipeline.',
              'cpu_threads': 4, 'corpora': {}}
    for name, (path, date, identifier, subgroups) in inputs.items():
        raw = load_table(path, preserve_text=True).frame
        frame = map_columns(raw, comment_column='comment_text', date_or_hearing_column=date,
                            respondent_id_column=identifier, subgroup_columns=subgroups).frame
        runs, manifests, elapsed = [], [], []
        for repeat in range(2):
            destination = args.output_dir / f'{name}-{repeat + 1}'
            arguments = [str(path), '--comment-column', 'comment_text', '--date-column', date,
                         '--id-column', identifier, '--output-dir', str(destination)]
            for subgroup in subgroups:
                arguments.extend(['--subgroup', subgroup])
            if name == 'synthetic':
                arguments.extend(['--references', str(references), '--agency-response', str(response)])
            start = perf_counter()
            manifest = run_all.run(run_all._parser().parse_args(arguments))
            elapsed.append(perf_counter() - start)
            manifests.append(manifest)
            runs.append(json.loads((destination / 'analysis.json').read_text()))
            assert all(hashlib.sha256((destination / file).read_bytes()).hexdigest() == digest
                       for file, digest in manifest['files'].items())
        result = runs[0]
        checks = check_result(result, frame)
        checks['repeat_identical'] = runs[0] == runs[1]
        if name == 'synthetic':
            independent = validate_gap_fixture(raw)
            checks['independent_gap_arithmetic'] = independent['all_checks_passed'] and result['gaps'] == independent['result']
        else:
            checks['missing_subgroups_explicit'] = result['gaps']['status'] == 'unavailable'
            checks['missing_response_explicit'] = result['questions']['response_status'] == 'not_provided'
        report['corpora'][name] = {'rows': len(frame), 'themes': len(result['themes']['themes']),
            'periods': len(result['timeline']['periods']), 'question_groups': len(result['questions']['groups']),
            'first_analysis_seconds': manifests[0]['analysis_seconds'],
            'repeat_analysis_seconds': manifests[1]['analysis_seconds'],
            'first_command_body_seconds': elapsed[0], 'repeat_command_body_seconds': elapsed[1],
            'checks': checks, 'all_checks_passed': all(checks.values()),
            'development_targets': {
                'five_to_fifteen_themes': 5 <= len(result['themes']['themes']) <= 15,
                'outliers_under_twenty_percent': result['themes']['outlier_share'] < .2,
                'three_quotes_each': all(len(t['quotes']) == 3 for t in result['themes']['themes']),
                'full_first_analysis_under_two_minutes': manifests[0]['analysis_seconds'] < 120,
                'full_repeat_analysis_under_thirty_seconds': manifests[1]['analysis_seconds'] < 30}}
        print(name, json.dumps(report['corpora'][name]), flush=True)
        (args.output_dir / 'full-validation.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    report['all_checks_passed'] = all(r['all_checks_passed'] for r in report['corpora'].values())
    (args.output_dir / 'full-validation.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    if not report['all_checks_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
