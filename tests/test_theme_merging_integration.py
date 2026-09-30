"""Public API checks for opt-in merging and rebuilt display output."""
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from pipeline.themes import ThemeError, analyze_themes


class ThemeMergingIntegrationTests(unittest.TestCase):
    def fixture(self):
        return pd.DataFrame({'comment_text': [
            '',
            'The library needs more books for children to borrow and read after school.',
            'Please extend library hours so working families can find books in the evening.',
            'Our library reading room needs quiet tables for students to study after classes.',
            'Please buy picture books for the library so young readers can learn new words. Email resident@example.org.',
            'Storm drains overflow after heavy rain and leave the road flooded outside our homes.',
        ], 'respondent_id': ['private-id'] * 6}, index=[9] * 6)

    def run_fixture(self, **kwargs):
        vectors = np.array([[1., 0.]] * 4 + [[0., 1.]])
        with patch('pipeline.themes._theme_vectors', return_value=vectors), patch(
            'pipeline.themes._cluster_vectors', return_value=(np.array([0, 0, 0, 1, 2]),
            {'selected_count': 3, 'fallback_reason': None, 'skipped_counts': [], 'candidate_scores': []})
        ):
            return analyze_themes(self.fixture(), theme_count=3, **kwargs)

    def test_default_and_explicit_disabled_match_and_do_not_merge(self):
        with patch('pipeline.themes.merge_small_groups') as merge:
            default = self.run_fixture()
            disabled = self.run_fixture(merge_small_themes=False)
        merge.assert_not_called()
        self.assertEqual(default, disabled)
        self.assertEqual(len(default['themes']), 3)

    def test_merged_counts_positions_labels_and_quotes_are_rebuilt(self):
        with patch('pipeline.themes._keywords', return_value=[['books'], ['drainage']]) as keywords:
            result = self.run_fixture(merge_small_themes=True)
        self.assertEqual(keywords.call_args.args[1], [[0, 1, 2, 3], [4]])
        self.assertEqual([t['count'] for t in result['themes']], [4, 1])
        self.assertEqual([t['share'] for t in result['themes']], [.8, .2])
        self.assertEqual(result['theme_selection']['selected_count'], 3)
        self.assertEqual(result['theme_merging']['final_count'], 2)
        self.assertEqual(result['theme_merging']['final_theme_sources'], [
            {'theme_id': 1, 'initial_theme_ids': [1, 2]}, {'theme_id': 2, 'initial_theme_ids': [3]}])
        self.assertEqual(result['theme_merging']['retained_small_theme_ids'], [2])
        self.assertEqual([a['row_position'] for a in result['assignments']], [1, 2, 3, 4, 5])
        assignments = {a['row_position']: a['theme_id'] for a in result['assignments']}
        for theme in result['themes']:
            for quote in theme['quotes']:
                self.assertEqual(assignments[quote['row_position']], theme['theme_id'])
                source = self.fixture().iloc[quote['row_position']].comment_text
                self.assertEqual(quote['text'], source.replace('resident@example.org', '[EMAIL_ADDRESS]'))
                self.assertTrue(12 <= len(quote['text'].split()) <= 60)
        self.assertNotIn('private-id', str(result))
        self.assertNotIn('resident@example.org', str(result))
        self.assertTrue(any('pre-merge' in warning for warning in result['warnings']))
        self.assertTrue(any('Retained 1 small' in warning for warning in result['warnings']))
        self.assertFalse(any('too few distinct' in warning for warning in result['warnings']))

    def test_final_display_ids_follow_merged_size_then_original_position(self):
        groups = [[0], [1, 2], [3, 4]]
        details = {'initial_count': 3, 'final_count': 2, 'history': [{}],
                   'initial_theme_ids_by_group': [[1], [2, 3]]}
        with patch('pipeline.themes.merge_small_groups', return_value=([[0], [1, 2, 3, 4]], details)):
            result = self.run_fixture(merge_small_themes=True)
        self.assertEqual(result['theme_merging']['final_theme_sources'][0], {'theme_id': 1, 'initial_theme_ids': [2, 3]})
        self.assertEqual(result['assignments'][0], {'row_position': 1, 'theme_id': 2})
        self.assertEqual(result['theme_merging']['retained_small_theme_ids'], [2])

    def test_invalid_flag_rejected_before_model_loading(self):
        for value in ['true', 1, None]:
            with self.subTest(value=value), patch('pipeline.themes._theme_vectors') as embed:
                with self.assertRaisesRegex(ThemeError, 'true or false'):
                    analyze_themes(self.fixture(), merge_small_themes=value)
                embed.assert_not_called()

    def test_merge_failure_does_not_leak_text(self):
        with patch('pipeline.themes.merge_small_groups', side_effect=RuntimeError('private text')):
            with self.assertRaises(ThemeError) as caught:
                self.run_fixture(merge_small_themes=True)
        self.assertNotIn('private text', str(caught.exception))

    def test_auto_fallback_remains_unscored_and_warns_no_partner(self):
        with patch('pipeline.themes._theme_vectors', return_value=np.ones((1, 2))):
            result = analyze_themes(self.fixture().iloc[[1]], theme_count='auto', merge_small_themes=True)
        self.assertEqual(result['theme_selection']['candidate_scores'], [])
        self.assertEqual(result['theme_merging']['history'], [])
        self.assertEqual(result['theme_merging']['retained_small_theme_ids'], [1])
        self.assertTrue(any('returned one group' in warning for warning in result['warnings']))
