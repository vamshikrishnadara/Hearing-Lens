"""Install known model revisions before accepting uploads; never fetch submissions."""
import json
from pathlib import Path

MODELS = {
    'all-MiniLM-L6-v2': {
        'model': 'sentence-transformers/all-MiniLM-L6-v2',
        'revision': '1110a243fdf4706b3f48f1d95db1a4f5529b4d41',
        'weights': 'model.safetensors',
        'files': ['model.safetensors', 'config.json', 'config_sentence_transformers.json',
                  'modules.json', 'sentence_bert_config.json', 'tokenizer.json',
                  'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt', '1_Pooling/config.json'],
    },
    'sentiment': {
        'model': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
        'revision': '3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7',
        'weights': 'pytorch_model.bin',
        'files': ['pytorch_model.bin', 'config.json', 'vocab.json', 'merges.txt', 'special_tokens_map.json'],
    },
    'emotion': {
        'model': 'j-hartmann/emotion-english-distilroberta-base',
        'revision': '0e1cd914e3d46199ed785853e12b57304e04178b',
        'weights': 'pytorch_model.bin',
        'files': ['pytorch_model.bin', 'config.json', 'tokenizer_config.json',
                  'vocab.json', 'merges.txt', 'special_tokens_map.json'],
    },
}
ROOT = Path(__file__).resolve().parents[1] / 'model_cache'


def install_model(name, root=ROOT):
    from huggingface_hub import snapshot_download
    model = MODELS[name]
    destination = Path(root) / name
    marker = destination / 'hearing_lens_source.json'
    provenance = {key: model[key] for key in ('model', 'revision', 'weights')}
    existing = None
    if marker.exists():
        existing = json.loads(marker.read_text())
        if any(existing.get(key) != model[key] for key in ('model', 'revision')):
            raise RuntimeError('The model cache contains a different revision. Use a fresh cache directory.')
    complete = all((destination / name).is_file() and (destination / name).stat().st_size > 0
                   for name in model['files'])
    if existing and complete:
        return
    snapshot_download(repo_id=model['model'], revision=model['revision'], local_dir=destination,
                      allow_patterns=model['files'] + ['tokenizer*.json'], max_workers=2)
    if not all((destination / name).is_file() and (destination / name).stat().st_size > 0
               for name in model['files']):
        raise RuntimeError('Model installation is incomplete.')
    marker.write_text(json.dumps(provenance, indent=2)+'\n')


def install_all():
    for name in MODELS:
        install_model(name)


if __name__ == '__main__':
    install_all()
