"""Run question mining on fixed local development corpora; write outside Git.

Results and review packets can contain redacted public text. No human labels,
independent reviewer picks or real agency-response matches are invented.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from time import perf_counter

import pandas as pd
import torch

from pipeline.ingest import map_columns
from pipeline.questions import mine_questions
from pipeline.redact import build_safe_display_frame
from scripts.validate_cfpb_themes import load_sample
from scripts.validate_core import load_federal


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def validate_result(result, frame):
    """Verify membership/counts/ranking/source spans without judging meaning."""
    safe = build_safe_display_frame(frame[['comment_text']]).frame.comment_text.tolist()
    groups = {g['question_group_id']: g for g in result['groups']}
    assignments = result['assignments']
    positions = {(a['row_position'], a['sentence_index']) for a in assignments}
    checks = {'all_candidates_assigned_once': len(assignments) == len(positions) == result['question_count'],
              'known_group_ids': all(a['question_group_id'] in groups for a in assignments),
              'per_comment_totals': sum(result['comment_question_counts']) == result['question_count'],
              'source_representatives': all(g['representative']['text'] ==
                  safe[g['representative']['row_position']][g['representative']['source_start']:g['representative']['source_end']]
                  for g in groups.values()),
              'frequency_counts': all(g['comment_count'] == len({a['row_position'] for a in assignments if a['question_group_id'] == key})
                                      for key,g in groups.items()),
              'sentence_counts': all(g['sentence_count'] == sum(a['question_group_id'] == key for a in assignments)
                                     for key,g in groups.items()),
              'top_three_from_eligible_ranked_groups': result['top_unanswered'] ==
                  [g['question_group_id'] for g in result['groups'] if g['response_match_status'] != 'possible_match'][:3]}
    return checks


def run_corpus(frame, response=None):
    start=perf_counter(); result=mine_questions(frame, agency_response=response); first=perf_counter()-start
    start=perf_counter(); repeat=mine_questions(frame, agency_response=response); repeated=perf_counter()-start
    checks=validate_result(result,frame)
    checks['repeat_identical']=result==repeat
    return result, {'input_rows':len(frame),'sentences':result['sentence_count'],
                   'candidate_sentences':result['question_count'],'groups':len(result['groups']),
                   'first_seconds':first,'repeat_seconds':repeated,
                   'response_status':result['response_status'],
                   'match_status_counts':dict(Counter(g['response_match_status'] for g in result['groups'])),
                   'top_three_count':len(result['top_unanswered']),'checks':checks,
                   'all_checks_passed':all(checks.values()),'human_top_three_review':'pending'}


def check_paraphrases():
    """Small authored wording pairs, not human or held-out quality evidence."""
    texts=['When will the public hearing start?', 'What time does the public hearing begin?',
           'How much money is allocated to the school bus service?', 'What is the school bus service budget?',
           'How can residents request a wheelchair-accessible entrance?',
           'How do residents ask for an entrance that is accessible to wheelchairs?']
    result=mine_questions(pd.DataFrame({'comment_text':texts}))
    members={g['question_group_id']:sorted(a['row_position'] for a in result['assignments'] if a['question_group_id']==g['question_group_id'])
             for g in result['groups']}
    expected=[[0,1],[2,3],[4,5]]
    return {'notice':'Authored fictional paraphrase examples; not a human accuracy measurement.',
            'texts':texts,'expected_pairs':expected,'actual_groups':sorted(members.values()),
            'passed':sorted(members.values())==expected}


def make_priority_review(result, response):
    # Hide algorithm picks/ranks/match guesses from the independent reviewer.
    groups = [{'question_group_id':g['question_group_id'],'question':g['representative']['text'],
               'comment_count':g['comment_count'],'visible_subgroup_spread':g['subgroup_spread'],
               'spread_is_lower_bound':g['spread_is_lower_bound']} for g in result['groups']]
    groups.sort(key=lambda g:g['question_group_id'])
    source={'response_text':response,'groups':groups}
    return {'sample_id':fingerprint(source), **source, 'reviewer':'', 'selected_group_ids':[],
            'no_unanswered_questions':False,'review_complete':False,'difference_explanations':{},
            'instructions':'Read the fictional response and choose up to three questions still needing an answer. '
                           'Prioritize comment frequency, then visible subgroup spread. Do not consult the algorithm result first. '
                           'If none remain, explicitly mark no_unanswered_questions true. Set review_complete only after '
                           'checking every group. Human review is pending.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cfpb-dir',type=Path,required=True)
    parser.add_argument('--federal-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.output_dir.exists():
        parser.error('Output directory exists; choose a new folder to preserve review work.')
    torch.set_num_threads(4)
    root=Path(__file__).resolve().parents[1]
    raw=pd.read_csv(root/'data/samples/synthetic_theme_benchmark.csv',dtype=str,keep_default_na=False)
    mapped=map_columns(raw,comment_column='comment_text',respondent_id_column='respondent_id',
                       subgroup_columns=['role','housing_tenure']).frame
    fixture=json.loads((root/'data/samples/synthetic_agency_responses.json').read_text())
    corpora={'synthetic':mapped,'cfpb':load_sample(args.cfpb_dir)[0],
             'federal':load_federal(args.federal_dir)[0]}
    args.output_dir.mkdir(parents=True)
    summaries={}
    for name,frame in corpora.items():
        response=fixture['response_text'] if name=='synthetic' else None
        result,summary=run_corpus(frame,response)
        summaries[name]=summary
        (args.output_dir/f'{name}-questions.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        if name=='synthetic':
            review=make_priority_review(result,response)
            (args.output_dir/'top-three-human-review.json').write_text(json.dumps(review,indent=2)+'\n')
            lines=['# Fictional question-priority review','',fixture['notice'],'',review['instructions'],'',
                   '## Supplied fictional response','',response,'','## Questions (algorithm picks hidden)','']
            for group in review['groups']:
                lines.extend([f"### {group['question_group_id']}",group['question'],'',
                              f"Comments: {group['comment_count']}; visible field/category pairs: {group['visible_subgroup_spread']}.", ''])
            lines.extend(['## Your review','Reviewer:','Top three question IDs:',
                          'Or confirm that no questions remain unanswered.','',
                          'After comparing with the algorithm, explain each differing selection in one sentence.'])
            (args.output_dir/'Top_Three_Question_Review.md').write_text('\n'.join(lines)+'\n')
            # Fixture expectation uses authored synthetic theme labels, not human
            # assessment. It is a sensitivity diagnostic, never acceptance proof.
            calibration=[]
            for threshold in [.55,.6,.65,.7]:
                trial=mine_questions(frame,agency_response=response,response_threshold=threshold)
                expected={g['question_group_id']:all(raw.iloc[a['row_position']]['validation_theme'] in fixture['intended_answered_themes']
                           for a in trial['assignments'] if a['question_group_id']==g['question_group_id']) for g in trial['groups']}
                calibration.append({'response_threshold':threshold,'groups':len(trial['groups']),
                                    'matches_authored_expectation':sum((g['response_match_status']=='possible_match')==expected[g['question_group_id']] for g in trial['groups']),
                                    'top_unanswered':trial['top_unanswered']})
            (args.output_dir/'synthetic-response-thresholds.json').write_text(json.dumps({'notice':'Fictional authored expectations, not human labels or held-out accuracy.', 'trials':calibration},indent=2)+'\n')
    paraphrases=check_paraphrases()
    (args.output_dir/'paraphrase-check.json').write_text(json.dumps(paraphrases,indent=2)+'\n')
    report={'notice':'Local four-thread development run. First synthetic run includes embedding-model load; subsequent corpora reuse the model. All repeats recompute. No human acceptance is claimed.',
            'corpora':summaries,'paraphrase_check_passed':paraphrases['passed'],
            'all_checks_passed':all(s['all_checks_passed'] for s in summaries.values()) and paraphrases['passed']}
    (args.output_dir/'question-validation.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report,indent=2))
    if not report['all_checks_passed']:raise SystemExit(1)


if __name__=='__main__':main()
