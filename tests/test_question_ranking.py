import json
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from pipeline.questions import mine_questions, QuestionError


def embed(texts):
    return np.array([[1.,0.] if 'A' in text else [0.,1.] for text in texts])


class QuestionRankingTests(unittest.TestCase):
    def run_miner(self, frame, **kwargs):
        with patch('pipeline.questions._embed',side_effect=embed):
            return mine_questions(frame, **kwargs)

    def test_frequency_then_visible_spread_order(self):
        frame=pd.DataFrame({'comment_text':['Why A?']*20+['Why B?']*20,
                            'subgroup__role':['One']*20+['One']*10+['Two']*10})
        result=self.run_miner(frame)
        self.assertEqual([g['representative']['text'] for g in result['groups']],['Why B?','Why A?'])
        self.assertEqual([g['subgroup_spread'] for g in result['groups']],[2,1])
        frame.loc[len(frame)]=['Why A?','One']
        self.assertEqual(self.run_miner(frame)['groups'][0]['representative']['text'],'Why A?')

    def test_small_categories_and_values_never_exposed(self):
        frame=pd.DataFrame({'comment_text':['Why A?']*20,
                            'subgroup__role':['RarePrivateValue']*9+['AnotherPrivateValue']*11})
        result=self.run_miner(frame); group=result['groups'][0]
        self.assertEqual(group['subgroup_spread'],1)
        self.assertTrue(group['spread_is_lower_bound'])
        self.assertTrue(group['subgroup_spread_by_field']['subgroup__role']['small_groups_suppressed'])
        exported=json.dumps(result)
        self.assertNotIn('RarePrivateValue',exported)
        self.assertNotIn('AnotherPrivateValue',exported)

    def test_missing_fields_are_unavailable_not_guessed(self):
        frame=pd.DataFrame({'comment_text':['Why A?']*12,'raw_role':['Parent']*12})
        self.assertIsNone(self.run_miner(frame)['groups'][0]['subgroup_spread'])
        frame['subgroup__role']=[None]*12
        group=self.run_miner(frame)['groups'][0]
        self.assertIsNone(group['subgroup_spread'])
        self.assertEqual(group['subgroup_spread_by_field']['subgroup__role']['coverage'],'missing')
        self.assertEqual(self.run_miner(frame,subgroup_columns=['raw_role'])['groups'][0]['subgroup_spread'],1)

    def test_casefold_trim_and_per_field_counts(self):
        frame=pd.DataFrame({'comment_text':['Why A?']*20,
                            'subgroup__role':[' Parent ']*10+['parent']*10,
                            'subgroup__ward':['001']*10+['002']*10})
        before=frame.copy(deep=True)
        group=self.run_miner(frame)['groups'][0]
        self.assertEqual(group['subgroup_spread'],3)
        self.assertFalse(group['spread_is_lower_bound'])
        pd.testing.assert_frame_equal(before,frame)

    def test_repeated_questions_cannot_make_a_small_category_visible(self):
        frame=pd.DataFrame({'comment_text':['Why A? Why A?']*9,'subgroup__role':['Private']*9})
        group=self.run_miner(frame)['groups'][0]
        self.assertEqual(group['comment_count'],9)
        self.assertEqual(group['subgroup_spread'],0)

    def test_partial_missingness_and_stricter_threshold(self):
        frame=pd.DataFrame({'comment_text':['Why A?']*25,'subgroup__role':['One']*20+[None]*5})
        group=self.run_miner(frame,minimum_group_size=21)['groups'][0]
        self.assertEqual(group['subgroup_spread'],0)
        self.assertTrue(group['spread_is_lower_bound'])
        self.assertEqual(group['subgroup_spread_by_field']['subgroup__role']['coverage'],'partial')

    def test_invalid_fields_and_thresholds_are_rejected(self):
        frame=pd.DataFrame({'comment_text':['Why A?'],'subgroup__role':['One']})
        for args in [{'subgroup_columns':'subgroup__role'}, {'subgroup_columns':[['bad']]},
                     {'subgroup_columns':['missing']},{'subgroup_columns':['comment_text']},
                     {'subgroup_columns':['subgroup__role']*2},{'minimum_group_size':9},
                     {'minimum_group_size':True}]:
            with self.subTest(args=args),self.assertRaises(QuestionError):self.run_miner(frame,**args)
        frame.at[0,'subgroup__role']=['private']
        with self.assertRaises(QuestionError):self.run_miner(frame)
