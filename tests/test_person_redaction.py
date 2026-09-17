"""Person redaction with the installed model and controlled failure cases."""

from types import SimpleNamespace
from unittest.mock import patch
import unittest

import pandas as pd

from pipeline.redact import (
    RedactionError,
    _get_person_model,
    _redact_detected_text,
    build_safe_display_frame,
    redact_frame,
    redact_text,
)


class PersonRedactionTests(unittest.TestCase):
    def test_redacts_a_full_name_with_the_real_model(self):
        result = redact_text("My name is John Smith and I support more counselors.")
        self.assertEqual(result.text, "My name is [PERSON] and I support more counselors.")
        self.assertEqual(result.entity_counts, {"PERSON": 1})

    def test_redacts_two_people_and_repeated_mentions(self):
        result = redact_text("Maria Garcia and David Johnson spoke at the hearing.")
        self.assertEqual(result.text, "[PERSON] and [PERSON] spoke at the hearing.")
        self.assertEqual(result.entity_counts, {"PERSON": 2})
        result = redact_text("John Smith asked a question. John Smith needs an answer.")
        self.assertNotIn("John Smith", result.text)
        self.assertEqual(result.entity_counts, {"PERSON": 2})

    def test_names_and_contacts_share_original_offsets(self):
        result = redact_text(
            "Contact Taylor Parker at resident@example.org or (312) 555-0199."
        )
        self.assertEqual(
            result.text, "Contact [PERSON] at [EMAIL_ADDRESS] or [PHONE_NUMBER]."
        )
        self.assertEqual(
            result.entity_counts, {"EMAIL_ADDRESS": 1, "PERSON": 1, "PHONE_NUMBER": 1}
        )

    def test_overlapping_address_and_person_get_one_complete_replacement(self):
        text = "Meet at 123 John Smith Road, please."
        name_start = text.index("John")
        entity = SimpleNamespace(
            start_char=name_start, end_char=name_start + len("John Smith"), label_="PERSON"
        )
        result = _redact_detected_text(text, [entity])
        self.assertEqual(result.text, "Meet at [STREET_ADDRESS] please.")
        self.assertEqual(result.entity_counts, {"STREET_ADDRESS": 1})

    def test_partial_overlap_does_not_leave_a_detected_name_fragment(self):
        text = "123 Main Street Jones spoke."
        entity = SimpleNamespace(start_char=4, end_char=21, label_="PERSON")
        result = _redact_detected_text(text, [entity])
        self.assertEqual(result.text, "[PERSON] spoke.")
        self.assertEqual(result.entity_counts, {"PERSON": 1})

    def test_frame_preserves_originals_and_aggregates_person_counts(self):
        raw = "My name is John Smith and I support more counselors."
        frame = pd.DataFrame({"comment_text": [raw, None, raw], "respondent_id": [1, 2, 3]})
        original = frame.copy(deep=True)
        result = redact_frame(frame)
        self.assertEqual(result.entity_counts, {"PERSON": 2})
        self.assertEqual(result.frame["redacted_comment_text"].iloc[1], "")
        pd.testing.assert_frame_equal(frame, original)
        self.assertEqual(result.frame["comment_text"].iloc[0], raw)
        preview = build_safe_display_frame(frame)
        self.assertEqual(list(preview.frame.columns), ["comment_text"])
        self.assertNotIn("John Smith", preview.frame.to_csv(index=False))

    def test_empty_text_does_not_need_a_model(self):
        with patch("pipeline.redact._get_person_model", side_effect=AssertionError):
            self.assertEqual(redact_text(None).text, "")
            self.assertEqual(redact_text("").text, "")

    def test_missing_model_blocks_preview_with_sanitized_error(self):
        _get_person_model.cache_clear()
        try:
            with patch("spacy.load", side_effect=OSError("private internal details")):
                with self.assertRaises(RedactionError) as caught:
                    build_safe_display_frame(pd.DataFrame({"comment_text": ["John Smith"]}))
            self.assertIn("preview was not generated", str(caught.exception))
            self.assertNotIn("private internal details", str(caught.exception))
        finally:
            _get_person_model.cache_clear()

    def test_inference_failure_never_returns_partial_results(self):
        class BrokenModel:
            def pipe(self, texts, **kwargs):
                yield SimpleNamespace(text=texts[0], ents=[])
                raise RuntimeError("John Smith was in the failing input")

        with patch("pipeline.redact._get_person_model", return_value=BrokenModel()):
            with self.assertRaises(RedactionError) as caught:
                redact_frame(pd.DataFrame({"comment_text": ["First", "John Smith"]}))
        self.assertNotIn("John Smith", str(caught.exception))

    def test_model_without_person_recognizer_is_rejected(self):
        _get_person_model.cache_clear()
        try:
            with patch("spacy.load", return_value=SimpleNamespace(pipe_names=[])):
                with self.assertRaises(RedactionError):
                    redact_text("John Smith")
        finally:
            _get_person_model.cache_clear()


if __name__ == "__main__":
    unittest.main()
