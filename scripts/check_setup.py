"""Check local installation metadata and model files without downloads or inference."""
from importlib import metadata
import json
from pathlib import Path
import sys

from scripts.model_setup import MODELS, ROOT

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def check_setup(model_root=ROOT):
    """Return actionable problems; do not import model libraries or modify files."""
    problems = []
    try:
        from packaging.requirements import Requirement
    except ImportError:
        return ['Package version checking is unavailable. Run: python -m pip install -r requirements.txt']

    for line in (PROJECT_ROOT / 'requirements.txt').read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        requirement = Requirement(line)
        if requirement.marker and not requirement.marker.evaluate():
            continue
        try:
            installed = metadata.version(requirement.name)
        except metadata.PackageNotFoundError:
            problems.append(f'Missing package: {requirement.name}. Run: python -m pip install -r requirements.txt')
            continue
        if installed not in requirement.specifier:
            problems.append(f'{requirement.name} {installed} does not meet {requirement.specifier}. '
                            'Run: python -m pip install -r requirements.txt')

    try:
        metadata.version('en-core-web-sm')
    except metadata.PackageNotFoundError:
        problems.append('Missing English name-detection model. Run: python -m spacy download en_core_web_sm')

    for name, model in MODELS.items():
        destination = Path(model_root) / name
        try:
            recorded = json.loads((destination / 'hearing_lens_source.json').read_text())
        except (OSError, ValueError):
            problems.append(f'{name}: missing or unreadable model source record. '
                            'See docs/troubleshooting.md before repairing the cache.')
            continue
        if not isinstance(recorded, dict) or any(
                recorded.get(key) != model[key] for key in ('model', 'revision')):
            problems.append(f'{name}: model revision does not match. '
                            'Preserve the old cache and follow docs/troubleshooting.md.')
            continue
        missing = []
        for filename in model['files']:
            path = destination / filename
            try:
                valid = path.is_file() and path.stat().st_size > 0
            except OSError:
                valid = False
            if not valid:
                missing.append(filename)
        if missing:
            problems.append(f'{name}: {len(missing)} required model file(s) missing or empty. '
                            'Run: python -m scripts.model_setup')
    return problems


def main():
    print(f'Hearing Lens local setup check (Python {sys.version.split()[0]}; Python 3.12 recommended)')
    problems = check_setup()
    if problems:
        print('\nSetup needs attention:')
        for problem in problems:
            print(f'- {problem}')
        print('\nNo files were changed or downloaded.')
        return 1
    print('Package versions and required model files match the setup requirements.')
    print('This does not load models, verify file contents, or test analysis. '
          'Next: python -m scripts.start_local, then try a small fictional file.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
