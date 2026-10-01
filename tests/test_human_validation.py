import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import hashlib
from scripts.prepare_hand_labels import make_sheet
from scripts.evaluate_hand_labels import evaluate
from scripts.prepare_federal_sample import clean_comment

class HumanValidationTests(unittest.TestCase):
    def sheet(self):
        return pd.DataFrame([{'review_id':'synthetic-01','corpus':'synthetic','status':'ready_for_human',
            'row_position':0,'text_sha256':hashlib.sha256(b'Example text').hexdigest(),
            'comment_text':'Example text','human_sentiment':'positive','human_emotion':'joy','reviewer':'Test reviewer'}])
    def predictions(self):return {'synthetic':[{'row_position':0,'status':'scored','sentiment':'positive','emotion':'sadness'}]}
    def test_blank_sheet_has_no_invented_agreement(self):
        sheet=self.sheet();sheet[['human_sentiment','human_emotion','reviewer']]=''
        result=evaluate(sheet,self.predictions(),{'synthetic':['Example text']})
        self.assertEqual(result['human_labeled_rows'],0);self.assertFalse(result['complete'])
        self.assertIsNone(result['corpora']['synthetic']['sentiment']['agreement'])
    def test_measured_agreement_and_low_score_flag(self):
        result=evaluate(self.sheet(),self.predictions(),{'synthetic':['Example text']})
        self.assertEqual(result['corpora']['synthetic']['sentiment']['agreement'],1.)
        self.assertEqual(result['corpora']['synthetic']['emotion']['agreement'],0.)
        self.assertTrue(result['corpora']['synthetic']['emotion']['remediation_required'])
        self.assertFalse(result['complete'])
    def test_invalid_partial_stale_and_duplicate_reviews_rejected(self):
        for column,value in [('human_emotion',''),('human_sentiment','invented'),('reviewer',''),('text_sha256','stale'),('status','pending_corpus')]:
            sheet=self.sheet();sheet[column]=value
            with self.subTest(column=column),self.assertRaises(ValueError):evaluate(sheet,self.predictions(),{'synthetic':['Example text']})
        sheet=pd.concat([self.sheet(),self.sheet()])
        with self.assertRaises(ValueError):evaluate(sheet,self.predictions(),{'synthetic':['Example text']})
    def test_language_exclusion_is_not_a_neutral_prediction(self):
        result=evaluate(self.sheet(),{'synthetic':[{'row_position':0,'status':'excluded_language'}]},{'synthetic':['Example text']})
        self.assertEqual(result['corpora']['synthetic']['excluded_or_missing_predictions'],1)
        self.assertIsNone(result['corpora']['synthetic']['sentiment']['agreement'])
    def test_prepare_blind_sheet_has_20_per_corpus_and_pending_missing(self):
        frame=pd.DataFrame({'comment_text':['A fictional comment for review.']*25})
        sheet=make_sheet({'synthetic':frame,'cfpb':frame})
        self.assertEqual(len(sheet),60)
        self.assertEqual((sheet.status=='ready_for_human').sum(),40)
        self.assertTrue(sheet.human_sentiment.eq('').all());self.assertTrue(sheet.human_emotion.eq('').all())
        self.assertTrue(sheet[sheet.corpus=='federal'].comment_text.eq('').all())
        self.assertEqual(sheet[sheet.corpus=='synthetic'].row_position.nunique(),20)

class FederalTextTests(unittest.TestCase):
    def test_federal_markup_normalization(self):
        self.assertEqual(clean_comment('<p>First &amp; second</p><p>Third</p>'),'First & second Third')
