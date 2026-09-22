"""Protect the narrow lighting correction and its name-redaction boundaries."""

import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import pandas as pd

from pipeline.redact import _redact_detected_text, build_safe_display_frame, redact_text


class LightingRedactionTests(unittest.TestCase):
    def test_focused_examples_with_real_model(self):
        fixture = Path(__file__).resolve().parents[1] / "data/samples/lighting_redaction_cases.json"
        for case in json.loads(fixture.read_text()):
            with self.subTest(text=case["text"]):
                self.assertEqual(redact_text(case["text"]).text, case["expected_output"])

    def test_rule_does_not_suppress_other_person_contexts_or_longer_spans(self):
        cases = [
            ("Broken Smith spoke.", "Broken", "[PERSON] Smith spoke."),
            ("Broken Smith spoke.", "Broken Smith", "[PERSON] spoke."),
            ("Contact Broken exterior lighting staff.", "Broken", "Contact [PERSON] exterior lighting staff."),
            ("Broken exterior lighting needs repair.", "Broken exterior", "[PERSON] lighting needs repair."),
            ("Broken exterior lightings were mentioned.", "Broken", "[PERSON] exterior lightings were mentioned."),
            ("Broken spoke at the hearing.", "Broken", "[PERSON] spoke at the hearing."),
        ]
        for text, detected, expected in cases:
            with self.subTest(text=text, detected=detected):
                start = text.index(detected)
                entity = SimpleNamespace(start_char=start, end_char=start + len(detected), label_="PERSON")
                result = _redact_detected_text(text, [entity])
                self.assertEqual(result.text, expected)
                self.assertEqual(result.entity_counts, {"PERSON": 1})

    def test_opening_phrase_preserves_whitespace_and_casing(self):
        for text, word in [
            ("  Broken exterior lighting needs repair.", "Broken"),
            ("BROKEN exterior lighting needs repair.", "BROKEN"),
            ("broken\texterior lighting needs repair.", "broken"),
        ]:
            with self.subTest(text=text):
                start = text.index(word)
                entity = SimpleNamespace(start_char=start, end_char=start + len(word), label_="PERSON")
                result = _redact_detected_text(text, [entity])
                self.assertEqual(result.text, text)
                self.assertEqual(result.entity_counts, {})

    def test_preview_keeps_other_names_contacts_and_counts_protected(self):
        source = (
            "Broken exterior lighting was reported by John Smith. "
            "Contact resident@example.org or (312) 555-0199."
        )
        frame = pd.DataFrame({"comment_text": [source], "respondent_id": ["TEST-001"]})
        result = build_safe_display_frame(frame)
        self.assertEqual(list(result.frame.columns), ["comment_text"])
        self.assertEqual(
            result.frame.iloc[0, 0],
            "Broken exterior lighting was reported by [PERSON]. "
            "Contact [EMAIL_ADDRESS] or [PHONE_NUMBER].",
        )
        self.assertEqual(result.entity_counts, {"EMAIL_ADDRESS": 1, "PERSON": 1, "PHONE_NUMBER": 1})
        self.assertEqual(frame.iloc[0]["comment_text"], source)


if __name__ == "__main__":
    unittest.main()
