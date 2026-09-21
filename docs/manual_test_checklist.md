# Upload and preview testing checklist

This is a reusable manual checklist, not a record of completed tests. Leave
boxes unchecked until a case has been run. Use only fictional data. Copy this
page into a local evidence folder for each run and record actual results there.

## Run details

- Date and tester:
- Commit tested:
- Python, Streamlit, spaCy, and English model versions:
- Browser and operating system:
- Overall result: Not run / Pass / Fail / Blocked
- Evidence location:

Follow the [setup and user guide](user_guide.md). Keep the development warning
visible. If setup fails, use [troubleshooting](troubleshooting.md) and mark the
affected cases blocked rather than passed.

## Prepare a small fictional file

Save this text as UTF-8 `upload_check.csv` outside the repository. There are six
data rows; the empty comment and missing IDs are intentional.

```csv
respondent_id,comment_text,hearing_date,ward
TEST-001,Please add library hours.,2026-09-18,1
TEST-001,Please keep the library open later.,2026-09-18,1
TEST-002,,2026-09-18,2
TEST-003,Contact demo@example.org about library hours.,2026-09-18,2
,Please add weekend activities.,2026-09-18,3
,Please improve classroom supplies.,2026-09-18,3
```

For XLSX testing, open this CSV in a spreadsheet application. Save its table
as sheet **Responses** in `upload_check.xlsx`. Add a second sheet **Other**
with the same four headers and one row:
`TEST-004`, `Please add art classes.`, `2026-09-18`, `4`.
Save both files locally. Do not merely rename the CSV extension.

## Basic cases

For each case, record Pass, Fail, or Blocked and the observed counts/messages.

- [ ] **1. CSV upload and mapping.** Upload `upload_check.csv`. Confirm that
  **Comment text** initially selects `comment_text`. Set **Date or hearing label** to
  `hearing_date`, **Respondent ID** to `respondent_id`, and subgroup to `ward`.
  Click **Validate mapping**. Expect **4 usable comments**, **1 empty comment
  removed**, and **1 repeated respondent ID removed**. Both missing-ID rows
  remain. Actual result / evidence:

- [ ] **2. Preview boundary.** Using case 1, inspect the table. Expect only
  `comment_text`, four rows, and `[EMAIL_ADDRESS]` instead of `demo@example.org`.
  IDs, date, and ward must not appear as table columns. Review other text for
  incorrect replacements; record them rather than assuming all redaction is
  correct. Actual result / evidence:

- [ ] **3. Optional mappings.** Set date and ID to **Not provided**, clear
  subgroups, and validate again. Expect **5 usable comments** and **1 empty
  comment removed**. Both TEST-001 responses remain because ID-based removal
  is disabled. Actual result / evidence:

- [ ] **4. Reused column error.** Set **Comment text** and **Respondent ID**
  both to `comment_text`, then validate. Expect **Each source column can be
  mapped only once.** and no successful preview for this attempt. Restore the
  valid mapping afterward. Actual result / evidence:

- [ ] **5. XLSX sheet selection.** Upload `upload_check.xlsx`, choose
  **Responses**, map as in case 1, and validate. Expect the same counts as
  case 1. Select **Other**, check the mappings, and validate again. Expect
  **1 usable comment** about art classes. Actual result / evidence:

- [ ] **6. No usable comments.** Make a separate CSV copy with all six comment
  cells empty, keeping headers and other values. Upload it, map
  `comment_text`, and validate. Expect **No usable comments remain after
  empty rows are removed.** and no successful preview. Actual result / evidence:

- [ ] **7. Headers without rows.** Make another CSV containing just the header
  line. Upload it. Expect **The file has column headers but no data rows.**
  and no preview. Actual result / evidence:

- [ ] **8. Larger sample preview.** Upload the repository's
  [1,000-row fictional sample](../data/samples/synthetic_chicago_hearing.csv)
  and use the [sample mappings](user_guide.md#3-map-the-columns). Expect a
  table showing only the first 20 usable comments. Record the full usable
  count and replacement count from the notices; replacements are counted
  across all usable comments, not just those displayed. Actual result / evidence:

## Finish the record

- Cases passed / failed / blocked / not run:
- Unexpected behavior and smallest fictional reproduction:
- Screenshots or notes saved locally:
- Next action:

This basic checklist does not establish complete privacy protection, model
accuracy, performance, or coverage of all file formats and edge cases. Keep
the [redaction limitations](redaction_design.md) alongside the results.
Do not mark a case passed solely because the source code describes it.
