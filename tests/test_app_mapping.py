"""Check comment-column defaults and manual choices in the running app."""

from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "streamlit_app.py"


class AppMappingTests(unittest.TestCase):
    def csv_upload(self, text):
        upload = BytesIO(text.encode("utf-8"))
        upload.name = "fictional_comments.csv"
        return upload

    def selectbox(self, app, label):
        return next(widget for widget in app.selectbox if widget.label == label)

    def test_sample_selects_comment_text_instead_of_respondent_id(self):
        sample = ROOT / "data" / "samples" / "synthetic_chicago_hearing.csv"
        with patch("streamlit.file_uploader", return_value=self.csv_upload(sample.read_text())):
            app = AppTest.from_file(str(APP)).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(self.selectbox(app, "Comment text").value, "comment_text")
        self.assertEqual(self.selectbox(app, "Respondent ID").value, "Not provided")

    def test_workbook_sheet_uses_its_own_comment_column_default(self):
        upload = BytesIO()
        with pd.ExcelWriter(upload, engine="openpyxl") as writer:
            pd.DataFrame({"note": ["Choose Responses"]}).to_excel(
                writer, sheet_name="Instructions", index=False
            )
            pd.DataFrame({"respondent_id": ["TEST-001"], "comment_text": ["More books."]}).to_excel(
                writer, sheet_name="Responses", index=False
            )
        upload.seek(0)
        upload.name = "fictional_comments.xlsx"
        with patch("streamlit.file_uploader", return_value=upload):
            app = AppTest.from_file(str(APP)).run()
            self.assertEqual(self.selectbox(app, "Comment text").value, "note")
            self.selectbox(app, "Workbook sheet").select("Responses").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(self.selectbox(app, "Comment text").value, "comment_text")

    def test_other_headers_keep_first_column_and_allow_manual_selection(self):
        upload = self.csv_upload("respondent_id,response\nTEST-001,More books.\n")
        with patch("streamlit.file_uploader", return_value=upload):
            app = AppTest.from_file(str(APP)).run()
            self.assertEqual(self.selectbox(app, "Comment text").value, "respondent_id")
            self.selectbox(app, "Comment text").select("response").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(self.selectbox(app, "Comment text").value, "response")

    def test_manual_override_survives_optional_mapping_rerun(self):
        upload = self.csv_upload(
            "respondent_id,comment_text,alternate_response\n"
            "TEST-001,More books.,More art classes.\n"
        )
        with patch("streamlit.file_uploader", return_value=upload):
            app = AppTest.from_file(str(APP)).run()
            self.assertEqual(self.selectbox(app, "Comment text").value, "comment_text")
            self.selectbox(app, "Comment text").select("alternate_response").run()
            self.selectbox(app, "Respondent ID").select("respondent_id").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(self.selectbox(app, "Comment text").value, "alternate_response")
        self.assertNotIn("alternate_response", app.multiselect[0].options)


if __name__ == "__main__":
    unittest.main()
