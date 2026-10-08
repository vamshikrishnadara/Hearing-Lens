import json
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from pipeline.full import analyze_all, PipelineError
from pipeline.ingest import map_columns
from pipeline.timeline import build_timeline


class FullPipelineTests(unittest.TestCase):
    def run_fixture(self, raw, **options):
        mapped = map_columns(raw, comment_column='text',
            date_or_hearing_column='date' if 'date' in raw else None,
            respondent_id_column='id' if 'id' in raw else None,
            subgroup_columns=['role'] if 'role' in raw else []).frame
        def themes(frame, **kwargs):
            return {'assignments': [{'row_position': i, 'theme_id': 1} for i in range(len(frame))]}
        def affect(frame):
            return {'rows': [{'row_position': i, 'status': 'excluded_language'} for i in range(len(frame))]}
        # Exercise real orchestration, mapping, gaps, timeline, question detection,
        # grouping and matching; replace only costly theme/affect/vector inference.
        with patch('pipeline.core.analyze_themes', side_effect=themes), \
             patch('pipeline.core.analyze_affect', side_effect=affect), \
             patch('pipeline.questions._embed', side_effect=lambda texts: np.ones((len(texts), 3))):
            return mapped, analyze_all(mapped, **options)

    def test_cleaned_rows_align_every_module_and_dates_survive_mapping(self):
        raw = pd.DataFrame({'text': ['When is the hearing?', '', 'Repeat', 'When is the hearing?'],
                            'id': ['secret-id', '', 'secret-id', 'other-id'],
                            'date': ['2026-10-01', '', '2026-10-02', '2026-10-02']})
        original = raw.copy(deep=True)
        mapped, result = self.run_fixture(raw)
        pd.testing.assert_frame_equal(raw, original)
        self.assertEqual(result['input_rows'], 2)
        self.assertEqual([r['row_position'] for r in result['affect']['rows']], [0, 1])
        self.assertEqual([r['row_position'] for r in result['questions']['assignments']], [0, 1])
        self.assertEqual(result['questions']['groups'][0]['comment_count'], 2)
        self.assertEqual(result['timeline']['mode'], 'date')
        self.assertEqual(len(result['timeline']['periods']), 2)
        self.assertNotIn('secret-id', json.dumps(result, allow_nan=False))

    def test_missing_optional_fields_have_explicit_states(self):
        _, result = self.run_fixture(pd.DataFrame({'text': ['When is the hearing?']}))
        self.assertEqual(result['gaps']['status'], 'unavailable')
        self.assertEqual(result['timeline']['mode'], 'single_period')
        self.assertEqual(result['questions']['response_status'], 'not_provided')
        self.assertEqual(result['questions']['selection_status'], 'response_unavailable')

    def test_invalid_reference_keeps_counts_and_other_analysis(self):
        _, result = self.run_fixture(pd.DataFrame({'text': ['When is the hearing?'] * 10,
                                                   'role': ['Resident'] * 10}),
                                     references={'subgroup__role': {'Resident': .3}})
        self.assertEqual(result['gaps']['fields'][0]['reference_status'], 'invalid')
        self.assertEqual(result['gaps']['rows'][0]['count'], 10)
        self.assertIsNone(result['gaps']['rows'][0]['gap_percentage_points'])
        self.assertEqual(result['questions']['input_rows'], 10)

    def test_same_privacy_minimum_applies_to_gaps_and_question_ranking(self):
        _, result = self.run_fixture(pd.DataFrame({'text': ['When is the hearing?'] * 10,
                                                   'role': ['Resident'] * 10}), minimum_group_size=11)
        self.assertIsNone(result['gaps']['rows'][0]['count'])
        self.assertEqual(result['questions']['groups'][0]['subgroup_spread'], 0)

    def test_no_questions_and_blank_subgroups_are_not_fabricated(self):
        _, result = self.run_fixture(pd.DataFrame({'text': ['The school needs more resources.'], 'role': ['']}))
        self.assertEqual(result['questions']['status'], 'no_questions')
        self.assertEqual(result['questions']['top_unanswered'], [])
        self.assertEqual(result['gaps']['status'], 'unavailable')

    def test_supplied_response_reaches_matching(self):
        _, result = self.run_fixture(pd.DataFrame({'text': ['When is the hearing?']}),
                                     agency_response='The hearing is on Monday.')
        self.assertEqual(result['questions']['response_status'], 'available')
        self.assertEqual(result['questions']['groups'][0]['response_match_status'], 'possible_match')

    def test_contact_details_are_redacted_in_questions_responses_and_hearing_labels(self):
        _, result = self.run_fixture(pd.DataFrame({
            'text': ['Can I email resident@example.org about the hearing?'],
            'date': ['Contact resident@example.org']}),
            agency_response='Please email resident@example.org about the hearing.')
        serialized = json.dumps(result, allow_nan=False)
        self.assertNotIn('resident@example.org', serialized)
        self.assertIn('[EMAIL_ADDRESS]', serialized)

    def test_bad_mapped_input_fails_before_models(self):
        for frame in [None, pd.DataFrame(), pd.DataFrame({'comment_text': ['']}),
                      pd.DataFrame({'comment_text': [None]}),
                      pd.DataFrame({'comment_text': ['ok'] * 5001}),
                      pd.DataFrame([['a', 'b']], columns=['comment_text', 'comment_text'])]:
            with self.subTest(frame_type=type(frame)), patch('pipeline.full.analyze_core') as core:
                with self.assertRaises(PipelineError): analyze_all(frame)
                core.assert_not_called()

    def test_model_failure_is_not_reported_as_partial_success(self):
        with patch('pipeline.full.analyze_core', side_effect=RuntimeError('model unavailable')):
            with self.assertRaises(RuntimeError):
                analyze_all(pd.DataFrame({'comment_text': ['When is the hearing?']}))

    def test_timeline_auto_detects_canonical_period_field(self):
        result = build_timeline(pd.DataFrame({'date_or_hearing': ['2026-10-08']}),
            {'rows': [{'row_position': 0, 'status': 'excluded_language'}]},
            [{'row_position': 0, 'theme_id': 1}])
        self.assertEqual(result['mode'], 'date')
        self.assertEqual(result['periods'][0]['group'], '2026-10-08')
