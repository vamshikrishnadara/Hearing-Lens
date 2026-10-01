"""Download public affect model weights explicitly during setup, never analysis."""
import json
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download

MODELS = {
    'sentiment': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
    'emotion': 'j-hartmann/emotion-english-distilroberta-base',
}


def main():
    root = Path(__file__).resolve().parents[1] / 'model_cache'
    for kind, repo in MODELS.items():
        info = HfApi().model_info(repo)
        files = {item.rfilename for item in info.siblings}
        weights = 'model.safetensors' if 'model.safetensors' in files else 'pytorch_model.bin'
        destination = root / kind
        snapshot_download(repo, revision=info.sha, local_dir=destination,
                          allow_patterns=[weights, 'config.json', 'tokenizer*', 'special_tokens_map.json', 'vocab.json', 'merges.txt', 'README.md'])
        (destination / 'hearing_lens_source.json').write_text(json.dumps({
            'model': repo, 'revision': info.sha, 'weights': weights}, indent=2))
        print(f'{kind}: downloaded pinned revision {info.sha}', flush=True)


if __name__ == '__main__':
    main()
