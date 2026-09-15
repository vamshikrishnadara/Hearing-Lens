from io import BytesIO
import unittest

import pandas as pd

from pipeline.ingest import IngestError, load_table, map_columns


def csv_upload(text: str) -> BytesIO:
    return BytesIO(text.encode("utf-8"))


class IngestTests(unittest.TestCase):
    def test_loads_csv_and_preserves_headers(self) -> None:
        result = load_table(
            csv_upload("response,ward\nKeep the school open,10\nAdd counselors,12\n"),
            filename="comments.csv",
        )

        self.assertEqual(list(result.frame.columns), ["response", "ward"])
        self.assertEqual(len(result.frame), 2)
        self.assertEqual(result.rows_omitted, 0)

    def test_row_cap_is_enforced_with_a_notice(self) -> None:
        result = load_table(
            csv_upload("comment\none\ntwo\nthree\n"),
            filename="comments.csv",
            row_cap=2,
        )

        self.assertEqual(len(result.frame), 2)
        self.assertEqual(result.rows_omitted, 1)
        self.assertTrue(result.warnings)

    def test_mapping_removes_empty_comments_and_repeated_ids(self) -> None:
        frame = pd.DataFrame(
            {
                "answer": [" First comment ", "", "Duplicate response", "New response"],
                "person": ["A", "B", "A", "C"],
                "ward": [1, 2, 1, 3],
            }
        )

        result = map_columns(
            frame,
            comment_column="answer",
            respondent_id_column="person",
            subgroup_columns=["ward"],
        )

        self.assertEqual(
            result.frame["comment_text"].tolist(), ["First comment", "New response"]
        )
        self.assertEqual(result.empty_comments_removed, 1)
        self.assertEqual(result.duplicate_respondents_removed, 1)
        self.assertIn("subgroup__ward", result.frame.columns)

    def test_mapping_rejects_a_missing_comment_column(self) -> None:
        with self.assertRaisesRegex(IngestError, "comment"):
            map_columns(pd.DataFrame({"answer": ["text"]}), comment_column="missing")

    def test_rejects_unsupported_file_type(self) -> None:
        with self.assertRaisesRegex(IngestError, "CSV or XLSX"):
            load_table(csv_upload("hello"), filename="comments.txt")


if __name__ == "__main__":
    unittest.main()
