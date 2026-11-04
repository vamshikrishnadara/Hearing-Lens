import json
from unittest.mock import patch
from functools import partial
import pytest
from scripts.model_setup import MODELS, install_model


def populate(root, name):
    model = MODELS[name]
    destination = root/name
    destination.mkdir()
    for file in model['files']:
        path = destination/file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('test')
    (destination/'hearing_lens_source.json').write_text(json.dumps(model))
    return destination


def test_complete_pinned_models_skip_download(tmp_path):
    for name in MODELS:
        populate(tmp_path, name)
        with patch('huggingface_hub.snapshot_download') as download:
            install_model(name, tmp_path)
            download.assert_not_called()


def test_missing_files_retry_fixed_revision_and_require_completion(tmp_path):
    name = 'sentiment'
    dest = populate(tmp_path, name)
    (dest/'config.json').unlink()
    with patch('huggingface_hub.snapshot_download') as download:
        with pytest.raises(RuntimeError, match='incomplete'):
            install_model(name, tmp_path)
        assert download.call_args.kwargs['revision'] == MODELS[name]['revision']
    # An incomplete install is not accepted on retry just because a marker exists.
    with patch('huggingface_hub.snapshot_download', side_effect=lambda **kwargs: (dest/'config.json').write_text('{}')):
        install_model(name, tmp_path)


def test_wrong_revision_is_not_silently_replaced(tmp_path):
    dest = populate(tmp_path, 'emotion')
    (dest/'hearing_lens_source.json').write_text(json.dumps({'model': MODELS['emotion']['model'], 'revision': 'wrong'}))
    with patch('huggingface_hub.snapshot_download') as download:
        with pytest.raises(RuntimeError, match='different revision'):
            install_model('emotion', tmp_path)
        download.assert_not_called()


@pytest.mark.parametrize('module_name,names', [
    ('scripts.setup_theme_model', ['all-MiniLM-L6-v2']),
    ('scripts.setup_affect_models', ['sentiment', 'emotion']),
])
def test_local_setup_commands_install_cloud_pins_and_reuse_matching_cache(tmp_path, module_name, names):
    import importlib
    module = importlib.import_module(module_name)

    def download(**kwargs):
        name = next(n for n in names if MODELS[n]['model'] == kwargs['repo_id'])
        assert kwargs['revision'] == MODELS[name]['revision']
        destination = kwargs['local_dir']
        for filename in MODELS[name]['files']:
            path = destination / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture model file')

    with patch.object(module, 'install_model', partial(install_model, root=tmp_path)), \
         patch('huggingface_hub.HfApi.model_info', side_effect=AssertionError('Do not select latest revision')), \
         patch('huggingface_hub.snapshot_download', side_effect=download) as fetch:
        module.main()
        assert fetch.call_count == len(names)
        for name in names:
            marker = json.loads((tmp_path / name / 'hearing_lens_source.json').read_text())
            assert marker == {key: MODELS[name][key] for key in ('model', 'revision', 'weights')}
        fetch.reset_mock()
        module.main()
        fetch.assert_not_called()


def test_legacy_setup_command_keeps_mismatched_cache_intact(tmp_path):
    from scripts import setup_theme_model
    name = 'all-MiniLM-L6-v2'
    destination = populate(tmp_path, name)
    marker = destination / 'hearing_lens_source.json'
    marker.write_text(json.dumps({'model': MODELS[name]['model'], 'revision': 'older-model'}))
    before = {str(p): p.read_bytes() for p in destination.rglob('*') if p.is_file()}
    with patch.object(setup_theme_model, 'install_model', partial(install_model, root=tmp_path)), \
         patch('huggingface_hub.snapshot_download') as fetch:
        with pytest.raises(RuntimeError, match='different revision'):
            setup_theme_model.main()
        fetch.assert_not_called()
    assert before == {str(p): p.read_bytes() for p in destination.rglob('*') if p.is_file()}


