"""Initial local embedding/K-means themes; returns no raw comment text or metadata."""

from collections import Counter
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
import re

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer

from pipeline.redact import build_safe_display_frame
from pipeline.theme_merging import merge_small_groups, MIN_THEME_SIZE
from pipeline.quotes import quote_spans, nearly_identical


class ThemeError(ValueError):
    """A theme-analysis problem safe to show without echoing comment content."""


MODEL_PATH = Path(__file__).resolve().parents[1] / "model_cache/all-MiniLM-L6-v2"
_MARKERS = re.compile(r"\[(?:PERSON|EMAIL_ADDRESS|PHONE_NUMBER|STREET_ADDRESS|UNIT_NUMBER|URL)\]")


def _analysis_text(redacted):
    # Ignore standalone contact/address boilerplate only when redaction already
    # found an identifier there. Preserve the original redacted quote for display.
    contact_words = {"contact", "at", "or", "i", "live", "email", "me", "us", "call", "on", "my", "address", "is"}
    sentences = re.split(r"(?<=[.!?])\s+", redacted)
    kept = []
    for sentence in sentences:
        clean = _MARKERS.sub(" ", sentence)
        words = set(re.findall(r"[^\W\d_]+", clean.casefold()))
        if _MARKERS.search(sentence) and words <= contact_words:
            continue
        kept.append(clean)
    return " ".join(" ".join(kept).split())


@lru_cache(maxsize=1)
def _get_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer

        if not (MODEL_PATH / "modules.json").is_file():
            raise FileNotFoundError
        return SentenceTransformer(
            str(MODEL_PATH), device="cpu", local_files_only=True, trust_remote_code=False
        )
    except Exception:
        raise ThemeError(
            "Theme model is unavailable. Run python -m scripts.setup_theme_model during setup."
        ) from None


def _embed(texts):
    try:
        vectors = np.asarray(_get_embedding_model().encode(
            texts, batch_size=32, show_progress_bar=False,
            convert_to_numpy=True, normalize_embeddings=True,
        ), dtype=float)
        if vectors.ndim != 2 or vectors.shape[0] != len(texts) or not np.isfinite(vectors).all():
            raise ValueError
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if (norms == 0).any():
            raise ValueError
        return vectors / norms
    except ThemeError:
        raise
    except Exception:
        raise ThemeError("Theme embedding failed; no theme results were produced.") from None


def _theme_vectors(texts, embedding_mode):
    if embedding_mode == "whole_comment":
        return _embed(texts)
    # Count a sentence at most once per comment. Repeated introductions should
    # have less influence than less-common content, without a topic-specific list.
    sentences = [list(dict.fromkeys(re.split(r"(?<=[.!?])\s+", text))) for text in texts]
    frequency = Counter(sentence for comment in sentences for sentence in comment)
    unique = list(frequency)
    encoded = _embed(unique)
    lookup = {sentence: index for index, sentence in enumerate(unique)}
    vectors = []
    for comment in sentences:
        weights = [np.log((1 + len(texts)) / (1 + frequency[sentence])) + 1 for sentence in comment]
        vector = np.average(encoded[[lookup[sentence] for sentence in comment]], axis=0, weights=weights)
        norm = np.linalg.norm(vector)
        if not np.isfinite(norm) or norm <= 1e-12:
            raise ThemeError("Theme embedding failed; no theme results were produced.")
        vectors.append(vector / norm)
    return np.asarray(vectors)


def _keywords(texts, groups):
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 3), max_features=5000,
            # All-X masks are not useful labels. Filter only keyword tokens;
            # modeling text, embeddings, assignments, and quotes are untouched.
            token_pattern=r"(?u)\b(?![xX]{3,}\b)[^\W\d_]{3,}\b",
        )
        matrix = vectorizer.fit_transform(texts)
    except ValueError:  # Empty vocabulary, e.g. a file containing only stop words.
        return [[] for _ in groups]
    terms = vectorizer.get_feature_names_out()
    output = []
    for members in groups:
        scores = np.asarray(matrix[members].mean(axis=0)).ravel()
        ranked = sorted(range(len(terms)), key=lambda i: (-scores[i], terms[i]))
        selected = []
        for index in ranked:
            if scores[index] <= 0:
                break
            term = str(terms[index])
            words = set(term.split())
            if any(words <= set(other.split()) or set(other.split()) <= words for other in selected):
                continue
            selected.append(term)
            if len(selected) == 5:
                break
        output.append(selected)
    return output


