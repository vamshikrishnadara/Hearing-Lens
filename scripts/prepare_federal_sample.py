"""Explicit development-only Regulations.gov download; never used by the app.

Uses the official API, a single parent document, deterministic posted-date order,
and only inline comment text. Public submissions are not assumed public domain.
Output stays in ignored data/public_samples; never commit narratives or IDs.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from datetime import datetime, timezone
import pandas as pd
import requests

BASE = 'https://api.regulations.gov/v4'


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, text):
        self.parts.append(text)


def clean_comment(value):
    parser = PlainText(); parser.feed(value or '')
    return ' '.join(' '.join(parser.parts).split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--document-id', required=True)
    parser.add_argument('--rows', type=int, default=20)
    parser.add_argument('--output-dir', type=Path, default=Path('data/public_samples/federal'))
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Z0-9-]+', args.document_id) or not 20 <= args.rows <= 100:
        parser.error('Use a document ID and 20-100 rows.')
    key = os.environ.get('REGULATIONS_API_KEY', 'DEMO_KEY')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if (args.output_dir / 'federal_sample.csv').exists():
        parser.error('Sample already exists; choose another directory to preserve provenance.')
    cache_path = args.output_dir / 'federal_progress.json'
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {'document_id': args.document_id, 'responses': {}}
    if cache['document_id'] != args.document_id:
        parser.error('Progress directory belongs to another document.')
    session = requests.Session()
    def get(path, **params):
        cache_key = json.dumps([path, params], sort_keys=True)
        if cache_key in cache['responses']:
            return cache['responses'][cache_key]
        response = session.get(BASE + path, params={**params, 'api_key': key}, timeout=45)
        # Never print request URLs or exceptions that might include the API key.
        if not response.ok:
            raise RuntimeError(f'Official API returned HTTP {response.status_code}; try later or configure REGULATIONS_API_KEY.')
        payload = response.json()
        cache['responses'][cache_key] = payload
        cache_path.write_text(json.dumps(cache))
        return payload
    try:
        parent = get('/documents/' + args.document_id)['data']['attributes']
        docket = parent['docketId']
        listing = get('/comments', **{'filter[commentOnId]': parent['objectId'],
                      'sort': 'postedDate', 'page[size]': 250})
        rows = []
        examined = 0
        for item in listing.get('data', []):
            attrs = get('/comments/' + item['id'])['data']['attributes']
            examined += 1
            text = clean_comment(attrs.get('comment'))
            if text and attrs.get('docketId') == docket:
                rows.append({'source_id': item['id'], 'comment_text': text, 'hearing_date': attrs.get('postedDate', '')})
            if len(rows) == args.rows:
                break
        if len(rows) < args.rows:
            raise RuntimeError(f'Only {len(rows)} inline comments available in examined records; no complete sample written.')
        args.output_dir.mkdir(parents=True, exist_ok=True)
        sample = args.output_dir / 'federal_sample.csv'
        if sample.exists():
            raise RuntimeError('Sample already exists; choose another output directory to preserve provenance.')
        pd.DataFrame(rows).to_csv(sample, index=False)
        manifest = {'source': 'https://www.regulations.gov/document/' + args.document_id,
            'api_documentation': 'https://open.gsa.gov/api/regulationsgov/',
            'docket_id': docket, 'document_id': args.document_id, 'sample_rows': len(rows),
            'examined_records': examined, 'selection': 'First nonempty inline comments in API postedDate order; attachments excluded; convenience sample, not representative.',
            'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'sample_sha256': hashlib.sha256(sample.read_bytes()).hexdigest(),
            'source_ids': [row['source_id'] for row in rows]}
        (args.output_dir / 'federal_manifest.json').write_text(json.dumps(manifest, indent=2))
        print(f'Prepared {len(rows)} federal comments; hash {manifest["sample_sha256"]}')
    except (requests.RequestException, KeyError, ValueError):
        parser.exit(1, 'Federal sample preparation failed; check the official API and selected document.\n')
    except RuntimeError as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
