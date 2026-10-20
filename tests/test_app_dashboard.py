"""Exercise session isolation, stale-result protection and quote review in the app."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.dashboard import STATE_KEY

APP = Path(__file__).resolve().parents[1] / 'app' / 'streamlit_app.py'


def upload(text='comment_text,other,id\nSchool needs accessible rooms.,Another comment.,001\n'):
    value = BytesIO(text.encode())
    value.name = 'fictional.csv'
    return value


def result():
    return {'input_rows': 1, 'themes': {
        'analyzed_comments': 1, 'outlier_count': 0, 'excluded_row_positions': [], 'warnings': [],
        'themes': [{'theme_id': 1, 'label': 'school / rooms', 'count': 1, 'share': 1.,
                    'quotes': [{'row_position': 0, 'text': '[PERSON] supports accessible rooms.', 'is_excerpt': True}],
                    'quote_alternatives': [{'row_position': 1, 'text': 'Students need accessible classrooms.'}]}]}}


def button(app, label):
    return next(w for w in app.button if w.label == label)


def select(app, label):
    return next(w for w in app.selectbox if w.label == label)


def ready(app):
    app.run()
    button(app, 'Validate mapping').click().run()
    button(app, 'Analyze comments').click().run()
    assert not app.exception
    return app


@pytest.fixture
def model():
    # Only replace costly model inference; exercise real loading, mapping,
    # preview redaction, Streamlit session state and quote-swap validation.
    with patch('app.dashboard.analyze_dashboard', side_effect=lambda frame, **kwargs: deepcopy(result())) as mock:
        yield mock


def test_analysis_waits_for_button_and_preserves_results_on_review_rerun(model):
    with patch('streamlit.file_uploader', return_value=upload()):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        model.assert_not_called()
        button(app, 'Validate mapping').click().run()
        model.assert_not_called()
        button(app, 'Analyze comments').click().run()
        assert [m.value for m in app.metric] == ['1', '1', '0']
        app.checkbox[0].check().run()
        assert app.checkbox[0].value
        assert model.call_count == 1
        assert not app.exception


def test_swap_preserves_original_model_result_and_resets_confirmation(model):
    original = result()
    model.side_effect = lambda frame, **kwargs: deepcopy(original)
    with patch('streamlit.file_uploader', return_value=upload()):
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        app.checkbox[0].check().run()
        select(app, 'Alternative for theme 1, quote 1').select(1).run()
        button(app, 'Use this quote').click().run()
        assert not app.exception
        theme = app.session_state[STATE_KEY]['result']['themes']['themes'][0]
        assert theme['quotes'][0]['row_position'] == 1
        assert theme['quote_alternatives'][0]['row_position'] == 0
        assert not app.checkbox[0].value
        assert model.call_count == 1
        assert original['themes']['themes'][0]['quotes'][0]['row_position'] == 0
        select(app, 'Alternative for theme 1, quote 1').select(0).run()
        button(app, 'Use this quote').click().run()
        assert app.session_state[STATE_KEY]['result']['themes']['themes'][0]['quotes'][0]['row_position'] == 0


@pytest.mark.parametrize('field,value', [('Comment text', 'other'), ('Respondent ID', 'id'), ('Date or hearing label', 'other')])
def test_mapping_change_clears_analysis_and_review(model, field, value):
    with patch('streamlit.file_uploader', return_value=upload()):
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        app.checkbox[0].check().run()
        select(app, field).select(value).run()
        assert not app.metric
        assert app.session_state[STATE_KEY]['result'] is None
        assert app.session_state[STATE_KEY]['mapped'] is None
        assert not app.checkbox


def test_subgroup_change_clears_analysis(model):
    with patch('streamlit.file_uploader', return_value=upload()):
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        app.multiselect[0].select('other').run()
        assert not app.metric
        assert app.session_state[STATE_KEY]['result'] is None


def test_same_filename_different_bytes_and_removal_clear_results(model):
    with patch('streamlit.file_uploader', return_value=upload()) as picker:
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        picker.return_value = upload('comment_text,other,id\nNew text.,Different.,002\n')
        app.run()
        assert not app.metric
        assert app.session_state[STATE_KEY]['mapped'] is None
        button(app, 'Validate mapping').click().run()
        button(app, 'Analyze comments').click().run()
        picker.return_value = None
        app.run()
        assert STATE_KEY not in app.session_state
        assert not app.metric


def test_sheet_change_invalidates_even_when_headers_match(model):
    data = BytesIO()
    with pd.ExcelWriter(data, engine='openpyxl') as writer:
        for sheet in ['A', 'B']:
            pd.DataFrame({'comment_text': [f'Fictional comment {sheet}']}).to_excel(writer, sheet_name=sheet, index=False)
    data.name = 'fictional.xlsx'
    with patch('streamlit.file_uploader', return_value=data):
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        select(app, 'Workbook sheet').select('B').run()
        assert app.session_state[STATE_KEY]['result'] is None
        assert not app.metric


def test_failure_hides_old_results_and_raw_error_then_allows_retry(model):
    with patch('streamlit.file_uploader', return_value=upload()):
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        model.side_effect = RuntimeError('secret@example.org raw source text')
        button(app, 'Analyze comments').click().run()
        assert not app.exception
        assert not app.metric
        assert app.session_state[STATE_KEY]['result'] is None
        assert len(app.error) == 1
        assert 'secret' not in app.error[0].value
        model.side_effect = lambda frame, **kwargs: deepcopy(result())
        button(app, 'Analyze comments').click().run()
        assert app.metric and not app.error


def test_sessions_do_not_share_results(model):
    with patch('streamlit.file_uploader', return_value=upload()):
        first = ready(AppTest.from_file(str(APP), default_timeout=30))
        second = AppTest.from_file(str(APP), default_timeout=30).run()
        assert first.session_state[STATE_KEY]['result'] is not None
        assert second.session_state[STATE_KEY]['result'] is None
        assert not second.metric


def test_model_receives_cleaned_mapped_rows_and_preserved_codes(model):
    data = upload('comment_text,hearing,id,zip\nFirst comment.,2026-10-12,001,00123\n,2026-10-12,002,00123\nDuplicate.,2026-10-12,001,00123\nOther comment.,2026-10-13,003,00456\n')
    with patch('streamlit.file_uploader', return_value=data):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        select(app, 'Date or hearing label').select('hearing').run()
        select(app, 'Respondent ID').select('id').run()
        app.multiselect[0].select('zip').run()
        button(app, 'Validate mapping').click().run()
        button(app, 'Analyze comments').click().run()
        frame = model.call_args.args[0]
        assert frame['respondent_id'].tolist() == ['001', '003']
        assert frame['subgroup__zip'].tolist() == ['00123', '00456']
        assert frame['date_or_hearing'].tolist() == ['2026-10-12', '2026-10-13']
        assert app.dataframe[0].value.columns.tolist() == ['comment_text']


def test_empty_themes_and_quote_shortages_are_explicit(model):
    value = result()
    value['themes']['themes'] = []
    value['themes']['outlier_count'] = 1
    model.side_effect = lambda frame, **kwargs: deepcopy(value)
    with patch('streamlit.file_uploader', return_value=upload()):
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        assert any('No themes were found' in m.value for m in app.info)
        assert not app.checkbox
        value['themes']['themes'] = result()['themes']['themes']
        value['themes']['themes'][0]['quotes'] = []
        value['themes']['themes'][0]['quote_alternatives'] = []
        button(app, 'Analyze comments').click().run()
        assert any('Fewer than three' in m.value for m in app.info)
        assert not any(b.label == 'Use this quote' for b in app.button)


def test_swapping_one_theme_keeps_other_theme_review(model):
    value = result()
    other = deepcopy(value['themes']['themes'][0])
    other['theme_id'] = 2
    value['themes']['themes'].append(other)
    model.side_effect = lambda frame, **kwargs: deepcopy(value)
    with patch('streamlit.file_uploader', return_value=upload()):
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        app.checkbox[0].check().run()
        app.checkbox[1].check().run()
        select(app, 'Alternative for theme 1, quote 1').select(1).run()
        next(b for b in app.button if b.label == 'Use this quote').click().run()
        assert not app.checkbox[0].value
        assert app.checkbox[1].value


def test_new_analysis_resets_all_review_choices(model):
    with patch('streamlit.file_uploader', return_value=upload()):
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        app.checkbox[0].check().run()
        button(app, 'Analyze comments').click().run()
        assert not app.checkbox[0].value
        assert model.call_count == 2


def test_invalid_replacement_file_drops_previous_workspace(model):
    with patch('streamlit.file_uploader', return_value=upload()) as picker:
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        picker.return_value = upload('comment_text\n')
        app.run()
        assert not app.exception
        assert app.error
        assert not app.metric
        assert STATE_KEY not in app.session_state


def test_failed_revalidation_drops_previous_results(model):
    from pipeline.redact import RedactionError
    with patch('streamlit.file_uploader', return_value=upload()):
        app = ready(AppTest.from_file(str(APP), default_timeout=30))
        with patch('pipeline.redact.build_safe_display_frame', side_effect=RedactionError('Preview blocked.')):
            button(app, 'Validate mapping').click().run()
        assert not app.metric
        assert app.session_state[STATE_KEY]['result'] is None
        assert app.session_state[STATE_KEY]['mapped'] is None
        assert len(app.error) == 1
