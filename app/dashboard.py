"""Session-only dashboard controls; no uploaded data is cached or written to disk."""
from hashlib import sha256
import json

import streamlit as st

from pipeline.quote_review import swap_quote

STATE_KEY = 'hearing_lens_workspace'
REVIEW_PREFIX = 'hl_review_'


def clear_workspace():
    st.session_state.pop(STATE_KEY, None)
    for key in list(st.session_state):
        if key.startswith((REVIEW_PREFIX, 'hl_option_')):
            del st.session_state[key]


def workspace_for(upload, sheet, mapping):
    """Invalidate results and review choices when bytes, sheet or mapping change."""
    signature = (sha256(upload.getvalue()).hexdigest(), sheet, json.dumps(mapping, sort_keys=True))
    current = st.session_state.get(STATE_KEY)
    if current is None or current['signature'] != signature:
        clear_workspace()
        current = {'signature': signature, 'mapped': None, 'preview': None,
                   'result': None, 'revision': 0, 'quote_revisions': {}}
        st.session_state[STATE_KEY] = current
    return current


def analyze_dashboard(frame, *, references=None, response=None):
    # Only models are shared by the analytical modules. Never cache these results.
    from app.runtime import run_analysis
    return run_analysis(frame, references=references, response=response)


def render_themes(workspace):
    result = workspace['result']
    core = result['themes']
    themes = core['themes']
    st.header('Themes')
    st.caption('Automatically grouped comments. Review the labels and supporting quotes before sharing findings.')
    columns = st.columns(3)
    columns[0].metric('Comments analyzed for themes', core['analyzed_comments'])
    columns[1].metric('Themes', len(themes))
    columns[2].metric('Ungrouped comments', core['outlier_count'])
    excluded = len(core.get('excluded_row_positions', []))
    if excluded:
        st.info(f'{excluded} comments had no usable text for theme analysis after cleaning and redaction.')
    st.caption('Theme percentages use comments analyzed for themes, including ungrouped comments, as the denominator.')
    for warning in core.get('warnings', []):
        st.warning(warning)
    if not themes:
        st.info('No themes were found. Try a file with more substantive comments.')
        return
    st.caption('Quote choices and review ticks last for this session only. They are not a measure of model accuracy.')
    for theme in themes:
        theme_id = theme['theme_id']
        quote_revision = workspace['quote_revisions'].get(theme_id, 0)
        base = f'{REVIEW_PREFIX}{workspace["revision"]}_{theme_id}_{quote_revision}'
        with st.container(border=True):
            st.subheader(f'Theme {theme_id}')
            st.text(theme['label'])
            st.caption(f'{theme["count"]:,} comments | {theme["share"]:.1%} of analyzed comments')
            if len(theme['quotes']) < 3:
                st.info('Fewer than three suitable distinct quotes are available for this theme.')
            alternatives = theme.get('quote_alternatives', [])
            for slot, quote in enumerate(theme['quotes']):
                st.markdown(f'**Supporting quote {slot + 1}**')
                st.text(quote['text'])
                kind = 'Excerpt from' if quote.get('is_excerpt') else 'From'
                st.caption(f'{kind} cleaned comment {quote["row_position"] + 1}')
                if alternatives:
                    choices = {q['row_position']: q for q in alternatives}
                    selected = st.selectbox(
                        f'Alternative for theme {theme_id}, quote {slot + 1}',
                        [None, *choices],
                        format_func=lambda value: 'Keep current quote' if value is None else f'Cleaned comment {value + 1}',
                        key=f'{base}_{slot}_choice',
                    )
                    if selected is not None:
                        st.text(choices[selected]['text'])
                    if st.button('Use this quote', key=f'{base}_{slot}_swap', disabled=selected is None):
                        result['themes'] = swap_quote(core, theme_id, slot, selected)
                        st.session_state.pop(f'{base}_confirmed', None)
                        # Reset alternatives before widgets are created on rerun.
                        workspace['quote_revisions'][theme_id] = quote_revision + 1
                        st.rerun()
            if not alternatives:
                st.caption('No additional eligible quotes are available for swapping.')
            st.checkbox('I reviewed this theme and its selected quotes for relevance and visible identifiers.',
                        key=f'{base}_confirmed')


def render_dashboard(workspace):
    from app.affect_panel import render_affect
    from app.timeline_panel import render_timeline
    from app.representation_panel import render_representation
    from app.questions_panel import render_questions
    from app.downloads import render_download
    from app.brief_download import render_brief_download
    tabs = st.tabs(['Themes', 'Sentiment and emotion', 'Timeline', 'Representation', 'Questions'])
    with tabs[0]:
        render_themes(workspace)
    with tabs[1]:
        render_affect(workspace['result'])
    with tabs[2]:
        render_timeline(workspace['result'])

    with tabs[3]:
        render_representation(workspace['result'])
    with tabs[4]:
        render_questions(workspace['result'])
    render_download(workspace)
    render_brief_download(workspace)
