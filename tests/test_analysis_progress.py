"""Progress is diagnostic only and cannot expose inputs or imply partial success."""
from unittest.mock import patch
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest
from pipeline.full import analyze_all
from pipeline.affect import analyze_affect
from pipeline.themes import analyze_themes
from app.runtime import AnalysisBusyError
from tests.test_dashboard_completion import upload, ready, APP
from tests.test_brief import result


def test_full_progress_orders_stages_without_changing_result():
    frame=pd.DataFrame({'comment_text':['When will classes start?']})
    def themes(frame,**kwargs):
        if kwargs.get('progress'):
            kwargs['progress']('embeddings');kwargs['progress']('clustering')
        return {'assignments':[{'row_position':0,'theme_id':1}]}
    def affect(frame,**kwargs):
        if kwargs.get('progress'):kwargs['progress']('sentiment')
        return {'rows':[{'row_position':0,'status':'excluded_language'}]}
    stages=[]
    with patch('pipeline.core.analyze_themes',side_effect=themes),patch('pipeline.core.analyze_affect',side_effect=affect),patch('pipeline.questions._embed',return_value=np.ones((1,3))):
        baseline=analyze_all(frame)
        actual=analyze_all(frame,progress=stages.append)
    assert actual==baseline
    assert stages==['representation','embeddings','clustering','sentiment','timeline','questions','complete']


def test_theme_and_affect_callbacks_report_real_work_boundaries():
    frame=pd.DataFrame({'comment_text':['Please add more books and extend the library hours for children after school.']})
    stages=[]
    with patch('pipeline.themes._theme_vectors',return_value=np.ones((1,2))):
        analyze_themes(frame,theme_count=1,progress=stages.append)
    assert stages==['redaction','embeddings','clustering','keywords','quotes']
    from tests.test_affect import predict
    stages=[]
    with patch('pipeline.affect.detect_language',return_value='en'),patch('pipeline.affect._predict',side_effect=predict):
        analyze_affect(frame,progress=stages.append)
    assert stages==['language','sentiment','emotion']


def test_dashboard_displays_completed_stage_only_after_success():
    def analyze(frame,**kwargs):
        kwargs['progress']('clustering');kwargs['progress']('emotion')
        return result()
    with patch('streamlit.file_uploader',return_value=upload()),patch('app.dashboard.analyze_dashboard',side_effect=analyze):
        app=ready(AppTest.from_file(str(APP),default_timeout=30))
    assert not app.error
    assert app.get('status')[0].label=='Analysis complete'


def test_busy_dashboard_shows_no_success_or_results():
    with patch('streamlit.file_uploader',return_value=upload()),patch('app.dashboard.analyze_dashboard',side_effect=AnalysisBusyError('Another analysis is still running.')):
        app=ready(AppTest.from_file(str(APP),default_timeout=30))
    assert not app.metric and not app.get('download_button')
    assert app.get('status')[0].label=='Analysis not started: another run is still active'
