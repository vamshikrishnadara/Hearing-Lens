"""Initial local embedding/K-means themes; returns no raw comment text or metadata."""

from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
import re

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from pipeline.redact import build_safe_display_frame


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


def _keywords(texts, groups):
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 3), max_features=5000,
            token_pattern=r"(?u)\b[^\W\d_]{3,}\b",
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


def analyze_themes(frame: pd.DataFrame, *, theme_count: int = 6) -> dict:
    """Analyze up to 5,000 English comments in memory; never write uploads.

    Assignments use zero-based input row positions, not respondent IDs. All
    textual output comes from the existing redaction boundary; missed PII can
    still remain. This function is not a privacy guarantee or a review workflow.
    """
    if isinstance(theme_count, bool) or not isinstance(theme_count, int) or not 1 <= theme_count <= 15:
        raise ThemeError("Choose between 1 and 15 themes.")
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
    vectors = _embed(texts)
    count = min(theme_count, len(np.unique(vectors, axis=0)))
    try:
        labels = KMeans(n_clusters=count, random_state=42, n_init=10).fit_predict(vectors)
    except Exception:
        raise ThemeError("Theme clustering failed; no theme results were produced.") from None
    # Stable display IDs: largest theme first, then first input position on ties.
    groups = [np.flatnonzero(labels == label).tolist() for label in sorted(set(labels))]
    groups.sort(key=lambda members: (-len(members), positions[members[0]]))
    if len(groups) < theme_count:
        notes.append(f"Produced {len(groups)} themes because there are too few distinct comment vectors.")
    keywords = _keywords(texts, groups)
    themes, assignments = [], []
    for theme_id, (members, words) in enumerate(zip(groups, keywords), start=1):
        center = vectors[members].mean(axis=0)
        norm = np.linalg.norm(center)
        if norm:
            center /= norm
        nearest = sorted(members, key=lambda i: (-float(vectors[i] @ center), positions[i]))
        selected = []
        selected_indices = []
        for index in nearest:
            quote = quotes[index]
            if not 12 <= len(quote.split()) <= 60:
                continue
            normalized = texts[index].casefold()
            if any(
                SequenceMatcher(None, normalized, texts[old].casefold()).ratio() >= 0.85
                or normalized in texts[old].casefold() or texts[old].casefold() in normalized
                or float(vectors[index] @ vectors[old]) >= 0.97
                for old in selected_indices
            ):
                continue
            selected.append({"row_position": positions[index], "text": quote})
            selected_indices.append(index)
            if len(selected) == 3:
                break
        if len(selected) < 3:
            notes.append(f"Theme {theme_id} has only {len(selected)} eligible distinct quotes of 12-60 words.")
        themes.append({
            "theme_id": theme_id, "label": " / ".join(words[:3]) or f"Theme {theme_id}",
            "keywords": words, "count": len(members), "share": len(members) / len(texts),
            "quotes": selected,
        })
        assignments.extend({"row_position": positions[i], "theme_id": theme_id} for i in members)
    return {
        "method": "all-MiniLM-L6-v2 + KMeans + TF-IDF keywords",
        "requested_themes": theme_count, "analyzed_comments": len(texts),
        "empty_comments_removed": len(frame) - len(raw[raw.ne("")]),
        "excluded_row_positions": excluded_positions,
        "themes": themes, "assignments": sorted(assignments, key=lambda item: item["row_position"]),
        "warnings": notes,
    }
