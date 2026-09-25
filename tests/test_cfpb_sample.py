"""Public sample preparation checks using fictional rows only."""

import csv
import io
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from scripts.prepare_cfpb_sample import REQUIRED, prepare, sample_records, sha256_file


def row(identifier, text='Fictional statement about bank service.', date='2017-05-01'):
    return {'Complaint ID': str(identifier), 'Consumer complaint narrative': text,
            'Date received': date, 'Product': 'Fictional product', 'Issue': 'Fictional issue',
            'Company': 'unused-company', 'State': 'XX'}


class CfpbSampleTests(unittest.TestCase):
    def test_deterministic_selection_scans_beyond_first_rows_and_omits_extra_fields(self):
        records = [row(i) for i in range(1, 101)]
        first, counts = sample_records(records, size=10, seed=42)
        second, _ = sample_records(records, size=10, seed=42)
        self.assertEqual(first, second)
        self.assertEqual(counts['eligible_unique_narratives'], 100)
        self.assertEqual(len({r['complaint_id'] for r in first}), 10)
        self.assertTrue(any(int(r['complaint_id']) > 10 for r in first))
        self.assertNotIn('Company', first[0])
        self.assertNotIn('State', first[0])

    def test_date_blank_and_duplicate_filters_do_not_filter_length(self):
        rows = [row(1, ''), row(2, date='2016-12-31'), row(3, date='2018-01-01'),
                row(4, 'Short.'), row(4, 'Duplicate.'), row(5, 'word ' * 100)]
        sample, counts = sample_records(rows, size=2)
        self.assertEqual([r['complaint_id'] for r in sample], ['4', '5'])
        self.assertEqual(counts['duplicate_eligible_ids_skipped'], 1)
        self.assertEqual(sample[1]['comment_text'], ('word ' * 100).strip())

    def test_invalid_schema_identifier_and_too_few_records_fail(self):
        for records in [[{}], [row('invalid')], [row(1, date='2017-02-30')], []]:
            with self.subTest(records=records), self.assertRaises(ValueError):
                sample_records(records, size=1)
        for size in [0, True, 5001]:
            with self.subTest(size=size), self.assertRaises(ValueError):
                sample_records([row(1)], size=size)

    def test_archive_manifest_hashes_and_no_silent_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / 'archive.zip'
            output = Path(folder) / 'out'
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=sorted(REQUIRED))
            writer.writeheader()
            writer.writerow({k: v for k, v in row(1).items() if k in REQUIRED})
            with ZipFile(archive, 'w') as zipped:
                zipped.writestr('public.csv', buffer.getvalue())
            manifest = prepare(archive, output, size=1)
            self.assertEqual(manifest['archive_sha256'], sha256_file(archive))
            self.assertEqual(manifest['sample_sha256'], sha256_file(output / 'cfpb_sample.csv'))
            self.assertEqual(manifest['selected_complaint_ids'], ['1'])
            original = (output / 'cfpb_sample.csv').read_bytes()
            with self.assertRaises(ValueError):
                prepare(archive, output, size=1)
            self.assertEqual((output / 'cfpb_sample.csv').read_bytes(), original)

    def test_ambiguous_archive_does_not_create_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / 'archive.zip'
            output = Path(folder) / 'out'
            with ZipFile(archive, 'w') as zipped:
                zipped.writestr('one.csv', '')
                zipped.writestr('two.csv', '')
            with self.assertRaises(ValueError):
                prepare(archive, output, size=1)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
