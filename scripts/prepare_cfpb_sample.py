"""Prepare a local development sample from the official public CFPB ZIP archive.

This offline utility is separate from the application's in-memory upload path.
It writes only to the explicitly supplied output directory; never downloads data.
"""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import random
from zipfile import BadZipFile, ZipFile


ARCHIVE_URL = 'https://files.consumerfinance.gov/f/documents/CCDB_Export_1_December_2011_through_April_2018.zip'
ARCHIVE_PAGE = 'https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/'
SEED = 20260925
FIELDS = ['complaint_id', 'comment_text', 'date_received', 'product', 'issue']
REQUIRED = {'Complaint ID', 'Consumer complaint narrative', 'Date received', 'Product', 'Issue'}


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def sample_records(records, *, size=100, seed=SEED):
    if isinstance(size, bool) or not isinstance(size, int) or not 1 <= size <= 5000:
        raise ValueError('Sample size must be between 1 and 5,000.')
    rng = random.Random(seed)
    sample, seen_ids = [], set()
    scanned = eligible = duplicates = 0
    for row in records:
        scanned += 1
        if not REQUIRED <= row.keys():
            raise ValueError('CFPB archive is missing required columns.')
        text = (row['Consumer complaint narrative'] or '').strip()
        date = (row['Date received'] or '').strip()
        if not text or not '2017-01-01' <= date <= '2017-12-31':
            continue
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise ValueError('CFPB archive contains an invalid eligible date.') from None
        identifier = (row['Complaint ID'] or '').strip()
        if not identifier.isascii() or not identifier.isdecimal():
            raise ValueError('CFPB archive contains an invalid complaint identifier.')
        if identifier in seen_ids:
            duplicates += 1
            continue
        seen_ids.add(identifier)
        eligible += 1
        selected = dict(zip(FIELDS, [identifier, text, date, row['Product'], row['Issue']]))
        if len(sample) < size:
            sample.append(selected)
        else:
            index = rng.randrange(eligible)
            if index < size:
                sample[index] = selected
    if len(sample) < size:
        raise ValueError('Not enough eligible narratives for the requested sample.')
    sample.sort(key=lambda row: int(row['complaint_id']))
    return sample, {'archive_rows_scanned': scanned, 'eligible_unique_narratives': eligible,
                    'duplicate_eligible_ids_skipped': duplicates}


def prepare(archive, output_dir, *, size=100, seed=SEED):
    archive, output_dir = Path(archive), Path(output_dir)
    csv_path, manifest_path = output_dir / 'cfpb_sample.csv', output_dir / 'cfpb_manifest.json'
    if csv_path.exists() or manifest_path.exists():
        raise ValueError('Sample output already exists; use a new output directory.')
    with ZipFile(archive) as zipped:
        members = [member for member in zipped.infolist() if member.filename.lower().endswith('.csv')]
        if len(members) != 1:
            raise ValueError('Expected exactly one CSV in the CFPB archive.')
        with zipped.open(members[0]) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
            if not REQUIRED <= set(reader.fieldnames or []):
                raise ValueError('CFPB archive is missing required columns.')
            rows, counts = sample_records(reader, size=size, seed=seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    with csv_path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        'source': 'CFPB public narrative archive', 'source_page': ARCHIVE_PAGE,
        'source_url': ARCHIVE_URL, 'archive_sha256': sha256_file(archive),
        'archive_member': members[0].filename,
        'sample_created_utc': datetime.now(timezone.utc).isoformat(),
        'selection': 'Reservoir sample of unique complaint IDs with nonempty narratives received in 2017; no length/product filter.',
        'seed': seed, 'sample_rows': len(rows), **counts,
        'sample_sha256': sha256_file(csv_path),
        'selected_complaint_ids': [row['complaint_id'] for row in rows],
        'notice': 'Public development data, not user uploads or a representative population sample. Keep narratives and identifiers local.',
    }
    with manifest_path.open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, indent=2)
        stream.write('\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = prepare(args.archive, args.output_dir)
    except (ValueError, OSError, BadZipFile, csv.Error) as exc:
        parser.exit(1, f'Sample preparation failed ({type(exc).__name__}); check the archive and output directory.\n')
    print(f"Prepared {manifest['sample_rows']} public narratives from {manifest['eligible_unique_narratives']} eligible records.")


if __name__ == '__main__':
    main()
