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

### Task 2 - Troubleshooting reference

- Added startup, missing-model, file-format, encoding, mapping, and count troubleshooting.
- Explained expected preview restrictions and how to record issues using fictional examples.
- Cross-checked the described errors and recovery steps against the loader, app, redaction behavior, and existing setup instructions.
- Linked the reference from the README. No runtime behavior changed.

### Task 3 - Reusable manual testing checklist

- Added eight manual cases with a six-row fictional CSV fixture, XLSX preparation steps, expected outcomes, and blank result fields.
- Covered normal upload, preview boundaries, optional mappings, duplicate mapping, sheet switching, empty comments, header-only input, and the 20-row display limit.
- The checklist is unexecuted; its unchecked boxes are not evidence that browser tests passed today.
- Today's verification checks documentation against source, the fixture's expected cleaning counts, relative file links, and whitespace. No application code was changed.
- Daily PDF evidence is stored locally outside the repository. Today's three commits require Vamshi's approval before pushing.

## September 19 2026

**Focused task:** Select the comment column automatically when the exact
`comment_text` header is available, while keeping manual selection available.
**Actual time:** Recorded separately by Vamshi in Jibble; the planned two-hour
session is not a claim of hours worked.

### Completed outputs

- Updated the comment dropdown to prefer `comment_text`; files without that exact header keep the first-column default.
- Added field help explaining the default and the ability to change it.
- Updated the README, user guide, troubleshooting reference, and manual checklist to match the new behavior.
- Added four app-level regression tests covering the included CSV sample, XLSX sheet selection, other headers, and manual overrides across reruns.

### Validation and boundaries

- All 39 automated tests passed, including the four new mapping tests.
- App checks used Streamlit's in-process test runner with fictional in-memory uploads. No browser-level upload test was performed today.
- Whitespace and documentation file-link checks passed.
- This chooses a default based on an exact header, not comment contents or other possible header names. Users still need to review their mapping.
- Existing redaction limitations remain; this task makes no claim of improved name detection or anonymity.

Implementation, tests, and documentation are kept in one focused local commit.
Push requires Vamshi's approval. A short daily evidence PDF is saved locally
outside the repository.

## September 21 2026

**Task:** Execute the upload and preview checklist in the browser using fictional files.
**Activity:** Design a Data Dashboard.

- Completed all eight checklist cases in the Codex in-app browser against local application revision `2b22f2e`.
- Verified CSV/XLSX uploads, sheet switching, automatic/manual column selection, empty-row removal, ID deduplication, mapping errors, and preview boundaries.
- Observed 1,000 usable comments, 438 redaction matches, and a 20-comment preview for the larger sample.
- Corrected the checklist's email marker from `[EMAIL]` to `[EMAIL_ADDRESS]` and rechecked the small CSV preview.
- Recorded the existing false-positive removal of “Broken” as an unresolved name-detection limitation. No application code changed.
- Saved [browser test results](upload_test_results_2026-09-21.md); fictional files, screenshots, and daily PDF evidence remain local outside the repository.
- Final workflow outcome: eight cases passed after one checklist correction. Automated tests were not rerun for this documentation-only change; these results concern actual browser testing.

Changes are separated into three local documentation commits: the checklist
correction, browser test report, and this daily work-log update. Each push
requires Vamshi's approval. Actual time is maintained separately in Jibble.

## September 22 2026

**Task:** Investigate and correct the known `Broken exterior lighting` false positive.
**Activity:** Analyze Open-Ended Responses.

- Reproduced 45 incorrect `Broken` replacements in the unchanged 1,000-row sample.
- Added six fictional validation cases and extended the reproducible report command.
- Added a phrase-specific exception and four regression tests; no model change or general word allowlist.
- All 43 automated tests passed. The six focused examples now all match their expected outputs (previously three).
- Incorrect `Broken` replacements in the sample fell to zero; planted-name coverage stayed at 67 of 79 and contact/address counts stayed unchanged.
- Documented the before/after comparison and remaining limitations, including the different `Broken windows` context and known name misses.
- No browser testing was performed today. JSON reports, test output, and PDF evidence are saved locally.

Work is separated into three commits: validation examples/reporting, correction
with tests, and documentation. Each push requires approval. Actual working time
is recorded separately in Jibble.

## September 23 2026

**Task:** Build and validate the first local theme-analysis pipeline.
**Activity:** Analyze Open-Ended Responses.

- Added MiniLM embeddings, deterministic K-means grouping, TF-IDF keyword labels, counts/shares, row assignments, and up to three redacted candidate quotes per theme.
- Added explicit model setup and local-only inference, input checks, failure handling, and duplicate/length filtering for quotes.
- All 55 automated tests passed, including 12 theme tests. Dependency consistency passed.
- The 1,000-row fictional sample produced six groups and 15 candidate quotes in one measured 4.075-second run; two groups had fewer than three eligible quotes.
- The adjusted Rand index was 0.1861; manual inspection confirmed mixed topics. This is an initial baseline, not completion of Week 2's quality benchmarks.
- A separate six-comment library/bus fixture split into two coherent groups, each with three quotes.
- Recorded [setup, results, and limitations](theme_prototype.md). Ground-truth sample categories were used only after clustering to evaluate results.
- No Streamlit theme panel or browser test was added today. The two public corpora, BERTopic path, and other remaining requirements are documented.

Three local commits separate implementation/tests, the validation command, and
documentation. Push each only after approval. Daily JSON results, test output,
and PDF evidence remain local. Actual work hours are recorded separately in Jibble.
