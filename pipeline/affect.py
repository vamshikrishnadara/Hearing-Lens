"""Local English sentiment/emotion inference. Cache models only, never inputs."""
from collections import Counter
from functools import lru_cache
from pathlib import Path
import re

import numpy as np
import pandas as pd

SENTIMENTS = ('negative', 'neutral', 'positive')
EMOTIONS = ('anger', 'disgust', 'fear', 'joy', 'neutral', 'sadness', 'surprise')
MODEL_ROOT = Path(__file__).resolve().parents[1] / 'model_cache'


class AffectError(ValueError):
    """Safe user-facing inference failure."""


@lru_cache(maxsize=1)
def _language_identifier():
    from langid.langid import LanguageIdentifier, model
    return LanguageIdentifier.from_modelstring(model, norm_probs=True)


def detect_language(text):
    if len(re.findall(r'[^\W\d_]', text)) < 3:
        return 'unknown'
    language, confidence = _language_identifier().classify(text)
    return language if confidence >= .8 else 'unknown'


@lru_cache(maxsize=2)
def _get_classifier(kind):
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        path = MODEL_ROOT / kind
        tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False)
        model = AutoModelForSequenceClassification.from_pretrained(
            path, local_files_only=True, trust_remote_code=False, weights_only=True).to('cpu').eval()
        expected = SENTIMENTS if kind == 'sentiment' else EMOTIONS
        labels = [str(model.config.id2label[i]).lower() for i in range(model.config.num_labels)]
        if set(labels) != set(expected):
            raise ValueError
        return tokenizer, model, labels
    except Exception:
        raise AffectError('Affect model is unavailable or incompatible. Run python -m scripts.setup_affect_models during setup.') from None


def _predict(texts, kind):
    import torch
    tokenizer, model, labels = _get_classifier(kind)
    scores, truncated = [], []
    try:
        for start in range(0, len(texts), 32):
            batch = texts[start:start+32]
            lengths = [len(ids) for ids in tokenizer(batch, truncation=False, add_special_tokens=True)['input_ids']]
            encoded = tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors='pt')
            with torch.inference_mode():
                probabilities = torch.softmax(model(**encoded).logits, dim=-1).cpu().numpy()
            if probabilities.shape != (len(batch), len(labels)) or not np.isfinite(probabilities).all():
                raise ValueError
            scores.extend([{label: float(value) for label, value in zip(labels, row)} for row in probabilities])
            truncated.extend(length > 512 for length in lengths)
    except AffectError:
        raise
    except Exception:
        raise AffectError('Affect inference failed; no affect results were produced.') from None
    return scores, truncated


def analyze_affect(frame):
    if 'comment_text' not in frame or len(frame) > 5000:
        raise AffectError('Affect analysis requires comment_text and at most 5,000 rows.')
    texts = frame.comment_text.fillna('').astype(str).str.strip().tolist()
    rows, unique = [], {}
    try:
        for position, text in enumerate(texts):
            language = detect_language(text) if text else 'unknown'
            status = 'empty' if not text else ('scored' if language == 'en' else 'excluded_language')
            rows.append({'row_position': position, 'language': language, 'status': status})
            if status == 'scored':
                # Follow sentiment model-card normalization; originals remain memory-only.
                normalized = re.sub(r'https?://\S+', 'http', re.sub(r'(?<!\w)@\w+', '@user', text))
                unique.setdefault(normalized, []).append(position)
        if unique:
            inputs = list(unique)
            sentiment, sentiment_cut = _predict(inputs, 'sentiment')
            emotion, emotion_cut = _predict(inputs, 'emotion')
            if not len(sentiment) == len(emotion) == len(sentiment_cut) == len(emotion_cut) == len(inputs):
                raise AffectError('Affect inference returned incomplete results.')
            for i, text in enumerate(inputs):
                if set(sentiment[i]) != set(SENTIMENTS) or set(emotion[i]) != set(EMOTIONS):
                    raise AffectError('Affect inference returned incompatible labels.')
                for values in (sentiment[i], emotion[i]):
                    array = np.asarray(list(values.values()))
                    if not np.isfinite(array).all() or (array < 0).any() or not np.isclose(array.sum(), 1):
                        raise AffectError('Affect inference returned invalid scores.')
                for position in unique[text]:
                    rows[position].update({
                        'sentiment': max(SENTIMENTS, key=sentiment[i].get),
                        'emotion': max(EMOTIONS, key=emotion[i].get),
                        'sentiment_score': sentiment[i]['positive'] - sentiment[i]['negative'],
                        'sentiment_probabilities': sentiment[i], 'emotion_probabilities': emotion[i],
                        'truncated': bool(sentiment_cut[i] or emotion_cut[i]),
                    })
    except AffectError:
        raise
    except Exception:
        raise AffectError('Language detection or affect analysis failed; no affect results were produced.') from None
    counts = Counter(row['status'] for row in rows)
    return {'rows': rows, 'scored_count': counts['scored'],
        'excluded_language_count': counts['excluded_language'], 'empty_count': counts['empty'],
        'truncated_count': sum(row.get('truncated', False) for row in rows),
        'language_counts': dict(Counter(row['language'] for row in rows if row['status'] != 'empty')),
        'warnings': ['English models only; detected non-English and uncertain-language comments are excluded from affect, not labeled neutral.',
            'Language detection can be wrong, especially for short or mixed-language comments.',
            'Probabilities are model scores, not calibrated certainty. Text beyond 512 tokens is truncated.']}


def aggregate_affect(rows, group_by_row):
    """Aggregate label proportions using scored rows as the denominator."""
    groups = {}
    positions = [row['row_position'] for row in rows]
    if len(set(positions)) != len(positions):
        raise AffectError('Affect row positions must be unique.')
    if not set(group_by_row) <= set(positions):
        raise AffectError('Group assignments refer to missing affect rows.')
    for row in rows:
        position = row['row_position']
        if position in group_by_row:
            groups.setdefault(group_by_row[position], []).append(row)
    output = []
    for group, members in groups.items():
        scored = [row for row in members if row['status'] == 'scored']
        n = len(scored)
        counts = {kind: Counter(row[kind] for row in scored) for kind in ('sentiment', 'emotion')}
        emotion = counts['emotion']
        top = max(emotion.values(), default=0)
        dominant = [label for label in EMOTIONS if emotion[label] == top] if n else []
        output.append({'group': group, 'total_comments': len(members), 'scored_comments': n,
            'excluded_comments': len(members)-n,
            'mean_sentiment': float(np.mean([row['sentiment_score'] for row in scored])) if n else None,
            'sentiment_counts': {label: counts['sentiment'][label] for label in SENTIMENTS},
            'sentiment_shares': {label: counts['sentiment'][label]/n if n else None for label in SENTIMENTS},
            'emotion_counts': {label: emotion[label] for label in EMOTIONS},
            'emotion_shares': {label: emotion[label]/n if n else None for label in EMOTIONS},
            'dominant_emotion': dominant[0] if len(dominant) == 1 else None,
            'dominant_emotion_ties': dominant if len(dominant) > 1 else []})
    return output
