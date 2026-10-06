import copy
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.prepare_question_review import make_packet, fingerprint, review_html, write_packet
from scripts.evaluate_question_review import evaluate


class QuestionReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.review = make_packet({'fictional': pd.DataFrame({'comment_text':
            ['When is the hearing?', 'The hearing ended.'] * 110})})

    def test_blind_reproducible_sample_keeps_both_classes_and_blank_labels(self):
        manifest, review = make_packet({'fictional': pd.DataFrame({'comment_text':
            ['When is the hearing?', 'The hearing ended.'] * 110})})
        self.assertEqual((manifest, review), (self.manifest, self.review))
        self.assertEqual(len(review['rows']), 200)
        self.assertEqual({r['predicted_question'] for r in manifest['rows']}, {True, False})
        self.assertTrue(all(not r['human_question'] and 'predicted_question' not in r and 'reasons' not in r for r in review['rows']))

    def test_blank_review_has_no_accuracy_claim(self):
        result = evaluate(self.review, self.manifest)
        self.assertEqual(result['human_labeled_rows'], 0)
        self.assertIsNone(result['recall'])
        self.assertIsNone(result['false_positive_rate'])
        self.assertIsNone(result['acceptance_passed'])

    def test_metrics_and_strict_false_positive_boundary(self):
        manifest = copy.deepcopy(self.manifest)
        for i, row in enumerate(manifest['rows']):
            row['predicted_question'] = i < 80 or 100 <= i < 110
        manifest['sample_id'] = fingerprint({k:v for k,v in manifest.items() if k != 'sample_id'})
        review = copy.deepcopy(self.review); review['sample_id'] = manifest['sample_id']
        for i, row in enumerate(review['rows']):
            row.update(human_question='yes' if i < 100 else 'no', reviewer='Fictional test reviewer')
        result = evaluate(review, manifest)
        self.assertEqual(result['recall'], .8)
        self.assertEqual(result['false_positive_rate'], .1)
        self.assertFalse(result['acceptance_passed'])
        review['rows'][109]['human_question'] = 'yes'
        result = evaluate(review, manifest)
        self.assertTrue(result['acceptance_passed'])

    def test_incomplete_unsure_and_missing_class_do_not_pass(self):
        for label in ['', 'unsure', 'yes']:
            review = copy.deepcopy(self.review)
            for row in review['rows']:
                row.update(human_question=label, reviewer='Fictional test reviewer')
            result = evaluate(review, self.manifest)
            self.assertIsNone(result['acceptance_passed'])

    def test_stale_edited_duplicate_or_unattributed_labels_rejected(self):
        for key, value in [('text','Changed'), ('source_start', -1), ('text_sha256','bad'),
                           ('human_question','maybe'), ('human_question','yes')]:
            review=copy.deepcopy(self.review); review['rows'][0][key]=value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                evaluate(review,self.manifest)
        review=copy.deepcopy(self.review);review['rows'][1]=review['rows'][0]
        with self.assertRaises(ValueError):evaluate(review,self.manifest)
        manifest=copy.deepcopy(self.manifest);manifest['rows'][0]['predicted_question']=False
        manifest['seed']=-1
        with self.assertRaises(ValueError):evaluate(self.review,manifest)

    def test_source_punctuation_is_escaped_in_html_not_executed(self):
        review=copy.deepcopy(self.review);review['rows'][0]['text']='</script><script>alert(1)</script>'
        html=review_html(review)
        self.assertNotIn('</script><script>alert(1)',html)
        self.assertIn('\\u003c/script\\u003e',html)
        self.assertNotIn('predicted_question',html)

    def test_existing_review_files_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            write_packet(folder,self.manifest,self.review)
            target=Path(folder)/'question-review.json';target.write_text('Human work')
            with self.assertRaises(ValueError):write_packet(folder,self.manifest,self.review)
            self.assertEqual(target.read_text(),'Human work')

    def test_small_pool_rejected_instead_of_inventing_sentences(self):
        with self.assertRaises(ValueError):
            make_packet({'fictional':pd.DataFrame({'comment_text':['One statement.']})})
