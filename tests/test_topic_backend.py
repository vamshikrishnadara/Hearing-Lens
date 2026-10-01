import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
from pipeline.themes import ThemeError, analyze_themes
from pipeline.topic_backend import cluster_bertopic, keybert_keywords
from pipeline.quote_review import swap_quote
import copy

class RoutingTests(unittest.TestCase):
    def analyze(self,n,**kwargs):
        frame=pd.DataFrame({'comment_text':['Please improve public bus services for residents in our neighborhood every morning.']*n})
        return analyze_themes(frame,**kwargs)

    def test_149_uses_kmeans_and_150_uses_density_before_cleaning(self):
        with patch('pipeline.themes._theme_vectors',side_effect=lambda texts,mode:np.tile([1.,0.],(len(texts),1))), patch('pipeline.themes._get_embedding_model'), patch('pipeline.topic_backend.cluster_bertopic') as density:
            self.assertEqual(self.analyze(149,backend='auto',theme_count='auto')['backend'],'kmeans')
            density.assert_not_called()
            density.return_value=(np.array([0]*149+[-1]),{'selected_count':1,'fallback_reason':None,'skipped_counts':[]})
            result=self.analyze(150,backend='auto',theme_count='auto')
        self.assertEqual(result['outlier_count'],1)
        self.assertEqual(result['assignments'][-1],{'row_position':149,'theme_id':0})
        self.assertEqual(result['themes'][0]['count'],149)
        self.assertAlmostEqual(result['themes'][0]['share'],149/150)

    def test_all_outliers_are_retained_and_warning_is_explicit(self):
        with patch('pipeline.themes._theme_vectors',return_value=np.ones((5,2))), patch('pipeline.themes._get_embedding_model'), patch('pipeline.topic_backend.cluster_bertopic', return_value=(np.full(5,-1),{'selected_count':0,'fallback_reason':None,'skipped_counts':[]})):
            result=self.analyze(5,backend='bertopic',theme_count='auto',merge_small_themes=True)
        self.assertEqual(result['themes'],[]);self.assertEqual(len(result['assignments']),5)
        self.assertTrue(any('20%' in w for w in result['warnings']))

    def test_backend_failure_does_not_expose_source(self):
        with patch('pipeline.themes._theme_vectors',return_value=np.ones((5,2))), patch('pipeline.themes._get_embedding_model'), patch('pipeline.topic_backend.cluster_bertopic',side_effect=RuntimeError('private')):
            with self.assertRaises(ThemeError) as caught:self.analyze(5,backend='bertopic')
        self.assertNotIn('private',str(caught.exception))

    def test_invalid_options_rejected_before_model(self):
        for kwargs in [{'backend':'invalid'},{'keyword_method':'invalid'},{'quote_pool_size':2}]:
            with patch('pipeline.themes._theme_vectors') as embed:
                with self.assertRaises(ThemeError):self.analyze(5,**kwargs)
            embed.assert_not_called()

class BackendDetailsTests(unittest.TestCase):
    def test_density_tiny_input_keeps_explicit_outliers(self):
        labels,selection=cluster_bertopic(['text']*4,np.ones((4,2)),object())
        self.assertEqual(labels.tolist(),[-1]*4);self.assertEqual(selection['selected_count'],0)

    def test_keybert_uses_mmr_and_only_within_comment_vocabulary(self):
        embedding=MagicMock();embedding.encode.side_effect=lambda words,**kwargs:np.ones((len(words),2))
        with patch('keybert.KeyBERT') as model:
            model.return_value.extract_keywords.return_value=[('bus service',.8)]
            result=keybert_keywords(['bus service','library books'],[[0,1]],np.eye(2),embedding)
        args=model.return_value.extract_keywords.call_args.kwargs
        self.assertTrue(args['use_mmr']);self.assertEqual(args['diversity'],.5)
        self.assertNotIn('service library',args['vectorizer'].vocabulary)
        self.assertEqual(result,[['bus service']])
    def test_quote_swap_only_uses_same_theme_candidates_without_mutation(self):
        original={'themes':[{'theme_id':1,'quotes':[{'row_position':0,'text':'redacted original'}],
                             'quote_alternatives':[{'row_position':2,'text':'redacted alternative'}]}]}
        before=copy.deepcopy(original)
        updated=swap_quote(original,1,0,2)
        self.assertEqual(original,before);self.assertEqual(updated['themes'][0]['quotes'][0]['row_position'],2)
        with self.assertRaises(ValueError):swap_quote(original,1,0,99)
