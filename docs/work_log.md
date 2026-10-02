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

## September 24 2026

**Task:** Refine theme grouping and compare it with the original prototype.
**Activity:** Analyze Open-Ended Responses.

- Investigated repeated introductory wording in the unchanged fictional sample.
- Added experimental sentence-frequency weighting while retaining the original whole-comment mode for comparison. Full redacted quotes and quote eligibility rules are preserved.
- Added seven behavioral regression tests; all 62 automated tests passed, including the real local model check.
- Added a reproducible comparison command with the original 1,000-comment sample and a separate 24-comment fixture.
- Development-sample ARI increased from 0.1861 to 0.2647, with six groups and 15 candidate quotes in both modes. Mixed groups and vague labels remain; this is not an accuracy percentage or independent quality certification.
- Both methods preserved all 12 introduction/no-introduction pairs in the new fixture and produced the expected three groups there. The earlier six-comment smoke check also still passes.
- Reviewed selected redacted quotes and recorded [results and limitations](theme_grouping_review_2026-09-24.md). Known redaction misses and the public-corpus validation gap remain.
- No interface change or browser test was performed. Week 2 and supervisor review gates remain incomplete.

Three local commits separate the improvement and regression tests, reproducible
comparison, and documentation. Each push requires approval. Daily PDF evidence,
JSON reports, and test output are stored locally outside the repository. Actual
hours are recorded separately in Jibble.

## September 25 2026

**Task:** Prepare the first small public corpus and review its theme results.
**Activity:** Analyze Open-Ended Responses.

- Verified the official CFPB archive and documented the published-data reuse basis and sampling limitations.
- Added a deterministic, offline preparation utility. Selected 100 nonempty 2017 narratives from 115,311 eligible unique records, with seed 20260925 and no length/product filter. Recorded source/sample hashes and provenance locally.
- Added a validation command that checks sample consistency and sends only comment text to the existing theme engine. Public narratives, complaint IDs, and detailed review reports remain local.
- The unchanged pipeline assigned all 100 comments to six groups and selected ten quotes in 6.774 seconds in one local run including model loading. Only two groups have three eligible quotes.
- Reviewed five full redacted members of each of the three largest groups and all ten selected quotes. This was assistant-assisted development review, not independent human coding or supervisor sign-off.
- Identified all-X source masks in four keyword lists/labels, long-comment quote gaps, mixed groups, a singleton, and ordinary-word false positives in the unit-number pattern. No runtime pipeline fix was claimed or made today.
- All 69 automated tests passed, including seven new preparation/validation checks using fictional data. Recorded [aggregate results and next fixes](cfpb_validation_2026-09-25.md).
- No browser test or new dependency installation was needed. The federal corpus and other analytical requirements remain outstanding.

Three local commits separate sample preparation/source notes/tests, the validation
command/tests, and findings/project documentation. Each push requires approval.
Daily evidence is saved locally outside the repository. Actual time is recorded
separately in Jibble; no hours are inferred from the work described here.

## September 28 2026

**Task:** Correct unit-number redaction of ordinary words and verify the result.
**Activity:** Analyze Open-Ended Responses.

- Reproduced the unit-prefix problem found during the CFPB review. Final inspection confirmed 17 ordinary-text matches across 12 of the fixed 100 public narratives.
- Added 28 fictional validation cases and a repeatable report command that prints only aggregate information for public data.
- Tightened label/value boundaries while retaining common numeric and single-letter apartment/suite identifiers. Added support for dotted abbreviations such as Ste. 200.
- All 74 automated tests passed, including five new regression tests. Exact pattern outcomes improved from 13/28 to 28/28; the confirmed public-data errors fell from 17 to zero.
- All 84 planted units and existing email, phone, and street-address detections in the fictional sample remained protected. Name coverage stayed at 67/79; known misses are not resolved.
- Reran public theme analysis and inspected all 12 selected quotes. Restored words changed group assignments and quote availability; grouping quality remains unresolved and the quote-selection algorithm was not changed.
- Documented [comparison results and supported-format limits](unit_redaction_review_2026-09-28.md). No browser test, model change, or new dependency was needed.

Four local commits separate validation cases/reporting, the correction and
regression tests, technical findings, and project progress. Each push requires approval. Daily PDF
and detailed evidence remain local outside the repository.

### Additional task - Clean placeholder keywords

- Excluded all-X tokens of at least three letters from theme keywords and phrases; meaningful words containing X remain eligible.
- All 77 automated tests passed, including three new keyword regression checks.
- On the same 100 public narratives, themes with placeholder keywords fell from four to zero. Assignments, counts, shares, and all 12 selected redacted quotes were identical to the same-day baseline.
- Documented the changed labels and limits in the theme prototype guide. This improves keyword presentation, not clustering quality; quote shortages and mixed groups remain.
- Prepared one additional focused commit, bringing today's total to five. This follow-up push requires separate approval. Its comparison report, test output, and evidence PDF are stored locally.


## September 29 2026

**Task:** Add optional automatic theme counts for small datasets and compare results.
**Activity:** Analyze Open-Ended Responses.

- Added an automatic library option for fewer than 150 input rows, comparing feasible counts from 4 through 12 using Euclidean silhouette scores.
- Preserved the default six-group mode and manual 1-15 selection. Recorded candidate scores, the chosen count, skipped counts, and explicit one-group fallback reasons for inputs that cannot be scored.
- Added 13 behavioral/reporting tests; all 90 automated tests passed, including the existing local-model integration check.
- Added an aggregate-only comparison command and reran the fixed 100-comment CFPB sample. Automatic mode selected six with silhouette 0.040712; the manual result's complete themes and assignments matched September 28 exactly.
- The 24-comment fictional fixture exposed a limitation: automatic selection split three planted topics into 12 pairs, reducing ARI from 1.0 to 0.188235. Recorded this as a limitation rather than a quality improvement.
- Documented behavior, results, and next priorities in the [selection review](theme_selection_review_2026-09-29.md). No UI change, dependency installation, or new public-data collection was performed.
- Remaining theme requirements and analytical-core review gates are not complete.

