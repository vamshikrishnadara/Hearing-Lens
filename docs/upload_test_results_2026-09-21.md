# Upload and preview browser test results - September 21, 2026

Executed by Codex for Vamshi Krishna Dara using the Codex in-app browser against
the local app at `http://127.0.0.1:8501`. Application revision: `2b22f2e`.
These are actual browser interactions with fictional uploads, not only source
inspection or Streamlit's in-process runner.

## Environment and fixtures

- macOS 26.6.2 (Apple silicon), Python 3.12.14.
- Streamlit 1.64.0, pandas 2.3.3, openpyxl 3.1.5.
- spaCy 3.8.16 with `en_core_web_sm` 3.8.0.
- Used the six-row fictional CSV in the [checklist](manual_test_checklist.md),
  a two-sheet XLSX containing Responses and Other, an all-empty-comment CSV,
  a header-only CSV, and the repository's 1,000-row fictional sample.
- The XLSX fixture was generated with pandas/openpyxl, rather than manually
  saved in a spreadsheet application; its values match the checklist.
- Fixtures, browser-state captures, screenshots, and daily PDF evidence are
  stored locally outside the repository in `daily-evidence/2026-09-21/`.

## Results

| Case | Result | Observed behavior |
| --- | --- | --- |
| 1. CSV upload and mapping | Pass | `comment_text` selected automatically. Date, ID, and ward mapped. Four usable comments; one empty row and one repeated ID removed. Both missing-ID rows retained. |
| 2. Preview boundary | Pass after correcting checklist wording | Four rows and only the `comment_text` data column. Email replaced with `[EMAIL_ADDRESS]`; no raw email, ID, date, or ward columns displayed. Other small-fixture text remained readable and unchanged. |
| 3. Optional mappings | Pass | Date and ID set to Not provided and subgroups empty. Five usable comments, one empty row removed, both responses sharing TEST-001 retained. |
| 4. Reused column | Pass | Reusing `comment_text` for respondent ID produced “Each source column can be mapped only once.” No success message or preview. |
| 5. XLSX sheet selection | Pass | Responses produced the same four-comment count and removal notices as CSV. Switching to Other produced one usable comment: “Please add art classes.” |
| 6. Empty comments | Pass | “No usable comments remain after empty rows are removed.” No successful preview. |
| 7. Header-only file | Pass | “The file has column headers but no data rows.” No mapping controls or preview. |
| 8. Larger sample | Pass for workflow/display scope | 1,000 usable comments and 438 replacement matches reported. Preview contained one data column and ended at row index 19 (20 comments). |

An additional browser check confirmed that the initial comment-column selection
can be changed manually and restored. The final small-CSV recheck again showed
four usable comments and the `[EMAIL_ADDRESS]` marker.

## Findings and correction

The original case 2 expected `[EMAIL]`, but the implemented marker and browser
output are `[EMAIL_ADDRESS]`. Corrected the checklist to match the existing
behavior; no application code was changed. Final outcome: eight workflow cases
passed, with one documentation correction and the known redaction limitation
below. This is not a claim that redaction is fully accurate.

The larger sample visibly reproduced the previously documented false positive:
“Broken exterior lighting...” appeared as “[PERSON] exterior lighting...”. Name
detection can still miss identifiers or remove ordinary words. Do not treat a
passing workflow check as proof of anonymity. See [redaction limitations](redaction_design.md).

One workbook validation click during a mapping rerun did not produce a result;
after the controls settled, clicking Validate mapping produced the expected
result. Recorded as a browser-test interaction timing observation, not a
confirmed application defect.

The local server initially needed to be started and granted permission to bind
to localhost. These setup steps preceded testing. No new processing defect was
identified within this checklist's scope.

## Follow-up

Investigate the known name-detector misses and false positives as a separate
task. The full automated suite was not rerun for this documentation-only change;
the last recorded suite result is 39 passing tests on September 19. Actual work
hours are recorded separately in Jibble.
