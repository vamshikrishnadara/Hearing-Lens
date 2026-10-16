"""Bound shared CPU inference while keeping each session's data separate."""
import os
from threading import Lock

_ANALYSIS_LOCK = Lock()


def analysis_threads():
    try:
        value = int(os.environ.get('HEARING_LENS_THREADS', '4'))
    except ValueError:
        return 4
    return max(1, min(value, 4))


def run_analysis(frame, *, references=None, response=None):
    import torch
    from pipeline.full import analyze_all
    # Concurrent sessions must not load duplicate model instances or multiply
    # inference batch memory. This lock retains no user data after returning.
    with _ANALYSIS_LOCK:
        torch.set_num_threads(analysis_threads())
        return analyze_all(frame, references=references, agency_response=response)