Four focused local commits separate the implementation and regression tests,
comparison utility and reporting checks, technical usage/findings, and project
progress. Each push requires approval. Personal evidence remains outside the repository.


## September 30 2026

**Task:** Add optional handling for small theme groups and compare the results.
**Activity:** Analyze Open-Ended Responses.

- Added an opt-in merging policy for groups of one or two comments, using a fixed experimental cosine threshold of 0.75 chosen before the comparison.
- Required all cross-pair original group centers to qualify, preventing similarity chains from bridging dissimilar initial groups. Kept groups without a qualifying partner and warned about them instead of removing comments.
- Integrated merge history, initial/final counts, final-to-initial theme mappings, and rebuilt labels, counts, shares, assignments, and quotes. Original selection scores remain explicitly pre-merge.
- Added 16 regression and reporting checks; all 106 automated tests passed. No new dependencies or browser tests were needed for this library-only change.
- Compared merging on/off on the existing 100-comment CFPB sample and 24-comment fictional fixture, in automatic and manual modes. The public sample remained at six groups with the singleton retained; themes and assignments were unchanged.
- The fictional automatic result changed from 12 groups to 11, with 10 small groups remaining. ARI increased from 0.188235 to 0.246628, but substantial over-splitting remains. Manual three stayed unchanged at ARI 1.0.
- Verified no analyzed rows were lost or duplicated, counts/shares matched assignments, and quotes belonged to the correct final themes and matched the redacted originals within the length limit.
- Recorded [policy, results, and limitations](small_theme_review_2026-09-30.md). Threshold calibration, broader corpus validation, BERTopic, and other analytical-core work remain outstanding; no review gate is marked complete.

Four local commits separate the merge policy/tests, pipeline integration/warnings/tests,
comparison utility/report checks, and usage/findings/project documentation. Each push
requires approval. Personal daily evidence remains outside the repository.


## October 1 2026

**Task:** Implement missing analytical-core features and establish an honest gate-status checklist.
**Activity:** Analyze Open-Ended Responses.

- Replanned daily work around the official weekly requirements and recorded Gate 0/1 as pending review.
- Added BERTopic routing at 150 input rows, KeyBERT/MMR labels, explicit density outliers, quote alternatives, and a safe library swap operation. Kept the legacy K-means API defaults for earlier comparisons.
- Added locally cached sentiment/emotion models, batch inference, language exclusions, truncation reporting, and aggregation by theme and period.
- Added timeline summaries and Plotly charts with date, hearing-label, missing-value, and single-period behavior. Visually checked both synthetic chart types.
- Added official federal sample preparation with resumable local checkpoints; download was blocked by HTTP 429. No completed federal sample is claimed.
- Prepared 40 blind human-review rows and 20 explicit federal placeholders, with agreement evaluation that rejects invalid/stale labels and does not invent scores.
- All 133 automated tests passed. Synthetic first/repeat core runs were 17.883/6.664 seconds; CFPB 18.188/17.243 seconds. Results were repeatable, and assignment/count/quote consistency checks passed.
- Documented that quote shortages, language-detection errors, human validation, federal-corpus review, and gate approval remain unresolved. Synthetic BERTopic ARI was 0.232002; no semantic-quality improvement is claimed.
- Prepared focused commits for the catch-up work. The fellow explicitly authorized today's repository pushes. Public narratives, model weights, review sheets, detailed outputs, and personal evidence stay local.


## October 2 2026

**Task:** Close the remaining technical Weeks 1-3 gaps and verify all three corpora.
**Activity:** Analyze Open-Ended Responses.

- Prepared a 300-comment FAA sample through the public Mirrulations archive, with
  provenance and hashes; direct agency API access remains a separate blocked route.
  Expanded the fixed CFPB sample to 300 and retained earlier samples.
- Added a richer 1,000-row fictional benchmark while preserving the original
  short/repetitive stress fixture and disclosing the change in evaluation data.
- Corrected duplicate-vector density fitting, topic reduction counts, and added
  experimental original-space assignment refinement that preserves outliers.
- Added source-traceable sentence excerpts, duplicate filtering, contact-tail
  avoidance, and a context-based contact-name redaction correction.
- Reduced unnecessary quote embedding and affect batch padding. Final repeated
  core runtimes were 5.369s (fictional), 29.044s (CFPB), and 20.636s (FAA), using
  four CPU threads. All main numeric checks passed; CFPB has little timing margin.
- All 150 tests passed. Executed the final notebook on all three main corpora and
  the original stress fixture; documented mixed groups and the old quote shortages.
- Prepared 60 blind review rows and a local review page. The fellow cannot review
  today; zero human labels, no agreement claim, and human theme review pending.
- Updated the board, weekly plan, source notes, public-update drafts, and license
  decision record. Benjamin's formal gate approval is no longer a prerequisite,
  as reported by the fellow. No license was selected or public post claimed.

See the [core validation report](core_validation_2026-10-02.md) and
[theme review](week2_validation_2026-10-02.md). These are technical-development
results, not full completion of all Weeks 1-3 deliverables. Changes are prepared
as focused local commits; pushing awaits the fellow's approval.
