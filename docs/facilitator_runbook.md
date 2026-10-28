# Facilitator runbook

A 90-minute discussion using Hearing Lens to examine feedback, check automated
findings and agree on follow-up questions. Use fictional examples for the current
development preview. This tool supports discussion; it does not decide what a
community believes or replace reading the comments.

## Before the session

- Agree on the discussion question, intended audience and who may receive exports.
- Prepare a CSV or XLSX with one comment per row and a header row. Check the
  intended sheet, comment column, blank rows and repeated IDs. Do not treat
  comments as unique participants unless the source supports that interpretation.
- Remove identifiers from your working copy. Do not map names, contact details or
  IDs as subgroup fields. Automatic redaction needs visual checking.
- Use only supplied subgroup categories. An appropriate reference distribution
  must describe the same categories and context; never infer demographics.
- Choose the workload: the online demo permits 60 cleaned comments and 24,000
  comment characters; use the local dashboard for larger files. Local ingestion
  reads at most 5,000 rows, with additional text/file limits. Never silently
  substitute a small sample for a whole-file report.
- Follow the [setup guide](../README.md#install-and-run), install models beforehand,
  and rehearse upload, analysis and all downloads on the presentation computer.
  For local operation, keep the terminal open. Have a previously checked PDF
  available if live hosting is asleep, busy or unavailable.
- Check display size, keyboard access and readable numeric tables. Offer the PDF
  and plain-language explanations; do not rely on chart colors alone.
- Assign a facilitator, a person operating the app and a person recording agreed
  actions. These can be combined for a small session. Keep notes outside the app.

## 90-minute agenda

| Minutes | Activity | Outcome |
| --- | --- | --- |
| 0-10 | Explain the purpose, input source, comment count and limitations. Confirm that participants can read the display. | Shared scope; no claim that the sample represents everyone. |
| 10-20 | Upload, map and validate. Compare retained counts with the source and inspect the redacted preview. | Correct sheet and mapping; cleaning decisions understood. |
| 20-40 | Run analysis once. Examine Themes, ungrouped comments, labels and supporting excerpts. Open source comments when an excerpt needs context. | Findings supported by actual text; disagreements retained. |
| 40-50 | Inspect sentiment/emotion and Timeline tables. Separate model tone from agreement with a proposal. Explain missing dates and excluded languages. | Cautious interpretation with the correct denominator. |
| 50-60 | Inspect Representation. Explain missing references and suppressed groups; do not reconstruct hidden counts. | Clear boundaries on what participation data can establish. |
| 60-75 | Inspect Questions and any possible response passages. Agree on up to three questions worth following up. | Human-selected questions; possible matches are not verified answers. |
| 75-85 | Review selected excerpts and prepare Word/PDF. Check totals, omitted themes, privacy and wording together. | A checked brief or a clearly identified correction list. |
| 85-90 | Assign an owner and next step for each agreed action. Confirm who receives the brief and when. | Distribution and follow-up plan. |

If analysis is slow, use the checked example rather than repeatedly clicking
Analyze. Clearly identify the example's source and scope. Do not describe an
unfinished run as a result for the current file.

## Interpreting difficult results

- **Ungrouped comments:** these remain in the CSV and totals. Read them separately;
  they are not automatically unimportant. Do not force them into a convenient theme.
- **Mixed themes or thin quote coverage:** inspect the underlying comments. A
  missing third distinct quote is a shortage, not permission to invent one.
- **Sentiment disagreement:** return to the text and describe the disagreement.
  Published agreement rates are limited measurements, not a guarantee of accuracy.
- **Missing comparison data:** state that the comparison is unavailable. An empty
  chart is not proof that no group or concern was missing.
- **Small categories:** keep suppression intact in discussion and exports.
- **Privacy concern:** stop distribution, correct the working input and rerun.
  A review checkbox does not guarantee that all identifiers were removed.

## After the session

1. Read the downloaded brief before sending it: correct source, comment counts,
   selected excerpts, question status and limitations. Check Word pagination in
   the recipient's editor; use the PDF when fixed layout is needed.
2. Share only with the agreed recipients. The labeled CSV contains comment text;
   do not attach it merely because it is available. Follow the organization's
   retention and consent arrangements.
3. Distribute the agreed questions and action owners alongside the brief. Preserve
   any corrections separately from the original automated output.
4. Close the dashboard and stop the local server when finished. Remove downloaded
   copies according to the agreed retention plan; closing the app does not delete
   files already saved on a device.

See [methodology](methods.md), [measured limitations](validation.md),
[app usage](user_guide.md) and [troubleshooting](troubleshooting.md).
