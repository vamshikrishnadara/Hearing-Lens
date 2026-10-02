"""Explicit development import from the public Mirrulations archive of Regulations.gov.

No credentials or agency API calls. Saves raw responses and source hashes locally;
never used by the application. Selection is by archived key order, not model output.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pandas as pd
import requests
from scripts.prepare_federal_sample import clean_comment

BASE = 'https://mirrulations.s3.amazonaws.com/'
NS = {'s': 'http://s3.amazonaws.com/doc/2006-03-01/'}


def extract_record(payload, document_id):
    data = payload['data']; attrs = data['attributes']
    docket = document_id.rsplit('-', 1)[0]
    if (data.get('type') != 'comments' or attrs.get('docketId') != docket
            or attrs.get('commentOnDocumentId') != document_id
            or attrs.get('withdrawn') or attrs.get('restrictReason')):
        return None
    text = clean_comment(attrs.get('comment'))
    if not text:
        return None
    if not re.fullmatch(re.escape(docket) + r'-\d+', data['id']):
        raise ValueError('Unexpected comment identifier in archive.')
    return {'source_id': data['id'], 'comment_text': text,
            'hearing_date': attrs.get('postedDate') or ''}


def prepare(document_id, directory, size=100):
    directory = Path(directory)
    if not re.fullmatch(r'[A-Z0-9-]+-\d+', document_id) or not 20 <= size <= 5000:
        raise ValueError('Choose a document ID and 20-5,000 rows.')
    if any((directory / n).exists() for n in ('federal_sample.csv', 'federal_manifest.json')):
        raise ValueError('Sample already exists; use another output directory.')
    directory.mkdir(parents=True, exist_ok=True)
    raw_dir = directory / 'raw'; raw_dir.mkdir(exist_ok=True)
    docket = document_id.rsplit('-', 1)[0]
    prefix = f'raw-data/{docket.split("-")[0]}/{docket}/text-{docket}/comments/'
    session = requests.Session()
    keys = []; token = None
    while True:
        params = {'list-type': 2, 'prefix': prefix, 'max-keys': 1000}
        if token: params['continuation-token'] = token
        response = session.get(BASE, params=params, timeout=45); response.raise_for_status()
        root = ET.fromstring(response.content)
        keys.extend(node.text for node in root.findall('s:Contents/s:Key', NS)
                    if node.text.endswith('.json'))
        if root.findtext('s:IsTruncated', namespaces=NS) != 'true': break
        token = root.findtext('s:NextContinuationToken', namespaces=NS)
        if not token: raise ValueError('Incomplete archive listing.')
    rows = []; records = []; examined = 0
    for key in sorted(set(keys)):
        if not key.startswith(prefix) or '/' in key[len(prefix):]:
            raise ValueError('Unexpected archive key.')
        path = raw_dir / key.rsplit('/', 1)[1]
        if not path.exists():
            response = session.get(BASE + key, timeout=45); response.raise_for_status()
            # Validate before caching a downloaded response.
            response.json(); path.write_bytes(response.content)
        payload = json.loads(path.read_bytes()); examined += 1
        row = extract_record(payload, document_id)
        if row is None: continue
        if row['source_id'] + '.json' != path.name:
            raise ValueError('Archive key and comment identifier disagree.')
        rows.append(row)
        records.append({'id': row['source_id'], 'archive_url': BASE + key,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        if len(rows) == size: break
    if len(rows) < size: raise ValueError(f'Only {len(rows)} eligible inline comments; sample not written.')
    sample = directory / 'federal_sample.csv'
    pd.DataFrame(rows).to_csv(sample, index=False)
    manifest = {'source': 'https://www.regulations.gov/document/' + document_id,
        'archive': 'https://registry.opendata.aws/mirrulations/',
        'retrieval_method': 'Public Mirrulations archive of Regulations.gov; not a direct agency download.',
        'docket_id': docket, 'document_id': document_id, 'sample_rows': len(rows),
        'listed_comments': len(keys), 'examined_records': examined,
        'selection': 'First nonempty unrestricted inline comments for the selected parent in archive key order; attachments excluded; convenience sample.',
        'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'sample_sha256': hashlib.sha256(sample.read_bytes()).hexdigest(),
        'source_ids': [r['source_id'] for r in rows], 'records': records}
    (directory / 'federal_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--document-id', default='FAA-2018-1084-0001')
    parser.add_argument('--rows', type=int, default=100)
    parser.add_argument('--output-dir', type=Path, default=Path('data/public_samples/federal_mirror'))
    args = parser.parse_args()
    try: result = prepare(args.document_id, args.output_dir, args.rows)
    except (ValueError, KeyError, OSError, requests.RequestException, ET.ParseError):
        parser.exit(1, 'Federal archive import failed; preserved cached responses. Check source and destination.\n')
    print(f"Prepared {result['sample_rows']} federal comments from {result['listed_comments']} archived records.")


if __name__ == '__main__': main()
