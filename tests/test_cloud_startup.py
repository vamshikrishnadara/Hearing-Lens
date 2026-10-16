from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


def test_cloud_setup_failure_hides_upload_and_exception_details():
    with patch('scripts.model_setup.install_all', side_effect=RuntimeError('PRIVATE_DETAIL')):
        app = AppTest.from_file(Path(__file__).resolve().parents[1] / 'deployment/cloud_app.py').run()
        assert not app.exception
        assert 'PRIVATE_DETAIL' not in str(app)
        assert len(app.error) == 1
        assert not app.get('file_uploader')


def test_cloud_startup_loads_regular_app():
    with patch('scripts.model_setup.install_all'), patch('streamlit.file_uploader', return_value=None):
        app = AppTest.from_file(Path(__file__).resolve().parents[1] / 'deployment/cloud_app.py').run()
        assert not app.exception
        assert app.title[0].value == 'Hearing Lens'
        assert not app.error
