"""Prepare a local, blind review using fixed fictional school examples only."""
import argparse
import hashlib
import json
from pathlib import Path

from pipeline.ingest import load_table, map_columns
from pipeline.questions import mine_questions
from scripts.prepare_question_review import make_packet, fingerprint, review_html
from scripts.evaluate_question_review import evaluate
from scripts.validate_questions import make_priority_review
from scripts.evaluate_question_priorities import evaluate_priorities
from scripts.prepare_gap_spreadsheet import prepare as prepare_gap_input
from scripts.validate_fictional import SAMPLE, RESPONSE, NOTICE, write_json


def build_packets(frame, response):
    manifest, review = make_packet({'fictional_school_comments': frame}, size=200, seed=20261009)
    manifest['scope'] = 'fictional_only'
    manifest['sample_id'] = fingerprint({k: v for k, v in manifest.items() if k != 'sample_id'})
    review.update(sample_id=manifest['sample_id'], scope='fictional_only')
    questions = mine_questions(frame, agency_response=response)
    priorities = make_priority_review(questions, response)
    priorities['scope'] = 'fictional_only'
    status = {'scope': 'fictional_only', 'notice': NOTICE,
              'question_review': evaluate(review, manifest),
              'priority_review': evaluate_priorities(priorities, questions, response),
              'gap_hand_check': 'pending', 'earlier_theme_and_affect_review': 'pending'}
    return manifest, review, questions, priorities, status


def prepare(destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('Choose a new folder to preserve human answers.')
    raw = load_table(SAMPLE, preserve_text=True).frame
    frame = map_columns(raw, comment_column='comment_text', respondent_id_column='respondent_id',
                        subgroup_columns=['role', 'housing_tenure']).frame
    fixture = json.loads(RESPONSE.read_text())
    manifest, review, questions, priorities, status = build_packets(frame, fixture['response_text'])
    gap_input = prepare_gap_input(SAMPLE)
    destination.mkdir(parents=True, mode=0o700)
    for name, value in {'question-review-manifest.json': manifest, 'question-review.json': review,
                        'priority-review.json': priorities, 'priority-predictions.json': questions,
                        'response-fixture.json': fixture, 'review-status.json': status,
                        'gap-spreadsheet-input.json': gap_input}.items():
        write_json(destination / name, value)
    html = review_html(review).replace(
        'This local review has 200 sentences from the project’s fictional and public development samples. The detector’s answers are hidden.',
        'This local review has 200 sentence occurrences from fictional school comments. Repeated wording is possible. The detector’s answers are hidden. Results apply only to these fictional examples.')
    (destination / 'Hearing_Lens_Fictional_Question_Review.html').write_text(html, encoding='utf-8')
    lines = ['# Fictional question-priority review', '', NOTICE, '', priorities['instructions'], '',
             '## Fictional response', fixture['response_text'], '', '## Question groups', '']
    for group in priorities['groups']:
        spread = group['visible_subgroup_spread']
        lines += [f"### {group['question_group_id']}", group['question'], '',
                  f"Supporting comments: {group['comment_count']}. Visible field/category pairs: {spread}.", '']
    lines += ['## Your answers', 'Reviewer:', 'Up to three question IDs, in priority order:',
              'Or explicitly confirm that no questions remain unanswered.', '',
              'Make your independent choices before viewing priority-predictions.json. '
              'Then compare and explain any differing selections. No answer has been prefilled.']
    (destination / 'Fictional_Top_Three_Review.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    instructions = '''# Fictional review - start here

All examples in this packet are fictional. The software has not filled in human
answers. Completing this packet evaluates the fictional sample only.

1. Open Hearing_Lens_Fictional_Question_Review.html in a browser. Enter your name,
   label the 200 sentences Yes / No / Unsure and save your answers. You may pause
   and resume with the downloaded JSON. Resolve Unsure before the final check.
2. Read Fictional_Top_Three_Review.md. Choose up to three question IDs after reading
   the fictional response, before looking at the predictions. Send your choices
   and reviewer name, or enter them in priority-review.json and set review_complete.
3. Open the separately prepared fictional gap-check workbook. Use its Source groups
   sheet and formulas to check all eight groups, then enter your name and review date.
   A software Match result is not a human check. Keep any discrepancies in your notes.

Do not consult question-review-manifest.json or priority-predictions.json before
making independent judgments. They contain the software's predictions.

Earlier theme and sentiment/emotion review remains separate and pending. These
fictional examples do not establish accuracy on real community submissions.
'''
    (destination / 'START_HERE.md').write_text(instructions, encoding='utf-8')
    write_json(destination / 'packet-manifest.json', {
        'scope': 'fictional_only', 'source_sha256': hashlib.sha256(SAMPLE.read_bytes()).hexdigest(),
        'response_sha256': hashlib.sha256(RESPONSE.read_bytes()).hexdigest(),
        'sentence_pool': manifest['pool_sentences'], 'sample_rows': manifest['sample_size'],
        'unique_sample_wordings': len({r['text'] for r in review['rows']}),
        'priority_groups': len(priorities['groups']), 'gap_groups': len(gap_input['pipeline_rows']),
        'notice': NOTICE})
    return status


def score_questions(answers, manifest):
    if answers.get('scope') != 'fictional_only' or manifest.get('scope') != 'fictional_only':
        raise ValueError('Use answers and a manifest from the fictional review packet.')
    result = evaluate(answers, manifest)
    return {'scope': 'fictional_only', **result,
            'notice': result['notice'] + ' ' + NOTICE}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    build = actions.add_parser('prepare')
    build.add_argument('--output-dir', type=Path, required=True)
    score = actions.add_parser('score-questions')
    score.add_argument('--answers', type=Path, required=True)
    score.add_argument('--manifest', type=Path, required=True)
    score.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.action == 'prepare':
        status = prepare(args.output_dir)
        print(json.dumps({'scope': 'fictional_only', 'question_rows': status['question_review']['sample_rows'],
                          'human_labeled_rows': status['question_review']['human_labeled_rows'],
                          'human_validation': 'pending'}))
    else:
        result = score_questions(json.loads(args.answers.read_text()), json.loads(args.manifest.read_text()))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.output, result)
        print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
