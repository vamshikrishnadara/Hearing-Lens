"""In-memory labeled exports with redacted text and no identifying metadata."""
import pandas as pd
import streamlit as st


def spreadsheet_safe(value):
    # Quoting CSV cells alone does not stop spreadsheet formula interpretation.
    if isinstance(value, str) and (value.lstrip().startswith(('=', '+', '-', '@'))
                                   or value.startswith(('\t', '\r', '\n'))):
        return "'" + value
    return value


def labeled_csv(result, redacted_frame):
    """Join by cleaned row position; never accept the original uploaded table."""
    if list(redacted_frame.columns) != ['comment_text'] or len(redacted_frame) != result['input_rows']:
        raise ValueError('The redacted preview does not match this analysis.')
    size = result['input_rows']
    themes = {t['theme_id']: t['label'] for t in result['themes']['themes']}
    assignments = {a['row_position']: a['theme_id'] for a in result['themes']['assignments']}
    affect = {r['row_position']: r for r in result['affect']['rows']}
    counts = result['questions']['comment_question_counts']
    if len(counts) != size or set(affect) != set(range(size)) or not set(assignments) <= set(range(size)):
        raise ValueError('The analysis rows do not match the redacted preview.')
    groups = {}
    for item in result['questions']['assignments']:
        groups.setdefault(item['row_position'], set()).add(item['question_group_id'])
    rows = []
    for i, text in enumerate(redacted_frame.comment_text):
        a = affect[i]
        theme_id = assignments.get(i)
        rows.append({'cleaned_comment_number': i + 1, 'redacted_comment': text,
                     'theme_id': theme_id, 'theme_label': themes.get(theme_id, ''),
                     'theme_status': 'excluded' if theme_id is None else 'ungrouped' if theme_id == 0 else 'assigned',
                     'sentiment': a.get('sentiment', ''), 'emotion': a.get('emotion', ''),
                     'sentiment_score': a.get('sentiment_score'), 'affect_status': a['status'],
                     'affect_truncated': a.get('truncated', False),
                     'question_count': counts[i], 'question_group_ids': ';'.join(sorted(groups.get(i, [])))})
    table = pd.DataFrame(rows)
    table['theme_id'] = table['theme_id'].astype('Int64')
    return table.map(spreadsheet_safe).to_csv(index=False).encode('utf-8-sig')


def render_download(workspace):
    result = workspace['result']
    st.subheader('Download labeled results')
    if not all(key in result for key in ['questions', 'affect']) or 'assignments' not in result['themes']:
        st.info('Labeled results are unavailable for this analysis.')
        return
    st.caption('CSV includes redacted comments, theme labels, sentiment/emotion and question-group labels. Respondent IDs, dates and subgroup values are excluded. Comment numbers refer to the cleaned table. Review redaction before sharing; it can miss identifiers.')
    try:
        data = labeled_csv(result, workspace['preview'].frame)
    except Exception:
        st.error('Labeled results could not be prepared. Validate the input and run analysis again; no partial file is offered.')
        return
    st.download_button('Download labeled CSV', data=data, file_name='hearing_lens_labeled_comments.csv',
                       mime='text/csv', key='hl_labeled_download', on_click='ignore')
    st.caption('Spreadsheet formula-like text is prefixed with an apostrophe. Downloads are generated in memory for this session.')
