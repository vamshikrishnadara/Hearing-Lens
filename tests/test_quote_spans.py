import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from pipeline.quotes import quote_spans, nearly_identical, valid_source_quote
from pipeline.themes import analyze_themes, ThemeError
from pipeline.redact import redact_text

class QuoteSpanTests(unittest.TestCase):
    def test_long_comment_yields_contiguous_complete_sentence_without_rewriting(self):
        sentence='The buses arrive late every morning and our children repeatedly miss their first lesson.'
        text=' '.join([sentence]*6)
        spans=quote_spans(text,'sentences')
        self.assertEqual(len(spans),6)
        self.assertTrue(all(12 <= len(text[a:b].split()) <= 60 and text[a:b].endswith('.') for a,b in spans))
        self.assertTrue(all(text[a:b].replace(sentence,'').strip()=='' for a,b in spans))
        self.assertEqual(quote_spans(text,'full_comment'),[])

    def test_no_padding_or_truncation_of_single_long_sentence(self):
        self.assertEqual(quote_spans('More books.','sentences'),[])
        self.assertEqual(quote_spans(' '.join(['word']*61),'sentences'),[])

    def test_contact_tail_is_not_included_with_surviving_location_context(self):
        substantive='The school buses need reliable routes so children can arrive in time for lessons.'
        text=substantive+' Contact me at [EMAIL_ADDRESS], [STREET_ADDRESS], Example City 12345.'
        self.assertEqual(quote_spans(text,'sentences'),[(0,len(substantive))])

    def test_span_validation_rejects_tampering_and_wrong_offsets(self):
        text='Our community library needs additional books and longer opening hours for all students.'
        q={'text':text,'source_start':0,'source_end':len(text),'is_excerpt':False}
        self.assertTrue(valid_source_quote(q,text))
        self.assertFalse(valid_source_quote({**q,'source_start':1},text))
        self.assertFalse(valid_source_quote({**q,'text':text+'!'},text))
        self.assertFalse(valid_source_quote({**q,'is_excerpt':True},text))

    def test_distinct_wording_is_not_rejected_only_for_similar_embeddings(self):
        texts=['Our library needs more books and longer opening hours for students after school.',
               'Please buy new library books so every student can borrow something to read.',
               'Children currently share outdated textbooks because our school cannot afford enough copies for everyone.']
        with patch('pipeline.themes._theme_vectors',return_value=np.tile([1.,0.],(3,1))):
            result=analyze_themes(pd.DataFrame({'comment_text':texts}),theme_count=1,quote_mode='sentences')
        self.assertEqual(len(result['themes'][0]['quotes']),3)
        self.assertTrue(all(valid_source_quote(q,texts[q['row_position']]) for q in result['themes'][0]['quotes']))

    def test_repeated_text_is_still_deduplicated(self):
        text='Please add new books and extend our library hours for all neighborhood children.'
        self.assertTrue(nearly_identical(text,text.upper()))
        with patch('pipeline.themes._theme_vectors',return_value=np.tile([1.,0.],(3,1))):
            result=analyze_themes(pd.DataFrame({'comment_text':[text]*3}),theme_count=1,quote_mode='sentences')
        self.assertEqual(len(result['themes'][0]['quotes']),1)

    def test_excerpt_redaction_and_original_row_positions(self):
        sentence='My name is John Smith and I need reliable bus transportation for my children.'
        text=' '.join([sentence]*6)
        with patch('pipeline.themes._embed',side_effect=lambda texts:np.tile([1.,0.],(len(texts),1))):
            result=analyze_themes(pd.DataFrame({'comment_text':['',text]}),theme_count=1,quote_mode='sentences')
        q=result['themes'][0]['quotes'][0]
        self.assertEqual(q['row_position'],1)
        self.assertTrue(q['is_excerpt']);self.assertNotIn('John Smith',q['text'])
        self.assertTrue(valid_source_quote(q,redact_text(text).text))

    def test_contact_context_catches_names_missed_by_ner(self):
        from pipeline.redact import _redact_detected_text
        for name in ('Avery Reed','Morgan Quinn',"Nora O'Connor"):
            result=_redact_detected_text(f'Contact {name} at person@example.org.',[])
            self.assertNotIn(name,result.text)
            self.assertEqual(result.text,'Contact [PERSON] at [EMAIL_ADDRESS].')
        self.assertEqual(_redact_detected_text('Contact Customer Services at the main office.',[]).text,
                         'Contact Customer Services at the main office.')

    def test_bad_quote_mode_rejected_before_inference(self):
        with patch('pipeline.themes._embed') as embedding:
            with self.assertRaises(ThemeError):
                analyze_themes(pd.DataFrame({'comment_text':['hello']}),quote_mode='other')
        embedding.assert_not_called()
