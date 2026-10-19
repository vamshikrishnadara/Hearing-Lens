"""Word download lifecycle and error boundaries in the Streamlit app."""
from io import BytesIO
from unittest.mock import patch
from docx import Document
import pytest
from streamlit.testing.v1 import AppTest
from app.dashboard import STATE_KEY
from tests.test_brief import result
from tests.test_dashboard_completion import upload, ready, widget, APP


def test_download_preparation_does_not_rerun_analysis_and_invalidates_on_quote_change():
    with patch('streamlit.file_uploader', return_value=upload()), patch('app.dashboard.analyze_dashboard', return_value=result()) as run:
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        assert len(app.get('download_button')) == 1
        widget(app, 'button', 'Prepare Word brief').click().run()
        assert not app.exception and len(app.get('download_button')) == 2
        assert run.call_count == 1
        current = app.session_state[STATE_KEY]
        current['quote_revisions'][1] = 1
        current['result']['themes']['themes'][0]['quotes'][0]['text'] = 'A different selected quote.'
        app.run()
        assert len(app.get('download_button')) == 1 and 'brief_docx' not in current
        widget(app, 'button', 'Prepare Word brief').click().run()
        doc = Document(BytesIO(app.session_state[STATE_KEY]['brief_docx']))
        assert 'A different selected quote.' in '\n'.join(p.text for p in doc.paragraphs)
        widget(app, 'text_area', 'Response text (optional)').input('Updated response.').run()
        assert not app.get('download_button')
        assert 'brief_docx' not in app.session_state[STATE_KEY]


def test_generation_failure_discards_old_file_and_hides_exception_text():
    with patch('streamlit.file_uploader', return_value=upload()), patch('app.dashboard.analyze_dashboard', return_value=result()):
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        widget(app, 'button', 'Prepare Word brief').click().run()
        with patch('app.brief_download.community_docx', side_effect=RuntimeError('PRIVATE TEXT')):
            widget(app, 'button', 'Prepare Word brief').click().run()
        assert not app.exception and len(app.get('download_button')) == 1
        assert 'brief_docx' not in app.session_state[STATE_KEY]
        assert all('PRIVATE TEXT' not in e.value for e in app.error)


@pytest.mark.parametrize('change', ['removed_upload', 'mapping', 'failed_analysis'])
def test_changed_session_inputs_cannot_offer_a_previous_brief(change):
    with patch('streamlit.file_uploader', return_value=upload()) as picker, patch('app.dashboard.analyze_dashboard', return_value=result()) as run:
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        widget(app, 'button', 'Prepare Word brief').click().run()
        assert 'brief_docx' in app.session_state[STATE_KEY]
        if change == 'removed_upload':
            picker.return_value = None
            app.run()
        elif change == 'mapping':
            widget(app, 'selectbox', 'Respondent ID').select('id').run()
        else:
            run.side_effect = RuntimeError('PRIVATE INPUT')
            widget(app, 'button', 'Analyze comments').click().run()
        assert not app.exception and not app.get('download_button')
        if STATE_KEY in app.session_state:
            assert 'brief_docx' not in app.session_state[STATE_KEY]
        assert all('PRIVATE INPUT' not in e.value for e in app.error)
