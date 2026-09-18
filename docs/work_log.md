# Hearing Lens Work Log

This log records real project outputs and plans. It is not a payroll record. Actual hours should be entered by Vamshi from time personally spent working, reviewing, testing, meeting, or completing related project activity. Planned time must not be presented as completed time.

## September 14 2026

**Reporting week:** September 8 through September 14
**Status:** Foundation package prepared; Vamshi review and validation pending
**Actual time:** To be entered by Vamshi

### Completed outputs

- Converted the project brief into a concise product description and a list of privacy principles.
- Created the initial repository structure and dependency list.
- Defined the user-input schema, internal mapped fields, validation behavior, representation-reference format, and privacy boundary.
- Drafted the upload and results wireframes, including empty and error states.
- Implemented a CSV and XLSX loader with sheet selection, a 5,000-row cap, readable failures, and warnings.
- Implemented comment-column mapping, empty-comment removal, optional respondent deduplication, and optional subgroup mapping.
- Added an initial Streamlit upload and mapping screen.
- Added unit tests for CSV loading, row limits, mapping cleanup, missing fields, and unsupported files.
- Verified all five ingestion tests pass using Python's built-in test runner.
- Converted the eight-week project brief into a gate-based delivery plan and Week 1 backlog.

### Evidence

- `README.md`
- `pipeline/ingest.py`
- `app/streamlit_app.py`
- `tests/test_ingest.py`
- Test result on September 14: 5 tests run, 5 passed
- `docs/schema.md`
- `docs/wireframe.md`
- `docs/project_plan.md`

### Ten-hour focus plan

This is a planning allocation, not a statement that ten hours were completed.

| Activity | Planned time | Completion evidence |
| --- | ---: | --- |
| Review the brief and extract non-negotiables | 0.5 hour | Notes in README and schema |
| Translate gates and acceptance criteria into a backlog | 1.0 hour | Project plan |
| Establish the repository structure and dependencies | 1.0 hour | Project folders and requirements |
| Define the input and internal data schemas | 1.5 hours | Schema document |
| Draft upload, results, and empty-state wireframes | 1.0 hour | Wireframe document |
| Implement ingestion and column mapping | 2.5 hours | Loader module and interface |
| Test loader and mapping behavior | 1.5 hours | Automated tests and results |
| Review outputs, record decisions, and prepare status | 1.0 hour | Updated log and backlog |
| **Total planned** | **10.0 hours** | |

### Review checklist for Vamshi

- Read the schema and confirm the field names make sense.
- Run the tests and save the result.
- Launch the interface and test one small CSV and one XLSX workbook.
- Record corrections or questions in the backlog.
- Enter only the actual time spent on these activities.

## September 15 2026

**Reporting week:** September 15 through September 21
**Status:** Development checkpoint complete; Vamshi review pending
**Daily session limit:** 5 hours
**Actual time:** To be entered by Vamshi

### Completed outputs

- Added Windows-1252 CSV support with a conversion notice.
- Added XLSX sheet listing, selected-sheet loading, and missing-sheet validation.
- Added protections against mapping one source column to multiple internal fields.
- Implemented baseline redaction for emails, URLs, North American phone numbers, common street addresses, and unit numbers.
- Documented the privacy boundary, baseline limitations, and validation plan.
- Changed the dashboard preview to remove the raw comment column and display only redacted text.
- Created a reproducible 1,000-row fictional hearing dataset with six planted themes, three hearing dates, subgroup fields, and controlled redaction examples.
- Added the sample generator and data dictionary.
- Expanded the automated suite from 5 tests to 22 tests; all 22 passed.

### Validation evidence

- The sample loader processed 1,000 rows and recognized all three hearing dates.
- Baseline redaction detected 79 emails, 79 phone numbers, 84 street addresses, and 84 unit numbers in the controlled sample.
- The safe-preview regression test confirms the original sensitive comment text is absent from the display table.

### GitHub commits

- `8d8e86a` Improve CSV encoding and XLSX sheet handling
- `a314553` Add baseline contact and address redaction
- `8b21006` Add reproducible synthetic hearing dataset
- `cd6c0dc` Protect raw comments in dashboard preview

### Remaining work

- Add personal-name and broader location detection to the redaction pipeline.
- Install and launch Streamlit, then complete a browser-level upload test.
- Begin the theme-clustering pipeline and its validation approach.
- Draft the methodology and limitations page.

## September 17 2026

**Focused task:** Add and test personal-name redaction in the existing preview.
**Status:** Initial implementation and local verification complete; Vamshi approved publication in focused commits.
**Actual time:** Recorded separately by Vamshi in Jibble; no hours inferred here.

### Completed outputs

- Added local English PERSON detection with spaCy 3.8.16 and model `en_core_web_sm` 3.8.0.
- Combined original-text name and pattern spans before replacement, including overlapping detections.
- Added model-resource caching, batched processing, and readable errors that block preview on detection failure.
- Updated the preview's warning and redaction summary, setup instructions, and redaction design.
- Added fictional name cases, a reproducible validation report command, and pipeline/app regression checks.

### Validation evidence

- All 35 automated tests passed, including the previous 23 tests and 12 added name/app checks.
- Streamlit's in-process runner verified PERSON markers in the preview and no preview/success message on model failure. No browser upload test was performed for this change.
- The expanded 22-case fixture fully removed 16 of 18 expected name mentions. One of six name-free controls was incorrectly redacted.
- The 1,000-row sample fully removed 67 of 79 planted names. Inspection found 45 false-positive removals of the word `Broken`.
- Existing sample totals remained 79 emails, 79 phones, 84 street addresses, and 84 unit numbers.
- Dependency consistency and whitespace checks passed.

### Remaining limitations

Names are not always detected, and ordinary words can be removed incorrectly. The recorded misses include a hyphenated/apostrophized full name and a contextual first name. Continue using fictional data; full privacy validation and broader location coverage are unfinished. The validation fixtures were used during development and are not an independent benchmark.

The daily evidence record and detailed JSON report are saved locally outside the repository. Vamshi approved committing and pushing today's work in separate, focused steps.

## September 18 2026

**Scope:** Three small documentation tasks, each in a separate local commit.
**Actual time:** Recorded separately by Vamshi in Jibble; no hours inferred here.

### Task 1 - Upload and preview user guide

- Added a walkthrough covering startup, CSV/XLSX selection, column mapping, and preview interpretation.
- Included the sample's exact headers and the need to change the default comment-column selection.
- Checked labels, cleaning order, row limits, and preview boundaries against the current app and ingestion source.
- Linked the guide from the README. This task changes documentation only.
