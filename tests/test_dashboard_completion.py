"""Check disclosure boundaries, optional inputs and complete dashboard downloads."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.dashboard import STATE_KEY
from app.downloads import labeled_csv
from app.representation_panel import representation_table
from pipeline.gaps import analyze_gaps

APP = Path(__file__).resolve().parents[1] / 'app/streamlit_app.py'


def sample_result(n=30):
    rows = [{'row_position': i, 'status': 'scored', 'sentiment': 'positive', 'emotion': 'joy',
             'sentiment_score': .5, 'truncated': False} for i in range(n)]
    return {'input_rows': n,
            'themes': {'analyzed_comments': n, 'outlier_count': 0, 'excluded_row_positions': [],
                       'warnings': [], 'themes': [{'theme_id': 1, 'label': 'Access', 'count': n, 'share': 1.,
                         'quotes': [{'row_position': 0, 'text': 'Can the center open later?'}], 'quote_alternatives': []}],
                       'assignments': [{'row_position': i, 'theme_id': 1} for i in range(n)]},
            'affect': {'rows': rows, 'truncated_count': 0, 'warnings': []}, 'affect_by_theme': [],
            'gaps': analyze_gaps(pd.DataFrame({'comment_text': ['Question']*n, 'subgroup__role': ['A']*(n//2)+['B']*(n-n//2)})),
            'questions': {'response_status': 'not_provided', 'top_unanswered': ['q001'],
                          'comment_question_counts': [1]*n,
                          'assignments': [{'row_position': i, 'question_group_id': 'q001'} for i in range(n)],
                          'groups': [{'rank': 1, 'question_group_id': 'q001', 'comment_count': n, 'sentence_count': n,
                                      'unique_wordings': 1, 'response_match_status': 'not_checked',
                                      'representative': {'text': 'Can the center open later?'},
                                      'response_matches': [], 'subgroup_spread': 2, 'spread_is_lower_bound': False}]}}


def upload(text=None):
    if text is None:
        text = 'comment_text,role,id\n' + ''.join(f'Can the center open later?,{("A" if i<15 else "B")},PRIVATE-{i}\n' for i in range(30))
    data = BytesIO(text.encode()); data.name = 'fictional.csv'
    return data


def widget(app, kind, label):
    return next(w for w in getattr(app, kind) if w.label == label)


def ready(app, subgroup=False):
    app.run()
    if subgroup:
        app.multiselect[0].select('role').run()
    widget(app, 'button', 'Validate mapping').click().run()
    widget(app, 'button', 'Analyze comments').click().run()
    assert not app.exception
    return app


def test_suppression_and_unknown_reference_are_not_reconstructed():
    f=pd.DataFrame({'comment_text':['Text']*35, 'subgroup__role':['Small']*5+['Large']*30})
    gaps=analyze_gaps(f,references={'subgroup__role': {'Small':.5,'Large':.5}})
    table=representation_table(gaps['rows'])
    for column in ['Comments','Participation (%)','Gap (percentage points)','Representation ratio']:
        assert table[column].isna().all()
    assert table['Reference (%)'].tolist()==[50,50]
    assert set(table['Status'])=={'Suppressed'}
    assert gaps['fields'][0]['known_rows']==35


def test_zero_reference_and_unmatched_categories_keep_unavailable_ratio():
    f=pd.DataFrame({'comment_text':['Text']*40,'subgroup__role':['A']*20+['B']*20})
    result=analyze_gaps(f,references={'subgroup__role': {'A':0,'C':1}})
    t=representation_table(result['rows']).set_index('Category')
    assert pd.isna(t.loc['A','Representation ratio'])
    assert pd.isna(t.loc['B','Gap (percentage points)'])
    assert 'Reference (%)' in t


def test_export_has_redacted_text_and_labels_without_metadata_or_formula_execution():
    r=sample_result(3)
    r['themes']['assignments']=[{'row_position':0,'theme_id':0},{'row_position':2,'theme_id':1}]
    r['themes']['themes'][0]['label']='=HYPERLINK("bad")'
    r['affect']['rows'][0]['sentiment_score']=-.5
    r['affect']['rows'][1]={'row_position':1,'status':'excluded_language'}
    safe=pd.DataFrame({'comment_text':['=1+1','[PERSON] supports access.','\t@SUM(1)']},index=[5,8,12])
    before=deepcopy(r)
    data=labeled_csv(r,safe)
    table=pd.read_csv(BytesIO(data),keep_default_na=False)
    assert data.startswith(b'\xef\xbb\xbf')
    assert table.redacted_comment.tolist()==["'=1+1",'[PERSON] supports access.',"'\t@SUM(1)"]
    assert table.theme_status.tolist()==['ungrouped','excluded','assigned']
    assert table.theme_label.iloc[2].startswith("'=")
    assert float(table.sentiment_score.iloc[0])==-.5
    assert table.sentiment.iloc[1]==''
    assert table.cleaned_comment_number.tolist()==[1,2,3]
    assert table.question_group_ids.tolist()==['q001']*3
    assert not {'respondent_id','date_or_hearing','subgroup__role'} & set(table)
    assert r==before


@pytest.mark.parametrize('text', [' +1', '-command', '@formula', '\n=1', '\r=2'])
def test_export_neutralizes_formula_prefixes(text):
    t=pd.read_csv(BytesIO(labeled_csv(sample_result(1),pd.DataFrame({'comment_text':[text]}))))
    assert t.redacted_comment[0]=="'"+text


def test_export_refuses_mismatched_rows_or_nonredacted_schema():
    r=sample_result(1)
    with pytest.raises(ValueError):labeled_csv(r,pd.DataFrame({'comment_text':['ok'],'respondent_id':['SECRET']}))
    r['questions']['comment_question_counts']=[]
    with pytest.raises(ValueError):labeled_csv(r,pd.DataFrame({'comment_text':['ok']}))


def test_all_panels_download_and_no_response_notice_without_extra_inference():
    with patch('streamlit.file_uploader',return_value=upload()), patch('app.dashboard.analyze_dashboard',return_value=sample_result()) as run:
        app=ready(AppTest.from_file(str(APP),default_timeout=30))
        assert len(app.tabs)==5
        assert len(app.get('download_button'))==1
        assert any('unverified follow-up priorities' in x.value for x in app.info)
        app.checkbox[0].check().run()
        assert run.call_count==1 and len(app.get('download_button'))==1


def test_response_change_clears_old_results_and_download_before_rerun():
    with patch('streamlit.file_uploader',return_value=upload()), patch('app.dashboard.analyze_dashboard',return_value=sample_result()) as run:
        app=ready(AppTest.from_file(str(APP),default_timeout=30))
        widget(app,'text_area','Response text (optional)').input('The center will open later.').run()
        assert not app.tabs and not app.get('download_button')
        assert app.session_state[STATE_KEY]['mapped'] is not None
        widget(app,'button','Analyze comments').click().run()
        assert run.call_args.kwargs['response']=='The center will open later.'
        assert len(app.tabs)==5
        run.side_effect=RuntimeError('SECRET RESPONSE')
        widget(app,'button','Analyze comments').click().run()
        assert not app.tabs and not app.get('download_button')
        assert 'SECRET' not in app.error[0].value


def test_invalid_reference_blocks_analysis_and_valid_reference_is_forwarded():
    with patch('streamlit.file_uploader',return_value=upload()), patch('app.dashboard.analyze_dashboard',return_value=sample_result()) as run:
        app=ready(AppTest.from_file(str(APP),default_timeout=30),subgroup=True)
        widget(app,'selectbox','Reference source').select('Enter reference').run()
        assert not app.tabs and widget(app,'button','Analyze comments').disabled
        widget(app,'text_area','Reference rows (CSV)').input('group,share\nSECRET,xyz').run()
        assert widget(app,'button','Analyze comments').disabled
        assert all('SECRET' not in x.value for x in app.error)
        widget(app,'text_area','Reference rows (CSV)').input('group,share\nA,60%\nB,40%').run()
        assert not widget(app,'button','Analyze comments').disabled
        widget(app,'button','Analyze comments').click().run()
        assert run.call_args.kwargs['references']['subgroup__role'].group.tolist()==['A','B']
        widget(app,'selectbox','Reference source').select('No reference').run()
        assert not app.tabs and not app.get('download_button')


def test_reference_csv_upload_and_new_upload_clear_auxiliary_inputs():
    ref=upload('group,share\nA,0.6\nB,0.4\n')
    main=upload()
    def picker(label,*args,**kwargs):return ref if label=='Reference CSV' else main
    with patch('streamlit.file_uploader',side_effect=picker), patch('app.dashboard.analyze_dashboard',return_value=sample_result()) as run:
        app=ready(AppTest.from_file(str(APP),default_timeout=30),subgroup=True)
        widget(app,'selectbox','Reference source').select('Upload reference CSV').run()
        widget(app,'button','Analyze comments').click().run()
        assert run.call_args.kwargs['references']['subgroup__role'].share.tolist()==['0.6','0.4']
        widget(app,'text_area','Response text (optional)').input('PRIVATE RESPONSE').run()
        main=upload('comment_text,role,id\nDifferent comment.,A,000\n')
        app.run()
        assert not app.tabs and not app.get('download_button')
        widget(app,'button','Validate mapping').click().run()
        assert widget(app,'text_area','Response text (optional)').value==''


@pytest.mark.parametrize('status', ['possible_match','partial_match','no_match'])
def test_response_matches_display_actual_passage_with_review_language(status):
    value=sample_result()
    value['questions']['response_status']='available'
    value['questions']['groups'][0].update(response_match_status=status,
       response_matches=[{'question_text':'Can the center open later?', 'similarity':.8,
                          'response':None if status=='no_match' else {'text':'The center opens late on Fridays.'}}])
    if status=='possible_match':value['questions']['top_unanswered']=[]
    with patch('streamlit.file_uploader',return_value=upload()), patch('app.dashboard.analyze_dashboard',return_value=value):
        app=ready(AppTest.from_file(str(APP),default_timeout=30))
        texts='\n'.join(x.value for x in app.text)
        if status!='no_match':assert 'Possible response passage: The center opens late on Fridays.' in texts
        else:assert any('No response passage met' in x.value for x in app.caption)
        assert not app.exception


def test_absent_subgroups_and_no_questions_have_explanations_and_export():
    value=sample_result()
    value['gaps']={'fields':[]}
    value['questions'].update(groups=[],top_unanswered=[],assignments=[],comment_question_counts=[0]*30)
    with patch('streamlit.file_uploader',return_value=upload()),patch('app.dashboard.analyze_dashboard',return_value=value):
        app=ready(AppTest.from_file(str(APP),default_timeout=30))
        assert any('No subgroup fields' in x.value for x in app.info)
        assert any('No question candidates' in x.value for x in app.info)
        assert len(app.get('download_button'))==1


def test_export_failure_offers_no_partial_download():
    with patch('streamlit.file_uploader',return_value=upload()),patch('app.dashboard.analyze_dashboard',return_value=sample_result()),patch('app.downloads.labeled_csv',side_effect=ValueError('PRIVATE')):
        app=ready(AppTest.from_file(str(APP),default_timeout=30))
        assert not app.get('download_button')
        assert len(app.tabs)==5
        assert 'PRIVATE' not in app.error[0].value
