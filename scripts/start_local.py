"""Start the complete dashboard on loopback, without the free-demo limit."""
import argparse
import importlib.util
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8501)
    parser.add_argument('--headless', action='store_true', help='Do not open the browser automatically.')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Choose a port from 1024 to 65535.')
    if importlib.util.find_spec('streamlit') is None:
        parser.exit(1, 'Install the project requirements in this Python environment first. See README.md.\n')
    # Do not inherit the cloud entrypoint's admission policy into local use.
    os.environ['HEARING_LENS_DEPLOYMENT'] = 'local'
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    os.chdir(ROOT)
    print(f'Opening Hearing Lens at http://127.0.0.1:{args.port}. '
          'Keep this window open while using the app. Press Ctrl+C to stop.', flush=True)
    os.execv(sys.executable, [sys.executable, '-m', 'streamlit', 'run',
        str(ROOT / 'app/streamlit_app.py'), '--server.address=127.0.0.1',
        f'--server.port={args.port}', f'--server.headless={str(args.headless).lower()}',
        '--browser.gatherUsageStats=false'])


if __name__ == '__main__':
    main()
