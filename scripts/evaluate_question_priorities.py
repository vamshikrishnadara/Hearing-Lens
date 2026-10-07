"""Compare a genuine independent review with the fictional top-three result."""
import argparse
import json
from pathlib import Path

from scripts.validate_questions import make_priority_review


def evaluate_priorities(review, result, response):
    expected=make_priority_review(result,response)
    if any(review.get(key)!=expected[key] for key in ['sample_id','response_text','groups']):
        raise ValueError('Review source questions or response have changed.')
    ids=review.get('selected_group_ids',[])
    known={g['question_group_id'] for g in result['groups']}
    if (not isinstance(ids,list) or any(not isinstance(i,str) for i in ids)
            or len(set(ids))!=len(ids) or len(ids)>3 or any(i not in known for i in ids)):
        raise ValueError('Choose at most three distinct question IDs from this review.')
    complete=review.get('review_complete',False)
    none=review.get('no_unanswered_questions',False)
    if type(complete) is not bool or type(none) is not bool or (none and ids):
        raise ValueError('Use explicit review-complete/no-unanswered flags without contradictory selections.')
    report={'sample_id':expected['sample_id'],'human_review_complete':complete,
            'status':'pending_human_review','selection_matches':None,'acceptance_passed':None}
    if not complete:
        return report
    if not isinstance(review.get('reviewer'),str) or not review['reviewer'].strip():
        raise ValueError('A completed review needs the human reviewer name.')
    if not ids and not none:
        raise ValueError('Choose questions or explicitly confirm none remain unanswered.')
    automated=result['top_unanswered']
    matches=ids==automated
    differing=set(ids)^set(automated)
    if not differing and not matches:
        differing={i for position,i in enumerate(ids) if i!=automated[position]}
    explanations=review.get('difference_explanations',{})
    if not isinstance(explanations,dict):
        raise ValueError('Provide explanations keyed by question ID.')
    explained=all(isinstance(explanations.get(i),str) and bool(explanations[i].strip())
                  and len(explanations[i].strip())<=500 and '\n' not in explanations[i].strip()
                  for i in differing)
    report.update(status='matched' if matches else 'explained_difference' if explained else 'needs_explanations',
                  reviewer=review['reviewer'].strip(),human_selection=ids,automated_selection=automated,
                  selection_matches=matches,differing_ids=sorted(differing),
                  acceptance_passed=matches or explained,
                  notice='Human judgments and explanations are self-reported. This does not measure question-detector recall or authenticate reviewer identity.')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',type=Path,required=True)
    parser.add_argument('--result',type=Path,required=True)
    parser.add_argument('--response-fixture',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('Output exists; preserve the earlier review result.')
    report=evaluate_priorities(json.loads(args.review.read_text()),json.loads(args.result.read_text()),
                               json.loads(args.response_fixture.read_text())['response_text'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as handle:handle.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
