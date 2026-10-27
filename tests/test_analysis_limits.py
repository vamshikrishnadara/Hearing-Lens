from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.limits import AnalysisLimitError, check_analysis_size
from app.runtime import run_analysis


@pytest.fixture(autouse=True)
def cloud_mode(monkeypatch):
    monkeypatch.setenv('HEARING_LENS_DEPLOYMENT', 'community_cloud')


@pytest.mark.parametrize('rows,width,allowed', [(60,400,True), (61,1,False),
                                                (60,401,False), (1,24001,False)])
def test_cleaned_row_and_text_limits(rows, width, allowed):
    frame = pd.DataFrame({'comment_text': ['a'*width]*rows})
    if allowed:
        check_analysis_size(frame)
    else:
        with pytest.raises(AnalysisLimitError): check_analysis_size(frame)


def test_oversized_runtime_request_never_enters_queue_or_models():
    stages = []
    frame = pd.DataFrame({'comment_text': ['PRIVATE CELL']*61})
    with patch('app.runtime._ANALYSIS_LOCK') as lock, patch('pipeline.full.analyze_all') as analyze:
        with pytest.raises(AnalysisLimitError) as error:
            run_analysis(frame, progress=stages.append)
    lock.acquire.assert_not_called()
    analyze.assert_not_called()
    assert not stages and 'PRIVATE CELL' not in str(error.value)


def test_local_full_file_has_no_demo_cap(monkeypatch):
    monkeypatch.setenv('HEARING_LENS_DEPLOYMENT', 'local')
    frame = pd.DataFrame({'comment_text': ['Fictional comment.']*2000})
    with patch('pipeline.full.analyze_all', return_value={'input_rows': 2000}) as analyze:
        assert run_analysis(frame) == {'input_rows': 2000}
    assert len(analyze.call_args.args[0]) == 2000


def test_cloud_rejects_before_redaction_and_hides_analysis_control():
    upload = BytesIO(pd.DataFrame({'comment_text': ['Fictional community comment.']*61}).to_csv(index=False).encode())
    upload.name = 'fictional.csv'
    with patch('streamlit.file_uploader', return_value=upload), patch('pipeline.redact.build_safe_display_frame') as redact:
        app = AppTest.from_file(Path(__file__).resolve().parents[1] / 'app/streamlit_app.py').run()
        next(b for b in app.button if b.label == 'Validate mapping').click().run()
    assert not app.exception
    assert not app.error
    assert any('No analysis was started' in w.value for w in app.warning)
    assert any('61 cleaned comments' in w.value for w in app.warning)
    assert any('Analyze this file on your computer' == h.value for h in app.subheader)
    assert app.code[0].value == 'python -m scripts.start_local'
    assert any('local installation instructions' in m.value for m in app.markdown)
    assert not any(b.label == 'Analyze comments' for b in app.button)
    redact.assert_not_called()


def test_cloud_limit_applies_after_empty_row_cleaning():
    upload = BytesIO(pd.DataFrame({'comment_text': ['Fictional community comment.']*60 + ['']*5}).to_csv(index=False).encode())
    upload.name = 'fictional.csv'
    with patch('streamlit.file_uploader', return_value=upload):
        app = AppTest.from_file(Path(__file__).resolve().parents[1] / 'app/streamlit_app.py', default_timeout=30).run()
        next(b for b in app.button if b.label == 'Validate mapping').click().run()
    assert not app.exception and not app.error
    assert any(b.label == 'Analyze comments' for b in app.button)
    assert '60 usable' in app.success[0].value
    assert not any(h.value == 'Analyze this file on your computer' for h in app.subheader)
