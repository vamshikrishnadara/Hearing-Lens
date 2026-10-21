"""Read-only methods page; no uploads, inference or personal evaluation records."""
from pathlib import Path
import re
from urllib.parse import urljoin

import streamlit as st

_DOCS = Path(__file__).resolve().parents[2] / 'docs'
_PUBLIC_DOCS = 'https://github.com/vamshikrishnadara/Hearing-Lens/blob/main/docs/'


def _document(name):
    text = (_DOCS / name).read_text(encoding='utf-8')
    # Repository-relative links need public destinations when shown in the app.
    text = re.sub(r'\]\(([^)]+)\)',
                  lambda match: '](' + urljoin(_PUBLIC_DOCS, match.group(1)) + ')', text)
    return text.split('\n', 1)[1].lstrip()


def render_methodology():
    st.title('Methodology and limitations')
    st.caption('How Hearing Lens analyzes feedback, what has been measured, and how to interpret the results.')
    st.markdown(_document('methods.md'))
    st.header('Validation results')
    st.markdown(_document('validation.md'))


if __name__ == '__main__':
    render_methodology()
