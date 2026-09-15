# Hearing Lens Data Schema

This document defines the fields accepted from a user export and the normalized names used inside the application. The only required input is a column containing one open-text comment per row.

## User input fields

| Field | Required | Accepted content | Use |
| --- | --- | --- | --- |
| Comment text | Yes | A public comment, survey answer, or meeting note | Themes, quotes, sentiment, emotion, and question detection |
| Date or hearing label | No | A date, timestamp, meeting name, or comment-period label | Timeline and comparisons across periods |
| Respondent ID | No | A stable identifier supplied by the source system | Removal of repeat submissions |
| Subgroup fields | No | Respondent-supplied categories such as ward, ZIP, role, language, tenure, age bracket, or school | Participation and representation analysis |
| Agency response | No | Official response, summary, or FAQ text | Optional unanswered-question matching |
| Reference distribution | No | A separate two-column table containing group and population share | Representation gap calculations |

## Normalized internal fields

| Internal field | Type | Rule |
| --- | --- | --- |
| `comment_text` | String | Trim whitespace and remove empty rows. Keep unredacted text only in memory for modeling. |
| `date_or_hearing` | Date or string | Parse as a date when reliable; otherwise treat as a categorical period label. |
| `respondent_id` | String | If supplied and non-empty, retain the first row for a repeated identifier. |
| `subgroup__<source>` | String | Preserve the respondent-supplied category. Do not infer missing values. |
| `source_row` | Integer | Preserve the original row number in later pipeline versions for traceability. |

## Validation behavior

1. Accept `.csv` and `.xlsx` files only.
2. Read UTF-8 CSV files by default and support Windows-1252 with a conversion notice.
3. Use the first workbook sheet by default but allow the user to select another sheet.
4. Require the mapped comment column to contain at least one non-empty value.
5. Analyze at most 5,000 rows in the MVP and display a notice when rows are omitted.
6. Drop empty comments before analysis.
7. Deduplicate on a mapped respondent ID only when the identifier is present and non-empty.
8. Treat subgroup fields as optional. Missing subgroup data must disable the representation panel without blocking the rest of the analysis.
9. Never infer demographic attributes from names or text.

## Representation reference format

The optional reference distribution is a separate CSV with exactly two mapped concepts:

| Field | Example | Validation |
| --- | --- | --- |
| Group | `Renter` | Non-empty category name |
| Share | `0.62` or `62%` | Numeric value normalized to a proportion from 0 through 1 |

Group labels should be matched after trimming whitespace and normalizing capitalization. Unmatched groups must be shown to the user rather than silently removed.

## Privacy boundary

Uploads are session data, not application content. The production application must not save the raw file, raw comments, or uploaded filenames to server storage or logs. Redaction must occur before any quote is displayed or exported. Modeling may use unredacted comment text only in memory during the active run.
