"""Reproduce complete-workflow checks using only explicitly fictional fixtures."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

import run_all
from pipeline.ingest import load_table, map_columns
from pipeline.quotes import valid_source_quote
from pipeline.redact import build_safe_display_frame
from scripts.validate_gaps import REFERENCES, run as independent_gaps

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / 'data/samples/synthetic_theme_benchmark.csv'
RESPONSE = ROOT / 'data/samples/synthetic_agency_responses.json'
NOTICE = ('Fictional examples only, for development. Passing these checks does not establish '
          'accuracy on real community submissions or replace independent human review.')


def cases():
    """Fixed fixture paths and authored rows; no external-data input option."""
    raw = load_table(SAMPLE, preserve_text=True).frame
    response = json.loads(RESPONSE.read_text())['response_text']
    reference = {key.removeprefix('subgroup__'): value for key, value in REFERENCES.items()}
    question = 'When will the school repair the leaking roof and replace the broken library windows?'
    statement = 'The library needs working lights and more books so children can read comfortably after class.'
    edge = pd.DataFrame({'comment_text': [question, 'Duplicate submission.', '', statement,
                                         'Students need safe transport to attend their classes regularly.'],
                         'respondent_id': ['001', '001', '', '002', '003'],
                         'hearing_date': ['Session one', '', '', '', 'Session two'],
                         'role': ['Parent', 'Parent', '', 'Teacher', 'Student']})
    small = pd.DataFrame({'comment_text': [question] * 31,
                          'role': ['Parent'] * 20 + ['Teacher'] * 10 + ['Student']})
    return {
        'school_benchmark': {'frame': raw, 'date': 'hearing_date', 'id': 'respondent_id',
            'subgroups': ['role', 'housing_tenure'], 'references': reference, 'response': response},
        'missing_optional': {'frame': raw[['comment_text']].head(24).copy(), 'subgroups': []},
        'cleaning_and_labels': {'frame': edge, 'date': 'hearing_date', 'id': 'respondent_id', 'subgroups': ['role']},
        'small_groups': {'frame': small, 'subgroups': ['role'],
            'references': {'role': {'Parent': '60%', 'Teacher': '30%', 'Student': '10%'}}},
        'statements_only': {'frame': pd.DataFrame({'comment_text': [statement] * 24, 'role': [''] * 24}),
            'subgroups': ['role'], 'response': ''},
    }


def check_result(result, frame):
    """Check row accounting, protected metrics and redacted source traces."""
    themes, affect, questions = result['themes'], result['affect'], result['questions']
    assignments = themes['assignments']
    membership = {a['row_position']: a['theme_id'] for a in assignments}
    safe = build_safe_display_frame(frame[['comment_text']]).frame.comment_text.tolist()
    n = len(frame)
    qgroups = {g['question_group_id']: g for g in questions['groups']}
    qa = questions['assignments']
    counts = [0] * n
    valid_question_positions = all(type(a['row_position']) is int and 0 <= a['row_position'] < n for a in qa)
    if valid_question_positions:
        for assignment in qa:
            counts[assignment['row_position']] += 1
    def source_matches(quote):
        position = quote['row_position']
        return (type(position) is int and 0 <= position < n and
                0 <= quote['source_start'] <= quote['source_end'] <= len(safe[position]) and
                quote['text'] == safe[position][quote['source_start']:quote['source_end']])
    return {
        'row_totals': result['input_rows'] == questions['input_rows'] == n,
        'affect_positions': [r['row_position'] for r in affect['rows']] == list(range(n)),
        'theme_membership': len(membership) == len(assignments) == themes['analyzed_comments']
            and all(type(i) is int and 0 <= i < n for i in membership),
        'theme_counts': sum(t['count'] for t in themes['themes']) + themes['outlier_count'] == len(assignments),
        'timeline_counts': sum(r['count'] for r in result['timeline']['theme_volumes']) == len(assignments)
            and sum(r['total_comments'] for r in result['timeline']['periods']) == n,
        'theme_affect_counts': sum(r['total_comments'] for r in result['affect_by_theme']) == len(assignments),
        'quote_sources': all(type(q['row_position']) is int and 0 <= q['row_position'] < n
            and membership.get(q['row_position']) == t['theme_id'] and valid_source_quote(q, safe[q['row_position']])
            for t in themes['themes'] for q in t['quotes'] + t.get('quote_alternatives', [])),
        'question_positions': valid_question_positions and len(qa) == len({(a['row_position'], a['sentence_index']) for a in qa}),
        'question_counts': counts == questions['comment_question_counts'] and len(qa) == questions['question_count'],
        'question_groups': len(qgroups) == len(questions['groups']) and all(a['question_group_id'] in qgroups for a in qa),
        'question_sources': all(source_matches(g['representative']) for g in qgroups.values()),
        'question_frequencies': all(g['comment_count'] == len({a['row_position'] for a in qa if a['question_group_id'] == key})
            and g['sentence_count'] == sum(a['question_group_id'] == key for a in qa) for key, g in qgroups.items()),
        'priority_selection': questions['top_unanswered'] == [g['question_group_id'] for g in questions['groups']
                                                           if g['response_match_status'] != 'possible_match'][:3],
        'suppressed_metrics': all(all(row[k] is None for k in ['count', 'participation_share',
            'gap_percentage_points', 'representation_ratio']) for row in result['gaps']['rows'] if row['suppressed']),
    }


def scenario_checks(name, result, raw):
    if name == 'school_benchmark':
        comparison = independent_gaps(raw)
        return {'independent_arithmetic': comparison['all_checks_passed'] and result['gaps'] == comparison['result'],
                'three_dates': result['timeline']['mode'] == 'date' and len(result['timeline']['periods']) == 3}
    if name == 'missing_optional':
        return {'single_period': result['timeline']['mode'] == 'single_period',
                'gaps_unavailable': result['gaps']['status'] == 'unavailable',
                'response_unavailable': result['questions']['response_status'] == 'not_provided'}
    if name == 'cleaning_and_labels':
        cleaning = result['ingestion']
        return {'cleaned_three_rows': result['input_rows'] == 3 and cleaning['empty_comments_removed'] == 1
                and cleaning['duplicate_respondents_removed'] == 1,
                'hearing_labels_retained': result['timeline']['mode'] == 'hearing_label'
                and {p['group'] for p in result['timeline']['periods']} == {'Session one', 'Session two', 'Missing period'}}
    if name == 'small_groups':
        rows = {r['group']: r for r in result['gaps']['rows']}
        return {'small_group_hidden': rows['Student']['suppressed'] and rows['Student']['count'] is None,
                'complement_hidden': rows['Teacher']['suppression_reason'] == 'complementary',
                'visible_count': rows['Parent']['count'] == 20}
    if name == 'statements_only':
        return {'no_questions': result['questions']['status'] == 'no_questions' and not result['questions']['top_unanswered'],
                'blank_response': result['questions']['response_status'] == 'empty',
                'blank_groups': result['gaps']['status'] == 'unavailable'}
    raise ValueError('Unknown fictional scenario.')


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def validate(destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('Choose a new folder to preserve previous results.')
    scenarios = cases()
    destination.mkdir(parents=True, mode=0o700)
    report = {'scope': 'fictional_only', 'notice': NOTICE, 'cpu_threads': 4,
              'source_sha256': hashlib.sha256(SAMPLE.read_bytes()).hexdigest(),
              'response_sha256': hashlib.sha256(RESPONSE.read_bytes()).hexdigest(),
              'timing_scope': 'Analysis only, four CPU threads. First benchmark includes model loading; '
              'other runs reuse model weights but recompute results. Loading, exports and process startup excluded.',
              'scenarios': {}}
    for name, case in scenarios.items():
        source = destination / f'{name}.csv'
        case['frame'].to_csv(source, index=False)
        base = [str(source), '--comment-column', 'comment_text']
        for key, flag in [('date', '--date-column'), ('id', '--id-column')]:
            if key in case:
                base.extend([flag, case[key]])
        for field in case['subgroups']:
            base.extend(['--subgroup', field])
        if 'references' in case:
            path = destination / f'{name}-references.json'
            write_json(path, case['references']); base.extend(['--references', str(path)])
        if 'response' in case:
            path = destination / f'{name}-response.txt'
            path.write_text(case['response'], encoding='utf-8'); base.extend(['--agency-response', str(path)])
        frame = map_columns(case['frame'], comment_column='comment_text', date_or_hearing_column=case.get('date'),
                            respondent_id_column=case.get('id'), subgroup_columns=case['subgroups']).frame
        results, seconds, hashes_ok = [], [], True
        for repeat in range(2):
            output = destination / f'{name}-run-{repeat + 1}'
            manifest = run_all.run(run_all._parser().parse_args(base + ['--output-dir', str(output)]))
            results.append(json.loads((output / 'analysis.json').read_text()))
            seconds.append(manifest['analysis_seconds'])
            hashes_ok &= all(hashlib.sha256((output / file).read_bytes()).hexdigest() == digest
                             for file, digest in manifest['files'].items())
        result = results[0]
        checks = {**check_result(result, frame), **scenario_checks(name, result, case['frame']),
                  'repeated_json_identical': results[0] == results[1], 'export_hashes': hashes_ok}
        # Small edge cases deliberately do not aim for 5-15 themes or three quotes.
        targets = None
        if name == 'school_benchmark':
            targets = {'five_to_fifteen_themes': 5 <= len(result['themes']['themes']) <= 15,
                       'outliers_under_twenty_percent': result['themes']['outlier_share'] < .2,
                       'three_quotes_each': bool(result['themes']['themes']) and all(len(t['quotes']) == 3 for t in result['themes']['themes']),
                       'first_under_two_minutes': seconds[0] < 120, 'repeat_under_thirty_seconds': seconds[1] < 30}
        report['scenarios'][name] = {'input_rows': len(case['frame']), 'cleaned_rows': len(frame),
            'first_analysis_seconds': seconds[0], 'repeat_analysis_seconds': seconds[1],
            'themes': len(result['themes']['themes']), 'question_groups': len(result['questions']['groups']),
            'checks': checks, 'all_checks_passed': all(checks.values()), 'benchmark_targets': targets}
        print(name, json.dumps(report['scenarios'][name]), flush=True)
    report['all_checks_passed'] = all(s['all_checks_passed'] for s in report['scenarios'].values())
    report['benchmark_targets_passed'] = all(report['scenarios']['school_benchmark']['benchmark_targets'].values())
    report['human_validation'] = 'pending'
    write_json(destination / 'fictional-validation.json', report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    report = validate(args.output_dir)
    return 0 if report['all_checks_passed'] and report['benchmark_targets_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
