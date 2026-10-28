"""Both entrypoints expose methods without altering an analysis workspace."""
from unittest.mock import patch
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app.dashboard import STATE_KEY
from tests.test_dashboard_completion import upload, ready, APP
from tests.test_brief import result


@pytest.mark.parametrize('entrypoint', [APP, APP.parents[1] / 'deployment/cloud_app.py'])
def test_methodology_view_preserves_results_and_does_not_run_analysis(entrypoint, monkeypatch):
    # The cloud entrypoint changes process-wide deployment mode. Restore it
    # after this test so later local-runtime checks do not inherit the demo cap.
    monkeypatch.setenv('HEARING_LENS_DEPLOYMENT', 'local')
    with patch('scripts.model_setup.install_all'), patch('streamlit.file_uploader', return_value=upload()), \
            patch('app.dashboard.analyze_dashboard', return_value=result()) as analyze:
        app = ready(AppTest.from_file(str(entrypoint), default_timeout=30))
        workspace = app.session_state[STATE_KEY]
        revision = workspace['revision']
        app.radio(key='hl_view').set_value('Methodology and limitations').run()
        assert not app.exception
        assert app.title[0].value == 'Methodology and limitations'
        text = '\n'.join(item.value for item in app.markdown)
        assert 'cardiffnlp/twitter-roberta-base-sentiment-latest' in text
        assert '11/20 (55%)' in text
        assert 'https://github.com/vamshikrishnadara/Hearing-Lens/blob/main/scripts/model_setup.py' in text
        assert 'personal-records' not in text and 'daily-evidence' not in text
        assert analyze.call_count == 1
        assert app.session_state[STATE_KEY]['revision'] == revision
        app.radio(key='hl_view').set_value('Analyze feedback').run()
        assert not app.exception and len(app.tabs) == 5
        assert analyze.call_count == 1
        assert app.session_state[STATE_KEY]['result'] == workspace['result']
