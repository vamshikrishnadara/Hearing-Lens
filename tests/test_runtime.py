from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch
import pytest
from app.runtime import analysis_threads, run_analysis


@pytest.mark.parametrize('raw,expected', [('2', 2), ('0', 1), ('99', 4), ('bad', 4)])
def test_thread_limit(monkeypatch, raw, expected):
    monkeypatch.setenv('HEARING_LENS_THREADS', raw)
    assert analysis_threads() == expected


def test_analysis_sessions_serialize_and_release_after_failure():
    entered, release, second = Event(), Event(), Event()
    def analyze(frame, **kwargs):
        if frame == 'first':
            entered.set()
            assert release.wait(5)
            raise ValueError('test failure')
        second.set()
        kwargs.pop('progress')('complete')
        return {'input': frame, **kwargs}
    with patch('pipeline.full.analyze_all', side_effect=analyze), patch('torch.set_num_threads'):
        with ThreadPoolExecutor(2) as pool:
            first = pool.submit(run_analysis, 'first')
            assert entered.wait(5)
            following = pool.submit(run_analysis, 'second', response='answer')
            assert not second.wait(.1)
            release.set()
            with pytest.raises(ValueError):
                first.result(timeout=5)
            assert following.result(timeout=5) == {
                'input': 'second', 'references': None, 'agency_response': 'answer'}


def test_busy_timeout_starts_no_second_job_and_keeps_lock_owned_by_first():
    from app.runtime import _ANALYSIS_LOCK, AnalysisBusyError
    stages = []
    assert _ANALYSIS_LOCK.acquire(timeout=1)
    try:
        with patch('app.runtime.QUEUE_TIMEOUT_SECONDS', .01), patch('pipeline.full.analyze_all') as run:
            with pytest.raises(AnalysisBusyError):run_analysis('SECRET', progress=stages.append)
        run.assert_not_called()
        assert stages == ['waiting'] and _ANALYSIS_LOCK.locked()
    finally:
        _ANALYSIS_LOCK.release()


def test_failure_logs_stage_timing_without_input_or_exception(caplog):
    def analyze(frame, **kwargs):
        kwargs['progress']('clustering')
        raise RuntimeError('SECRET UPLOADED TEXT')
    stages=[]
    with patch('pipeline.full.analyze_all', side_effect=analyze),patch('torch.set_num_threads'):
        with pytest.raises(RuntimeError):run_analysis('SECRET INPUT',progress=stages.append)
    assert stages==['waiting','initializing','clustering']
    assert 'stage=clustering event=failed' in caplog.text
    assert 'seconds=' in caplog.text and 'SECRET' not in caplog.text
    from app.runtime import _ANALYSIS_LOCK
    assert not _ANALYSIS_LOCK.locked()




def test_stage_timings_reach_console_without_root_logging_configuration():
    import subprocess
    import sys
    from pathlib import Path
    script = """
import logging
assert not logging.getLogger().handlers
from app.runtime import AnalysisProgress
progress = AnalysisProgress()
progress('waiting')
progress('initializing')
progress.failed()
"""
    run = subprocess.run([sys.executable, '-c', script],
                         cwd=Path(__file__).resolve().parents[1],
                         capture_output=True, text=True, check=True)
    assert run.stderr.count('stage=waiting event=started') == 1
    assert 'stage=waiting event=finished seconds=' in run.stderr
    assert 'stage=initializing event=failed seconds=' in run.stderr
    assert not run.stdout
