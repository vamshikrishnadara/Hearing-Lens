from io import BytesIO
import unittest

import pandas as pd

from pipeline.ingest import IngestError, list_excel_sheets, load_table, map_columns


def csv_upload(text: str) -> BytesIO:
    return BytesIO(text.encode("utf-8"))


def xlsx_upload(sheets: dict[str, pd.DataFrame]) -> BytesIO:
    stream = BytesIO()
    with pd.ExcelWriter(stream, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
    stream.seek(0)
    return stream


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

    def test_loads_windows_1252_csv_with_a_notice(self) -> None:
        stream = BytesIO("comment\nSchool needs books – now\n".encode("cp1252"))

        result = load_table(stream, filename="comments.csv")

        self.assertEqual(result.frame.iloc[0]["comment"], "School needs books – now")
        self.assertTrue(any("Windows-1252" in warning for warning in result.warnings))

    def test_lists_and_loads_selected_excel_sheet(self) -> None:
        stream = xlsx_upload(
            {
                "Instructions": pd.DataFrame({"note": ["Choose Responses"]}),
                "Responses": pd.DataFrame(
                    {"comment": ["Keep the program"], "ward": [8]}
                ),
            }
        )

        self.assertEqual(
            list_excel_sheets(stream, filename="comments.xlsx"),
            ["Instructions", "Responses"],
        )
        result = load_table(
            stream,
            filename="comments.xlsx",
            sheet_name="Responses",
        )

        self.assertEqual(result.sheet_name, "Responses")
        self.assertEqual(result.frame.iloc[0]["comment"], "Keep the program")

    def test_rejects_missing_excel_sheet(self) -> None:
        stream = xlsx_upload({"Responses": pd.DataFrame({"comment": ["Text"]})})

        with self.assertRaisesRegex(IngestError, "selected sheet"):
            load_table(stream, filename="comments.xlsx", sheet_name="Missing")

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

    def test_mapping_rejects_reusing_one_source_column(self) -> None:
        frame = pd.DataFrame({"answer": ["text"]})

        with self.assertRaisesRegex(IngestError, "only once"):
            map_columns(
                frame,
                comment_column="answer",
                subgroup_columns=["answer"],
            )

    def test_rejects_unsupported_file_type(self) -> None:
        with self.assertRaisesRegex(IngestError, "CSV or XLSX"):
            load_table(csv_upload("hello"), filename="comments.txt")


if __name__ == "__main__":
    unittest.main()
