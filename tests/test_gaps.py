import json
import unittest
import pandas as pd
from pipeline.gaps import analyze_gaps, GapError
from pipeline.ingest import map_columns


def frame(groups):
    return pd.DataFrame({'comment_text': ['A comment'] * len(groups), 'subgroup__role': groups})


def rows_by_group(result):
    return {r['group']: r for r in result['rows']}


class GapTests(unittest.TestCase):
    def test_known_arithmetic_and_direction(self):
        source = frame(['Renter'] * 20 + ['Owner'] * 80)
        before = source.copy(deep=True)
        result = analyze_gaps(source, references={'subgroup__role': {'Renter': '.5', 'Owner': '50%'}})
        rows = rows_by_group(result)
        self.assertEqual(rows['Renter']['count'], 20)
        self.assertEqual(rows['Renter']['participation_share'], .2)
        self.assertEqual(rows['Renter']['gap_percentage_points'], -30)
        self.assertEqual(rows['Renter']['representation_ratio'], .4)
        self.assertEqual(rows['Renter']['flag'], 'underrepresented')
        self.assertEqual(rows['Owner']['gap_percentage_points'], 30)
        self.assertEqual(rows['Owner']['flag'], 'overrepresented')
        json.dumps(result, allow_nan=False)
        pd.testing.assert_frame_equal(source, before)

    def test_exact_thresholds_are_not_flagged(self):
        rows = rows_by_group(analyze_gaps(frame(['A'] * 30 + ['B'] * 50 + ['C'] * 20),
            references={'subgroup__role': {'A': '.4', 'B': '.4', 'C': '.2'}}))
        self.assertEqual(rows['A']['representation_ratio'], .75)
        self.assertEqual(rows['B']['representation_ratio'], 1.25)
        self.assertEqual(rows['A']['flag'], 'within_range')
        self.assertEqual(rows['B']['flag'], 'within_range')

    def test_suppression_hides_all_derived_metrics_and_complement(self):
        result = analyze_gaps(frame(['A'] * 9 + ['B'] * 10 + ['C'] * 81),
            references={'subgroup__role': {'A': '.2', 'B': '.2', 'C': '.6'}})
        rows = rows_by_group(result)
        for group in ['A', 'B']:
            self.assertTrue(rows[group]['suppressed'])
            for key in ['count', 'participation_share', 'gap_percentage_points', 'representation_ratio']:
                self.assertIsNone(rows[group][key])
        self.assertEqual(rows['B']['suppression_reason'], 'complementary')
        self.assertEqual(rows['A']['reference_share'], .2)
        self.assertEqual(rows['C']['count'], 81)
        self.assertEqual(rows['C']['participation_share'], .81)

    def test_ten_rows_visible_and_nine_not_visible(self):
        r = rows_by_group(analyze_gaps(frame(['A'] * 10 + ['B'] * 10)))
        self.assertTrue(all(not v['suppressed'] for v in r.values()))
        r = rows_by_group(analyze_gaps(frame(['A'] * 9 + ['B'] * 9 + ['C'] * 20)))
        self.assertFalse(r['C']['suppressed'])
        self.assertTrue(r['A']['suppressed'])

    def test_missing_values_and_empty_comments_do_not_change_known_denominator(self):
        source = frame([' A '] * 10 + ['a'] * 10 + ['B'] * 20 + ['', None] * 5)
        source.loc[len(source)] = ['  ', 'B']
        result = analyze_gaps(source)
        self.assertEqual(rows_by_group(result)['A']['participation_share'], .5)
        self.assertEqual(result['fields'][0]['eligible_rows'], 50)
        self.assertEqual(result['fields'][0]['known_rows'], 40)
        self.assertEqual(result['fields'][0]['missing_rows'], 10)
        self.assertTrue(all(r['flag'] == 'no_reference' for r in result['rows']))

    def test_unmatched_category_stays_in_denominator(self):
        r = rows_by_group(analyze_gaps(frame(['A'] * 40 + ['Other'] * 60),
            references={'subgroup__role': {'A': '.5', 'B': '.5'}}))
        self.assertEqual(r['A']['participation_share'], None)  # complementary to B (0-9)
        self.assertEqual(r['Other']['participation_share'], .6)
        self.assertEqual(r['Other']['flag'], 'unmatched')
        self.assertIsNone(r['Other']['representation_ratio'])
        self.assertIsNone(r['B']['count'])

    def test_zero_reference_never_produces_infinity(self):
        r = rows_by_group(analyze_gaps(frame(['A'] * 10 + ['B'] * 10),
            references={'subgroup__role': {'A': 0, 'B': 1}}))
        self.assertIsNone(r['A']['representation_ratio'])
        self.assertEqual(r['A']['gap_percentage_points'], 50)
        self.assertEqual(r['A']['flag'], 'zero_reference')

    def test_invalid_reference_preserves_counts_and_other_fields(self):
        source = frame(['A'] * 10 + ['B'] * 10)
        source['subgroup__language'] = ['English'] * 20
        result = analyze_gaps(source, references={'subgroup__role': {'A': 99},
            'subgroup__language': {'English': 1}})
        self.assertEqual(result['fields'][0]['reference_status'], 'invalid')
        self.assertEqual(result['fields'][1]['status'], 'comparison')
        self.assertTrue(all(r['gap_percentage_points'] is None for r in result['rows'] if r['field'] == 'subgroup__role'))

    def test_missing_fields_all_unknown_and_empty_frame_are_unavailable(self):
        self.assertEqual(analyze_gaps(pd.DataFrame({'comment_text': ['Parent speaks English']}))['status'], 'unavailable')
        for source in [frame([None, ' ']), frame([])]:
            r = analyze_gaps(source, references={'subgroup__role': {'A': 1}})
            self.assertEqual(r['rows'], [])
            self.assertEqual(r['status'], 'unavailable')

    def test_only_explicit_or_mapped_fields_used(self):
        source = pd.DataFrame({'comment_text': ['Parent speaks English'] * 20, 'role': ['Parent'] * 20})
        self.assertEqual(analyze_gaps(source)['rows'], [])
        self.assertEqual(analyze_gaps(source, subgroup_columns=['role'])['rows'][0]['count'], 20)
        for options in [{'subgroup_columns': ['missing']}, {'subgroup_columns': ['comment_text']},
                        {'subgroup_columns': ['role', 'role']}, {'minimum_group_size': 9},
                        {'minimum_group_size': True}, {'references': {'wrong': {'A': 1}}}]:
            with self.subTest(options=options), self.assertRaises(GapError): analyze_gaps(source, **options)

    def test_ingest_integration_counts_cleaned_rows(self):
        source = pd.DataFrame({'text': ['x'] * 21 + [' '], 'id': list(range(20)) + [0, 21], 'role': ['A'] * 22})
        mapped = map_columns(source, comment_column='text', respondent_id_column='id', subgroup_columns=['role'])
        result = analyze_gaps(mapped.frame, references={'subgroup__role': {'A': 1}})
        self.assertEqual(result['rows'][0]['count'], 20)
        self.assertEqual(result['rows'][0]['representation_ratio'], 1)

    def test_only_small_groups_no_synthetic_other_bucket(self):
        r = analyze_gaps(frame(['A'] * 3 + ['B'] * 4))
        self.assertEqual(len(r['rows']), 2)
        self.assertTrue(all(x['count'] is None for x in r['rows']))
        self.assertEqual(r['fields'][0]['known_rows'], 7)

    def test_stricter_threshold_supported(self):
        r = analyze_gaps(frame(['A'] * 15 + ['B'] * 25), minimum_group_size=20)
        self.assertTrue(all(x['suppressed'] for x in r['rows']))

    def test_inputs_are_not_echoed_in_error(self):
        source = frame([['sensitive value']])
        with self.assertRaises(GapError) as caught: analyze_gaps(source)
        self.assertNotIn('sensitive value', str(caught.exception))
