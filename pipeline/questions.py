"""Local, explainable English question candidates with redacted source spans.

No files, network calls, demographic inference or cached user results.
"""
from functools import lru_cache
from collections import Counter
import hashlib
import re

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering

from pipeline.redact import build_safe_display_frame
from pipeline.themes import _embed, ThemeError
from pipeline.reference import group_label, ReferenceError


DETECTOR_VERSION = 'interrogatives-v1'
WH_WORDS = frozenset('who whom whose what which when where why how'.split())
AUXILIARIES = frozenset(
    'am is are was were do does did have has had can could shall should will would may might must'.split())
MAX_UNIQUE_QUESTIONS = 2000


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


def _threshold(value, *, allow_zero=False):
    if (isinstance(value, (bool, str)) or not isinstance(value, (int, float))
            or not np.isfinite(value) or not (0 <= value <= 1)
            or (value == 0 and not allow_zero)):
        raise QuestionError('Use a finite similarity threshold between zero and one; grouping distance must be positive.')
    return float(value)


def _question_vectors(texts):
    try:
        vectors = np.asarray(_embed(texts), dtype=float)
        if (vectors.ndim != 2 or vectors.shape[0] != len(texts)
                or vectors.shape[1] == 0 or not np.isfinite(vectors).all()):
            raise ValueError
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if (norms <= 1e-12).any():
            raise ValueError
        return vectors / norms
    except (ThemeError, ValueError, TypeError):
        raise QuestionError('Question embeddings are unavailable. Check the local MiniLM model setup.') from None


def _group_candidates(candidates, distance_threshold):
    by_text = {}
    for row in candidates:
        key = ' '.join(row['text'].casefold().split())
        by_text.setdefault(key, []).append(row)
    keys = sorted(by_text)
    if len(keys) > MAX_UNIQUE_QUESTIONS:
        raise QuestionError('Too many distinct question sentences for local grouping (maximum 2,000). Use a smaller input; no partial result was produced.')
    if not keys:
        return [], [], [], np.empty((0, 0))
    # Embed each distinct wording once; repeats still count as source occurrences.
    examples = [min(by_text[key], key=lambda r: (r['text'], r['row_position'], r['sentence_index'])) for key in keys]
    vectors = _question_vectors([row['text'] for row in examples])
    if len(keys) == 1:
        labels = np.zeros(1, dtype=int)
    else:
        labels = AgglomerativeClustering(n_clusters=None, metric='cosine', linkage='complete',
                                        distance_threshold=distance_threshold).fit_predict(vectors)
    clusters = {}
    for i, label in enumerate(labels):
        clusters.setdefault(int(label), []).append(i)
    groups, assignments = [], []
    # IDs and ties follow sorted wording, not sklearn's incidental label numbers.
    for number, indices in enumerate(sorted(clusters.values(), key=lambda ids: tuple(keys[i] for i in ids)), 1):
        members = [r for i in indices for r in by_text[keys[i]]]
        similarities = vectors[indices] @ vectors[indices].T
        centrality = similarities.mean(axis=1)
        center = min(range(len(indices)), key=lambda j: (-float(centrality[j]), keys[indices[j]]))
        representative = examples[indices[center]]
        group_id = f'q{number:03d}'
        groups.append({'question_group_id': group_id,
                       'representative': {k: representative[k] for k in ['text', 'row_position', 'sentence_index', 'source_start', 'source_end', 'text_sha256']},
                       'comment_count': len({r['row_position'] for r in members}),
                       'sentence_count': len(members), 'unique_wordings': len(indices),
                       '_variant_indices': indices,
                       '_positions': sorted({r['row_position'] for r in members})})
        assignments.extend({'row_position': r['row_position'], 'sentence_index': r['sentence_index'],
                            'question_group_id': group_id} for r in members)
    assignments.sort(key=lambda r: (r['row_position'], r['sentence_index']))
    return groups, assignments, examples, vectors


