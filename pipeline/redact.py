"""Deterministic first-pass redaction for displayed and exported comment text."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re
from typing import Pattern

import pandas as pd


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


def _replace_pattern(
    text: str,
    *,
    entity_type: str,
    pattern: Pattern[str],
    counts: Counter[str],
) -> str:
    placeholder = f"[{entity_type}]"

    def replace(match: re.Match[str]) -> str:
        value = match.group(0)
        trailing = ""
        if entity_type == "URL":
            value = value.rstrip(".,;:!?")
            trailing = match.group(0)[len(value) :]
        counts[entity_type] += 1
        return placeholder + trailing

    return pattern.sub(replace, text)


def redact_text(text: object) -> RedactionResult:
    """Replace deterministic contact and address patterns with typed markers."""

    if text is None or pd.isna(text):
        return RedactionResult(text="", entity_counts={})

    redacted = str(text)
    counts: Counter[str] = Counter()
    for entity_type, pattern in _PATTERNS:
        redacted = _replace_pattern(
            redacted,
            entity_type=entity_type,
            pattern=pattern,
            counts=counts,
        )

    return RedactionResult(text=redacted, entity_counts=dict(sorted(counts.items())))


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
    for value in redacted_frame[source_column]:
        result = redact_text(value)
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
    """Return a display-safe table that contains no raw comment-text column."""

    result = redact_frame(frame, source_column=source_column)
    display_frame = result.frame.drop(columns=[source_column]).rename(
        columns={"redacted_comment_text": source_column}
    )
    return FrameRedactionResult(
        frame=display_frame,
        entity_counts=result.entity_counts,
    )
