"""On-demand Word briefs retained only in the current analysis workspace."""
import streamlit as st

from pipeline.brief import community_docx


def render_brief_download(workspace):
    st.subheader('Community brief')
    st.caption('Prepare a one-page Word summary of the current results and selected quotes. Review excerpts and possible identifiers before sharing. Missing references or response text are explained in the brief.')
    signature = (workspace['revision'], tuple(sorted(workspace['quote_revisions'].items())))
    if workspace.get('brief_signature') != signature:
        workspace.pop('brief_docx', None)
        workspace['brief_signature'] = signature
    if st.button('Prepare Word brief', key='hl_prepare_brief'):
        workspace.pop('brief_docx', None)
        try:
            with st.spinner('Preparing the community brief...'):
                workspace['brief_docx'] = community_docx(workspace['result'])
        except Exception:
            st.error('The Word brief could not be prepared. No partial document is offered. Check the analysis and local redaction model before trying again.')
    if workspace.get('brief_docx'):
        st.download_button('Download Word brief', data=workspace['brief_docx'],
                           file_name='hearing_lens_community_brief.docx',
                           mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                           key='hl_word_download')
