"""Session-only PDF downloads, invalidation and failure handling."""
from io import BytesIO
from unittest.mock import patch
from pypdf import PdfReader
import pytest
from streamlit.testing.v1 import AppTest
from app.dashboard import STATE_KEY
from tests.test_brief import result
from tests.test_dashboard_completion import upload, ready, widget, APP


@pytest.mark.parametrize('change',['quote','response','mapping','upload','rerun_failure'])
def test_pdf_is_current_and_disappears_when_its_inputs_change(change):
    with patch('streamlit.file_uploader',return_value=upload()) as picker,patch('app.dashboard.analyze_dashboard',return_value=result()) as run:
        app=ready(AppTest.from_file(str(APP),default_timeout=30))
        widget(app,'button','Prepare PDF brief').click().run()
        current=app.session_state[STATE_KEY]
        assert len(PdfReader(BytesIO(current['brief_pdf'])).pages)==1
        assert len(app.get('download_button'))==2 and run.call_count==1
        if change=='quote':
            current['quote_revisions'][1]=1
            current['result']['themes']['themes'][0]['quotes'][0]['text']='Updated selected wording.'
            app.run()
        elif change=='response':widget(app,'text_area','Response text (optional)').input('Changed.').run()
        elif change=='mapping':widget(app,'selectbox','Respondent ID').select('id').run()
        elif change=='upload':picker.return_value=None;app.run()
        else:
            run.side_effect=RuntimeError('PRIVATE')
            widget(app,'button','Analyze comments').click().run()
        assert not app.exception
        if STATE_KEY in app.session_state:assert 'brief_pdf' not in app.session_state[STATE_KEY]
        assert not any(w.label=='Download PDF brief' for w in app.get('download_button'))


def test_pdf_failure_discards_old_pdf_but_word_remains_available():
    with patch('streamlit.file_uploader',return_value=upload()),patch('app.dashboard.analyze_dashboard',return_value=result()):
        app=ready(AppTest.from_file(str(APP),default_timeout=30))
        widget(app,'button','Prepare Word brief').click().run()
        widget(app,'button','Prepare PDF brief').click().run()
        assert len(app.get('download_button'))==3
        with patch('app.brief_download.community_pdf',side_effect=RuntimeError('SECRET')):
            widget(app,'button','Prepare PDF brief').click().run()
        assert 'brief_pdf' not in app.session_state[STATE_KEY]
        assert 'brief_docx' in app.session_state[STATE_KEY]
        assert len(app.get('download_button'))==2
        assert not app.exception and all('SECRET' not in e.value for e in app.error)


def test_prepared_downloads_do_not_request_a_dashboard_rerun():
    with patch('streamlit.file_uploader', return_value=upload()), patch('app.dashboard.analyze_dashboard', return_value=result()) as analyze:
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        widget(app, 'button', 'Prepare Word brief').click().run()
        widget(app, 'button', 'Prepare PDF brief').click().run()
        buttons = app.get('download_button')
        assert len(buttons) == 3
        assert all(b.proto.ignore_rerun for b in buttons)
        assert analyze.call_count == 1
        # A separate input change must still discard every old download.
        widget(app, 'text_area', 'Response text (optional)').input('Different response.').run()
        assert not app.get('download_button')
