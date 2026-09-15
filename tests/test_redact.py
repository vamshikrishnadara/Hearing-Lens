import unittest

import pandas as pd

from pipeline.redact import redact_frame, redact_text


class RedactionTests(unittest.TestCase):
    def test_redacts_email_phone_and_url(self) -> None:
        result = redact_text(
            "Email resident@example.org, call (312) 555-0199, or visit "
            "https://example.org/form."
        )

        self.assertEqual(
            result.text,
            "Email [EMAIL_ADDRESS], call [PHONE_NUMBER], or visit [URL].",
        )
        self.assertEqual(
            result.entity_counts,
            {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "URL": 1},
        )

    def test_redacts_street_address_and_unit(self) -> None:
        result = redact_text("I live at 1234 W Main Street, Apt 4B near the school.")

        self.assertNotIn("1234", result.text)
        self.assertNotIn("4B", result.text)
        self.assertIn("[STREET_ADDRESS]", result.text)
        self.assertIn("[UNIT_NUMBER]", result.text)

    def test_preserves_non_pii_numbers_and_public_comment_text(self) -> None:
        text = "Ward 10 needs 3 additional counselors before the next hearing."

        result = redact_text(text)

        self.assertEqual(result.text, text)
        self.assertEqual(result.entity_counts, {})

    def test_handles_empty_and_missing_values(self) -> None:
        self.assertEqual(redact_text("").text, "")
        self.assertEqual(redact_text(None).text, "")
        self.assertEqual(redact_text(float("nan")).text, "")

    def test_redacts_a_frame_without_changing_original_comments(self) -> None:
        frame = pd.DataFrame(
            {
                "comment_text": [
                    "Contact me at person@example.com",
                    "My number is 773-555-0100",
                ],
                "theme": ["communication", "communication"],
            }
        )

        result = redact_frame(frame)

        self.assertEqual(
            result.frame["comment_text"].tolist(), frame["comment_text"].tolist()
        )
        self.assertEqual(
            result.frame["redacted_comment_text"].tolist(),
            ["Contact me at [EMAIL_ADDRESS]", "My number is [PHONE_NUMBER]"],
        )
        self.assertEqual(
            result.entity_counts,
            {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1},
        )

    def test_rejects_an_existing_output_column(self) -> None:
        frame = pd.DataFrame(
            {"comment_text": ["Text"], "redacted_comment_text": ["Existing"]}
        )

        with self.assertRaisesRegex(ValueError, "already exists"):
            redact_frame(frame)


if __name__ == "__main__":
    unittest.main()
