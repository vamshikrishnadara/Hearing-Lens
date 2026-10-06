"""Local, explainable English question candidates with redacted source spans.

Detection only: grouping, ranking and response matching are separate stages.
No files, network calls, demographic inference or cached user results.
"""
from functools import lru_cache
import hashlib
import re

import pandas as pd

from pipeline.redact import build_safe_display_frame


DETECTOR_VERSION = 'interrogatives-v1'
WH_WORDS = frozenset('who whom whose what which when where why how'.split())
AUXILIARIES = frozenset(
    'am is are was were do does did have has had can could shall should will would may might must'.split())


class QuestionError(ValueError):
    """Safe schema/segmentation errors without uploaded content."""


@lru_cache(maxsize=1)
def _sentence_model():
    import spacy
    nlp = spacy.blank('en')
    nlp.add_pipe('sentencizer')
    return nlp


def question_reasons(sentence):
    """Brief's baseline: terminal ? or initial wh-word/auxiliary.

    These are candidates, not proof of an information request. Relative clauses,
    rhetorical questions and auxiliary-led statements require human evaluation.
    """
    text = sentence.strip()
    if not any(c.isalpha() for c in text):
        return []
    reasons = []
    if text.rstrip('"\'”’)]} ').endswith('?'):
        reasons.append('question_mark')
    # Ignore opening quotation/list punctuation, but not arbitrary leading words.
    text = re.sub(r'^\s*(?:(?:\d+[.)]|[-*•])\s+)?[\s\"\'“‘(\[]*', '', text)
    token = re.match(r'[A-Za-z]+', text)
    first = token.group().casefold() if token else ''
    if first in WH_WORDS:
        reasons.append('wh_word')
    elif first in AUXILIARIES:
        reasons.append('auxiliary')
    return reasons


def sentence_records(redacted_texts):
    """Internal segmentation of already-redacted strings; offsets are verbatim.

    Use analyze_questions for raw input. Do not expose raw text through this helper.
    English spaCy tokenization preserves many abbreviations and decimals. It does
    not guarantee perfect boundaries in lists, unpunctuated text or other languages.
    """
    records = []
    try:
        docs = _sentence_model().pipe(redacted_texts, batch_size=64)
        for position, doc in enumerate(docs):
            for index, span in enumerate(doc.sents):
                start, end = span.start_char, span.end_char
                while start < end and doc.text[start].isspace():
                    start += 1
                while end > start and doc.text[end - 1].isspace():
                    end -= 1
                text = doc.text[start:end]
                if not text or not any(c.isalpha() for c in text):
                    continue
                reasons = question_reasons(text)
                records.append({'row_position': position, 'sentence_index': index,
                                'source_start': start, 'source_end': end, 'text': text,
                                'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                                'is_question': bool(reasons), 'reasons': reasons})
    except Exception:
        raise QuestionError('Sentence splitting could not finish. Try shorter comments or a smaller file.') from None
    return records


def analyze_questions(frame):
    """Redact a mapped comment table and return every sentence plus candidates.

    Row positions refer to the supplied frame's order, never its index or IDs.
    Call after map_columns for upstream blank removal/respondent deduplication.
    Empty input has zero candidates; it is not an accuracy measurement.
    """
    if (not isinstance(frame, pd.DataFrame) or not frame.columns.is_unique
            or 'comment_text' not in frame):
        raise QuestionError('Provide a table with a mapped comment column and unique column names.')
    if any(not pd.api.types.is_scalar(value) for value in frame.comment_text):
        raise QuestionError('Comment cells must contain single text values.')
    safe = build_safe_display_frame(frame[['comment_text']])
    texts = safe.frame.comment_text.tolist()
    records = sentence_records(texts)
    counts = [0] * len(frame)
    for record in records:
        counts[record['row_position']] += int(record['is_question'])
    return {'status': 'available' if records else 'unavailable',
            'detector_version': DETECTOR_VERSION, 'input_rows': len(frame),
            'sentence_count': len(records), 'question_count': sum(counts),
            'comment_question_counts': counts, 'sentences': records,
            'redaction_counts': safe.entity_counts,
            'notice': 'English rule-based candidates, not verified questions or answers. '
                      'Offsets refer to redacted comments. Redaction can miss identifiers. '
                      'Human recall and false-positive evaluation is required.'}
