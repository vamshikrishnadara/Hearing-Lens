"""Period aggregation and Plotly figures; explicit missing-date behavior."""
from collections import Counter
import pandas as pd
from pipeline.affect import aggregate_affect
from pipeline.redact import build_safe_display_frame


class TimelineError(ValueError):
    pass


def build_timeline(frame, affect, assignments, period_column=None):
    if period_column is None:
        period_column = next((c for c in ('date_or_hearing', 'hearing_date', 'date', 'hearing_id') if c in frame), None)
    if period_column is not None and period_column not in frame:
        raise TimelineError('Selected period column is not available.')
    notes = []
    if period_column is None:
        periods, mode = ['All comments'] * len(frame), 'single_period'
        notes.append('No date or hearing column supplied; showing a single period.')
    else:
        raw = frame[period_column].fillna('').astype(str).str.strip()
        parsed = pd.to_datetime(raw.where(raw.ne('')), errors='coerce', format='mixed', utc=True)
        if raw.ne('').any() and parsed[raw.ne('')].notna().all():
            mode = 'date'
            periods = parsed.dt.strftime('%Y-%m-%d').fillna('Missing period').tolist()
            notes.append('Dates are grouped by UTC calendar day; ambiguous dates use month-first parsing.')
        else:
            mode = 'hearing_label'
            # Arbitrary user-supplied labels can contain PII too.
            safe = build_safe_display_frame(pd.DataFrame({'comment_text': raw})).frame.comment_text.tolist()
            periods = [value or 'Missing period' for value in safe]
            notes.append('Some values are not dates; all values are treated as redacted hearing labels in input order.')
    positions = [a['row_position'] for a in assignments]
    if len(set(positions)) != len(positions) or any(not isinstance(i, int) or not 0 <= i < len(frame) for i in positions):
        raise TimelineError('Theme assignments must use unique valid input row positions.')
    scored_positions = [r['row_position'] for r in affect['rows']]
    if scored_positions != list(range(len(frame))):
        raise TimelineError('Affect rows must match the input frame in original order.')
    # Include every nonempty input in the period affect summary, even if redaction
    # excluded it from themes. Theme volumes use assignments only, including 0=outlier.
    group_map = {r['row_position']: periods[r['row_position']] for r in affect['rows'] if r['status'] != 'empty'}
    summary = aggregate_affect(affect['rows'], group_map)
    if mode == 'date':
        summary.sort(key=lambda row: (row['group'] == 'Missing period', row['group']))
    counts = Counter((periods[a['row_position']], a['theme_id']) for a in assignments)
    volumes = [{'period': period['group'], 'theme_id': theme, 'count': counts[period['group'], theme]}
               for period in summary for theme in sorted({a['theme_id'] for a in assignments})]
    return {'mode': mode, 'period_column': period_column, 'periods': summary,
            'theme_volumes': volumes, 'warnings': notes}


def timeline_figures(result):
    import plotly.graph_objects as go
    periods = result['periods']
    sentiment = go.Figure(go.Scatter(x=[p['group'] for p in periods],
        y=[p['mean_sentiment'] for p in periods], mode='lines+markers', connectgaps=False))
    sentiment.update_layout(title='Mean sentiment by period', xaxis_title='Period',
        yaxis_title='Mean P(positive) minus P(negative)', yaxis_range=[-1, 1])
    volume = go.Figure()
    for theme in sorted({row['theme_id'] for row in result['theme_volumes']}):
        rows = [row for row in result['theme_volumes'] if row['theme_id'] == theme]
        volume.add_trace(go.Scatter(x=[r['period'] for r in rows], y=[r['count'] for r in rows],
            mode='lines+markers', name='Outliers' if theme == 0 else f'Theme {theme}'))
    volume.update_layout(title='Theme volume by period', xaxis_title='Period', yaxis_title='Comments')
    return {'sentiment': sentiment, 'theme_volume': volume}
