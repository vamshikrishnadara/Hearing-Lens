import unittest
from decimal import Decimal
import pandas as pd
from pipeline.reference import parse_reference, ReferenceError


class ReferenceTests(unittest.TestCase):
    def test_manual_percent_and_proportion_agree(self):
        a = parse_reference({'Renter': '62%', 'Owner': '38%'})
        b = parse_reference({'Renter': .62, 'Owner': .38})
        self.assertEqual(a, b)
        self.assertEqual(a[0].share, Decimal('.62'))

    def test_custom_columns_preserve_zero_padded_groups(self):
        frame = pd.DataFrame({'district': [' 01 ', '02'], 'population': ['.4', '.6']})
        before = frame.copy(deep=True)
        groups = parse_reference(frame, group_column='district', share_column='population')
        self.assertEqual([g.key for g in groups], ['01', '02'])
        pd.testing.assert_frame_equal(frame, before)

    def test_duplicate_and_blank_labels_rejected(self):
        for labels in [[' Renter', 'renter '], ['', 'Owner'], [None, 'Owner']]:
            with self.subTest(labels=labels), self.assertRaises(ReferenceError):
                parse_reference(pd.DataFrame({'group': labels, 'share': [.5, .5]}))

    def test_reject_bad_units_nonfinite_and_negative_without_echoing(self):
        for value in [62, -0.1, 'NaN', 'Infinity', True, 'secret value', None, [1], '1e-400', '1e1000000%']:
            with self.subTest(value=value), self.assertRaises(ReferenceError) as caught:
                parse_reference({'group': value})
            self.assertNotIn('secret value', str(caught.exception))

    def test_require_complete_distribution_without_rescaling(self):
        for values in [{}, {'A': .4, 'B': .5}, {'A': .6, 'B': .5}]:
            with self.assertRaises(ReferenceError): parse_reference(values)
        groups = parse_reference({'A': '33.333333%', 'B': '66.666667%'})
        self.assertEqual(groups[0].share, Decimal('.33333333'))

    def test_bad_mapping_and_duplicate_columns_rejected(self):
        for frame in [pd.DataFrame({'group': ['A']}), pd.DataFrame([['A', 1, 1]], columns=['group', 'share', 'share'])]:
            with self.assertRaises(ReferenceError): parse_reference(frame)
        with self.assertRaises(ReferenceError): parse_reference('untrusted upload text')

class ReferenceCSVTests(unittest.TestCase):
    def test_csv_preserves_group_codes_and_maps_headers(self):
        from io import BytesIO
        from pipeline.reference import load_reference_csv
        stream = BytesIO(b'\xef\xbb\xbfarea,population\n001,60%\n002,40%\n')
        result = load_reference_csv(stream, group_column='area', share_column='population')
        self.assertEqual(result.group.tolist(), ['001', '002'])
        self.assertEqual(stream.tell(), 0)
        self.assertEqual(parse_reference(result)[0].share, Decimal('.6'))

    def test_unreadable_csv_and_invalid_mapping_are_safe(self):
        from io import BytesIO
        from pipeline.reference import load_reference_csv
        for content in [b'', b'private,secret\nA,1\n', b'group,share\n"private,1']:
            with self.subTest(content=content), self.assertRaises(ReferenceError) as caught:
                load_reference_csv(BytesIO(content))
            self.assertNotIn('private', str(caught.exception))

    def test_oversized_reference_is_rejected_not_sampled(self):
        from io import StringIO
        from pipeline.reference import load_reference_csv
        stream = StringIO('group,share\n' + '\n'.join(f'{i},0' for i in range(5001)))
        with self.assertRaisesRegex(ReferenceError, '5,000'):
            load_reference_csv(stream)
