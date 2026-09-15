from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from scripts.generate_synthetic_sample import FIELDNAMES, generate_rows, write_csv


class SampleGeneratorTests(unittest.TestCase):
    def test_generates_requested_size_and_schema(self) -> None:
        rows = generate_rows(count=1_000)

        self.assertEqual(len(rows), 1_000)
        self.assertEqual(tuple(rows[0]), FIELDNAMES)
        self.assertEqual(len({row["respondent_id"] for row in rows}), 1_000)

    def test_contains_all_planted_themes_and_hearing_dates(self) -> None:
        rows = generate_rows(count=1_000)

        self.assertEqual(len({row["validation_theme"] for row in rows}), 6)
        self.assertEqual(len({row["hearing_date"] for row in rows}), 3)

    def test_includes_synthetic_redaction_examples(self) -> None:
        comments = " ".join(
            str(row["comment_text"]) for row in generate_rows(count=1_000)
        )

        self.assertIn("@example.org", comments)
        self.assertIn("312-555-", comments)
        self.assertIn(" Apt ", comments)

    def test_seed_is_reproducible(self) -> None:
        self.assertEqual(
            generate_rows(count=25, seed=42),
            generate_rows(count=25, seed=42),
        )
        self.assertNotEqual(
            generate_rows(count=25, seed=42),
            generate_rows(count=25, seed=43),
        )

    def test_rejects_nonpositive_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 1"):
            generate_rows(count=0)

    def test_writes_a_readable_csv(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            write_csv(path, generate_rows(count=12, seed=7))
            frame = pd.read_csv(path)

        self.assertEqual(len(frame), 12)
        self.assertEqual(tuple(frame.columns), FIELDNAMES)


if __name__ == "__main__":
    unittest.main()
