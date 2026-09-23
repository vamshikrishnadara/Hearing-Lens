"""Download the fixed public embedding model during setup, never during analysis."""

import json
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download


def main():
    repo = "sentence-transformers/all-MiniLM-L6-v2"
    destination = Path(__file__).resolve().parents[1] / "model_cache/all-MiniLM-L6-v2"
    revision = HfApi().model_info(repo).sha
    snapshot_download(
        repo_id=repo, revision=revision, local_dir=destination,
        allow_patterns=["*.json", "*.txt", "*.safetensors", "1_Pooling/*"],
        ignore_patterns=["onnx/*", "openvino/*"],
    )
    (destination / "hearing_lens_source.json").write_text(
        json.dumps({"model": repo, "revision": revision}, indent=2)
    )
    print(f"Downloaded {repo} at {revision} to {destination}")


if __name__ == "__main__":
    main()
