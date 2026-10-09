from copy import deepcopy
import json
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from scripts.prepare_fictional_review import build_packets, prepare, score_questions
from scripts.prepare_question_review import review_html


class FictionalReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = pd.DataFrame({'comment_text': ['When is the school meeting?', 'The school needs books.'] * 100})
        with patch('pipeline.questions._embed', side_effect=lambda texts: np.ones((len(texts), 3))):
            cls.packet = build_packets(cls.frame, 'The school meeting is next Monday.')

    def test_blank_review_is_blind_and_pending(self):
        manifest, review, predictions, priorities, status = self.packet
        self.assertEqual(len(review['rows']), 200)
        self.assertEqual(review['scope'], 'fictional_only')
        self.assertTrue(all(not r['human_question'] and not r['reviewer'] for r in review['rows']))
        self.assertNotIn('predicted_question', json.dumps(review))
        self.assertNotIn('response_match_status', json.dumps(priorities))
        self.assertNotIn('top_unanswered', priorities)
        self.assertFalse(priorities['review_complete'])
        self.assertIsNone(status['question_review']['acceptance_passed'])
        self.assertIsNone(status['priority_review']['acceptance_passed'])

    def test_wrong_scope_rejected(self):
        manifest, review, *_ = deepcopy(self.packet)
        review['scope'] = 'other'
        with self.assertRaises(ValueError): score_questions(review, manifest)

    def test_changed_source_and_changed_manifest_rejected(self):
        manifest, review, *_ = deepcopy(self.packet)
        review['rows'][0]['text'] = 'Changed'
        with self.assertRaises(ValueError): score_questions(review, manifest)
        manifest, review, *_ = deepcopy(self.packet)
        manifest['seed'] += 1
        with self.assertRaises(ValueError): score_questions(review, manifest)

    def test_partial_human_input_cannot_complete_review(self):
        manifest, review, *_ = deepcopy(self.packet)
        review['rows'][0].update(human_question='yes', reviewer='Unit test fixture')
        result = score_questions(review, manifest)
        self.assertEqual(result['human_labeled_rows'], 1)
        self.assertFalse(result['complete'])
        self.assertIsNone(result['acceptance_passed'])
        self.assertEqual(result['scope'], 'fictional_only')

    def test_missing_reviewer_rejected(self):
        manifest, review, *_ = deepcopy(self.packet)
        review['rows'][0]['human_question'] = 'yes'
        with self.assertRaises(ValueError): score_questions(review, manifest)

    def test_unit_fixture_labels_can_score_without_claiming_real_accuracy(self):
        manifest, review, *_ = deepcopy(self.packet)
        for row in review['rows']:
            row.update(human_question='yes' if row['text'].startswith('When') else 'no', reviewer='Unit test fixture')
        result = score_questions(review, manifest)
        self.assertTrue(result['complete'])
        self.assertTrue(result['acceptance_passed'])
        self.assertIn('does not establish accuracy on real community', result['notice'])

    def test_html_keeps_sample_scope_for_saved_answers_and_escapes_text(self):
        _, review, *_ = deepcopy(self.packet)
        review['rows'][0]['text'] = '</script><script>alert(1)</script>'
        html = review_html(review)
        self.assertNotIn('</script><script>alert', html)
        self.assertIn('fictional_only', html)

    def test_existing_destination_preserved(self):
        with tempfile.TemporaryDirectory() as temp, patch('scripts.prepare_fictional_review.load_table') as load:
            with self.assertRaises(ValueError): prepare(temp)
            load.assert_not_called()
