# Redaction Design

Hearing Lens must redact identifying information before a comment is displayed as a representative quote or included in an export. Unredacted comment text may be used for modeling only during the active in-memory session.

## Baseline implementation

The deterministic first pass currently recognizes:

- Email addresses
- Web addresses
- North American phone numbers
- Common street-address formats
- Apartment, unit, and suite identifiers

Each detected value is replaced with a typed marker such as `[EMAIL_ADDRESS]` or `[STREET_ADDRESS]`. Detection counts contain only entity categories and totals; they do not retain the sensitive values.

The table-level function creates a separate `redacted_comment_text` field. The original `comment_text` remains available for in-memory modeling and must never be displayed, exported, written to logs, or persisted on the server.

The dashboard preview uses a display-specific table containing only the redacted comment column. Respondent IDs and all other mapped metadata are excluded because those fields may contain identifiers that have not been redacted. The original mapped table remains in memory for processing. Basic redaction can still miss personal names and other identifiers inside comments; the interface makes that limitation explicit and directs development testing to fictional data.

## Person detection added September 17 2026

The preview now runs spaCy's `en_core_web_sm` English entity recognizer and
replaces its `PERSON` spans with `[PERSON]`. This focused step uses spaCy
directly alongside the existing patterns; the broader Presidio integration is
still future work. Model setup is explicit in the README. The tested versions
are spaCy 3.8.16 and `en_core_web_sm` 3.8.0.

The process caches the model resource, not comments or results, and processes
frames in batches of 64. No upload is sent to a hosted model. A missing model,
missing person recognizer, or inference failure raises a sanitized error and
prevents the preview from being displayed. Original modeling text stays in
memory; the preview contains only redacted comments.

Both pattern and person spans refer to the original text. Overlapping spans
are merged to cover their full union; the longest detection supplies the
replacement category. Each merged span counts as one replacement. This avoids
leaving fragments or inserting nested markers. URL punctuation is preserved.
One narrow false-positive rule preserves the command `Email` immediately
before an email address, including `Email me at` and `Email us at`.

### Initial measurements - September 17

The initial 21-case fictional check contained 18 expected name mentions and
five name-free controls. It fully removed 16 of the 18 mentions; neither
`Anne-Marie O'Neill` in a self-introduction nor `Elena` in a sentence about a
daughter was recognized. No PERSON markers appeared in those five controls.
A sixth control, `Broken exterior lighting has been reported repeatedly without
a response.`, was then added after sample inspection exposed a false positive
on the word `Broken`. The expanded check preserves that known failure for review.

On the existing 1,000-row fictional sample, 67 of 79 planted names were fully
removed. There were 112 PERSON replacements, including 45 false positives on
`Broken`. Contact/address counts remained 79 emails, 79 phones, 84 street
addresses, and 84 unit numbers. These are small development fixtures used during
implementation, not an independent benchmark or a guarantee of privacy.

Reproduce the report with `python -m scripts.validate_person_redaction`.
Names with punctuation, contextual first names, and some two-word names can
be missed; ordinary words can be removed incorrectly. Keep fictional-data
testing and human review in place. Broader location detection, international
formats, and the quote-review workflow remain unfinished.

Implementation reference: [spaCy English models](https://spacy.io/models/en).

### Targeted lighting correction - September 22

The initial measurements above are retained as historical evidence. A narrow
post-detection rule now preserves a standalone PERSON span `Broken` only when
it opens the comment (allowing leading whitespace) and is immediately followed
by `exterior lighting`, separated by whitespace. Matching is case-insensitive
and requires a word boundary after `lighting`. It does not change the model,
exempt longer PERSON spans, or whitelist `Broken` elsewhere. Names and contact
patterns later in the same comment still go through redaction.

On the same 1,000-row development sample, the known false replacements of
`Broken` fell from 45 to 0. Fully removed planted names stayed at 67 of 79;
PERSON markers fell from 112 to 67 because the 45 false positives were removed.
Email, phone, street-address, and unit counts remained 79, 79, 84, and 84.
The original 22-case fixture still removes 16 of 18 expected name mentions;
name-free controls receiving a PERSON marker fell from 1 of 6 to 0 of 6.

A separate six-case [lighting fixture](../data/samples/lighting_redaction_cases.json)
checks two adjective examples, a name later in the same comment, and three
name contexts that must remain redacted. Exact expected outputs improved from
3 of 6 to 6 of 6. Run the existing validation command to see both the original
fixtures and these focused checks. All 43 automated tests passed, including
four new tests covering real-model examples, the rule's boundaries, formatting,
and preview counts. No browser test was performed for this correction.

This is a phrase-specific development correction, not a general improvement to
name recognition. For example, the model also tagged `Broken` in `Broken windows
need repair.` during investigation; that different context is not addressed.
The rule assumes the opening phrase describes lighting, so an unusual actual
name used in that exact context could be retained. Known missed names and
broader privacy limitations remain. See the [comparison report](redaction_validation_2026-09-22.md).

## Validation plan

1. Build test cases containing names, addresses, phones, email addresses, web addresses, unit numbers, and benign numbers.
2. Confirm that detected values never appear in redacted output or entity-count summaries.
3. Inspect at least 30 representative quotes manually at Gate 3 and again at Gate 4.
4. Record false negatives by category and add regression tests for every confirmed miss.
5. Do not display a quote unless the redacted version has passed through every enabled redaction stage.

## Known limitations

- Personal-name detection is present but incomplete, with the misses and false positives above.
- International phone and address formats require additional coverage.
- A location name may be ordinary public context rather than identifying information; automated removal requires conservative rules and review.
- Free-form text can contain unexpected identifiers, so automated detection does not replace the quote-review control required before export.