def _subgroup_labels(frame, columns):
    if not isinstance(frame, pd.DataFrame) or not frame.columns.is_unique:
        raise QuestionError('Provide a mapped table with unique column names.')
    if columns is None:
        columns = [c for c in frame.columns if isinstance(c, str) and c.startswith('subgroup__')]
    if (not isinstance(columns, (list, tuple)) or any(not isinstance(c, str) for c in columns)
            or len(set(columns)) != len(columns) or any(c not in frame for c in columns)
            or any(c in {'comment_text', 'respondent_id', 'source_row', 'date_or_hearing'} for c in columns)):
        raise QuestionError('Select distinct supplied subgroup columns, separate from text and identifier fields.')
    try:
        return {field: [group_label(value).casefold() for value in frame[field]] for field in columns}
    except ReferenceError:
        raise QuestionError('Subgroup cells must contain single supplied categories.') from None


def _rank_groups(groups, labels, minimum_group_size):
    for group in groups:
        spread, details, any_known, hidden = 0, {}, False, False
        for field, values in labels.items():
            observed = [values[i] for i in group['_positions'] if values[i]]
            counts = Counter(observed)
            visible = sum(count >= minimum_group_size for count in counts.values())
            suppressed = any(count < minimum_group_size for count in counts.values())
            any_known = any_known or bool(observed)
            hidden = hidden or suppressed or len(observed) < len(group['_positions'])
            spread += visible
            # Never return category labels, their counts or a suppressed group's
            # existence in a specific named category. Rank only visible breadth.
            details[field] = {'visible_group_count': visible if observed else None,
                              'coverage': ('complete' if len(observed) == len(group['_positions']) else
                                           'partial' if observed else 'missing'),
                              'small_groups_suppressed': suppressed}
        group['subgroup_spread'] = spread if any_known else None
        group['subgroup_spread_by_field'] = details
        group['spread_is_lower_bound'] = hidden
    groups.sort(key=lambda g: (-g['comment_count'], -(g['subgroup_spread'] or 0),
                               g['representative']['text'].casefold(), g['question_group_id']))
    for rank, group in enumerate(groups, 1):
        group['rank'] = rank


def mine_questions(frame, *, grouping_distance=.35, subgroup_columns=None, minimum_group_size=10):
    """Group redacted candidate questions; preserve analyze_questions' frozen API.

    Complete-linkage cosine clustering prevents similarity chains from joining
    distant questions. Frequency counts distinct comment rows, not repeated
    sentences inside one comment. It is not a count of unique people.
    """
    grouping_distance = _threshold(grouping_distance)
    if type(minimum_group_size) is not int or minimum_group_size < 10:
        raise QuestionError('The minimum subgroup size must be a whole number of at least 10.')
    labels = _subgroup_labels(frame, subgroup_columns)
    detection = analyze_questions(frame)
    candidates = [r for r in detection['sentences'] if r['is_question']]
    groups, assignments, _, _ = _group_candidates(candidates, grouping_distance)
    _rank_groups(groups, labels, minimum_group_size)
    for group in groups:
        group.pop('_variant_indices')
        group.pop('_positions')
    return {'status': 'available' if groups else 'no_questions', 'detector_version': DETECTOR_VERSION,
            'input_rows': detection['input_rows'], 'sentence_count': detection['sentence_count'],
            'question_count': detection['question_count'],
            'comment_question_counts': detection['comment_question_counts'],
            'grouping_distance': grouping_distance, 'groups': groups, 'assignments': assignments,
            'minimum_group_size': minimum_group_size,
            'ranking': 'Distinct comment count descending; visible subgroup spread descending; wording tie-break.',
            'notice': 'English question candidates grouped by local MiniLM cosine similarity. '
                      'Frequency counts comment rows, not unique people. Semantic similarity is not '
                      'equivalence; long sentences may be truncated by the embedding model. '
                      'Subgroup spread sums field/category pairs with at least the minimum number of '
                      'supporting comments in this question group, without inferring missing categories. '
                      'Small or missing categories can make this a lower bound. Review before sharing.'}
