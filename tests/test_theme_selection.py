"""Automatic selection contracts using controlled geometry and public API checks."""
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from pipeline.themes import ThemeError, _cluster_vectors, analyze_themes


class ThemeSelectionTests(unittest.TestCase):
    def test_highest_score_wins_and_scores_are_auditable(self):
        with patch('pipeline.themes.silhouette_score', side_effect=[.2, .7, .4]):
            labels, selection = _cluster_vectors(np.eye(7), 'auto')
        self.assertEqual(len(set(labels)), 5)
        self.assertEqual(selection['candidate_scores'], [
            {'count': 4, 'score': .2}, {'count': 5, 'score': .7}, {'count': 6, 'score': .4}])
        self.assertEqual(selection['metric'], 'euclidean')

    def test_exact_tie_prefers_smaller_count(self):
        with patch('pipeline.themes.silhouette_score', return_value=.3):
            _, selection = _cluster_vectors(np.eye(8), 'auto')
        self.assertEqual(selection['selected_count'], 4)

    def test_candidate_range_stops_at_twelve(self):
        with patch('pipeline.themes.silhouette_score', return_value=.3):
            _, selection = _cluster_vectors(np.eye(15), 'auto')
        self.assertEqual([item['count'] for item in selection['candidate_scores']], list(range(4, 13)))

    def test_small_and_duplicate_heavy_inputs_have_explicit_fallback(self):
        for vectors in [np.eye(1), np.eye(4), np.tile(np.eye(3), (4, 1))]:
            with self.subTest(rows=len(vectors)), patch('pipeline.themes.silhouette_score') as score:
                labels, selection = _cluster_vectors(vectors, 'auto')
            score.assert_not_called()
            self.assertEqual(labels.tolist(), [0] * len(vectors))
            self.assertIsNotNone(selection['fallback_reason'])

    def test_four_distinct_vectors_can_be_scored_with_repeated_rows(self):
        _, selection = _cluster_vectors(np.tile(np.eye(4), (2, 1)), 'auto')
        self.assertEqual(selection['candidate_scores'], [{'count': 4, 'score': 1.0}])

    def test_manual_assignments_match_original_algorithm(self):
        vectors = np.random.default_rng(42).normal(size=(20, 6))
        expected = KMeans(n_clusters=6, random_state=42, n_init=10).fit_predict(vectors)
        actual, selection = _cluster_vectors(vectors, 6)
        np.testing.assert_array_equal(actual, expected)
        self.assertEqual(selection['mode'], 'manual')
        self.assertEqual(selection['candidate_scores'], [])

    def test_failures_do_not_echo_private_exception(self):
        for target in ['KMeans', 'silhouette_score']:
            with self.subTest(target=target), patch('pipeline.themes.' + target, side_effect=RuntimeError('private text')):
                with self.assertRaises(ThemeError) as caught:
                    _cluster_vectors(np.eye(6), 'auto')
                self.assertNotIn('private text', str(caught.exception))

    def test_nonfinite_scores_and_collapsed_candidates_are_not_selected(self):
        with patch('pipeline.themes.silhouette_score', return_value=float('nan')):
            _, selection = _cluster_vectors(np.eye(6), 'auto')
        self.assertEqual(selection['selected_count'], 1)
        self.assertEqual(selection['skipped_counts'], [4, 5])
        with patch('pipeline.themes.KMeans') as model, patch('pipeline.themes.silhouette_score') as score:
            model.return_value.fit_predict.return_value = np.zeros(6, dtype=int)
            _, selection = _cluster_vectors(np.eye(6), 'auto')
        score.assert_not_called()
        self.assertEqual(selection['skipped_counts'], [4, 5])

    def test_149_rows_allowed_150_rejected_before_embedding_including_blanks(self):
        text = 'Please improve local bus service for residents who travel to work every morning.'
        with patch('pipeline.themes._theme_vectors', return_value=np.ones((149, 2))):
            result = analyze_themes(pd.DataFrame({'comment_text': [text] * 149}), theme_count='auto')
        self.assertEqual(result['analyzed_comments'], 149)
        with patch('pipeline.themes._theme_vectors') as embed:
            with self.assertRaisesRegex(ThemeError, 'fewer than 150 input rows'):
                analyze_themes(pd.DataFrame({'comment_text': [text] + [''] * 149}), theme_count='auto')
        embed.assert_not_called()

    def test_auto_preserves_positions_counts_and_redacted_original_quotes(self):
        text = 'Please improve local bus service for residents who travel to work every morning. Email resident@example.org.'
        frame = pd.DataFrame({'comment_text': ['', text, 'resident@example.org', text]}, index=[9, 9, 3, 2])
        with patch('pipeline.themes._theme_vectors', return_value=np.ones((2, 2))) as embed:
            result = analyze_themes(frame, theme_count='auto')
        self.assertEqual(result['assignments'], [{'row_position': 1, 'theme_id': 1}, {'row_position': 3, 'theme_id': 1}])
        self.assertEqual(result['excluded_row_positions'], [2])
        self.assertEqual(result['empty_comments_removed'], 1)
        self.assertEqual(result['themes'][0]['count'], 2)
        self.assertEqual(result['themes'][0]['share'], 1)
        self.assertEqual(result['themes'][0]['quotes'][0]['text'], text.replace('resident@example.org', '[EMAIL_ADDRESS]'))
        self.assertNotIn('resident@example.org', str(embed.call_args))
        self.assertTrue(any('returned one group' in w for w in result['warnings']))

    def test_invalid_count_rejected_before_embedding(self):
        for count in ['AUTO', '6', True, 0, 16, None, 1.5]:
            with self.subTest(count=count), patch('pipeline.themes._theme_vectors') as embed:
                with self.assertRaises(ThemeError):
                    analyze_themes(pd.DataFrame({'comment_text': ['hello']}), theme_count=count)
                embed.assert_not_called()
