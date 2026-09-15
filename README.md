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

The analytical models and final dashboard panels are not implemented yet.

## Local setup

1. Create and activate a Python 3.11 or later virtual environment.
2. Install the dependencies with `pip install -r requirements.txt`.
3. Run the tests with `python -m unittest discover -s tests -v`.
4. Start the current interface with `streamlit run app/streamlit_app.py`.

## Repository layout

```text
hearing-lens/
  app/streamlit_app.py       Current upload and mapping interface
  pipeline/ingest.py         File loading, validation, and column mapping
  docs/schema.md             Canonical input and internal schemas
  docs/wireframe.md          First dashboard wireframe
  docs/project_plan.md       Gate-based delivery plan
  docs/work_log.md           Completed and planned activity record
  data/samples/              Development-only sample data location
  tests/test_ingest.py       Unit tests for the loader
```

## Decisions still requiring confirmation

- The repository license and intellectual-property language must be confirmed with ChiEAC before public release.
- The fixed weekly check-in time and Gate 0 review date must be agreed with Benjamin.
- Test-data licenses and attribution must be recorded before public datasets are committed.
