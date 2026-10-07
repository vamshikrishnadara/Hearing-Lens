import copy
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from pipeline.questions import mine_questions
from scripts.validate_questions import validate_result, make_priority_review
from scripts.evaluate_question_priorities import evaluate_priorities


class QuestionValidationTests(unittest.TestCase):
    def setUp(self):
        self.frame=pd.DataFrame({'comment_text':['Why A?']*4+['Why B?']*3+['Why C?']*2+['Why D?']})
        with patch('pipeline.questions._embed',return_value=np.eye(4)):
            self.result=mine_questions(self.frame)
        self.review=make_priority_review(self.result,'Fictional response.')

    def test_structural_checks_detect_bad_counts_and_source_spans(self):
        self.assertTrue(all(validate_result(self.result,self.frame).values()))
        changed=copy.deepcopy(self.result)
        changed['groups'][0]['comment_count']=100
        changed['groups'][0]['representative']['source_start']=99
        checks=validate_result(changed,self.frame)
        self.assertFalse(checks['frequency_counts'])
        self.assertFalse(checks['source_representatives'])

    def test_blind_packet_and_blank_review_never_claim_acceptance(self):
        self.assertNotIn('top_unanswered',self.review)
        self.assertNotIn('response_match_status',str(self.review))
        result=evaluate_priorities(self.review,self.result,'Fictional response.')
        self.assertIsNone(result['acceptance_passed'])
        self.assertFalse(result['human_review_complete'])

    def completed(self):
        review=copy.deepcopy(self.review)
        review.update(reviewer='Fictional test reviewer',review_complete=True,
                      selected_group_ids=self.result['top_unanswered'].copy())
        return review

    def test_matching_completed_review(self):
        result=evaluate_priorities(self.completed(),self.result,'Fictional response.')
        self.assertEqual(result['status'],'matched')
        self.assertTrue(result['acceptance_passed'])

    def test_differences_need_written_explanations(self):
        review=self.completed();review['selected_group_ids'][-1]='q004'
        result=evaluate_priorities(review,self.result,'Fictional response.')
        self.assertFalse(result['acceptance_passed'])
        for i in result['differing_ids']:review['difference_explanations'][i]='Fictional reviewer disagrees with the response interpretation.'
        self.assertTrue(evaluate_priorities(review,self.result,'Fictional response.')['acceptance_passed'])

    def test_reordered_picks_need_explanations_too(self):
        review=self.completed();review['selected_group_ids'].reverse()
        self.assertEqual(evaluate_priorities(review,self.result,'Fictional response.')['status'],'needs_explanations')

    def test_invalid_stale_duplicate_and_unattributed_reviews_rejected(self):
        for key,value in [('sample_id','stale'),('selected_group_ids',['q001','q001']),('selected_group_ids',['missing']),
                          ('reviewer',''),('review_complete','yes'),('no_unanswered_questions',True)]:
            review=self.completed();review[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):evaluate_priorities(review,self.result,'Fictional response.')

    def test_no_questions_requires_explicit_human_confirmation(self):
        result={'groups':[],'top_unanswered':[]};review=make_priority_review(result,'')
        self.assertIsNone(evaluate_priorities(review,result,'')['acceptance_passed'])
        review.update(review_complete=True,reviewer='Fictional test reviewer')
        with self.assertRaises(ValueError):evaluate_priorities(review,result,'')
        review['no_unanswered_questions']=True
        self.assertTrue(evaluate_priorities(review,result,'')['acceptance_passed'])
