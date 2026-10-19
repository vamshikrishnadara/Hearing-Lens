"""Check report claims, disclosure boundaries and session download lifecycle."""
from copy import deepcopy
from io import BytesIO
from zipfile import ZipFile

from docx import Document
import pytest

from pipeline.brief import BriefError, build_brief, community_docx, _short
from tests.test_dashboard_completion import sample_result


def result():
    r = sample_result()
    r['affect']['rows'][0] = {'row_position': 0, 'status': 'excluded_language'}
    r['affect']['rows'][1]['sentiment'] = 'negative'
    r['timeline'] = {'mode': 'date', 'theme_volumes': [], 'periods': [
        {'group': '2026-10-02', 'total_comments': 12, 'scored_comments': 12, 'excluded_comments': 0, 'mean_sentiment': -.4},
        {'group': 'Missing period', 'total_comments': 6, 'scored_comments': 5, 'excluded_comments': 1, 'mean_sentiment': .9},
        {'group': '2026-10-01', 'total_comments': 12, 'scored_comments': 12, 'excluded_comments': 0, 'mean_sentiment': .2}]}
    return r


def test_actual_counts_denominators_and_dated_comparison():
    r = result(); before = deepcopy(r)
    brief = build_brief(r)
    assert '29 scored comments; 1 unscored' in brief['sentiment']
    assert '3% negative' in brief['sentiment']
    assert '+0.20 on 2026-10-01 to -0.40 on 2026-10-02' in brief['timeline']
    assert '6 undated comments excluded' in brief['timeline']
    assert 'not confirmed unanswered' in brief['question_note']
    assert 'No usable reference' in brief['representation']
    assert r == before


def test_unscored_missing_dates_and_no_questions_do_not_invent_findings():
    r = result()
    r['affect']['rows'] = [{'row_position': i, 'status': 'excluded_language'} for i in range(30)]
    r['timeline']['mode'] = 'hearing_label'
    r['gaps'] = {'fields': []}
    r['questions'].update(groups=[], top_unanswered=[])
    b = build_brief(r)
    assert 'No sentiment scores' in b['sentiment'] and 'not neutral' in b['sentiment']
    assert 'unavailable' in b['timeline']
    assert 'cannot be assessed' in b['representation']
    assert 'concerns may still be present' in b['question_note']


def test_all_matched_does_not_claim_all_questions_answered():
    r = result()
    r['questions'].update(response_status='available', top_unanswered=[])
    b = build_brief(r)
    assert not b['questions'] and 'does not confirm answers' in b['question_note']


def test_suppressed_and_invalid_reference_rows_never_reappear_in_brief():
    r = result()
    r['gaps'] = {'fields': [{'field': 'subgroup__role', 'reference_status': 'valid', 'status': 'comparison'}],
                 'rows': [{'field': 'subgroup__role', 'group': 'SECRET HIDDEN', 'suppressed': True,
                           'flag': 'underrepresented', 'gap_percentage_points': -99},
                          {'field': 'subgroup__role', 'group': 'Visitors', 'suppressed': False,
                           'flag': 'underrepresented', 'gap_percentage_points': -20.5},
                          {'field': 'subgroup__unmatched', 'group': 'SECRET INVALID', 'suppressed': False,
                           'flag': 'underrepresented', 'gap_percentage_points': -50}]}
    b = build_brief(r)
    assert 'Visitors' in b['representation'] and '20.5 percentage points' in b['representation']
    assert 'SECRET' not in b['representation']
    assert 'hidden or unmatched' in b['representation']


def test_quotes_labels_and_questions_are_redacted_before_export():
    r = result()
    secret = 'Contact Jane Smith at jane@example.com or 312-555-0123.'
    r['themes']['themes'][0].update(label=secret, quotes=[{'text': secret}])
    r['questions']['groups'][0]['representative']['text'] = secret
    doc = Document(BytesIO(community_docx(r)))
    text = '\n'.join(p.text for p in doc.paragraphs)
    assert all(s not in text for s in ['jane@example.com', '312-555-0123', 'Jane Smith'])
    assert '[EMAIL_ADDRESS]' in text


@pytest.mark.parametrize('change', ['counts', 'rows', 'priority', 'missing'])
def test_malformed_analysis_fails_without_partial_brief(change):
    r = result()
    if change == 'counts': r['themes']['themes'][0]['count'] = 999
    if change == 'rows': r['affect']['rows'][0]['row_position'] = 1
    if change == 'priority': r['questions']['top_unanswered'] = ['absent']
    if change == 'missing': del r['themes']
    with pytest.raises(BriefError): community_docx(r)


def test_bounded_editable_document_uses_current_quotes_and_no_external_links():
    r = result()
    r['themes']['themes'][0]['quotes'][0]['text'] = 'Updated selected quote. ' * 50
    data = community_docx(r)
    doc = Document(BytesIO(data))
    text = '\n'.join(p.text for p in doc.paragraphs)
    assert 'Updated selected quote.' in text and '...' in text
    assert 'Can the center open later?' in text and 'Method:' in text
    assert doc.styles['Normal'].font.size.pt == 11
    assert doc.styles['Title'].font.size.pt == 16
    assert not doc.core_properties.author and not doc.core_properties.last_modified_by
    with ZipFile(BytesIO(data)) as z:
        assert all(b'TargetMode="External"' not in z.read(n) for n in z.namelist() if n.endswith('.rels'))
    assert len(_short('W' * 10000, 140)) <= 140
    assert '\x00' not in _short('test\x00text', 100)


