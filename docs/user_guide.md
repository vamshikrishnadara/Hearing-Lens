# Upload and analysis dashboard user guide

This guide covers the current development preview. Use fictional test data:
automatic redaction can miss identifiers and remove ordinary words incorrectly.
The app displays Themes, Sentiment and emotion, Timeline, Representation and
Questions tabs, with an in-memory labeled CSV download.

## 1. Start the app

Complete the [README setup](../README.md#install-and-run), including the English
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
interface does not write them to files or a shared result cache. The download
button offers an explicit export to your own device.

## 6. Review supporting quotes

Read each theme label and selected quote for relevance and visible identifiers.
When alternatives are available, select one to preview its redacted text, then
click **Use this quote**. Only candidates from that theme can be chosen. The
replaced quote becomes an alternative, so the choice is reversible.

Use the checkbox to mark a theme and its selected quotes reviewed. Swapping a
quote resets that theme's checkbox; other themes keep their review choices.
Running analysis again resets all choices. Choices last only in the current
session. They are not a guarantee of anonymity or a measure of model accuracy.


## 7. Explore sentiment and emotion

The **Sentiment and emotion** tab displays overall model-label counts and
percentages, followed by a summary for each theme. Percentages use scored
comments only. Excluded-language and empty inputs are counted separately and
are never assigned a substitute neutral label. Long-input truncation is reported.

The mean sentiment score averages positive minus negative model probability
and ranges from -1 to +1. Emotion ties remain explicit instead of choosing a
winner arbitrarily. A theme with no scored comments shows unavailable values.
These model estimates describe expressed tone; they do not measure agreement
with a proposal or infer a person's characteristics.

If no comments can be scored, the tab explains the exclusion and does not draw
zero-valued sentiment or emotion charts. Each displayed distribution has a
numeric table with the same denominator.

## 8. Explore the timeline

The **Timeline** tab shows mean sentiment and stacked theme counts by period,
with period and theme-count tables beneath the charts. Dates use UTC calendar
days. Periods without scored comments leave gaps in the dated sentiment line.
Comments with missing dates remain in the tables and volume chart, but cannot
be positioned on the dated trend.

When the mapped values are hearing labels or cannot all be parsed as dates,
they appear as categories in input order with a bar chart. No chronological
trend is inferred from these labels. With no mapped date/hearing field, a single
summary appears with an explanation that it cannot show change over time.

Theme volumes count assigned comments, including ungrouped comments. They can
differ from the period's total comments if text was excluded from theme analysis.
Changing tabs or reviewing quotes reuses the current analysis rather than running
models again. Changing the input or mapping clears every results tab.

## 9. Add optional references and response text

After validating the mapping, expand **Optional reference values and response
text**. For each mapped subgroup, choose **No reference**, **Enter reference**
or **Upload reference CSV**. A reference uses `group,share` column headers,
with one category and share per row. For example, a fictional reference is:

```csv
group,share
Example A,60%
Example B,40%
```

Shares must total 100%. Use proportions such as `0.6` or explicit percentages
such as `60%`; bare `60` is invalid. Category labels must be unique ignoring
case and surrounding spaces. The uploaded reference has a 5,000-group limit.
Only supply reference values appropriate to your comment categories and context;
the app does not select or retrieve a population baseline. Invalid or missing
entries in an enabled reference block analysis until corrected or set to
**No reference**. CSV category codes retain leading zeros.

Paste an optional response in **Response text (optional)**. The limit is
100,000 characters and 1,000 usable sentences. Text is redacted before matching.
Response similarity only suggests a passage to inspect; it is not proof that
the question was answered. No response means unverified follow-up priorities.

Changing a reference or response clears results and downloads immediately.
Click **Analyze comments** to use the new inputs. Changing the main input or
column mapping also clears optional inputs; validate and enter them again.

## 10. Read representation results

Each field has a category table with counts, participation shares, supplied
reference shares, gaps in percentage points, ratios and status. Shares use
known category values; missing-value coverage is shown separately. Without a
reference, the panel shows counts and shares only. Unmatched categories have
no gap or ratio; a zero reference has no ratio.

Groups with fewer than 10 comments have counts and derived figures suppressed.
An additional group can be hidden to prevent recovering a small count by
subtraction. Suppressed values remain blank, not zero. Supplied labels and
reference percentages stay visible. Do not map identifiers as subgroup fields.
Counts describe comments, not necessarily unique people.

## 11. Read questions and possible responses

The **Questions** tab shows up to three suggested follow-up priorities, a ranked
summary and expandable groups. Each group displays the actual representative
question, supporting-comment count and response comparison status. Possible
response passages are shown next to their question wording for inspection.
No match, partial match and possible match are distinct from a verified answer.

Ranking uses supporting-comment frequency, then visible subgroup spread and
a wording tie-break. Visible field/category pairs are not a count of people;
small or missing categories can make spread a lower bound. An empty candidate
list does not establish that all concerns or requests have been answered.

## 12. Download labeled comments

Use **Download labeled CSV** below the panels. Each row corresponds to the
cleaned input order and includes a comment number, redacted comment text, theme
ID/label/status, sentiment, emotion, score, affect status/truncation, question
count and question-group IDs. Excluded scores stay blank. Theme ID `0` means
ungrouped; a blank ID with `excluded` status means no theme assignment.

Respondent IDs, dates and subgroup values are not included. Row numbers refer
to the cleaned table, not original spreadsheet rows. This export contains
comment labels, not quote selections or review checkbox state. Automatic
redaction can miss identifying details; inspect the CSV before sharing it.
Formula-like text is prefixed with an apostrophe to reduce spreadsheet formula
execution. Numeric negative sentiment scores remain numeric. UTF-8 with a BOM
supports common spreadsheet readers. Generation occurs in memory, and failures
do not offer a partial file.

## 13. Prepare a community Word brief

Below the dashboard, select **Prepare Word brief**, then **Download Word brief**.
The one-page summary includes leading themes with quote excerpts, sentiment,
available time and representation comparisons, and follow-up questions. It uses
the current selected quotes. Changed inputs or quote selections remove the old
download; prepare it again to include the changes. Read the document before
sharing, especially shortened passages and possible identifiers. See the
[brief guide](community_brief.md) for selection rules and limitations.
