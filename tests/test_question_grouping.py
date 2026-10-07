import json
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from pipeline.questions import mine_questions, QuestionError
from pipeline.themes import ThemeError


class QuestionGroupingTests(unittest.TestCase):
    def test_similar_wordings_group_but_unrelated_stays_separate(self):
        frame = pd.DataFrame({'comment_text':['When is the meeting?', 'When does the meeting start?', 'How much will this cost?']})
        def embed(texts):
            return np.array([[0,1] if 'cost' in text else [1,.02] for text in texts])
        with patch('pipeline.questions._embed', side_effect=embed):
            result = mine_questions(frame)
        self.assertEqual(sorted(g['comment_count'] for g in result['groups']),[1,2])
        self.assertEqual(len(result['assignments']),3)
        self.assertEqual(result['question_count'],3)
        json.dumps(result, allow_nan=False)

    def test_repeats_in_one_comment_do_not_inflate_frequency(self):
        frame=pd.DataFrame({'comment_text':['When is the hearing? When is the hearing?', 'When is the hearing?']})
        with patch('pipeline.questions._embed', return_value=np.array([[1.,0.]])) as embed:
            group=mine_questions(frame)['groups'][0]
        self.assertEqual(len(embed.call_args.args[0]),1)
        self.assertEqual(group['comment_count'],2)
        self.assertEqual(group['sentence_count'],3)
        self.assertEqual(group['unique_wordings'],1)

    def test_empty_candidates_do_not_load_embedding_model(self):
        with patch('pipeline.questions._embed') as embed:
            result=mine_questions(pd.DataFrame({'comment_text':['The meeting ended.', None]}))
        embed.assert_not_called()
        self.assertEqual(result['groups'],[])
        self.assertEqual(result['status'],'no_questions')

    def test_complete_linkage_does_not_bridge_distant_questions(self):
        frame=pd.DataFrame({'comment_text':['Can A happen?', 'Can B happen?', 'Can C happen?']})
        vectors=np.array([[np.cos(x),np.sin(x)] for x in [0,.6,1.2]])
        with patch('pipeline.questions._embed',return_value=vectors):
            result=mine_questions(frame,grouping_distance=.3)
        self.assertEqual(len(result['groups']),2)

    def test_representative_is_verbatim_and_embedded_input_is_redacted(self):
        frame=pd.DataFrame({'comment_text':['Can you email private@example.com?'], 'respondent_id':['private-id']})
        with patch('pipeline.questions._embed',return_value=np.array([[1.,0.]])) as embed:
            result=mine_questions(frame)
        self.assertNotIn('private@example.com',embed.call_args.args[0][0])
        self.assertNotIn('private-id',json.dumps(result))
        self.assertEqual(result['groups'][0]['representative']['text'],embed.call_args.args[0][0])

    def test_invalid_thresholds_and_embedding_failures_are_safe(self):
        frame=pd.DataFrame({'comment_text':['Why now?']})
        for threshold in [0, -1, 1.1, float('nan'), True, '0.3']:
            with self.subTest(threshold=threshold),self.assertRaises(QuestionError):mine_questions(frame,grouping_distance=threshold)
        for vectors in [np.zeros((1,2)), np.array([[float('nan'),1]]), np.ones((2,2)), np.array([1.])]:
            with patch('pipeline.questions._embed',return_value=vectors),self.assertRaises(QuestionError):mine_questions(frame)
        with patch('pipeline.questions._embed',side_effect=ThemeError('private text')),self.assertRaises(QuestionError) as caught:mine_questions(frame)
        self.assertNotIn('private text',str(caught.exception))

    def test_distinct_wording_limit_rejects_before_embedding(self):
        frame=pd.DataFrame({'comment_text':['Why one?', 'Why two?']})
        with patch('pipeline.questions.MAX_UNIQUE_QUESTIONS',1),patch('pipeline.questions._embed') as embed,self.assertRaises(QuestionError):
            mine_questions(frame)
        embed.assert_not_called()

    def test_reordering_rows_keeps_group_wordings_and_counts(self):
        frame=pd.DataFrame({'comment_text':['Why one?', 'Why two?', 'Why one?']})
        with patch('pipeline.questions._embed',return_value=np.eye(2)):
            first=mine_questions(frame)
            second=mine_questions(frame.iloc[::-1])
        self.assertEqual([(g['question_group_id'],g['representative']['text'],g['comment_count']) for g in first['groups']],
                         [(g['question_group_id'],g['representative']['text'],g['comment_count']) for g in second['groups']])
