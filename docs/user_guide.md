# Upload and Themes dashboard user guide

This guide covers the current development preview. Use fictional test data:
automatic redaction can miss identifiers and remove ordinary words incorrectly.
The app runs the complete analysis and displays the Themes panel. Sentiment, emotion, representation, timeline and question dashboard views are still being built.

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
[synthetic_theme_benchmark.csv](../data/samples/synthetic_theme_benchmark.csv).

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

**Comment text initially selects a column named exactly `comment_text` when
available, so the included sample starts with the correct selection.** Otherwise,
it selects the first source column. This is a header-based default, not a check
of the responses. Review the selection and change it in the dropdown if needed;
other header names must be selected manually when they are not the first column.

For your own fictional file, select the corresponding headers. Leave optional
date and ID fields at **Not provided** when absent, and leave subgroup fields
empty if unused. Each source column can be mapped only once. Date values are
retained as supplied; the analysis uses dates or hearing labels when available. CSV text codes such as `00123` retain their leading zeros.

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
Old results and review choices are cleared automatically when the file contents,
workbook sheet or selected columns change. Removing the upload also clears them.

## 5. Run analysis and view themes

Click **Analyze comments** after validating the mapping. Install the local models
using the [analytical-core setup](analytical_core.md) before running analysis.
The first run can take longer while models load. Analysis runs only when clicked;
changing a review choice does not rerun the models.

The Themes panel shows the number of analyzed comments, theme groups and
ungrouped comments. Each theme includes its label, count, percentage and up to
three supporting quotes. Percentages use the theme-analysis comment total,
including ungrouped comments; excluded comments are reported separately.
Shortages and analytical warnings remain visible. No missing quotes are invented.
The displayed source number refers to the cleaned table, not an original sheet
row number or respondent ID. Quotes may be sentence excerpts.

If analysis fails, no old or partial analysis is displayed. Check model setup
and try again. Uploads and analytical results remain in session memory; this
interface does not write them to files or a shared result cache. Other analytical
modules run internally but their dashboard panels are not yet available.

## 6. Review supporting quotes

Read each theme label and selected quote for relevance and visible identifiers.
When alternatives are available, select one to preview its redacted text, then
click **Use this quote**. Only candidates from that theme can be chosen. The
replaced quote becomes an alternative, so the choice is reversible.

Use the checkbox to mark a theme and its selected quotes reviewed. Swapping a
quote resets that theme's checkbox; other themes keep their review choices.
Running analysis again resets all choices. Choices last only in the current
session and are not exported or saved as project human-validation evidence.
They are not a guarantee of anonymity. The separate human-validation exercise
still requires its own completed review records.
