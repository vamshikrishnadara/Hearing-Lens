"""Timeline charts and accessible numeric summaries from existing analysis."""
from html import escape
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def period_table(timeline):
    return pd.DataFrame([{'Period': p['group'], 'Comments': p['total_comments'],
                          'Scored': p['scored_comments'], 'Excluded': p['excluded_comments'],
                          'Mean sentiment': p['mean_sentiment']} for p in timeline['periods']])


def volume_table(timeline):
    rows = [{'Period': r['period'], 'Theme': 'Ungrouped' if r['theme_id'] == 0 else f'Theme {r["theme_id"]}',
             'Comments': r['count']} for r in timeline['theme_volumes']]
    return pd.DataFrame(rows, columns=['Period', 'Theme', 'Comments'])


def dashboard_timeline_figures(timeline):
    periods = timeline['periods']
    # Missing dates are disclosed in the tables and volume chart, but cannot be
    # positioned on a dated trend. Arbitrary hearing labels remain categories.
    dated = timeline['mode'] == 'date'
    plotted = [p for p in periods if not dated or p['group'] != 'Missing period']
    labels = [escape(str(p['group'])) for p in plotted]
    values = [p['mean_sentiment'] for p in plotted]
    sentiment = go.Figure()
    if dated:
        sentiment.add_trace(go.Scatter(x=labels, y=values, mode='lines+markers', connectgaps=False,
                            hovertemplate='%{x}: %{y:.3f}<extra></extra>', line_color='#276582'))
    else:
        sentiment.add_trace(go.Bar(x=labels, y=values, marker_color='#276582',
                            hovertemplate='%{x}: %{y:.3f}<extra></extra>'))
    sentiment.update_layout(title='Mean sentiment by period', xaxis_title='Date (UTC)' if dated else 'Period',
                            xaxis_type='date' if dated else 'category',
                            yaxis_title='Mean P(positive) minus P(negative)', yaxis_range=[-1, 1], height=370)
    volume = go.Figure()
    for theme in sorted({r['theme_id'] for r in timeline['theme_volumes']}):
        rows = [r for r in timeline['theme_volumes'] if r['theme_id'] == theme]
        volume.add_trace(go.Bar(x=[escape(str(r['period'])) for r in rows], y=[r['count'] for r in rows],
                               name='Ungrouped' if theme == 0 else f'Theme {theme}',
                               hovertemplate='%{x}: %{y} comments<extra>%{fullData.name}</extra>'))
    volume.update_layout(title='Theme volume by period', barmode='stack', xaxis_title='Period',
                         xaxis=dict(type='category', categoryorder='array',
                                    categoryarray=[escape(str(p['group'])) for p in periods]),
                         yaxis_title='Comments assigned to themes', yaxis=dict(rangemode='tozero', tickformat=',d'), height=370)
    return {'sentiment': sentiment, 'theme_volume': volume}


def render_timeline(result):
    st.header('Timeline')
    timeline = result.get('timeline')
    if not timeline or not timeline['periods']:
        st.info('No timeline periods are available for this run.')
        return
    for warning in timeline.get('warnings', []):
        st.info(warning)
    if timeline['mode'] == 'single_period':
        st.info('A single summary is shown because no date or hearing field was mapped. It cannot show change over time.')
    elif timeline['mode'] == 'hearing_label':
        st.caption('Hearing labels appear in input order as categories, not as a chronological trend.')
    elif len([p for p in timeline['periods'] if p['group'] != 'Missing period']) < 2:
        st.info('Only one dated period is available. More dates are needed to compare change over time.')
    if timeline['mode'] == 'date' and any(p['group'] == 'Missing period' for p in timeline['periods']):
        st.info('Comments without dates remain in the tables and volume chart under Missing period; they are excluded from the dated sentiment trend.')
    charts = dashboard_timeline_figures(timeline)
    periods_with_scores = [p for p in timeline['periods'] if p['mean_sentiment'] is not None
                           and (timeline['mode'] != 'date' or p['group'] != 'Missing period')]
    if periods_with_scores:
        st.plotly_chart(charts['sentiment'], use_container_width=True, key='hl_timeline_sentiment', config={'displaylogo': False})
    else:
        st.info('No sentiment scores are available for the plotted periods. Comment volumes can still be inspected.')
    if timeline['theme_volumes']:
        st.plotly_chart(charts['theme_volume'], use_container_width=True, key='hl_timeline_volume', config={'displaylogo': False})
    else:
        st.info('No theme assignments are available to plot.')
    st.caption('Sentiment averages use scored comments only. Theme volumes count assigned comments, including ungrouped comments, and can differ from total submissions when text is excluded from theme analysis.')
    st.subheader('Period summary')
    st.dataframe(period_table(timeline), hide_index=True, use_container_width=True)
    if timeline['theme_volumes']:
        st.subheader('Theme counts by period')
        st.dataframe(volume_table(timeline), hide_index=True, use_container_width=True)
