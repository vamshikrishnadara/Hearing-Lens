from unittest.mock import patch
from pathlib import Path
from scripts import start_local


def test_local_launcher_binds_loopback_and_clears_inherited_cloud_policy(monkeypatch):
    monkeypatch.setenv('HEARING_LENS_DEPLOYMENT', 'community_cloud')
    monkeypatch.setattr('sys.argv', ['start_local', '--headless', '--port', '8517'])
    with patch('scripts.start_local.os.execv') as launch, patch('scripts.start_local.os.chdir'):
        start_local.main()
    import os
    assert os.environ['HEARING_LENS_DEPLOYMENT'] == 'local'
    args = launch.call_args.args[1]
    assert '--server.address=127.0.0.1' in args
    assert '--server.port=8517' in args
    assert '--server.headless=true' in args
    assert str(Path(start_local.ROOT) / 'app/streamlit_app.py') in args
