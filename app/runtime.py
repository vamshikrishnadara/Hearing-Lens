"""Bound shared CPU inference while keeping each session's data separate."""
import os
import logging
from threading import Lock
from time import monotonic
from pipeline.progress import STAGES, notify
from streamlit.logger import get_logger

_ANALYSIS_LOCK = Lock()
# Streamlit configures console handlers separately from Python's root logger.
# Use its handler so INFO stage timings reach hosting logs without basicConfig.
_LOG = get_logger('hearing_lens.analysis')
_LOG.setLevel(logging.INFO)
QUEUE_TIMEOUT_SECONDS = 30


class AnalysisBusyError(ValueError):
    """Bounded queue wait; no second inference job is started."""


class AnalysisProgress:
    def __init__(self, callback=None):
        self.callback = callback
        self.stage = None
        self.started = monotonic()

    def __call__(self, stage):
        if stage not in STAGES:
            raise ValueError('Unknown analysis stage.')
        now = monotonic()
        if self.stage is not None:
            _LOG.info('stage=%s event=finished seconds=%.3f', self.stage, now-self.started)
        self.stage, self.started = stage, now
        _LOG.info('stage=%s event=started', stage)
        notify(self.callback, stage)

    def failed(self):
        # Never log exception text, uploaded cells, labels or filenames.
        _LOG.info('stage=%s event=failed seconds=%.3f', self.stage, monotonic()-self.started)


def analysis_threads():
    try:
        value = int(os.environ.get('HEARING_LENS_THREADS', '4'))
    except ValueError:
        return 4
    return max(1, min(value, 4))


def run_analysis(frame, *, references=None, response=None, progress=None):
    report = AnalysisProgress(progress)
    report('waiting')
    # Concurrent sessions must not load duplicate model instances or multiply
    # inference batch memory. This lock retains no user data after returning.
    if not _ANALYSIS_LOCK.acquire(timeout=QUEUE_TIMEOUT_SECONDS):
        report.failed()
        raise AnalysisBusyError('Another analysis is still running. No new analysis was started. Wait for it to finish before retrying.')
    try:
        report('initializing')
        import torch
        from pipeline.full import analyze_all
        torch.set_num_threads(analysis_threads())
        return analyze_all(frame, references=references, agency_response=response, progress=report)
    except BaseException:
        report.failed()
        raise
    finally:
        _ANALYSIS_LOCK.release()
