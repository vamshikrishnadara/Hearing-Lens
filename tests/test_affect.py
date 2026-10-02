import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import torch
from pipeline.affect import AffectError, analyze_affect, aggregate_affect, SENTIMENTS, EMOTIONS, _predict, _get_classifier, detect_language, MODEL_ROOT

def predict(texts, kind):
    labels = SENTIMENTS if kind == 'sentiment' else EMOTIONS
    winner = 'positive' if kind == 'sentiment' else 'joy'
    return [{label: float(label == winner) for label in labels} for _ in texts], [False] * len(texts)

class AffectTests(unittest.TestCase):
    def test_language_exclusions_empty_rows_and_no_text_in_result(self):
        frame = pd.DataFrame({'comment_text': ['I support the bus plan.', 'Me gusta mucho este plan.', ''], 'name':['private']*3}, index=[5,5,8])
        with patch('pipeline.affect.detect_language', side_effect=['en', 'es']), patch('pipeline.affect._predict', side_effect=predict):
            result = analyze_affect(frame)
        self.assertEqual([r['row_position'] for r in result['rows']], [0,1,2])
        self.assertEqual(result['scored_count'], 1)
        self.assertEqual(result['excluded_language_count'], 1)
        self.assertEqual(result['empty_count'], 1)
        self.assertNotIn('sentiment', result['rows'][1])
        self.assertNotIn('private', str(result)); self.assertNotIn('bus plan', str(result))

    def test_dedup_is_run_local_and_reexpands_in_original_order(self):
        frame = pd.DataFrame({'comment_text':['Same English text.']*2})
        with patch('pipeline.affect.detect_language', return_value='en'), patch('pipeline.affect._predict', side_effect=predict) as model:
            result=analyze_affect(frame)
            analyze_affect(frame)
        self.assertEqual(model.call_count,4)
        self.assertTrue(all(len(call.args[0]) == 1 for call in model.call_args_list))
        self.assertEqual(result['scored_count'],2)

    def test_nonenglish_only_does_not_load_models(self):
        with patch('pipeline.affect.detect_language', return_value='fr'), patch('pipeline.affect._predict') as model:
            result=analyze_affect(pd.DataFrame({'comment_text':['Bonjour tout le monde']}))
        model.assert_not_called(); self.assertEqual(result['scored_count'],0)

    def test_failure_is_sanitized(self):
        with patch('pipeline.affect.detect_language', side_effect=RuntimeError('private input')):
            with self.assertRaises(AffectError) as caught:
                analyze_affect(pd.DataFrame({'comment_text':['private input']}))
        self.assertNotIn('private input',str(caught.exception))

    def test_invalid_probabilities_are_rejected(self):
        def bad(texts,kind):
            result,flags=predict(texts,kind); result[0][next(iter(result[0]))]=float('nan');return result,flags
        with patch('pipeline.affect.detect_language', return_value='en'), patch('pipeline.affect._predict',side_effect=bad):
            with self.assertRaises(AffectError): analyze_affect(pd.DataFrame({'comment_text':['text']}))

    def test_aggregation_uses_scored_denominator_and_null_for_no_scores(self):
        rows=[{'row_position':0,'status':'scored','sentiment':'positive','emotion':'joy','sentiment_score':.7},
              {'row_position':1,'status':'excluded_language'}, {'row_position':2,'status':'excluded_language'}]
        result=aggregate_affect(rows,{0:1,1:1,2:0})
        self.assertEqual(result[0]['sentiment_shares']['positive'],1)
        self.assertEqual(result[0]['excluded_comments'],1)
        self.assertIsNone(result[1]['mean_sentiment']); self.assertIsNone(result[1]['dominant_emotion'])
        with self.assertRaises(AffectError): aggregate_affect(rows+rows,{0:1})
        with self.assertRaises(AffectError): aggregate_affect(rows,{99:1})

    def test_tied_emotions_do_not_invent_a_dominant_label(self):
        rows=[{'row_position':i,'status':'scored','sentiment':'neutral','emotion':e,'sentiment_score':0.} for i,e in enumerate(['joy','fear'])]
        result=aggregate_affect(rows,{0:1,1:1})[0]
        self.assertIsNone(result['dominant_emotion']); self.assertEqual(result['dominant_emotion_ties'],['fear','joy'])

class ModelBoundaryTests(unittest.TestCase):
    def test_length_buckets_restore_predictions_and_truncation_to_source_order(self):
        class Tokenizer:
            def __init__(self):self.seen=[]
            def __call__(self,batch,**kwargs):
                if kwargs.get('return_tensors'):
                    self.seen.extend(batch)
                    return {'input_ids':torch.tensor([[int(t[0])] for t in batch])}
                return {'input_ids':[[1]*(600 if t.startswith('2') else 3) for t in batch]}
        class Model:
            def __call__(self,**kwargs):
                values=kwargs['input_ids'][:,0].float()
                return type('Output',(),{'logits':torch.stack([values,torch.zeros_like(values),-values],dim=1)})()
        tokenizer=Tokenizer();texts=['2 long text','1','3 medium']
        with patch('pipeline.affect._get_classifier',return_value=(tokenizer,Model(),['positive','neutral','negative'])):
            result,truncated=_predict(texts,'sentiment')
        self.assertEqual(tokenizer.seen,['1','3 medium','2 long text'])
        self.assertEqual(truncated,[True,False,False])
        self.assertGreater(result[2]['positive'],result[0]['positive'])
        self.assertGreater(result[0]['positive'],result[1]['positive'])

    def test_batch_size_truncation_and_id_label_mapping(self):
        class Tokenizer:
            def __call__(self,batch,**kwargs):
                if kwargs.get('return_tensors'):
                    self.options=kwargs
                    return {'input_ids':torch.ones((len(batch),4),dtype=torch.long)}
                return {'input_ids':[[1]*600 for _ in batch]}
        class Model:
            def __init__(self):self.sizes=[]
            def __call__(self,**kwargs):
                n=kwargs['input_ids'].shape[0];self.sizes.append(n)
                return type('Output',(),{'logits':torch.tensor([[4.,1.,0.]]*n)})()
        tokenizer,model=Tokenizer(),Model()
        with patch('pipeline.affect._get_classifier',return_value=(tokenizer,model,['positive','negative','neutral'])):
            result,truncated=_predict(['text']*65,'sentiment')
        self.assertEqual(model.sizes,[32,32,1]);self.assertTrue(all(truncated))
        self.assertEqual(tokenizer.options['max_length'],512)
        self.assertGreater(result[0]['positive'],result[0]['negative'])
        self.assertAlmostEqual(sum(result[0].values()),1,places=6)

    @unittest.skipUnless((MODEL_ROOT/'sentiment/config.json').exists(),'Local affect models not set up')
    def test_real_model_cached_and_runs_offline(self):
        with patch('requests.Session.request',side_effect=AssertionError('Network forbidden')):
            first=_get_classifier('sentiment');second=_get_classifier('sentiment')
            rows,flags=_predict(['I am pleased with the service.'],'sentiment')
        self.assertIs(first,second);self.assertEqual(set(rows[0]),set(SENTIMENTS));self.assertEqual(flags,[False])

    def test_language_detection_marks_short_text_uncertain(self):
        self.assertEqual(detect_language('12'),'unknown')
        self.assertEqual(detect_language('The bus service needs better schedules for people traveling to work.'),'en')
        self.assertNotEqual(detect_language('Necesitamos mejorar el transporte público para todas las personas.'),'en')
