import json
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from pipeline.questions import mine_questions, QuestionError


class QuestionMatchingTests(unittest.TestCase):
    def frame(self):return pd.DataFrame({'comment_text':['When is the hearing?']})

    def test_matching_response_has_redacted_traceable_excerpt(self):
        with patch('pipeline.questions._embed',side_effect=[np.array([[1.,0.]]),np.array([[1.,0.]])]) as embed:
            result=mine_questions(self.frame(),agency_response='The hearing is tomorrow; email secret@example.com for details.')
        group=result['groups'][0]
        self.assertEqual(group['response_match_status'],'possible_match')
        self.assertEqual(result['top_unanswered'],[])
        self.assertNotIn('secret@example.com',json.dumps(result))
        response=group['response_matches'][0]['response']
        self.assertEqual(response['text'],embed.call_args_list[1].args[0][0])
        self.assertGreater(response['source_end'],response['source_start'])

    def test_unrelated_response_leaves_question_eligible(self):
        with patch('pipeline.questions._embed',side_effect=[np.array([[1.,0.]]),np.array([[0.,1.]])]):
            result=mine_questions(self.frame(),agency_response='The budget was approved.')
        self.assertEqual(result['groups'][0]['response_match_status'],'no_match')
        self.assertEqual(result['top_unanswered'],['q001'])
        self.assertIsNone(result['groups'][0]['response_matches'][0]['response'])

    def test_partial_cluster_match_does_not_hide_unmatched_wording(self):
        frame=pd.DataFrame({'comment_text':['Can A happen?', 'Can B happen?']})
        with patch('pipeline.questions._embed',side_effect=[np.array([[1.,0.],[.8,.6]]),np.array([[1.,0.]])]):
            result=mine_questions(frame,agency_response='A will happen.',response_threshold=.9)
        self.assertEqual(len(result['groups']),1)
        group=result['groups'][0]
        self.assertEqual(group['response_match_status'],'partial_match')
        self.assertEqual(group['matched_wordings'],1)
        self.assertEqual(result['top_unanswered'],[group['question_group_id']])

    def test_no_response_is_not_a_claim_of_unanswered(self):
        for response,status in [(None,'not_provided'),('  ','empty'),('123 !!!','empty')]:
            with patch('pipeline.questions._embed',return_value=np.array([[1.,0.]])):
                result=mine_questions(self.frame(),agency_response=response)
            self.assertEqual(result['response_status'],status)
            self.assertEqual(result['selection_status'],'response_unavailable')
            self.assertEqual(result['groups'][0]['response_match_status'],'not_checked')
            self.assertIsNone(result['groups'][0]['matched_wordings'])

    def test_inclusive_match_threshold(self):
        with patch('pipeline.questions._embed',side_effect=[np.array([[.6,.8]]),np.array([[1.,0.]])]):
            result=mine_questions(self.frame(),agency_response='A response.',response_threshold=.6)
        self.assertEqual(result['groups'][0]['response_match_status'],'possible_match')

    def test_top_three_obey_ranking_and_never_fabricate_questions(self):
        frame=pd.DataFrame({'comment_text':['Why A?']*4+['Why B?']*3+['Why C?']*2+['Why D?']})
        with patch('pipeline.questions._embed',return_value=np.eye(4)):
            result=mine_questions(frame)
        self.assertEqual(result['top_unanswered'],[g['question_group_id'] for g in result['groups'][:3]])
        self.assertEqual([g['comment_count'] for g in result['groups']],[4,3,2,1])
        with patch('pipeline.questions._embed',return_value=np.array([[1.,0.]])):
            result=mine_questions(self.frame())
        self.assertEqual(len(result['top_unanswered']),1)

    def test_no_questions_no_response_embeddings(self):
        with patch('pipeline.questions._embed') as embed:
            result=mine_questions(pd.DataFrame({'comment_text':['The hearing ended.']}),agency_response='The budget is approved.')
        embed.assert_not_called();self.assertEqual(result['top_unanswered'],[])
        self.assertEqual(result['selection_status'],'no_questions')

    def test_invalid_response_types_thresholds_and_resource_limits(self):
        for kwargs in [{'agency_response':[]},{'response_threshold':True},{'response_threshold':float('inf')},
                       {'response_threshold':-1},{'response_threshold':1.1}]:
            with self.subTest(kwargs=kwargs),self.assertRaises(QuestionError):mine_questions(self.frame(),**kwargs)
        with patch('pipeline.questions.MAX_RESPONSE_CHARACTERS',5),self.assertRaises(QuestionError):
            mine_questions(self.frame(),agency_response='Longer response.')
        with patch('pipeline.questions.MAX_RESPONSE_SENTENCES',1),self.assertRaises(QuestionError):
            mine_questions(self.frame(),agency_response='First response. Second response.')

    def test_cosine_is_not_an_answer_entailment_claim(self):
        # Similar embeddings can include opposite statements. The public result
        # must label this only a possible match and disclose the limitation.
        with patch('pipeline.questions._embed',side_effect=[np.array([[1.,0.]]),np.array([[1.,0.]])]):
            result=mine_questions(self.frame(),agency_response='There will not be a hearing.')
        self.assertEqual(result['groups'][0]['response_match_status'],'possible_match')
        self.assertIn('contradict',result['selection_notice'])
        self.assertNotIn('answered',result['groups'][0])

    def test_response_model_failure_never_becomes_unanswered(self):
        with patch('pipeline.questions._embed',side_effect=[np.array([[1.,0.]]),np.array([[0.,0.]])]),self.assertRaises(QuestionError):
            mine_questions(self.frame(),agency_response='A response.')
