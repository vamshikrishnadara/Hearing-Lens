"""Create a reproducible Chicago-style hearing dataset for development tests."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import random
from typing import Iterable


FIELDNAMES = (
    "respondent_id",
    "comment_text",
    "hearing_date",
    "ward",
    "role",
    "language",
    "housing_tenure",
    "school",
    "validation_theme",
)

THEME_COMMENTS: dict[str, tuple[str, ...]] = {
    "classroom_resources": (
        "Class sizes are too large and students need more classroom materials.",
        "Please protect funding for teachers, books, and after-school tutoring.",
        "Why are classroom positions being reduced when enrollment is stable?",
        "The proposal should add counselors instead of cutting school staff.",
    ),
    "school_safety": (
        "Students need a safer arrival plan and trained staff at dismissal.",
        "Please explain how the safety budget will be used at each school.",
        "Broken exterior lighting has been reported repeatedly without a response.",
        "Will families be included when the new safety procedures are reviewed?",
    ),
    "mental_health": (
        "Every school needs reliable access to social workers and counselors.",
        "Students are waiting too long for mental-health support.",
        "How many additional clinicians will this proposal place in schools?",
        "The district should fund trauma-informed services throughout the year.",
    ),
    "transportation": (
        "The current bus schedule causes students to arrive late.",
        "Families need clear transportation updates before routes change.",
        "Will the district publish route performance and missed-pickup data?",
        "Long travel times are making after-school participation difficult.",
    ),
    "accessibility": (
        "Meeting materials should be accessible before the public hearing.",
        "Families need interpretation and disability accommodations at every meeting.",
        "Why was the accessibility plan not included with the proposal?",
        "The online form must work with keyboards and screen readers.",
    ),
    "communication": (
        "Families received the notice too late to prepare meaningful comments.",
        "Please publish decisions, supporting data, and meeting dates in one place.",
        "Who is responsible for answering questions submitted at the hearing?",
        "Regular multilingual updates would make this process easier to follow.",
    ),
}

HEARING_DATES = ("2026-09-02", "2026-09-07", "2026-09-12")
WARDS = (5, 6, 7, 8, 10, 20)
ROLES = ("Parent", "Resident", "Teacher", "Student", "Community organizer")
LANGUAGES = ("English", "Spanish", "Polish", "Mandarin")
TENURES = ("Renter", "Owner", "Other")
SCHOOLS = (
    "Community School A",
    "Community School B",
    "Community School C",
    "Community School D",
)

FIRST_NAMES = ("Jordan", "Taylor", "Morgan", "Casey", "Avery", "Riley")
LAST_NAMES = ("Parker", "Reed", "Hayes", "Brooks", "Quinn", "Lane")
STREETS = ("Civic Way", "Learning Street", "Community Avenue", "Public Square Road")


def _weighted_choice(
    rng: random.Random, values: tuple[object, ...], weights: tuple[int, ...]
) -> object:
    return rng.choices(values, weights=weights, k=1)[0]


def _synthetic_contact(rng: random.Random, row_number: int) -> str:
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    email = f"sample.person{row_number}@example.org"
    phone = f"312-555-{1000 + row_number % 9000:04d}"
    return f" Contact {first} {last} at {email} or {phone}."


def _synthetic_address(rng: random.Random, row_number: int) -> str:
    number = 100 + row_number % 9800
    street = rng.choice(STREETS)
    unit = f"{1 + row_number % 30}{rng.choice(('A', 'B', 'C'))}"
    return f" I live at {number} {street}, Apt {unit}."


def generate_rows(count: int = 1_000, seed: int = 20_260_915) -> list[dict[str, object]]:
    """Return deterministic sample rows with planted themes and skewed groups."""

    if count < 1:
        raise ValueError("count must be at least 1")

    rng = random.Random(seed)
    themes = tuple(THEME_COMMENTS)
    rows: list[dict[str, object]] = []
    for index in range(1, count + 1):
        theme = themes[(index - 1) % len(themes)]
        comment = rng.choice(THEME_COMMENTS[theme])

        hearing_date = _weighted_choice(rng, HEARING_DATES, (30, 33, 37))
        if hearing_date == HEARING_DATES[-1] and rng.random() < 0.45:
            comment = "After attending multiple hearings, I am increasingly concerned. " + comment
        if rng.random() < 0.08:
            comment += _synthetic_contact(rng, index)
        if rng.random() < 0.08:
            comment += _synthetic_address(rng, index)

        rows.append(
            {
                "respondent_id": f"SYN-{index:04d}",
                "comment_text": comment,
                "hearing_date": hearing_date,
                "ward": _weighted_choice(rng, WARDS, (8, 12, 18, 30, 22, 10)),
                "role": _weighted_choice(rng, ROLES, (55, 20, 12, 8, 5)),
                "language": _weighted_choice(rng, LANGUAGES, (82, 10, 4, 4)),
                "housing_tenure": _weighted_choice(rng, TENURES, (68, 25, 7)),
                "school": rng.choice(SCHOOLS),
                "validation_theme": theme,
            }
        )

    return rows


def write_csv(path: str | Path, rows: Iterable[dict[str, object]]) -> None:
    """Write sample rows using a stable field order and UTF-8 encoding."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/samples/synthetic_chicago_hearing.csv"),
    )
    parser.add_argument("--count", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=20_260_915)
    args = parser.parse_args()

    rows = generate_rows(count=args.count, seed=args.seed)
    write_csv(args.output, rows)
    print(f"Wrote {len(rows):,} synthetic rows to {args.output}")


if __name__ == "__main__":
    main()
