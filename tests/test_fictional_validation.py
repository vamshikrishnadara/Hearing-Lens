from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from scripts.validate_fictional import cases, check_result, scenario_checks, validate, main


class FictionalValidationTests(unittest.TestCase):
    def fixture(self):
        frame = pd.DataFrame({'comment_text': ['The school needs books.'] * 3})
        result = {'input_rows': 3,
            'themes': {'assignments': [{'row_position': i, 'theme_id': 1} for i in range(3)],
                       'analyzed_comments': 3, 'outlier_count': 0,
                       'themes': [{'theme_id': 1, 'count': 3, 'quotes': []}]},
            'affect': {'rows': [{'row_position': i} for i in range(3)]},
            'timeline': {'theme_volumes': [{'count': 3}], 'periods': [{'total_comments': 3}]},
            'affect_by_theme': [{'total_comments': 3}], 'gaps': {'rows': []},
            'questions': {'input_rows': 3, 'groups': [], 'assignments': [], 'question_count': 0,
                          'comment_question_counts': [0, 0, 0], 'top_unanswered': []}}
        return frame, result

    def test_consistent_fixture_and_broken_module_totals(self):
        frame, good = self.fixture()
        self.assertTrue(all(check_result(good, frame).values()))
        mutations = [lambda r: r.update(input_rows=4),
            lambda r: r['affect']['rows'].reverse(),
            lambda r: r['themes']['assignments'].append({'row_position': 0, 'theme_id': 1}),
            lambda r: r['timeline']['theme_volumes'][0].update(count=2),
            lambda r: r['affect_by_theme'][0].update(total_comments=2)]
        for mutate in mutations:
            result = deepcopy(good); mutate(result)
            self.assertFalse(all(check_result(result, frame).values()))

    def test_question_integrity_and_priority_corruption_fail(self):
        frame, result = self.fixture()
        result['questions']['comment_question_counts'] = [1, 0, 0]
        self.assertFalse(check_result(result, frame)['question_counts'])
        result['questions']['top_unanswered'] = ['unknown']
        self.assertFalse(check_result(result, frame)['priority_selection'])

    def test_suppressed_metrics_cannot_be_visible(self):
        frame, result = self.fixture()
        result['gaps']['rows'] = [{'suppressed': True, 'count': 1,
            'participation_share': None, 'gap_percentage_points': None, 'representation_ratio': None}]
        self.assertFalse(check_result(result, frame)['suppressed_metrics'])
        result['gaps']['rows'][0]['count'] = None
        self.assertTrue(check_result(result, frame)['suppressed_metrics'])

    def test_invalid_question_position_does_not_pass(self):
        frame, result = self.fixture()
        result['questions']['assignments'] = [{'row_position': -1, 'sentence_index': 0, 'question_group_id': 'q001'}]
        checks = check_result(result, frame)
        self.assertFalse(checks['question_positions'])
        self.assertFalse(checks['question_groups'])

    def test_wrong_representative_source_fails(self):
        frame, result = self.fixture()
        result['questions']['groups'] = [{'question_group_id': 'q001', 'comment_count': 0,
            'sentence_count': 0, 'response_match_status': 'not_checked',
            'representative': {'row_position': 0, 'source_start': 0, 'source_end': 3, 'text': 'Wrong'}}]
        self.assertFalse(check_result(result, frame)['question_sources'])

    def test_fixed_scenarios_have_expected_edges(self):
        fixtures = cases()
        self.assertEqual(len(fixtures), 5)
        self.assertEqual(len(fixtures['school_benchmark']['frame']), 1000)
        self.assertEqual(list(fixtures['missing_optional']['frame']), ['comment_text'])
        self.assertEqual(fixtures['small_groups']['frame'].role.value_counts().to_dict(),
                         {'Parent': 20, 'Teacher': 10, 'Student': 1})

    def test_existing_destination_preserved_before_loading(self):
        with tempfile.TemporaryDirectory() as temp, patch('scripts.validate_fictional.cases') as load:
            with self.assertRaises(ValueError): validate(temp)
            load.assert_not_called()

    def test_failed_target_produces_unsuccessful_exit(self):
        for structural, target in [(False, True), (True, False), (True, True)]:
            with patch('scripts.validate_fictional.validate', return_value={
                    'all_checks_passed': structural, 'benchmark_targets_passed': target}):
                self.assertEqual(main(['--output-dir', 'unused']), 0 if structural and target else 1)

    def test_unknown_scenario_rejected(self):
        with self.assertRaises(ValueError): scenario_checks('unknown', {}, pd.DataFrame())
