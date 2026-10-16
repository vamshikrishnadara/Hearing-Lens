"""Community Cloud entrypoint: prepare model files before showing the upload UI."""
import os
from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('HEARING_LENS_THREADS', '2')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

import streamlit as st
from scripts.model_setup import install_all


@st.cache_resource(show_spinner='Preparing analysis models. The first startup may take several minutes.')
def prepare_models():
    # Only setup completion is shared, never uploads, labels or analytical results.
    install_all()
    return True


try:
    prepare_models()
except Exception:
    st.error('Analysis models could not be prepared. Please retry later or contact the app operator.')
    st.stop()

runpy.run_module('app.streamlit_app', run_name='__main__')
