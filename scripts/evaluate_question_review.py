"""Score genuine human question labels against a frozen development sample."""
import argparse
import json
from pathlib import Path

from scripts.prepare_question_review import fingerprint


def evaluate(review, manifest):
    payload = {k: v for k, v in manifest.items() if k != 'sample_id'}
    if (manifest.get('sample_id') != fingerprint(payload)
            or review.get('sample_id') != manifest['sample_id']
            or review.get('schema_version') != 1 or manifest.get('schema_version') != 1):
        raise ValueError('Review sample fingerprint or schema does not match.')
    expected = {row['review_id']: row for row in manifest['rows']}
    rows = review.get('rows', [])
    if (len(expected) != manifest['sample_size'] or len(rows) != len(expected)
            or len({row['review_id'] for row in rows}) != len(rows)):
        raise ValueError('Review rows are missing or duplicated.')
    counts = {'true_positive': 0, 'false_positive': 0, 'true_negative': 0, 'false_negative': 0}
    unanswered = unsure = 0
    for row in rows:
        source = expected.get(row['review_id'])
        if source is None or any(row.get(k) != v for k, v in source.items() if k != 'predicted_question'):
            raise ValueError('Review source text, position or fingerprint has changed.')
        if type(source['predicted_question']) is not bool:
            raise ValueError('Prediction must be a boolean.')
        label = row.get('human_question', '')
        if label not in ('', 'yes', 'no', 'unsure'):
            raise ValueError('Human labels must be yes, no, unsure, or blank.')
        if label and (not isinstance(row.get('reviewer'), str) or not row['reviewer'].strip()):
            raise ValueError('Labeled rows need the human reviewer name.')
        if not label:
            unanswered += 1
        elif label == 'unsure':
            unsure += 1
        else:
            human, predicted = label == 'yes', source['predicted_question']
            key = ('true_positive' if predicted else 'false_negative') if human else (
                'false_positive' if predicted else 'true_negative')
            counts[key] += 1
    positive = counts['true_positive'] + counts['false_negative']
    negative = counts['true_negative'] + counts['false_positive']
    recall = counts['true_positive'] / positive if positive else None
    fpr = counts['false_positive'] / negative if negative else None
    complete = len(rows) == 200 and unanswered == 0 and unsure == 0
    measured = complete and recall is not None and fpr is not None
    return {'sample_id': manifest['sample_id'], 'detector_version': manifest['detector_version'],
            'required_rows': 200, 'sample_rows': len(rows), 'human_labeled_rows': positive + negative,
            'blank_rows': unanswered, 'unsure_rows': unsure, 'confusion': counts,
            'recall': recall, 'false_positive_rate': fpr, 'complete': complete,
            'acceptance_passed': (recall >= .8 and fpr < .1) if measured else None,
            'status': 'evaluated' if measured else 'pending_human_validation',
            'notice': 'Recall = TP/(TP+FN); false-positive rate = FP/(FP+TN). '
                      'Partial rates are provisional. Acceptance requires 200 resolved human labels '
                      'and both classes. Reviewer identity is self-reported, not independently authenticated.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; choose another file to preserve earlier results.')
    result = evaluate(json.loads(args.review.read_text()), json.loads(args.manifest.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as handle:
        handle.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