def _cluster_vectors(vectors, theme_count):
    """Choose k from geometry only; keep manual clustering backward compatible."""
    distinct = len(np.unique(vectors, axis=0))
    automatic = theme_count == "auto"
    selection = {
        "mode": "automatic" if automatic else "manual",
        "metric": "euclidean" if automatic else None,
        "candidate_scores": [], "skipped_counts": [], "fallback_reason": None,
    }
    try:
        if not automatic:
            labels = KMeans(n_clusters=min(theme_count, distinct), random_state=42, n_init=10).fit_predict(vectors)
        else:
            labels, best_score = None, -np.inf
            for count in range(4, min(12, distinct, len(vectors) - 1) + 1):
                candidate = KMeans(n_clusters=count, random_state=42, n_init=10).fit_predict(vectors)
                if len(set(candidate)) != count:
                    selection["skipped_counts"].append(count)
                    continue
                score = float(silhouette_score(vectors, candidate, metric="euclidean"))
                if not np.isfinite(score):
                    selection["skipped_counts"].append(count)
                    continue
                selection["candidate_scores"].append({"count": count, "score": score})
                # Ascending candidates and strict comparison prefer smaller k on exact ties.
                if score > best_score:
                    labels, best_score = candidate, score
            if labels is None:
                labels = np.zeros(len(vectors), dtype=int)
                selection["fallback_reason"] = "No valid silhouette candidate in the 4-12 range; returned one group. Use a manual count to explore alternatives."
    except Exception:
        raise ThemeError("Theme clustering or selection failed; no theme results were produced.") from None
    selection["selected_count"] = len(set(labels))
    return labels, selection


