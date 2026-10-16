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


