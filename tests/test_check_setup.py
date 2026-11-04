import json
from importlib import metadata
from unittest.mock import patch

import pytest

from scripts import check_setup
from scripts.model_setup import MODELS


@pytest.fixture
def installed(tmp_path, monkeypatch):
    project = tmp_path / 'project'
    project.mkdir()
    (project / 'requirements.txt').write_text('streamlit>=1.43,<2.0\n')
    monkeypatch.setattr(check_setup, 'PROJECT_ROOT', project)
    monkeypatch.setattr(check_setup.metadata, 'version', lambda name: '1.50.0')
    root = tmp_path / 'models'
    for name, spec in MODELS.items():
        folder = root / name
        folder.mkdir(parents=True)
        (folder / 'hearing_lens_source.json').write_text(json.dumps(spec))
        for filename in spec['files']:
            path = folder / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture')
    return root


def test_matching_setup_is_read_only(installed):
    before = {p: p.read_bytes() for p in installed.rglob('*') if p.is_file()}
    with patch('socket.socket', side_effect=AssertionError('No network')):
        assert check_setup.check_setup(installed) == []
    assert before == {p: p.read_bytes() for p in installed.rglob('*') if p.is_file()}


@pytest.mark.parametrize('name', ['streamlit', 'en-core-web-sm'])
def test_missing_dependency_has_repair_command(installed, monkeypatch, name):
    def version(package):
        if package == name:
            raise metadata.PackageNotFoundError(package)
        return '1.50.0'
    monkeypatch.setattr(check_setup.metadata, 'version', version)
    problems = check_setup.check_setup(installed)
    assert len(problems) == 1
    assert 'Run: python -m' in problems[0]


def test_incompatible_package_version(installed, monkeypatch):
    monkeypatch.setattr(check_setup.metadata, 'version', lambda name: '2.0.0')
    assert any('does not meet' in item for item in check_setup.check_setup(installed))


@pytest.mark.parametrize('record', ['not json', '[]', '{"revision":"wrong"}'])
def test_invalid_provenance_does_not_pass_or_change_files(installed, record):
    marker = installed / 'sentiment/hearing_lens_source.json'
    marker.write_text(record)
    assert len(check_setup.check_setup(installed)) == 1
    assert marker.read_text() == record


def test_empty_model_file_does_not_pass(installed):
    (installed / 'sentiment/config.json').write_bytes(b'')
    assert any('missing or empty' in item for item in check_setup.check_setup(installed))


@pytest.mark.parametrize('problems,code', [([], 0), (['Missing test dependency'], 1)])
def test_command_exit_status_and_scope(monkeypatch, capsys, problems, code):
    monkeypatch.setattr(check_setup, 'check_setup', lambda: problems)
    assert check_setup.main() == code
    output = capsys.readouterr().out
    assert ('does not load models' if code == 0 else 'No files were changed') in output