def analyze_themes(
    frame: pd.DataFrame, *, theme_count: int | str = 6,
    embedding_mode: str = "sentence_weighted",
    merge_small_themes: bool = False,
    backend: str = "kmeans",
    keyword_method: str = "tfidf",
    quote_pool_size: int = 3,
    quote_mode: str = "full_comment",
) -> dict:
    """Analyze up to 5,000 English comments in memory; never write uploads.

    Assignments use zero-based input row positions, not respondent IDs. All
    textual output comes from the existing redaction boundary; missed PII can
    still remain. This function is not a privacy guarantee or a review workflow.
    sentence_weighted is experimental; whole_comment retains the original baseline.
    merge_small_themes optionally consolidates groups with fewer than three members.
    Selection scores describe initial groups; theme_merging records the final count.
    """
    if quote_mode not in ('full_comment', 'sentences'):
        raise ThemeError('Choose full_comment or sentences for quotes.')
    if backend not in ("auto", "kmeans", "bertopic"):
        raise ThemeError("Choose auto, kmeans, or bertopic clustering.")
    if keyword_method not in ("tfidf", "keybert"):
        raise ThemeError("Choose tfidf or keybert keywords.")
    if isinstance(quote_pool_size, bool) or not isinstance(quote_pool_size, int) or not 3 <= quote_pool_size <= 10:
        raise ThemeError("Choose a quote pool between 3 and 10.")
    actual_backend = ("bertopic" if len(frame) >= 150 else "kmeans") if backend == "auto" else backend
    if not isinstance(merge_small_themes, bool):
        raise ThemeError("Choose true or false for small-theme merging.")
    if not (isinstance(theme_count, str) and theme_count == "auto") and (
        isinstance(theme_count, bool) or not isinstance(theme_count, int) or not 1 <= theme_count <= 15
    ):
        raise ThemeError('Choose between 1 and 15 themes, or "auto" for fewer than 150 input rows.')
    if actual_backend == "kmeans" and theme_count == "auto" and len(frame) >= 150:
        raise ThemeError("Automatic theme selection requires fewer than 150 input rows; choose a manual count for this prototype.")
    if embedding_mode not in ("sentence_weighted", "whole_comment"):
        raise ThemeError("Choose sentence_weighted or whole_comment embedding mode.")
    if "comment_text" not in frame.columns:
        raise ThemeError("A comment_text column is required for theme analysis.")
    if len(frame) > 5000:
        raise ThemeError("Theme analysis accepts at most 5,000 rows; select a smaller file.")
    raw = frame["comment_text"].fillna("").astype(str).str.strip()
    positions = np.flatnonzero(raw.ne("").to_numpy()).tolist()
    if not positions:
        raise ThemeError("No nonempty comments are available for theme analysis.")
    # Redact before deriving labels/quotes. Never use subgroup or validation labels.
    safe = build_safe_display_frame(pd.DataFrame({"comment_text": raw.iloc[positions].tolist()}))
    quotes = safe.frame["comment_text"].tolist()
    texts = [_analysis_text(text) for text in quotes]
    eligible = [i for i, text in enumerate(texts) if re.search(r"[^\W\d_]", text)]
    if not eligible:
        raise ThemeError("No analyzable text remains after redaction.")
    excluded_positions = [positions[i] for i in range(len(positions)) if i not in set(eligible)]
    positions = [positions[i] for i in eligible]
    quotes = [quotes[i] for i in eligible]
    texts = [texts[i] for i in eligible]
    notes = [
        "Experimental English-only K-means themes: every analyzed comment is assigned; no outlier detection.",
        "Automatic redaction can miss identifiers. Review labels and quotes before sharing.",
    ]
    if excluded_positions:
        notes.append(f"Excluded {len(excluded_positions)} comments with no analyzable text after redaction.")
    if np.median([len(text.split()) for text in texts]) < 8:
        notes.append("Median comment length is under eight words; theme quality may be poor.")
    vectors = _theme_vectors(texts, embedding_mode)
    if embedding_mode == "sentence_weighted":
        notes.append("Sentence weighting is experimental: repeated substantive statements can also be downweighted.")
    if actual_backend == "bertopic":
        try:
            from pipeline.topic_backend import cluster_bertopic
            labels, selection = cluster_bertopic(texts, vectors, _get_embedding_model(),
                target_topics=6 if theme_count == "auto" else theme_count)
        except Exception:
            raise ThemeError("BERTopic clustering failed; check dependencies and available resources. No theme results were produced.") from None
        notes[0] = "Experimental BERTopic themes; unmatched comments remain explicit outliers."
        if theme_count != "auto":
            notes.append("BERTopic reduces toward the requested count but cannot create missing density groups; use backend=kmeans for an exact manual count.")
    else:
        labels, selection = _cluster_vectors(vectors, theme_count)
    outliers = np.flatnonzero(labels == -1).tolist()
    outlier_share = len(outliers) / len(texts)
    if outlier_share >= .2:
        notes.append("Outlier share is at least 20%; the project quality target is not met. Review rather than force assignments.")
    if selection["fallback_reason"]:
        notes.append(selection["fallback_reason"])
    if selection["skipped_counts"]:
        notes.append("Some automatic candidates could not be scored; inspect theme_selection.skipped_counts.")
    if theme_count == "auto" and actual_backend == "kmeans":
        notes.append("Automatic selection measures vector separation, not semantic accuracy; review the themes and consider a manual count.")
    # Stable display IDs: largest theme first, then first input position on ties.
    groups = [np.flatnonzero(labels == label).tolist() for label in sorted(set(labels) - {-1})]
    groups.sort(key=lambda members: (-len(members), positions[members[0]]))
    if actual_backend == "kmeans" and isinstance(theme_count, int) and len(groups) < theme_count:
        notes.append(f"Produced {len(groups)} themes because there are too few distinct comment vectors.")
    merging = {"enabled": merge_small_themes, "initial_count": len(groups), "final_count": len(groups)}
    if merge_small_themes:
        try:
            groups, details = merge_small_groups(vectors, groups)
        except Exception:
            raise ThemeError("Small-theme merging failed; no theme results were produced.") from None
        paired = sorted(zip(groups, details.pop("initial_theme_ids_by_group")),
                        key=lambda item: (-len(item[0]), positions[item[0][0]]))
        groups = [members for members, _ in paired]
        merging.update(details)
        merging["final_theme_sources"] = [
            {"theme_id": i, "initial_theme_ids": ids}
            for i, (_, ids) in enumerate(paired, start=1)
        ]
        merging["retained_small_theme_ids"] = [
            i for i, members in enumerate(groups, start=1) if len(members) < MIN_THEME_SIZE
        ]
        notes.append("Small-theme merging is experimental; similarity does not guarantee shared meaning. Review merged themes and minority viewpoints.")
        if details["history"]:
            notes.append(f"Small-theme merging reduced {merging['initial_count']} initial themes to {len(groups)}; requested counts and selection scores describe the pre-merge groups.")
        if merging["retained_small_theme_ids"]:
            notes.append(f"Retained {len(merging['retained_small_theme_ids'])} small themes without a qualifying merge partner; no comments were discarded.")
    if keyword_method == "keybert":
        try:
            from pipeline.topic_backend import keybert_keywords
            keywords = keybert_keywords(texts, groups, vectors, _get_embedding_model())
        except Exception:
            raise ThemeError("Keyword labeling failed; no theme results were produced.") from None
    else:
        keywords = _keywords(texts, groups)
    themes, assignments = [], []
    # Enumerate spans cheaply. Encode only rows reached by nearest-first selection;
    # encoding every sentence in every comment wastes most work after slots fill.
    spans_by_row = [quote_spans(quote, quote_mode) for quote in quotes]
    for theme_id, (members, words) in enumerate(zip(groups, keywords), start=1):
        center = vectors[members].mean(axis=0)
        norm = np.linalg.norm(center)
        if norm:
            center /= norm
        nearest = sorted(members, key=lambda i: (-float(vectors[i] @ center), positions[i]))
        selected = []
        selected_indices = []
        for index in nearest:
            spans = spans_by_row[index]
            if not spans:
                continue
            if len(spans) == 1:
                start, end = spans[0]
            else:
                span_vectors = _embed([quotes[index][a:b] for a, b in spans])
                start, end = spans[int(np.argmax(span_vectors @ center))]
            quote = quotes[index][start:end]
            normalized = texts[index].casefold()
            if quote_mode == 'sentences' and any(nearly_identical(_analysis_text(quote), _analysis_text(q['text'])) for q in selected):
                continue
            if quote_mode == 'full_comment' and any(
                SequenceMatcher(None, normalized, texts[old].casefold()).ratio() >= 0.85
                or normalized in texts[old].casefold() or texts[old].casefold() in normalized
                or float(vectors[index] @ vectors[old]) >= 0.97
                for old in selected_indices
            ):
                continue
            selected.append({"row_position": positions[index], "text": quote,
                **({'source_start': start, 'source_end': end,
                    'is_excerpt': start != 0 or end != len(quotes[index])}
                   if quote_mode == 'sentences' else {})})
            selected_indices.append(index)
            if len(selected) == quote_pool_size:
                break
        if len(selected) < 3:
            notes.append(f"Theme {theme_id} has only {len(selected)} eligible distinct quotes of 12-60 words.")
        themes.append({
            "theme_id": theme_id, "label": " / ".join(words[:3]) or f"Theme {theme_id}",
            "keywords": words, "count": len(members), "share": len(members) / len(texts),
            "quotes": selected[:3],
            **({"quote_alternatives": selected[3:]} if quote_pool_size > 3 else {}),
        })
        assignments.extend({"row_position": positions[i], "theme_id": theme_id} for i in members)
    assignments.extend({"row_position": positions[i], "theme_id": 0} for i in outliers)
    if backend != "kmeans" and not 5 <= len(themes) <= 15:
        notes.append("Final theme count is outside the 5-15 project target.")
    return {
        "method": f"all-MiniLM-L6-v2 + {actual_backend} + {keyword_method} keywords",
        "backend": actual_backend,
        "outlier_count": len(outliers), "outlier_share": outlier_share,
        "embedding_mode": embedding_mode,
        "quote_mode": quote_mode,
        "theme_selection": selection,
        "theme_merging": merging,
        "requested_themes": theme_count, "analyzed_comments": len(texts),
        "empty_comments_removed": len(frame) - len(raw[raw.ne("")]),
        "excluded_row_positions": excluded_positions,
        "themes": themes, "assignments": sorted(assignments, key=lambda item: item["row_position"]),
        "warnings": notes,
    }
