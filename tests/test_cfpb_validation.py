"""CFPB validation checks use fictional records and controlled theme results."""

import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from scripts.prepare_cfpb_sample import FIELDS, sha256_file
from scripts.validate_cfpb_themes import evaluate, load_sample


class CfpbValidationTests(unittest.TestCase):
    def test_changed_sample_or_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            sample = folder / 'cfpb_sample.csv'
            with sample.open('w') as stream:
                writer = csv.DictWriter(stream, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerow(dict(zip(FIELDS, ['123', 'Fictional comment.', '2017-01-01', 'product', 'issue'])))
            manifest = {'sample_sha256': sha256_file(sample), 'sample_rows': 1, 'selected_complaint_ids': ['123']}
            path = folder / 'cfpb_manifest.json'
            path.write_text(json.dumps(manifest))
            self.assertEqual(len(load_sample(folder)[0]), 1)
            manifest['selected_complaint_ids'] = ['different']
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'rows'):
                load_sample(folder)
            sample.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                load_sample(folder)

    def test_analysis_excludes_metadata_and_review_packet_is_redacted(self):
        frame = pd.DataFrame({'comment_text': ['Please contact resident@example.org about this fictional issue.'],
                              'complaint_id': ['private-id'], 'product': ['context-only'], 'issue': ['hidden-issue']})
        fake = {'themes': [{'theme_id': 1, 'label': 'xxxx', 'keywords': ['xxxx'], 'quotes': []}],
                'assignments': [{'row_position': 0, 'theme_id': 1}]}
        with patch('scripts.validate_cfpb_themes.analyze_themes', return_value=fake) as analyze:
            report = evaluate(frame)
        self.assertEqual(analyze.call_args.args[0].columns.tolist(), ['comment_text'])
        self.assertNotIn('resident@example.org', json.dumps(report))
        self.assertNotIn('private-id', json.dumps(report))
        self.assertNotIn('hidden-issue', json.dumps(report))
        self.assertIn('[EMAIL_ADDRESS]', json.dumps(report))
        self.assertEqual(report['themes_with_source_placeholder_keywords'], 1)
        self.assertEqual(report['candidate_quote_count'], 0)
        self.assertEqual(report['product_composition_context_only'], {'1': {'context-only': 1}})


if __name__ == '__main__':
    unittest.main()
