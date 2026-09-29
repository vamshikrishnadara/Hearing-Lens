"""Ensure comparison output contains aggregates and no comment/quote text."""
import json
import unittest
from unittest.mock import patch

import pandas as pd

from scripts.compare_theme_selection import compare, summarize


class ThemeSelectionReportTests(unittest.TestCase):
    def test_summary_omits_text_and_row_positions_and_checks_quote_lengths(self):
        result = {
            'theme_selection': {'selected_count': 1}, 'analyzed_comments': 2,
            'themes': [{'count': 2, 'label': 'private label', 'quotes': [
                {'row_position': 99, 'text': 'private short quote'}]}],
            'assignments': [{'row_position': 99, 'theme_id': 1}],
        }
        report = summarize(result)
        self.assertEqual(report['group_sizes'], [2])
        self.assertFalse(report['all_quote_lengths_valid'])
        self.assertNotIn('private', json.dumps(report))
        self.assertNotIn('row_position', json.dumps(report))

    def test_comparison_passes_text_only_and_uses_truth_afterward(self):
        frame = pd.DataFrame({'comment_text': ['one', 'two'], 'validation_theme': ['a', 'b'], 'complaint_id': ['x', 'y']})
        result = {'theme_selection': {}, 'analyzed_comments': 2, 'themes': [],
                  'assignments': [{'row_position': 0, 'theme_id': 1}, {'row_position': 1, 'theme_id': 2}]}
        with patch('scripts.compare_theme_selection.analyze_themes', return_value=result) as analyze:
            summaries, _ = compare(frame, 3)
        self.assertEqual([call.kwargs['theme_count'] for call in analyze.call_args_list], [3, 'auto'])
        for call in analyze.call_args_list:
            self.assertEqual(call.args[0].columns.tolist(), ['comment_text'])
        self.assertEqual(summaries['auto']['adjusted_rand_index'], 1)
