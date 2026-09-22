"""Local person detection and pattern redaction for comment display and export."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
import re
from typing import Pattern

import pandas as pd


class RedactionError(ValueError):
    """A redaction failure that can be displayed without exposing input text."""


@lru_cache(maxsize=1)
def _get_person_model():
    """Cache model resources only; never cache comments or inference results."""
    try:
        import spacy

        model = spacy.load(
            "en_core_web_sm",
            exclude=["tagger", "parser", "attribute_ruler", "lemmatizer"],
        )
        if "ner" not in model.pipe_names or "PERSON" not in model.get_pipe("ner").labels:
            raise ValueError("Missing person recognizer")
        return model
    except Exception:
        raise RedactionError(
            "Name detection is unavailable, so the preview was not generated. "
            "Install the English name-detection model using the README setup steps."
        ) from None


@dataclass(frozen=True)
class RedactionResult:
    """Redacted text and counts that do not retain the detected values."""

    text: str
    entity_counts: dict[str, int]


@dataclass(frozen=True)
class FrameRedactionResult:
    """A copied table with a redacted text column and aggregate counts."""

    frame: pd.DataFrame
    entity_counts: dict[str, int]


_PATTERNS: tuple[tuple[str, Pattern[str]], ...] = (
    (
        "EMAIL_ADDRESS",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    ),
    (
        "URL",
        re.compile(r"\b(?:https?://|www\.)[^\s<>()]+", re.IGNORECASE),
    ),
    (
        "PHONE_NUMBER",
        re.compile(
            r"(?<!\w)(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})"
            r"[\s.-]\d{3}[\s.-]\d{4}(?!\w)"
        ),
    ),
    (
        "STREET_ADDRESS",
        re.compile(
            r"\b\d{1,6}\s+"
            r"(?:[A-Z0-9.'-]+\s+){0,5}"
            r"(?:STREET|ST|AVENUE|AVE|ROAD|RD|BOULEVARD|BLVD|DRIVE|DR|"
            r"LANE|LN|COURT|CT|PLACE|PL|PARKWAY|PKWY|WAY)\b\.?,?",
            re.IGNORECASE,
        ),
    ),
    (
        "UNIT_NUMBER",
        re.compile(
            r"\b(?:APT|APARTMENT|UNIT|SUITE|STE)\s*#?\s*[A-Z0-9-]+\b",
            re.IGNORECASE,
        ),
    ),
)


def _redact_detected_text(text: str, entities) -> RedactionResult:
    # All offsets refer to the original text. Replacements happen only after
    # merging overlaps, so one stage cannot corrupt another stage's offsets.
    spans: list[tuple[int, int, str]] = []
    for entity_type, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            end = match.end()
            if entity_type == "URL":
                end = match.start() + len(match.group().rstrip(".,;:!?"))
            spans.append((match.start(), end, entity_type))
    for entity in entities:
        if entity.label_ != "PERSON":
            continue
        start, end = entity.start_char, entity.end_char
        # Preserve the adjective in this observed opening phrase only. Do not
        # whitelist "Broken" as a name elsewhere, or discard longer PERSON spans.
        if (
            text[start:end].casefold() == "broken"
            and not text[:start].strip()
            and re.match(r"\s+exterior\s+lighting\b", text[end:], re.IGNORECASE)
        ):
            continue
        # The small English model can tag the command "Email" as a person
        # before an email address (including "Email me/us at"). Exclude only
        # these contact instructions, not arbitrary names or capitalized words.
        if text[start:end].casefold() == "email" and any(
            kind == "EMAIL_ADDRESS" and address_start >= end
            and text[end:address_start].strip().casefold() in ("", "me at", "us at")
            for address_start, _, kind in spans
        ):
            continue
        spans.append((start, end, "PERSON"))
    spans.sort(key=lambda span: (span[0], -span[1]))
    merged: list[tuple[int, int, str]] = []
    longest = 0
    for start, end, entity_type in spans:
        if merged and start < merged[-1][1]:
            old_start, old_end, old_type = merged[-1]
            label = entity_type if end - start > longest else old_type
            longest = max(longest, end - start)
            merged[-1] = (old_start, max(old_end, end), label)
        else:
            merged.append((start, end, entity_type))
            longest = end - start

    parts: list[str] = []
    counts: Counter[str] = Counter()
    cursor = 0
    for start, end, entity_type in merged:
        parts.extend((text[cursor:start], f"[{entity_type}]"))
        counts[entity_type] += 1
        cursor = end
    parts.append(text[cursor:])
    return RedactionResult("".join(parts), dict(sorted(counts.items())))


def _redact_texts(texts: list[str]) -> list[RedactionResult]:
    if not any(texts):
        return [RedactionResult("", {}) for _ in texts]
    model = _get_person_model()
    try:
        results = [
            _redact_detected_text(doc.text, doc.ents)
            for doc in model.pipe(texts, batch_size=64)
        ]
        if len(results) != len(texts):
            raise ValueError("Incomplete redaction")
        return results
    except Exception:
        raise RedactionError(
            "Name detection could not finish, so the preview was not generated. "
            "Try a smaller file or shorter comments."
        ) from None


def redact_text(text: object) -> RedactionResult:
    """Replace detected names, contacts, and addresses with typed markers."""

    if text is None or pd.isna(text):
        return RedactionResult(text="", entity_counts={})

    return _redact_texts([str(text)])[0]


def redact_frame(
    frame: pd.DataFrame,
    *,
    source_column: str = "comment_text",
    output_column: str = "redacted_comment_text",
) -> FrameRedactionResult:
    """Return a copy with redacted display text while preserving modeling text."""

    if source_column not in frame.columns:
        raise ValueError(f"Missing source column: {source_column}")
    if output_column in frame.columns and output_column != source_column:
        raise ValueError(f"Output column already exists: {output_column}")

    redacted_frame = frame.copy()
    aggregate: Counter[str] = Counter()
    output: list[str] = []
    texts = ["" if pd.isna(value) else str(value) for value in frame[source_column]]
    for result in _redact_texts(texts):
        output.append(result.text)
        aggregate.update(result.entity_counts)

    redacted_frame[output_column] = output
    return FrameRedactionResult(
        frame=redacted_frame,
        entity_counts=dict(sorted(aggregate.items())),
    )


def build_safe_display_frame(
    frame: pd.DataFrame,
    *,
    source_column: str = "comment_text",
) -> FrameRedactionResult:
    """Return only redacted comments, excluding identifiers and mapped metadata.

    This is a display boundary, not a guarantee of complete de-identification:
    names and other values outside the baseline patterns can remain in text.
    """

    result = redact_frame(frame, source_column=source_column)
    display_frame = result.frame.loc[:, ["redacted_comment_text"]].rename(
        columns={"redacted_comment_text": source_column}
    )
    return FrameRedactionResult(
        frame=display_frame,
        entity_counts=result.entity_counts,
    )
