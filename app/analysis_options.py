"""Optional, user-supplied analysis inputs held only in the current session."""
from hashlib import sha256
from io import BytesIO
import json

import streamlit as st
from pipeline.reference import ReferenceError, load_reference_csv


def render_analysis_options(frame):
    references, signature, errors = {}, [], []
    fields = [c for c in frame.columns if c.startswith('subgroup__')]
    with st.expander('Optional reference values and response text'):
        st.caption('Supply reference shares only when they cover the same categories and context as your comments. Without them, Representation shows counts and participation shares.')
        for field in fields:
            label = field.removeprefix('subgroup__')
            st.text(f'Reference for {label}')
            mode = st.selectbox('Reference source', ['No reference', 'Enter reference', 'Upload reference CSV'], key=f'hl_option_mode_{field}')
            content = b''
            if mode == 'Enter reference':
                text = st.text_area('Reference rows (CSV)', key=f'hl_option_manual_{field}',
                                    placeholder='group,share\nExample A,60%\nExample B,40%', max_chars=100_000,
                                    help='Use group and share headers. Shares must total 100%. Use 0.6 or 60%, not 60.')
                content = text.encode('utf-8')
            elif mode == 'Upload reference CSV':
                upload = st.file_uploader('Reference CSV', type=['csv'], key=f'hl_option_upload_{field}')
                content = upload.getvalue() if upload is not None else b''
            signature.append([field, mode, sha256(content).hexdigest()])
            if mode != 'No reference':
                try:
                    if not content.strip():
                        raise ReferenceError('Add reference rows or select No reference.')
                    references[field] = load_reference_csv(BytesIO(content))
                except ReferenceError as exc:
                    st.error(str(exc))
                    errors.append(field)
        response = st.text_area('Response text (optional)', key='hl_option_response', max_chars=100_000,
                                help='Paste an actual response to compare with question candidates. A similar passage is only a possible match, not proof of an answer.')
        st.caption('Without response text, question priorities remain unverified follow-up suggestions.')
    signature.append(['response', sha256(response.encode()).hexdigest()])
    return references, response or None, json.dumps(signature), not errors


def invalidate_options(workspace, signature):
    """Preserve validated mapping but discard results when auxiliary inputs change."""
    if workspace.get('options_signature') != signature:
        workspace['options_signature'] = signature
        workspace['result'] = None
        workspace['revision'] += 1
        workspace['quote_revisions'] = {}
        for key in list(st.session_state):
            if key.startswith('hl_review_'):
                del st.session_state[key]
