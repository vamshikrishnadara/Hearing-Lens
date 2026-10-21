# Upload and setup troubleshooting

Use fictional files while troubleshooting. Start with the
[user guide](user_guide.md) for the normal workflow.

## The app will not start

Run commands from the repository root, in the Python environment used for the
[README setup](../README.md#install-and-run).

| Symptom | What to do |
| --- | --- |
| `No module named pipeline` | Start with `python -m streamlit run app/streamlit_app.py` from the repository root. |
| A dependency such as Streamlit, pandas, or spaCy is missing | Activate the project environment, then run `python -m pip install -r requirements.txt` and restart the app. |
| Name detection is unavailable and no preview appears | In that same environment, run `python -m spacy download en_core_web_sm`, then restart the app and validate the mapping again. The model is a separate setup download. |
| Name detection could not finish | Try a smaller fictional file or shorter comments, then validate again. If it persists, record the message and reproduction steps. |

Do not disable the name check to obtain a preview. The app deliberately stops
display generation when the check cannot run.

## The hosted page says the app is sleeping

A page saying **This app has gone to sleep due to inactivity** is a hosting sleep
screen, not an analysis result. Select **Yes, get this app back up!** once and
allow startup to finish. Initial startup may also prepare model files. If the
page changes to an error, record that message and check the hosting logs.
Waking the upload screen does not establish that a previous slow analysis is fixed.

## The file will not load

| Message or symptom | What to check |
| --- | --- |
| Only CSV and XLSX files are accepted | Export a real `.csv` or `.xlsx` file. Renaming another format's extension does not convert it. Legacy `.xls` files are not supported. |
| The XLSX workbook could not be opened | Open the workbook in a spreadsheet application and save a fresh, unencrypted `.xlsx` copy containing fictional data. |
| The selected sheet or table could not be read, or the file is not a valid table | Check the selected sheet, headers, and file structure. Re-export a simple table; quote CSV comments containing commas or line breaks. |
| The file has column headers but no data rows | Add at least one fictional comment below the header, or choose the sheet containing the data. |
| Windows-1252 warning or unexpected characters | Export the CSV as UTF-8 and upload it again. The Windows-1252 warning alone does not block loading. |
| Blank-header warning or `Unnamed:` columns | Give meaningful headers to columns you need, or omit those columns from mapping. |

## Mapping or counts look wrong

| Message or symptom | What to check |
| --- | --- |
| Each source column can be mapped only once | Choose different columns for comment, date, and ID; set unused optional fields to **Not provided**. |
| No usable comments remain after empty rows are removed | Check **Comment text**. The selected column must contain nonempty responses. |
| IDs appear where comments should be | Change **Comment text** to the response column. It initially selects a column named exactly `comment_text` when available, otherwise the first source column. Always review the selection. |
| Fewer usable comments than expected | Empty comments are removed first. If an ID is mapped, repeated nonempty IDs keep only their first usable row. Also check for the 5,000-row limit notice. |
| Only 20 comments appear | The display intentionally shows the first 20 usable comments. The success count describes the full usable set within the row limit. |
| Dates, IDs, or subgroup columns are absent from the preview | These mapped fields are intentionally excluded from the displayed table. |
| Preview disappears after changing a selection | Click **Validate mapping** again to regenerate the result for the new settings. |

## Redaction or expected features look wrong

Automatic redaction can miss names and identifiers, and can replace ordinary
words incorrectly. A successful preview is not a guarantee of anonymity.
Record a fictional example of the problem and consult the
[measured limitations](redaction_design.md). Do not use real personal data in
an issue, screenshot, or example file.

The five analytical tabs appear after
**Validate mapping** and **Analyze comments**.
If analysis cannot finish, install the models listed in the
[analytical-core guide](analytical_core.md), restart the app and retry.
Error details containing uploaded text are not shown. Old analysis is cleared
before retrying, so a failed run cannot leave stale findings on screen.

If results disappear after a file, sheet or mapping change, validate the new
mapping and analyze again. If quote alternatives are absent, the theme did not
produce additional eligible candidates. Review checkboxes are session-only;
replacing a quote resets the affected theme's review confirmation.

If sentiment or emotion charts are absent, check the scored/excluded
counts. A single-period timeline means no date/hearing field was mapped;
uncertain dates become categorical hearing labels rather than being discarded.

## Analysis is slow or does not finish

1. Note the exact status, such as **Grouping related comments into themes** or
   **Analyzing sentiment**. Do not repeatedly click Analyze or open parallel runs.
2. If the message says another analysis is active, the new request waits at most
   30 seconds before returning. It does not cancel the earlier job. Closing a
   browser tab alone does not establish that server computation stopped.
3. The app operator can open **Manage app** and inspect console logs. Find
   `hearing_lens.analysis` lines: `event=started`, `event=finished seconds=...`
   and `event=failed`. A started stage without a finish locates the wait; it
   does not by itself distinguish computation, throttling, memory pressure or
   interruption. Use host resource/error messages to investigate the cause.
4. If startup or dependency installation failed, resolve that error before a
   new upload. A working upload page alone does not validate model inference.
   The cloud deployment uses Python 3.12 and `deployment/cloud_app.py`.
5. After resolving an error or restarting an unresponsive app, begin with
   20-60 fictional comments. Verify results and downloads before trying larger
   input. Restarting loses session inputs/results; retain the original file.

First runs can load models and compile clustering routines. Local performance
is not a hosted speed guarantee. A throttle message concerns the host's resource
allocation; copying the same file into several sessions can add more work.
Record only stage names, elapsed times, safe error details and fictional inputs.
Never publish uploaded text, access tokens or session cookies in an issue.

## Word or PDF download is missing

Reports appear only after successful analysis. Scroll below the five panels,
select **Prepare Word brief** or **Prepare PDF brief**, and then the matching
**Download** button. The first click prepares the file; it does not save it to
your computer. Changing inputs or selected quotes clears previous downloads.
Prepare them again from the new results.

If PDF reports unsupported characters or cannot fit one page, use the editable
Word format and check its layout. PDF errors do not indicate that a previous
analysis was wrong. A generic preparation error requires operator investigation;
no partial file is offered. If the PDF controls are absent entirely, check that
the deployed app has the revision containing them and that its rebuild succeeded.

## Record a reproducible issue

Include the app revision, file type, sheet name if relevant, selected mappings,
steps taken, expected result, and actual message or behavior. Attach only a
small fictional example. Do not copy real uploaded comments into issue reports.

## Optional inputs and downloads

If Analyze comments is disabled, correct the enabled reference or select
No reference. The CSV needs group/share headers, unique categories and shares
totalling 100%; use 0.6 or 60%, not 60. A blank reference is not a valid baseline.
No subgroup fields means the Representation tab explains how to map them.
Suppressed counts intentionally remain blank and cannot be restored by a download.

Response text changes clear previous results. Re-run analysis before downloading.
An absent response leaves question priorities unverified; a possible match still
needs inspection. Shorten responses over 1,000 usable sentences if analysis fails.

If a labeled download cannot be prepared, validate the input and analyze again.
No partial CSV is offered. Downloaded comments are automatically redacted but
should still be inspected before sharing. Leading apostrophes on formula-like
text are deliberate spreadsheet protection.
