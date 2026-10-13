"""Verify displayed denominators, exclusions, periods and session-only rendering."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
import json

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from app.affect_panel import overall_affect,label_table,theme_affect_table
from app.timeline_panel import dashboard_timeline_figures,period_table,volume_table
from pipeline.affect import aggregate_affect
from pipeline.timeline import build_timeline

APP=Path(__file__).resolve().parents[1]/'app/streamlit_app.py'


def fixture(mode='date',unscored=False):
    rows=[{'row_position':i,'status':'scored','language':'en','sentiment':s,'emotion':e,'sentiment_score':v,'truncated':i==0}
          for i,(s,e,v) in enumerate([('positive','joy',.8),('negative','anger',-.4),('neutral','neutral',0.),('positive','fear',.2)])]
    rows.insert(3,{'row_position':3,'status':'excluded_language','language':'unknown'})
    rows[-1]['row_position']=4
    if unscored:rows=[{'row_position':i,'status':'excluded_language','language':'unknown'} for i in range(5)]
    assignments=[{'row_position':i,'theme_id':theme} for i,theme in enumerate([1,1,0,2,1])]
    frame=pd.DataFrame({'comment_text':['Fictional community feedback for the test.']*5})
    if mode=='date':frame['date_or_hearing']=['2026-10-12','2026-10-13','2026-10-13','2026-10-14','']
    if mode=='hearing_label':frame['date_or_hearing']=['Session B','Session A','Session A','Session C','']
    affect={'rows':rows,'scored_count':0 if unscored else 4,'excluded_language_count':5 if unscored else 1,
            'empty_count':0,'truncated_count':0 if unscored else 1,'warnings':['English model estimates; excluded rows are not neutral.']}
    timeline=build_timeline(frame,affect,assignments)
    return {'input_rows':5,'affect':affect,'affect_by_theme':aggregate_affect(rows,{a['row_position']:a['theme_id'] for a in assignments}),
            'timeline':timeline,'themes':{'analyzed_comments':5,'outlier_count':1,'excluded_row_positions':[],
            'warnings':[],'themes':[{'theme_id':i,'label':f'Fictional topic {i}','count':n,'share':n/5,'quotes':[],
                                     'quote_alternatives':[]} for i,n in [(1,3),(2,1)]]}}


def test_overall_denominators_and_theme_exclusions():
    value=fixture();before=deepcopy(value)
    summary=overall_affect(value)
    assert summary['total_comments']==5 and summary['scored_comments']==4 and summary['excluded_comments']==1
    sentiment=label_table(summary,'sentiment').set_index('Label')
    assert sentiment.loc['Positive','Comments']==2
    assert sentiment.loc['Positive','Share of scored comments (%)']==50
    assert sentiment.loc['Neutral','Share of scored comments (%)']==25
    assert label_table(summary,'emotion')['Comments'].sum()==4
    themes=theme_affect_table(value).set_index('Theme')
    assert themes.loc['Theme 2','Scored']==0
    assert pd.isna(themes.loc['Theme 2','Mean sentiment'])
    assert themes.loc['Theme 2','Most frequent emotion']=='Not available'
    assert 'Ungrouped' in themes.index
    assert value==before


def test_tied_emotions_are_not_arbitrarily_selected():
    value=fixture();value['affect_by_theme']=aggregate_affect(value['affect']['rows'],{0:1,1:1})
    assert theme_affect_table(value).iloc[0]['Most frequent emotion']=='anger, joy (tie)'


def test_all_excluded_returns_null_shares_and_no_mean():
    value=fixture(unscored=True);summary=overall_affect(value)
    assert summary['scored_comments']==0 and summary['mean_sentiment'] is None
    assert label_table(summary,'sentiment')['Share of scored comments (%)'].isna().all()


def test_empty_affect_has_no_fabricated_summary():
    assert overall_affect({'affect':{'rows':[]}}) is None


def test_dated_chart_omits_unknown_date_but_preserves_volume_and_null_gap():
    value=fixture()['timeline'];before=deepcopy(value)
    charts=dashboard_timeline_figures(value)
    trace=charts['sentiment'].data[0]
    assert list(trace.x)==['2026-10-12','2026-10-13','2026-10-14']
    assert list(trace.y)==[.8,-.2,None]
    assert trace.connectgaps is False
    assert charts['sentiment'].layout.xaxis.type=='date'
    assert sum(sum(t.y) for t in charts['theme_volume'].data)==5
    assert 'Missing period' in charts['theme_volume'].data[0].x
    assert period_table(value)['Comments'].sum()==5
    assert volume_table(value)['Comments'].sum()==5
    assert value==before


def test_hearing_labels_keep_order_and_use_categories_without_trend_lines():
    value=fixture('hearing_label')['timeline'];charts=dashboard_timeline_figures(value)
    assert list(charts['sentiment'].data[0].x)==['Session B','Session A','Session C','Missing period']
    assert charts['sentiment'].data[0].type=='bar'
    assert charts['sentiment'].layout.xaxis.type=='category'


def test_html_in_labels_is_escaped_for_plotly():
    value=fixture('single_period')['timeline']
    label='<a href="https://example.invalid">click</a>'
    value['periods'][0]['group']=label
    for row in value['theme_volumes']:row['period']=label
    charts=dashboard_timeline_figures(value)
    for fig in charts.values():
        for trace in fig.data:
            assert all('<' not in x and '&lt;' in x for x in trace.x)
    assert period_table(value).iloc[0]['Period']==label


def button(app,label):return next(b for b in app.button if b.label==label)


def uploaded():
    data=BytesIO(('comment_text,alternate\n'+'Fictional school feedback.,Alternative feedback.\n'*5).encode());data.name='fictional.csv';return data


def render(value):
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    button(app,'Validate mapping').click().run()
    button(app,'Analyze comments').click().run()
    assert not app.exception
    return app


def plots(app):return [json.loads(w.proto.spec) for w in app.get('plotly_chart')]


def test_app_shows_three_tabs_correct_counts_and_numeric_tables():
    value=fixture()
    with patch('streamlit.file_uploader',return_value=uploaded()),patch('app.dashboard.analyze_dashboard',return_value=value) as model:
        app=render(value)
        assert [tab.label for tab in app.tabs]==['Themes','Sentiment and emotion','Timeline']
        metrics={m.label:m.value for m in app.metric}
        assert metrics['Comments scored']=='4' and metrics['Comments excluded']=='1'
        assert metrics['Long comments truncated']=='1'
        assert len(plots(app))==4
        assert any('Comments without dates' in m.value for m in app.info)
        tables=[d.value for d in app.dataframe]
        assert any('Share of scored comments (%)' in t for t in tables)
        assert any('Period' in t and 'Mean sentiment' in t for t in tables)
        app.checkbox[0].check().run()
        assert model.call_count==1
        assert len(plots(app))==4
        assert not app.exception


def test_app_excluded_only_keeps_volume_without_sentiment_charts():
    value=fixture(unscored=True)
    with patch('streamlit.file_uploader',return_value=uploaded()),patch('app.dashboard.analyze_dashboard',return_value=value):
        app=render(value)
        assert any('No comments received' in m.value for m in app.info)
        assert any('No sentiment scores' in m.value for m in app.info)
        assert len(plots(app))==1
        assert plots(app)[0]['layout']['title']['text']=='Theme volume by period'


@pytest.mark.parametrize('mode,needle',[('single_period','single summary'),('hearing_label','input order')])
def test_app_missing_or_nondated_periods_explained(mode,needle):
    value=fixture(mode)
    with patch('streamlit.file_uploader',return_value=uploaded()),patch('app.dashboard.analyze_dashboard',return_value=value):
        app=render(value)
        assert any(needle in m.value for m in [*app.info,*app.caption])


def test_app_empty_periods_and_affect_do_not_crash():
    value=fixture();value['affect']['rows']=[];value['timeline']['periods']=[]
    with patch('streamlit.file_uploader',return_value=uploaded()),patch('app.dashboard.analyze_dashboard',return_value=value):
        app=render(value)
        assert not plots(app)
        assert any('No timeline periods' in m.value for m in app.info)
        assert any('No comments are available' in m.value for m in app.info)


def test_app_clears_all_panels_after_mapping_change_and_failed_rerun():
    value=fixture()
    with patch('streamlit.file_uploader',return_value=uploaded()),patch('app.dashboard.analyze_dashboard',return_value=value) as model:
        app=render(value)
        model.side_effect=RuntimeError('private input not for display')
        button(app,'Analyze comments').click().run()
        assert not app.tabs and not plots(app)
        assert 'private input' not in app.error[0].value
        model.side_effect=None
        button(app,'Analyze comments').click().run()
        next(s for s in app.selectbox if s.label=='Comment text').select('alternate').run()
        assert not app.tabs and not plots(app)


def test_app_no_theme_assignments_keeps_period_summary():
    value=fixture();value['timeline']['theme_volumes']=[]
    with patch('streamlit.file_uploader',return_value=uploaded()),patch('app.dashboard.analyze_dashboard',return_value=value):
        app=render(value)
        assert any('No theme assignments' in m.value for m in app.info)
        assert len(plots(app))==3


def test_zero_sentiment_is_displayed_as_a_score_not_missing():
    value=fixture('single_period')
    value['timeline']['periods'][0]['mean_sentiment']=0.
    with patch('streamlit.file_uploader',return_value=uploaded()),patch('app.dashboard.analyze_dashboard',return_value=value):
        app=render(value)
        chart=next(p for p in plots(app) if p['layout']['title']['text']=='Mean sentiment by period')
        assert chart['data'][0]['y']==[0.]
        assert not any('No sentiment scores' in m.value for m in app.info)


def test_one_date_is_explained_without_inventing_additional_periods():
    value=fixture()
    value['timeline']['periods']=value['timeline']['periods'][:1]
    value['timeline']['theme_volumes']=[r for r in value['timeline']['theme_volumes'] if r['period']=='2026-10-12']
    with patch('streamlit.file_uploader',return_value=uploaded()),patch('app.dashboard.analyze_dashboard',return_value=value):
        app=render(value)
        assert any('Only one dated period' in m.value for m in app.info)
        chart=next(p for p in plots(app) if p['layout']['title']['text']=='Mean sentiment by period')
        assert chart['data'][0]['x']==['2026-10-12']
