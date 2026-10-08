"""Run all local Hearing Lens analyses and explicitly export to a new folder.

This CLI writes user-requested local results. The in-memory API is pipeline.full;
do not connect this export command to a server's upload handler.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter


class CommandError(ValueError):
    """Curated message that contains no uploaded values or raw exception text."""


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='User-supplied CSV or XLSX')
    parser.add_argument('--comment-column', required=True)
    parser.add_argument('--date-column', help='Date or hearing-label column')
    parser.add_argument('--id-column', help='Optional respondent ID for deduplication')
    parser.add_argument('--subgroup', action='append', default=[], help='Supplied category column; repeat for more')
    parser.add_argument('--sheet', help='XLSX sheet name; default first sheet')
    parser.add_argument('--references', type=Path, help='JSON: source subgroup column -> {category: proportion or percent string}')
    parser.add_argument('--agency-response', type=Path, help='Optional supplied UTF-8 response text; no response is fetched')
    parser.add_argument('--minimum-group-size', type=int, default=10)
    parser.add_argument('--row-limit', type=int, default=5000)
    parser.add_argument('--cpu-threads', type=int, choices=[1, 2, 4], default=4)
    parser.add_argument('--output-dir', type=Path, required=True,
                        help='New local results folder; existing folders are never overwritten')
    return parser


def _read_text(path, max_bytes):
    with path.open('rb') as stream:
        data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError('Sidecar file too large')
    return data.decode('utf-8-sig')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def _references(path, subgroups):
    if path is None:
        return None
    value = json.loads(_read_text(path, 1_000_000), object_pairs_hook=_unique_object)
    if (not isinstance(value, dict) or any(key not in subgroups for key in value)
            or any(not isinstance(ref, dict) for ref in value.values())):
        raise ValueError('Reference mappings must use selected source subgroup names')
    return {f'subgroup__{key}': ref for key, ref in value.items()}


def _write_new(path, content):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        stream.write(content)


def run(args):
    """Return the manifest only after all output files have been written.

    Input validation/model/serialization failures create no result directory.
    A disk failure may leave an incomplete directory, without a manifest; choose
    a new directory for retry. Raw exceptions are handled only by main().
    """
    if args.output_dir.exists() or args.output_dir.is_symlink():
        raise CommandError('The output folder already exists. Choose a new folder; existing results were preserved.')
    if not 1 <= args.row_limit <= 5000 or args.minimum_group_size < 10:
        raise CommandError('Use a row limit of 1–5000 and a minimum group size of at least 10.')
    if args.sheet and args.input.suffix.lower() != '.xlsx':
        raise CommandError('Sheet selection requires an XLSX input file.')
    try:
        references = _references(args.references, args.subgroup)
        response = _read_text(args.agency_response, 400_000) if args.agency_response else None
    except (ValueError, OSError):
        raise CommandError('Could not read the sidecar files. Use UTF-8 text and reference JSON keyed by '
                           'selected source subgroup columns, with no duplicate keys. Reference files '
                           'are limited to 1 MB and response files to 400 KB.') from None
    # Imports and setup are counted in total wall time; inference never downloads.
    import torch
    from pipeline.ingest import load_table, map_columns
    from pipeline.full import analyze_all
    from pipeline.timeline import timeline_figures

    torch.set_num_threads(args.cpu_threads)
    loaded = load_table(args.input, sheet_name=args.sheet, row_cap=args.row_limit, preserve_text=True)
    mapped = map_columns(loaded.frame, comment_column=args.comment_column,
                         date_or_hearing_column=args.date_column, respondent_id_column=args.id_column,
                         subgroup_columns=args.subgroup)
    start = perf_counter()
    result = analyze_all(mapped.frame, references=references, agency_response=response,
                         minimum_group_size=args.minimum_group_size)
    analysis_seconds = perf_counter() - start
    result['ingestion'] = {'loaded_rows': len(loaded.frame),
        'analyzed_rows': len(mapped.frame), 'row_limit': args.row_limit,
        'rows_omitted_at_least': loaded.rows_omitted,
        'empty_comments_removed': mapped.empty_comments_removed,
        'duplicate_respondents_removed': mapped.duplicate_respondents_removed,
        'warnings': list(loaded.warnings)}
    # Serialize everything before creating any destination. Never coerce unknown
    # objects to str: that could silently export a raw table or invalid metric.
    payloads = {'analysis.json': json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n'}
    for name, figure in timeline_figures(result['timeline']).items():
        payloads[f'timeline-{name}.html'] = figure.to_html(full_html=True, include_plotlyjs=True)
    manifest = {'schema_version': '1.0', 'status': 'complete', 'input_rows': len(mapped.frame),
        'cpu_threads': args.cpu_threads, 'analysis_seconds': analysis_seconds,
        'files': {name: hashlib.sha256(value.encode('utf-8')).hexdigest() for name, value in payloads.items()},
        'notice': 'Complete means the automated run finished, not human acceptance. '
                  'Local outputs can contain sensitive text and supplied category labels. '
                  'Review before sharing; do not commit private data.'}
    args.output_dir.mkdir(parents=True, mode=0o700, exist_ok=False)
    for name, content in payloads.items():
        _write_new(args.output_dir / name, content)
    _write_new(args.output_dir / 'manifest.json', json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    return manifest


def main(argv=None):
    args = _parser().parse_args(argv)
    start = perf_counter()
    try:
        manifest = run(args)
    except CommandError as error:
        print(str(error), file=sys.stderr)
        return 1
    except Exception:
        # Parser, Excel, model and filesystem errors may contain source values.
        # Never print their raw messages or tracebacks with user-supplied data.
        print('Analysis did not finish. Check input/mapped columns, selected reference fields, '
              'UTF-8 sidecar files, local model setup, and available disk/memory. Use a new output '
              'folder, a row limit of 1–5000 and a minimum group size of at least 10. '
              'A folder without manifest.json is incomplete.', file=sys.stderr)
        return 1
    print(f"Complete: {manifest['input_rows']} comments; analysis {manifest['analysis_seconds']:.2f}s; "
          f"total {perf_counter() - start:.2f}s. Results saved in the requested local folder. "
          'Human validation remains separate.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
