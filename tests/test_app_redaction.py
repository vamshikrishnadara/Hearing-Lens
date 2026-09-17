"""Exercise the preview and error UI in Streamlit's in-process test runner."""

from io import BytesIO
from pathlib import Path
from unittest.mock import patch
import unittest

from streamlit.testing.v1 import AppTest

from pipeline.redact import RedactionError


APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


class AppRedactionTests(unittest.TestCase):
    def make_upload(self):
        upload = BytesIO(b"comment\nMy name is John Smith and I support more counselors.\n")
        upload.name = "fictional_names.csv"
        return upload

    def test_preview_displays_person_marker(self):
        with patch("streamlit.file_uploader", return_value=self.make_upload()):
            app = AppTest.from_file(str(APP), default_timeout=30).run()
            app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertEqual(len(app.dataframe), 1)
        rendered = app.dataframe[0].value.to_csv(index=False)
        self.assertIn("[PERSON]", rendered)
        self.assertNotIn("John Smith", rendered)

    def test_model_failure_shows_error_without_preview_or_success(self):
        with patch("streamlit.file_uploader", return_value=self.make_upload()):
            app = AppTest.from_file(str(APP), default_timeout=30).run()
            with patch(
                "pipeline.redact._get_person_model",
                side_effect=RedactionError("Name detection unavailable; preview blocked."),
            ):
                app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.dataframe), 0)
        self.assertEqual(len(app.success), 0)
        self.assertEqual(app.error[0].value, "Name detection unavailable; preview blocked.")


if __name__ == "__main__":
    unittest.main()
