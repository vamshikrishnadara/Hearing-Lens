# Upload and setup troubleshooting

Use fictional files while troubleshooting. Start with the
[user guide](user_guide.md) for the normal workflow.

## The app will not start

Run commands from the repository root, in the Python environment used for the
[README setup](../README.md#local-setup).

| Symptom | What to do |
| --- | --- |
| `No module named pipeline` | Start with `python -m streamlit run app/streamlit_app.py` from the repository root. |
| A dependency such as Streamlit, pandas, or spaCy is missing | Activate the project environment, then run `python -m pip install -r requirements.txt` and restart the app. |
| Name detection is unavailable and no preview appears | In that same environment, run `python -m spacy download en_core_web_sm`, then restart the app and validate the mapping again. The model is a separate setup download. |
| Name detection could not finish | Try a smaller fictional file or shorter comments, then validate again. If it persists, record the message and reproduction steps. |

Do not disable the name check to obtain a preview. The app deliberately stops
display generation when the check cannot run.

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

Theme summaries, sentiment, representation charts, timelines, and full report
exports are planned features. Their absence is expected in this version.

## Record a reproducible issue

Include the app revision, file type, sheet name if relevant, selected mappings,
steps taken, expected result, and actual message or behavior. Attach only a
small fictional example. Do not copy real uploaded comments into issue reports.
