import json
from unittest.mock import patch
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


