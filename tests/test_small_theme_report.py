"""Comparison reports must expose failures without exposing comment text."""
import copy
import json
import unittest
from unittest.mock import patch
import pandas as pd
from scripts.compare_small_themes import compare, summarize


class SmallThemeReportTests(unittest.TestCase):
    def result(self):
        return {
            'theme_selection': {'selected_count': 1}, 'theme_merging': {'enabled': False},
            'analyzed_comments': 1,
            'themes': [{'theme_id': 1, 'count': 1, 'share': 1., 'label': 'private label',
                        'quotes': [{'row_position': 0, 'text': 'private ' * 12}]}],
            'assignments': [{'row_position': 0, 'theme_id': 1}],
        }

    def test_correct_results_pass_and_report_omits_text(self):
        report = summarize(self.result(), ['private ' * 12])
        self.assertTrue(all(report['checks'].values()))
        self.assertNotIn('private', json.dumps(report))
        self.assertNotIn('row_position', json.dumps(report))

    def test_incorrect_counts_quotes_and_duplicate_assignments_are_detected(self):
        result = self.result()
        result['assignments'] *= 2
        result['themes'][0]['share'] = .5
        result['themes'][0]['quotes'][0] = {'row_position': 9, 'text': 'changed'}
        checks = summarize(result, ['private ' * 12])['checks']
        self.assertFalse(any(checks.values()))

    def test_only_comment_text_enters_analysis_and_modes_are_explicit(self):
        frame = pd.DataFrame({'comment_text': ['private ' * 12], 'respondent_id': ['private-id'], 'validation_theme': ['one']})
        safe = type('Safe', (), {'frame': frame[['comment_text']]})()
        with patch('scripts.compare_small_themes.build_safe_display_frame', return_value=safe), patch(
            'scripts.compare_small_themes.analyze_themes', side_effect=[self.result(), copy.deepcopy(self.result())]
        ) as analyze:
            report, _ = compare(frame, 'auto')
        self.assertEqual([call.kwargs['merge_small_themes'] for call in analyze.call_args_list], [False, True])
        for call in analyze.call_args_list:
            self.assertEqual(call.args[0].columns.tolist(), ['comment_text'])
        self.assertTrue(report['same_analyzed_positions'])
        self.assertNotIn('private', json.dumps(report))
