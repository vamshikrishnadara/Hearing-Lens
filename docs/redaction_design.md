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

## Required second pass

Pattern matching cannot reliably identify personal names or every location phrase. Before the redaction module is considered complete, it must add an entity-recognition pass for:

- Person names
- Location names when they identify a residence or individual
- Address formats not covered by the baseline patterns

The planned implementation uses Microsoft Presidio with spaCy and combines its spans with the deterministic patterns. Overlapping detections should use the longest supported span and one replacement marker.

## Validation plan

1. Build test cases containing names, addresses, phones, email addresses, web addresses, unit numbers, and benign numbers.
2. Confirm that detected values never appear in redacted output or entity-count summaries.
3. Inspect at least 30 representative quotes manually at Gate 3 and again at Gate 4.
4. Record false negatives by category and add regression tests for every confirmed miss.
5. Do not display a quote unless the redacted version has passed through every enabled redaction stage.

## Known limitations

- The baseline does not yet redact personal names.
- International phone and address formats require additional coverage.
- A location name may be ordinary public context rather than identifying information; automated removal requires conservative rules and review.
- Free-form text can contain unexpected identifiers, so automated detection does not replace the quote-review control required before export.
