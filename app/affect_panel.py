"""Display aggregate model labels without exposing comment text or identifiers."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pipeline.affect import SENTIMENTS, EMOTIONS, aggregate_affect, sentiment_score_details


def overall_affect(result):
    rows = result['affect']['rows']
    groups = aggregate_affect(rows, {row['row_position']: 'All comments' for row in rows})
    return groups[0] if groups else None


def label_table(summary, kind):
    labels = SENTIMENTS if kind == 'sentiment' else EMOTIONS
    return pd.DataFrame({
        'Label': [label.capitalize() for label in labels],
        'Comments': [summary[f'{kind}_counts'][label] for label in labels],
        'Share of scored comments (%)': [
            None if summary[f'{kind}_shares'][label] is None else round(summary[f'{kind}_shares'][label] * 100, 2)
            for label in labels],
    })


def theme_affect_table(result):
    rows = []
    for group in result.get('affect_by_theme', []):
        ties = group['dominant_emotion_ties']
        dominant = group['dominant_emotion']
        row = {'Theme': 'Ungrouped' if group['group'] == 0 else f'Theme {group["group"]}',
               'Comments': group['total_comments'], 'Scored': group['scored_comments'],
               'Excluded': group['excluded_comments'], 'Mean sentiment': group['mean_sentiment'],
               'Most frequent emotion': ', '.join(ties) + ' (tie)' if ties else (dominant or 'Not available')}
        for label in SENTIMENTS:
            share = group['sentiment_shares'][label]
            row[f'{label.capitalize()} (%)'] = None if share is None else round(share * 100, 2)
        rows.append(row)
    return pd.DataFrame(rows)


def sentiment_details_table(result):
    """Link scores to CSV comment numbers without displaying source text."""
    rows = []
    for row in result['affect']['rows']:
        scores = sentiment_score_details(row)
        if scores is None:
            continue
        rows.append({'Cleaned comment number': row['row_position'] + 1,
                     'Model label': row['sentiment'].capitalize(),
                     **{f'{label.capitalize()} score (%)': scores[label] * 100 for label in SENTIMENTS},
                     'Top-two gap (percentage points)': scores['gap'] * 100})
    if not rows:
        return pd.DataFrame()
    # Sort unrounded values so close decisions retain their actual order.
    return (pd.DataFrame(rows).sort_values(
        ['Top-two gap (percentage points)', 'Cleaned comment number'])
        .reset_index(drop=True).round(2))


def distribution_chart(table, title):
    fig = go.Figure(go.Bar(x=table['Label'].tolist(), y=table['Comments'].tolist(),
                          marker_color='#276582', hovertemplate='%{x}: %{y} comments<extra></extra>'))
    fig.update_layout(title=title, xaxis_title='Model label', yaxis_title='Scored comments',
                      yaxis=dict(rangemode='tozero', tickformat=',d'), height=320)
    return fig


def render_affect(result):
    st.header('Sentiment and emotion')
    st.caption('Model estimates of expressed tone, not agreement with a proposal or a judgment about a person.')
    if not result.get('affect'):
        st.info('No sentiment or emotion results are available for this run.')
        return
    affect = result['affect']
    summary = overall_affect(result)
    if summary is None:
        st.info('No comments are available for sentiment or emotion analysis.')
        return
    cols = st.columns(3)
    cols[0].metric('Comments scored', summary['scored_comments'])
    cols[1].metric('Comments excluded', summary['excluded_comments'])
    cols[2].metric('Long comments truncated', affect['truncated_count'])
    st.caption('Percentages use scored comments only. Excluded comments receive no substitute neutral label. Long inputs may be shortened to the model context limit.')
    for warning in affect.get('warnings', []):
        st.warning(warning)
    if not summary['scored_comments']:
        st.info('No comments received sentiment or emotion scores. Check the language and text quality; unavailable scores are not zero or neutral.')
    else:
        cols = st.columns(2)
        for column, kind, title in [(cols[0], 'sentiment', 'Sentiment distribution'),
                                    (cols[1], 'emotion', 'Emotion distribution')]:
            table = label_table(summary, kind)
            with column:
                st.plotly_chart(distribution_chart(table, title), use_container_width=True,
                                key=f'hl_affect_{kind}', config={'displaylogo': False})
                st.dataframe(table, hide_index=True, use_container_width=True)
        with st.expander('Inspect sentiment scores'):
            st.caption('The closest decisions appear first. The gap is the largest minus the second-largest model score; a small gap means the model scores are close. A large gap does not prove the label is correct. Mixed praise and criticism can be difficult to classify.')
            details = sentiment_details_table(result)
            if details.empty:
                st.info('Per-comment sentiment scores are unavailable for this result. Missing scores are not zero.')
            else:
                st.caption('Match cleaned comment numbers to the labeled CSV to read the redacted text. Scores are not calibrated certainty. This table does not change labels, counts or reports.')
                st.dataframe(details, hide_index=True, use_container_width=True)
                unavailable = summary['scored_comments'] - len(details)
                if unavailable:
                    st.info(f'{unavailable:,} scored comments have no usable detailed scores in this result and are omitted from this table; they remain in the totals.')
    table = theme_affect_table(result)
    if not table.empty:
        st.subheader('Tone by theme')
        st.caption('Theme IDs match the Themes panel. Mean sentiment ranges from -1 to +1 and averages positive minus negative model probability. A dash means no score is available; ties are retained.')
        st.dataframe(table, hide_index=True, use_container_width=True)
