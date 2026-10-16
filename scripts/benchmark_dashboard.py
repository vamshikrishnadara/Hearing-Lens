"""Reproducible fictional-only AppTest benchmark; no browser/hosting claims."""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import platform
from threading import Event, Thread
from time import perf_counter
from unittest.mock import patch

import pandas as pd

from scripts.fictional_closeout_samples import CONTEXT, TOPICS


def make_benchmark(rows=2000):
    """Distinct text combinations, balanced across 12 authored topics.

    Wording repeats intentionally: this tests software load, not model accuracy.
    Unique IDs alone are not counted as unique comments.
    """
    if not 1 <= rows <= 2400:
        raise ValueError('Choose 1–2,400 rows.')
    topics = [(name, topic, context, statements)
              for name, values in TOPICS.items()
              for topic, (context, statements) in values.items()]
    output = []
    for closing in CONTEXT:
        for first in range(5):
            for offset in range(1, 5):
                for name, topic, context, statements in topics:
                    output.append({
                        'respondent_id': f'fictional-{len(output)+1:04d}',
                        'comment_text': f'{context}. {statements[first]} '
                                        f'{statements[(first+offset)%5]} {closing}',
                        'hearing_date': ['2026-08-03', '2026-08-10', '2026-08-17'][len(output)%3],
                        'role': ['Member', 'Volunteer', 'Visitor'][(len(output)//3)%3],
                    })
                    if len(output) == rows:
                        return pd.DataFrame(output)


def benchmark(rows=2000, repeats=2, entrypoint="app/streamlit_app.py"):
    import psutil
    import torch
    from streamlit.testing.v1 import AppTest
    from app.dashboard import STATE_KEY
    from app.downloads import labeled_csv
    from pipeline.affect import _get_classifier
    from pipeline.themes import _get_embedding_model

    frame = make_benchmark(rows)
    content = frame.to_csv(index=False).encode()
    upload = BytesIO(content)
    upload.name = 'fictional-performance.csv'
    process = psutil.Process()
    peak = [process.memory_info().rss]
    done = Event()

    def monitor():
        while not done.wait(.05):
            peak[0] = max(peak[0], process.memory_info().rss)

    watcher = Thread(target=monitor, daemon=True)
    watcher.start()
    measurements = []
    try:
        with patch('streamlit.file_uploader', return_value=upload):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / entrypoint),
                                    default_timeout=600).run()
            for label, value in [('Date or hearing label', 'hearing_date'), ('Respondent ID', 'respondent_id')]:
                next(w for w in app.selectbox if w.label == label).select(value).run()
            app.multiselect[0].select('role').run()
            for number in range(repeats):
                start = perf_counter()
                next(w for w in app.button if w.label == 'Validate mapping').click().run()
                validated = perf_counter()
                next(w for w in app.button if w.label == 'Analyze comments').click().run()
                rendered = perf_counter()
                if app.exception or app.error:
                    raise RuntimeError('Dashboard did not complete successfully.')
                workspace = app.session_state[STATE_KEY]
                result = workspace['result']
                if result is None or result['input_rows'] != rows or len(app.tabs) != 5:
                    raise RuntimeError('Dashboard result or panel count is incomplete.')
                exported = pd.read_csv(BytesIO(labeled_csv(result, workspace['preview'].frame)))
                if len(exported) != rows or 'respondent_id' in exported:
                    raise RuntimeError('Download row count or metadata boundary failed.')
                measurements.append({
                    'run': number+1, 'validation_seconds': round(validated-start, 3),
                    'analysis_to_render_seconds': round(rendered-validated, 3),
                    'validation_to_render_seconds': round(rendered-start, 3),
                    'under_180_seconds': rendered-start < 180,
                    'rss_mib_after_run': round(process.memory_info().rss/1024**2, 1),
                    'themes': len(result['themes']['themes']), 'panels': len(app.tabs),
                    'csv_rows': len(exported),
                    'embedding_cache': _get_embedding_model.cache_info()._asdict(),
                    'affect_cache': _get_classifier.cache_info()._asdict(),
                })
                print(json.dumps(measurements[-1]), flush=True)
    finally:
        done.set()
        watcher.join()
    return {
        'entrypoint': entrypoint,
        'torch_threads': torch.get_num_threads(),
        'scope': 'Local Streamlit AppTest with real models; not browser or hosted acceptance.',
        'fixture': 'Authored fictional combinations; repeated wording, not accuracy evidence.',
        'rows': rows, 'distinct_comments': frame.comment_text.nunique(),
        'fixture_sha256': sha256(content).hexdigest(),
        'platform': platform.platform(), 'python': platform.python_version(),
        'peak_process_rss_mib': round(peak[0]/1024**2, 1),
        'runs': measurements,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entrypoint', choices=['app/streamlit_app.py', 'deployment/cloud_app.py'], default='app/streamlit_app.py')
    parser.add_argument('--rows', type=int, default=2000)
    parser.add_argument('--repeats', type=int, default=2)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fixture-output', type=Path)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    if args.fixture_output:
        args.fixture_output.parent.mkdir(parents=True, exist_ok=True)
        args.fixture_output.write_text(make_benchmark(args.rows).to_csv(index=False))
    report = benchmark(args.rows, args.repeats, args.entrypoint)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
