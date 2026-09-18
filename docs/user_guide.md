# Upload and preview user guide

This guide covers the current development preview. Use fictional test data:
automatic redaction can miss identifiers and remove ordinary words incorrectly.
Theme, sentiment, representation, and timeline analysis are not available yet.

## 1. Start the app

Complete the [README setup](../README.md#local-setup), including the English
name-detection model. In the same Python environment, from the repository root:

```sh
python -m streamlit run app/streamlit_app.py
```

Open the local address printed in the terminal. Keep that terminal running.

## 2. Choose a file

Under **Upload a CSV or XLSX file**, choose a `.csv` or `.xlsx` file with column
headers in the first row and a comment in each following row. Prefer UTF-8 for
CSV files. For an XLSX workbook, select the intended **Workbook sheet**; the
first sheet is selected initially.

For a first walkthrough, use the repository's fictional sample:
[synthetic_chicago_hearing.csv](../data/samples/synthetic_chicago_hearing.csv).

The current app loads at most the first 5,000 data rows, before removing empty
comments or repeated IDs. A notice appears when additional rows are omitted.
This is a first-rows limit, not a random sample or an on-screen setting.

## 3. Map the columns

For the included sample, choose:

| App field | Selection | Purpose |
| --- | --- | --- |
| Comment text | `comment_text` | Required response text |
| Date or hearing label | `hearing_date` | Optional date or hearing metadata |
| Respondent ID | `respondent_id` | Optional ID used to remove repeats |
| Subgroup fields (optional) | For example, `ward`, `role`, `language` | Optional supplied metadata |

**Comment text initially selects the first column, which is `respondent_id` in
this sample. Change it to `comment_text` before continuing.** The app does not
automatically decide which column contains meaningful responses.

For your own fictional file, select the corresponding headers. Leave optional
date and ID fields at **Not provided** when absent, and leave subgroup fields
empty if unused. Each source column can be mapped only once. Date values are
retained as supplied; mapping a date does not create a timeline.

## 4. Validate and inspect

Click **Validate mapping**. The app removes empty or whitespace-only comments.
When an ID is mapped, it keeps the first usable comment for each nonempty ID;
rows with missing IDs remain separate. With **Not provided**, ID-based removal
does not run. Review whether this behavior suits your test data.

After name and contact checks succeed, the app reports the usable-comment
count and any removals. Its table shows only the first 20 usable comments after
automatic redaction. IDs, date values, and subgroup fields are excluded from
this display. The replacement count covers all usable comments, not just the
20 shown. A message saying comments are ready for analysis does not mean that
analysis has run.

Review the displayed text for missed identifiers and incorrect replacements.
The app blocks the preview if name detection fails. See the
[redaction limitations](redaction_design.md) for current measurements.

After changing a file, sheet, or mapping, click **Validate mapping** again.
The current workflow ends at the preview; full analytical reports are planned.
