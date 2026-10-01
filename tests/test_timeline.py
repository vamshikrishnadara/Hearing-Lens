import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
from pipeline.timeline import TimelineError, build_timeline, timeline_figures

class TimelineTests(unittest.TestCase):
    def fixture(self):
        return {'rows':[{'row_position':0,'status':'scored','sentiment':'positive','emotion':'joy','sentiment_score':.8},
                        {'row_position':1,'status':'excluded_language'},
                        {'row_position':2,'status':'scored','sentiment':'negative','emotion':'anger','sentiment_score':-.4}]}
    def assignments(self):return [{'row_position':i,'theme_id':i%2} for i in range(3)]
    def test_date_order_missing_dates_and_zero_filled_volumes(self):
        frame=pd.DataFrame({'date':['2026-10-02','','2026-10-01']})
        result=build_timeline(frame,self.fixture(),self.assignments())
        self.assertEqual([p['group'] for p in result['periods']],['2026-10-01','2026-10-02','Missing period'])
        self.assertIsNone(result['periods'][-1]['mean_sentiment'])
        self.assertEqual(sum(v['count'] for v in result['theme_volumes']),3)
        self.assertEqual(len(timeline_figures(result)),2)
    def test_hearing_fallback_does_not_drop_unparseable_values(self):
        result=build_timeline(pd.DataFrame({'date':['2026-10-02','Hearing two','']}),self.fixture(),self.assignments())
        self.assertEqual(result['mode'],'hearing_label');self.assertEqual(len(result['periods']),3)
    def test_missing_column_is_single_period_and_invalid_selection_errors(self):
        frame=pd.DataFrame({'comment_text':['a','b','c']})
        result=build_timeline(frame,self.fixture(),self.assignments())
        self.assertEqual(result['mode'],'single_period');self.assertAlmostEqual(result['periods'][0]['mean_sentiment'],.2)
        with self.assertRaises(TimelineError):build_timeline(frame,self.fixture(),self.assignments(),'absent')
    def test_duplicate_and_out_of_range_positions_rejected(self):
        frame=pd.DataFrame({'date':['a','b','c']})
        for assignments in [[{'row_position':3,'theme_id':1}],self.assignments()*2]:
            with self.assertRaises(TimelineError):build_timeline(frame,self.fixture(),assignments)
