"""PDF content parity, disclosure, typography and bounded output checks."""
from copy import deepcopy
from io import BytesIO
import re

from docx import Document
from pypdf import PdfReader
import pytest

from pipeline.brief import BriefError, build_brief, community_docx, community_pdf, pdf_bytes
from tests.test_brief import result


def compact(text):
    return re.sub(r'\s+', ' ', text).strip()


def test_pdf_matches_word_claims_and_embeds_fonts_without_links_or_author():
    data=result()
    data['questions']['groups'][0]['comment_count']=1
    document=Document(BytesIO(community_docx(data)))
    reader=PdfReader(BytesIO(community_pdf(data)))
    assert len(reader.pages)==1 and not reader.metadata.author
    page=reader.pages[0]
    assert not page.get('/Annots')
    assert compact(page.extract_text())==compact(' '.join(p.text for p in document.paragraphs))
    assert '(1 comment)' in page.extract_text() and '(1 comments)' not in page.extract_text()
    assert '29 scored comments; 1 unscored' in page.extract_text()
    for font in page['/Resources']['/Font'].values():
        font=font.get_object()
        if '/FontDescriptor' in font:
            assert '/FontFile2' in font['/FontDescriptor']
    sizes=[]
    page.extract_text(visitor_text=lambda text,cm,tm,font,size:sizes.append(size) if text.strip() else None)
    assert min(sizes)==11 and max(sizes)==16


def test_pdf_escapes_markup_preserves_accents_and_redacts_contact_details():
    data=result()
    data['themes']['themes'][0].update(label='Café <access> & transport',quotes=[{
        'text':'Contact Jane Smith at jane@example.com or 312-555-0123. Café access matters.'}])
    brief=build_brief(data)
    # Exercise font/markup handling independently of NER's interpretation of a
    # capitalized word as a possible name; contact redaction remains real.
    brief['themes'][0]['label']='Café <access> & transport'
    text=PdfReader(BytesIO(pdf_bytes(brief))).pages[0].extract_text()
    assert 'Café <access> & transport' in text
    assert '[EMAIL_ADDRESS]' in text
    assert all(secret not in text for secret in ('Jane Smith','jane@example.com','312-555-0123'))


def test_pdf_never_restores_suppressed_categories_or_invents_optional_results():
    data=result()
    data['gaps']={'fields':[{'field':'subgroup__role','status':'comparison','reference_status':'valid'}],
                  'rows':[{'field':'subgroup__role','group':'HIDDEN CATEGORY','suppressed':True,
                           'flag':'underrepresented','gap_percentage_points':-90}]}
    data['timeline']=None
    data['questions'].update(groups=[],top_unanswered=[])
    text=PdfReader(BytesIO(community_pdf(data))).pages[0].extract_text()
    assert 'HIDDEN CATEGORY' not in text
    assert 'No visible category' in text and 'unavailable without comparable dates' in text
    assert 'No question candidates' in text


def test_pdf_rejects_unsupported_glyphs_and_overflow_instead_of_returning_bad_file():
    brief=build_brief(result())
    bad=deepcopy(brief);bad['title']='\u6f22\u5b57'
    with pytest.raises(BriefError,match='font cannot display'):pdf_bytes(bad)
    long=deepcopy(brief);long['summary']='Long paragraph. '*3000
    with pytest.raises(BriefError,match='one page'):pdf_bytes(long)


def test_pdf_invalid_analysis_has_no_partial_output():
    data=result();data['input_rows']=4999
    with pytest.raises(BriefError):community_pdf(data)
