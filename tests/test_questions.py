import json
import unittest
from unittest.mock import patch

import pandas as pd

from pipeline.questions import analyze_questions, question_reasons, sentence_records, QuestionError
from pipeline.redact import RedactionError


class QuestionTests(unittest.TestCase):
    def test_terminal_punctuation_and_quoted_questions(self):
        for text in ['Please explain?', '“This costs how much?”', '(Why now?)', 'WHY now', '  2. Can we attend', "Isn't this public?"]:
            with self.subTest(text=text):
                self.assertTrue(question_reasons(text))
        for text in ['', '?!', 'The room is open.', 'We wonder why it closed.', 'Whatever works.', 'Maybe tomorrow.', 'See https://example.org/?page=2.']:
            with self.subTest(text=text):
                self.assertEqual(question_reasons(text), [])

    def test_reasons_are_explainable_and_deterministic(self):
        self.assertEqual(question_reasons('When will it open?'), ['question_mark', 'wh_word'])
        self.assertEqual(question_reasons('Can we attend'), ['auxiliary'])

    def test_spacy_boundaries_preserve_abbreviations_decimals_and_offsets(self):
        text = '  Dr. Green spoke at 3.5 hours. Can we join? Why now?  '
        rows = sentence_records([text])
        self.assertEqual(len(rows), 3)
        self.assertEqual([r['is_question'] for r in rows], [False, True, True])
        for row in rows:
            self.assertEqual(text[row['source_start']:row['source_end']], row['text'])

    def test_privacy_row_positions_no_mutation_and_json(self):
        frame = pd.DataFrame({'comment_text': ['Contact me at private@example.com. When is the hearing?', None, 'The room is open.'],
                              'respondent_id': ['secret', 'id2', 'id3'], 'subgroup__role': ['private'] * 3}, index=[7, 7, 42])
        before = frame.copy(deep=True)
        result = analyze_questions(frame)
        exported = json.dumps(result, allow_nan=False)
        self.assertNotIn('private@example.com', exported)
        self.assertNotIn('secret', exported)
        self.assertNotIn('subgroup__role', exported)
        self.assertEqual(result['comment_question_counts'], [1, 0, 0])
        self.assertEqual(result['sentences'][-1]['row_position'], 2)
        pd.testing.assert_frame_equal(frame, before)

    def test_redaction_failure_never_falls_back_to_raw_text(self):
        with patch('pipeline.questions.build_safe_display_frame', side_effect=RedactionError('Unavailable')):
            with self.assertRaises(RedactionError):
                analyze_questions(pd.DataFrame({'comment_text': ['Private input?']}))

    def test_invalid_schema_and_nested_cells_rejected(self):
        for frame in [None, pd.DataFrame({'other': ['sensitive']}),
                      pd.DataFrame([['x', 'y']], columns=['comment_text', 'comment_text']),
                      pd.DataFrame({'comment_text': [['sensitive']]})]:
            with self.subTest(frame=type(frame)), self.assertRaises(QuestionError) as caught:
                analyze_questions(frame)
            self.assertNotIn('sensitive', str(caught.exception))

    def test_blank_and_no_question_inputs_are_distinct(self):
        self.assertEqual(analyze_questions(pd.DataFrame({'comment_text': [None, ' ']}))['status'], 'unavailable')
        result = analyze_questions(pd.DataFrame({'comment_text': ['The hearing ended.']}))
        self.assertEqual(result['status'], 'available')
        self.assertEqual(result['question_count'], 0)

    def test_duplicate_sentences_retain_occurrences(self):
        result = sentence_records(['Why now?', 'Why now?'])
        self.assertEqual([r['row_position'] for r in result], [0, 1])
        self.assertEqual(result[0]['text_sha256'], result[1]['text_sha256'])

    def test_known_ambiguous_starters_are_candidates_not_accuracy_claims(self):
        self.assertTrue(question_reasons('What we need is more time.'))
        self.assertTrue(question_reasons('Will Smith attended.'))
