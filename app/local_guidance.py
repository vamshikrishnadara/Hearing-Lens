"""Practical next steps when a file exceeds the free online demo capacity."""
import streamlit as st


def render_local_guidance():
    st.subheader('Analyze this file on your computer')
    st.markdown(
        '1. **First time:** follow the [local installation instructions]'
        '(https://github.com/vamshikrishnadara/Hearing-Lens#install-and-run) '
        'to install Hearing Lens and its models. No paid hosting account is required.\n'
        '2. **Already installed:** open a terminal in the Hearing Lens project, '
        'activate its Python environment, and run the command below.\n'
        '3. In the local dashboard, upload **the complete file**, map the columns, '
        'and select **Analyze comments**. The same result tabs and CSV, Word and PDF downloads are available.'
    )
    st.code('python -m scripts.start_local', language='bash')
    st.caption('Keep the terminal open while using the dashboard. The local address works only on your computer.')
    st.info('For a quick online demonstration, upload a smaller sample within both displayed limits. '
            'A sample describes only those comments. Do not combine separate sample reports '
            'as if they were one full-file analysis; themes and comparisons can differ.')
