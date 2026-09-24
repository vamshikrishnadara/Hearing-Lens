"""Behavioral checks for initial themes; fake vectors keep most tests lightweight."""

import json
from unittest.mock import patch
import unittest

import numpy as np
import pandas as pd

from pipeline.redact import RedactionError
from pipeline.themes import MODEL_PATH, ThemeError, _analysis_text, _embed, _get_embedding_model, _theme_vectors, analyze_themes


class ThemeTests(unittest.TestCase):
    def test_common_intro_has_less_influence_than_each_topic(self):
        texts = ['I attended. Please improve buses.', 'I attended. Please improve books.']
        with patch('pipeline.themes._embed', return_value=np.eye(3)) as embed:
            vectors = _theme_vectors(texts, 'sentence_weighted')
        self.assertEqual(embed.call_args.args[0], ['I attended.', 'Please improve buses.', 'Please improve books.'])
        self.assertGreater(vectors[0, 1], vectors[0, 0])
        self.assertGreater(vectors[1, 2], vectors[1, 0])
        np.testing.assert_allclose(np.linalg.norm(vectors, axis=1), 1)

    def test_repeating_sentence_within_one_comment_cannot_increase_its_weight(self):
        texts = ['I attended. Buses are late.', 'Books are needed.']
        with patch('pipeline.themes._embed', return_value=np.eye(3)):
            ordinary = _theme_vectors(texts, 'sentence_weighted')
            repeated = _theme_vectors(['I attended. I attended. Buses are late.', texts[1]], 'sentence_weighted')
        np.testing.assert_allclose(ordinary, repeated)

    def test_single_sentence_vectors_and_input_order_are_preserved(self):
        texts = ['More books.', 'More buses.', 'More books.']
        with patch('pipeline.themes._embed', return_value=np.eye(2)) as embed:
            result = _theme_vectors(texts, 'sentence_weighted')
        np.testing.assert_allclose(result, [[1, 0], [0, 1], [1, 0]])
        self.assertEqual(embed.call_args.args[0], ['More books.', 'More buses.'])

    def test_whole_comment_mode_keeps_original_embedding_path(self):
        texts = ['First sentence. Second sentence.']
        with patch('pipeline.themes._embed', return_value=np.array([[1., 0.]])) as embed:
            _theme_vectors(texts, 'whole_comment')
        embed.assert_called_once_with(texts)

    def test_weighting_preserves_the_complete_redacted_quote(self):
        text = 'Thank you for listening. Please add new books to our library for children. Email resident@example.org.'
        with patch('pipeline.themes._embed', side_effect=lambda texts: np.tile([1., 0.], (len(texts), 1))):
            result = analyze_themes(pd.DataFrame({'comment_text': [text]}), theme_count=1)
        self.assertEqual(result['embedding_mode'], 'sentence_weighted')
        quote = result['themes'][0]['quotes'][0]['text']
        self.assertEqual(quote, text.replace('resident@example.org', '[EMAIL_ADDRESS]'))

    def test_zero_average_sentence_vector_blocks_results(self):
        with patch('pipeline.themes._embed', return_value=np.array([[1., 0.], [-1., 0.]])):
            with self.assertRaisesRegex(ThemeError, 'embedding failed'):
                _theme_vectors(['First sentence. Opposite sentence.'], 'sentence_weighted')

    def test_invalid_embedding_mode_rejected_before_model_load(self):
        with patch('pipeline.themes._embed') as embed:
            with self.assertRaisesRegex(ThemeError, 'embedding mode'):
                analyze_themes(pd.DataFrame({'comment_text': ['Hello']}), embedding_mode='private-invalid-value')
            embed.assert_not_called()

    def test_contact_suffixes_do_not_create_different_analysis_text(self):
        core = 'Please improve transportation for families.'
        self.assertEqual(_analysis_text(core + ' Contact [PERSON] at [EMAIL_ADDRESS].'), core)
        self.assertEqual(_analysis_text(core + ' I live at [STREET_ADDRESS] [UNIT_NUMBER].'), core)
        self.assertIn('Please improve transportation', _analysis_text('Please improve transportation for [PERSON].'))

    def test_counts_shares_assignments_and_no_metadata(self):
        frame = pd.DataFrame({
            "comment_text": [
                "Our library needs more books and longer opening hours for students after school.",
                "Please buy new library books so every student can borrow something to read.",
                "Our bus route arrives late every morning and students miss their first class.",
                "Please improve bus service so children can get to school safely every day.",
            ],
            "respondent_id": ["secret-id"] * 4,
            "validation_theme": ["hidden-answer"] * 4,
        }, index=[7, 7, 20, 90])
        original = frame.copy(deep=True)
        with patch("pipeline.themes._embed", return_value=np.array([[1., 0.], [1., .01], [0., 1.], [.01, 1.]])):
            result = analyze_themes(frame, theme_count=2)
        self.assertEqual(sorted(t['count'] for t in result['themes']), [2, 2])
        self.assertAlmostEqual(sum(t['share'] for t in result['themes']), 1)
        assignments = result['assignments']
        self.assertEqual([a['row_position'] for a in assignments], [0, 1, 2, 3])
        self.assertEqual(assignments[0]['theme_id'], assignments[1]['theme_id'])
        self.assertNotEqual(assignments[0]['theme_id'], assignments[2]['theme_id'])
        self.assertNotIn('secret-id', json.dumps(result))
        self.assertNotIn('hidden-answer', json.dumps(result))
        pd.testing.assert_frame_equal(frame, original)

    def test_rejects_invalid_inputs_before_loading_model(self):
        with patch('pipeline.themes._get_embedding_model', side_effect=AssertionError):
            for frame, count in [
                (pd.DataFrame({'other': ['Text']}), 6),
                (pd.DataFrame({'comment_text': ['', None, '  ']}), 6),
                (pd.DataFrame({'comment_text': ['Text'] * 5001}), 6),
                (pd.DataFrame({'comment_text': ['Text']}), 0),
                (pd.DataFrame({'comment_text': ['Text']}), 16),
                (pd.DataFrame({'comment_text': ['Text']}), True),
            ]:
                with self.subTest(count=count, rows=len(frame)):
                    with self.assertRaises(ThemeError):
                        analyze_themes(frame, theme_count=count)

    def test_identical_vectors_reduce_theme_count_and_deduplicate_quotes(self):
        text = 'Please add library books and extend weekend hours for all students in our neighborhood.'
        with patch('pipeline.themes._embed', return_value=np.ones((3, 2))):
            result = analyze_themes(pd.DataFrame({'comment_text': [text] * 3}))
        self.assertEqual(len(result['themes']), 1)
        self.assertEqual(result['themes'][0]['count'], 3)
        self.assertEqual(len(result['themes'][0]['quotes']), 1)
        self.assertTrue(any('too few distinct' in w for w in result['warnings']))

    def test_quotes_obey_length_limits_without_padding(self):
        texts = ['More books.', ' '.join(['books'] * 61)]
        with patch('pipeline.themes._embed', return_value=np.array([[1., 0.], [0., 1.]])):
            result = analyze_themes(pd.DataFrame({'comment_text': texts}), theme_count=1)
        self.assertEqual(result['themes'][0]['quotes'], [])
        self.assertTrue(any('only 0 eligible' in w for w in result['warnings']))

    def test_names_and_contacts_redacted_before_labels_quotes_and_embedding(self):
        text = 'My name is John Smith and I support more books for students. Email resident@example.org.'
        with patch('pipeline.themes._embed', side_effect=lambda texts: np.tile([1., 0.], (len(texts), 1))) as embed:
            result = analyze_themes(pd.DataFrame({'comment_text': [text]}), theme_count=1)
        rendered = json.dumps(result)
        self.assertNotIn('John Smith', rendered)
        self.assertNotIn('resident@example.org', rendered)
        self.assertIn('[PERSON]', rendered)
        self.assertNotIn('John Smith', ' '.join(embed.call_args.args[0]))
        self.assertNotIn('[EMAIL_ADDRESS]', ' '.join(embed.call_args.args[0]))

    def test_empty_and_fully_redacted_comments_keep_input_positions(self):
        frame = pd.DataFrame({'comment_text': ['', 'resident@example.org', 'Please add more books.', None]})
        with patch('pipeline.themes._embed', return_value=np.array([[1., 0.]])):
            result = analyze_themes(frame)
        self.assertEqual(result['empty_comments_removed'], 2)
        self.assertEqual(result['excluded_row_positions'], [1])
        self.assertEqual(result['assignments'], [{'row_position': 2, 'theme_id': 1}])

    def test_missing_model_error_is_sanitized(self):
        _get_embedding_model.cache_clear()
        try:
            with patch('pipeline.themes.MODEL_PATH') as path:
                (path / 'modules.json').is_file.return_value = False
                with self.assertRaisesRegex(ThemeError, 'setup_theme_model'):
                    _get_embedding_model()
        finally:
            _get_embedding_model.cache_clear()

    def test_embedding_failures_and_invalid_vectors_are_sanitized(self):
        for output in [np.array([[np.nan]]), np.array([[0., 0.]]), np.zeros((2, 2))]:
            with self.subTest(output=output):
                with patch('pipeline.themes._get_embedding_model') as model:
                    model.return_value.encode.return_value = output
                    with self.assertRaisesRegex(ThemeError, 'embedding failed'):
                        _embed(['private comment'])
        with patch('pipeline.themes._get_embedding_model') as model:
            model.return_value.encode.side_effect = RuntimeError('private comment')
            with self.assertRaises(ThemeError) as caught:
                _embed(['private comment'])
        self.assertNotIn('private comment', str(caught.exception))

    def test_redaction_failure_blocks_theme_results(self):
        with patch('pipeline.themes.build_safe_display_frame', side_effect=RedactionError('Unavailable')):
            with patch('pipeline.themes._embed') as embed:
                with self.assertRaises(RedactionError):
                    analyze_themes(pd.DataFrame({'comment_text': ['Private name']}))
                embed.assert_not_called()

    def test_no_keyword_vocabulary_uses_generic_label(self):
        with patch('pipeline.themes._embed', return_value=np.array([[1., 0.]])):
            result = analyze_themes(pd.DataFrame({'comment_text': ['the and or']}), theme_count=1)
        self.assertEqual(result['themes'][0]['label'], 'Theme 1')
        self.assertEqual(result['themes'][0]['keywords'], [])

    @unittest.skipUnless((MODEL_PATH / 'modules.json').is_file(), 'Run scripts.setup_theme_model for integration check')
    def test_real_model_returns_finite_normalized_vectors(self):
        vectors = _embed(['Library books help children read.', 'The bus route needs reliable service.'])
        self.assertEqual(vectors.shape, (2, 384))
        self.assertTrue(np.isfinite(vectors).all())
        np.testing.assert_allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-6)


if __name__ == '__main__':
    unittest.main()
