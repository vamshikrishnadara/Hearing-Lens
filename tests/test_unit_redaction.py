"""Regression checks for ordinary words versus apartment/suite identifiers."""

import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import pandas as pd

from pipeline.redact import _PATTERNS, _redact_detected_text, build_safe_display_frame, redact_frame


class UnitRedactionTests(unittest.TestCase):
    def test_all_fictional_pattern_cases(self):
        cases = json.loads((Path(__file__).resolve().parents[1] / 'data/samples/unit_redaction_cases.json').read_text())
        for case in cases:
            with self.subTest(text=case['text']):
                self.assertEqual(_redact_detected_text(case['text'], []).text, case['expected_pattern_output'])

    def test_full_pipeline_preserves_ordinary_words_and_redacts_supported_units(self):
        texts = [
            'Please take the next step and do not steal money.',
            'My address includes Apt 4B and Ste. 200.',
            'My address includes Unit A and Suite B12.',
        ]
        result = redact_frame(pd.DataFrame({'comment_text': texts}))
        self.assertEqual(result.frame.redacted_comment_text.tolist(), [
            texts[0], 'My address includes [UNIT_NUMBER] and [UNIT_NUMBER].',
            'My address includes [UNIT_NUMBER] and [UNIT_NUMBER].',
        ])
        self.assertEqual(result.entity_counts, {'UNIT_NUMBER': 4})

    def test_pattern_does_not_match_partial_identifiers_or_label_prefixes(self):
        pattern = dict(_PATTERNS)['UNIT_NUMBER']
        for text in ['step2', 'united12', 'suite of tools', 'Unit Alpha', 'Unit A-name', 'Unit B_name', 'AptB', 'ApartmentBlue']:
            with self.subTest(text=text):
                self.assertIsNone(pattern.search(text))

    def test_person_detection_remains_active_for_names_starting_with_ste(self):
        text = 'Steve lives in Apt 4B.'
        entity = SimpleNamespace(label_='PERSON', start_char=0, end_char=5)
        result = _redact_detected_text(text, [entity])
        self.assertEqual(result.text, '[PERSON] lives in [UNIT_NUMBER].')
        self.assertEqual(result.entity_counts, {'PERSON': 1, 'UNIT_NUMBER': 1})

    def test_preview_keeps_wording_and_excludes_metadata(self):
        frame = pd.DataFrame({'comment_text': ['Take the next step. I live in Apt 4B.'], 'respondent_id': ['private-id']})
        original = frame.copy(deep=True)
        result = build_safe_display_frame(frame)
        self.assertEqual(result.frame.columns.tolist(), ['comment_text'])
        self.assertEqual(result.frame.iloc[0, 0], 'Take the next step. I live in [UNIT_NUMBER].')
        pd.testing.assert_frame_equal(frame, original)


if __name__ == '__main__':
    unittest.main()
