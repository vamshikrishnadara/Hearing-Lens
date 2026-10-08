import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

import run_all
from pipeline.ingest import load_table


class RunAllTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'input.csv'
        self.source.write_text('text,id,role,date\nHello.,001,001,2026-10-08\nHello again.,1,NA,2026-10-09\n')
        self.output = self.root / 'results'

    def args(self, *extra):
        return run_all._parser().parse_args([str(self.source), '--comment-column', 'text',
            '--id-column', 'id', '--date-column', 'date', '--subgroup', 'role',
            '--output-dir', str(self.output), *extra])

    def result(self, frame, **kwargs):
        return {'input_rows': len(frame), 'timeline': {'periods': [], 'theme_volumes': []}}

    def test_export_hashes_json_and_offline_charts(self):
        with patch('pipeline.full.analyze_all', side_effect=self.result) as analysis:
            manifest = run_all.run(self.args())
        passed = analysis.call_args.args[0]
        self.assertEqual(passed.respondent_id.tolist(), ['001', '1'])
        self.assertEqual(passed.subgroup__role.tolist(), ['001', 'NA'])
        self.assertEqual(manifest['status'], 'complete')
        self.assertEqual(len(manifest['files']), 3)
        for name, digest in manifest['files'].items():
            data = (self.output / name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
            self.assertEqual((self.output / name).stat().st_mode & 0o777, 0o600)
        result = json.loads((self.output / 'analysis.json').read_text())
        self.assertEqual(result['ingestion']['analyzed_rows'], 2)
        self.assertNotIn('respondent_id', json.dumps(result))
        self.assertNotIn('<script src=', (self.output / 'timeline-sentiment.html').read_text())

    def test_cleaning_and_row_cap_are_reported(self):
        self.source.write_text('text,id,role,date\nHello.,1,A,\nDuplicate.,1,A,\n,2,B,\nLast.,3,B,\nOmitted.,4,C,\n')
        with patch('pipeline.full.analyze_all', side_effect=self.result):
            run_all.run(self.args('--row-limit', '4'))
        result = json.loads((self.output / 'analysis.json').read_text())['ingestion']
        self.assertEqual(result['analyzed_rows'], 2)
        self.assertEqual(result['empty_comments_removed'], 1)
        self.assertEqual(result['duplicate_respondents_removed'], 1)
        self.assertEqual(result['rows_omitted_at_least'], 1)
        self.assertTrue(result['warnings'])

    def test_reference_and_response_sidecars_reach_api(self):
        references = self.root / 'reference.json'
        references.write_text('{"role": {"001": "50%", "NA": "50%"}}')
        response = self.root / 'response.txt'
        response.write_text('The hearing is tomorrow.')
        with patch('pipeline.full.analyze_all', side_effect=self.result) as analysis:
            run_all.run(self.args('--references', str(references), '--agency-response', str(response)))
        self.assertEqual(analysis.call_args.kwargs['references'], {'subgroup__role': {'001': '50%', 'NA': '50%'}})
        self.assertEqual(analysis.call_args.kwargs['agency_response'], 'The hearing is tomorrow.')

    def test_existing_folder_is_untouched_before_analysis(self):
        self.output.mkdir()
        (self.output / 'keep.txt').write_text('keep')
        with patch('pipeline.full.analyze_all') as analysis:
            with self.assertRaises(ValueError): run_all.run(self.args())
            analysis.assert_not_called()
        self.assertEqual([p.name for p in self.output.iterdir()], ['keep.txt'])

    def test_model_failure_and_nonfinite_result_never_export(self):
        for outcome in [RuntimeError('private source'), {'bad': float('nan')}]:
            kwargs = {'side_effect': outcome} if isinstance(outcome, Exception) else {'return_value': outcome}
            with patch('pipeline.full.analyze_all', **kwargs):
                with self.assertRaises((ValueError, RuntimeError)): run_all.run(self.args())
            self.assertFalse(self.output.exists())

    def test_failure_message_never_echoes_model_exception(self):
        stream = io.StringIO()
        with patch('pipeline.full.analyze_all', side_effect=RuntimeError('private-secret-552')), \
             contextlib.redirect_stderr(stream):
            code = run_all.main([str(self.source), '--comment-column', 'text', '--output-dir', str(self.output)])
        self.assertEqual(code, 1)
        self.assertNotIn('private-secret', stream.getvalue())
        self.assertFalse(self.output.exists())

    def test_bad_reference_shapes_duplicates_and_unselected_fields_fail(self):
        sidecar = self.root / 'ref.json'
        for value in ['[]', '{"not_selected": {"A":1}}', '{"role":[]}',
                      '{"role":{"A":1,"A":0}}', '{"role":{},"role":{}}']:
            sidecar.write_text(value)
            with self.subTest(value=value), patch('pipeline.full.analyze_all') as analysis:
                with self.assertRaises(ValueError): run_all.run(self.args('--references', str(sidecar)))
                analysis.assert_not_called()
            self.assertFalse(self.output.exists())

    def test_oversized_response_fails_before_models(self):
        sidecar = self.root / 'response.txt'
        sidecar.write_bytes(b'x' * 400001)
        with patch('pipeline.full.analyze_all') as analysis:
            with self.assertRaises(ValueError): run_all.run(self.args('--agency-response', str(sidecar)))
            analysis.assert_not_called()

    def test_invalid_limits_and_csv_sheet_rejected(self):
        for options in [('--row-limit', '0'), ('--row-limit', '5001'),
                        ('--minimum-group-size', '9'), ('--sheet', 'Sheet1')]:
            with self.subTest(options=options), patch('pipeline.full.analyze_all') as analysis:
                with self.assertRaises(ValueError): run_all.run(self.args(*options))
                analysis.assert_not_called()

    def test_xlsx_sheet_and_text_codes_preserved(self):
        path = self.root / 'sample.xlsx'
        with pd.ExcelWriter(path) as writer:
            pd.DataFrame({'text': ['other']}).to_excel(writer, sheet_name='Other', index=False)
            pd.DataFrame({'text': ['First', 'Second'], 'code': ['001', 'NA']}).to_excel(writer, sheet_name='Selected', index=False)
        loaded = load_table(path, sheet_name='Selected', preserve_text=True)
        self.assertEqual(loaded.frame.code.tolist(), ['001', 'NA'])
        self.assertEqual(loaded.sheet_name, 'Selected')

    def test_disk_failure_cannot_leave_success_manifest(self):
        with patch('pipeline.full.analyze_all', side_effect=self.result), \
             patch('run_all._write_new', side_effect=OSError('disk full')):
            with self.assertRaises(OSError): run_all.run(self.args())
        self.assertFalse((self.output / 'manifest.json').exists())
