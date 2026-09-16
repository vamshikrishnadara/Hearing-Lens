# Hearing Lens

Hearing Lens is a privacy-conscious analyzer for public comments, community survey responses, and meeting sign-up exports. The planned application accepts CSV or XLSX files, lets a user map their columns, and produces transparent summaries of themes, sentiment, representation gaps, timelines, and unanswered questions.

This repository currently contains the Week 1 project foundation: an input loader, a first-pass column-mapping interface, schema documentation, a dashboard wireframe, an implementation plan, tests, and a work log.

## Project principles

- The production application will analyze only data supplied by the user.
- Uploaded content must remain in memory and must not be written to server logs or storage.
- Personally identifying information must be redacted before quotes are displayed or exported.
- Demographic traits must never be inferred from names or comment text.
- Methods, validation results, and limitations must be explained in plain language.

## Current functionality

- Accepts CSV and XLSX files.
- Lists workbook sheets and allows sheet selection.
- Enforces a configurable row limit.
- Supports mapping the required comment column and optional date, respondent ID, and subgroup columns.
- Drops empty comments and can remove repeated respondent IDs.
- Reports validation problems in readable language.
- Redacts common email, web, phone, street-address, and unit-number patterns from display text.

Personal-name detection, the analytical models, and the final dashboard panels are not implemented yet.

## Local setup

1. Create and activate a Python 3.11 or later virtual environment.
2. Install the dependencies with `python -m pip install -r requirements.txt`.
3. Run the tests with `python -m unittest discover -s tests -v`.
4. From the repository root, start the interface with `python -m streamlit run app/streamlit_app.py`.

Using `python -m streamlit` keeps the repository root available for the app's
pipeline imports. Use fictional data while testing: the current redaction pass
does not remove personal names or all identifiers. The preview displays only
the comment column after basic redaction; mapped identifiers and metadata remain
in memory for processing and are excluded from the preview.

## Repository layout

```text
hearing-lens/
  app/streamlit_app.py       Current upload and mapping interface
  pipeline/ingest.py         File loading, validation, and column mapping
  pipeline/redact.py         Baseline contact and address redaction
  docs/schema.md             Canonical input and internal schemas
  docs/redaction_design.md   Redaction boundary, limitations, and validation plan
  docs/wireframe.md          First dashboard wireframe
  docs/project_plan.md       Gate-based delivery plan
  docs/work_log.md           Completed and planned activity record
  data/samples/              Reproducible development fixture and data dictionary
  scripts/                   Development-data utilities
  tests/test_ingest.py       Unit tests for the loader
```

## Decisions still requiring confirmation

- The repository license and intellectual-property language must be confirmed with ChiEAC before public release.
- The fixed weekly check-in time and Gate 0 review date must be agreed with Benjamin.
- Test-data licenses and attribution must be recorded before public datasets are committed.

## Development sample

The repository includes a reproducible 1,000-row fictional hearing dataset with six planted themes, three hearing dates, skewed subgroup distributions, and controlled redaction examples. It contains no collected resident data. Run `python scripts/generate_synthetic_sample.py` to recreate it.
