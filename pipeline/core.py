"""Week 3 analytical-core entry point; all processing stays in memory."""
from pipeline.affect import analyze_affect, aggregate_affect
from pipeline.themes import analyze_themes
from pipeline.timeline import build_timeline
from pipeline.progress import notify


def analyze_core(frame, *, period_column=None, theme_count='auto', backend='auto', progress=None):
    options = {'progress': progress} if progress is not None else {}
    themes = analyze_themes(frame, theme_count=theme_count, backend=backend,
        keyword_method='keybert', merge_small_themes=True, quote_pool_size=6,
        quote_mode='sentences', **options)
    affect = analyze_affect(frame, **options)
    notify(progress, 'timeline')
    by_theme = aggregate_affect(affect['rows'], {a['row_position']: a['theme_id'] for a in themes['assignments']})
    timeline = build_timeline(frame, affect, themes['assignments'], period_column)
    return {'themes': themes, 'affect': affect, 'affect_by_theme': by_theme, 'timeline': timeline}
