# Community Word and PDF briefs

After running analysis, select **Prepare Word brief**, then **Download Word
brief**, or **Prepare PDF brief** followed by **Download PDF brief**, below the
dashboard. Both formats use the same selected content and 11-point body text.
Word remains editable; PDF uses embedded fonts and a checked single-page layout.
Generation uses the current analysis and selected quotes; it does not rerun
clustering or sentiment models. The PDF is generated directly in memory using
ReportLab; no office installation or external conversion service is required.

The brief contains a process summary, the three largest themes with one selected
quote excerpt each, sentiment distribution, a dated tone comparison where
possible, up to two visible representation gaps, up to three follow-up questions,
and a method footnote. The full dashboard and labeled CSV retain the more detailed
results. Themes tie-break by ID; questions retain pipeline priority order.

Long labels, quotes and questions are shortened with `...`. All quotes are marked
as excerpts; inspect the full source in the dashboard before interpreting a
shortened passage. The document reports counts of cleaned comments, not a count
of unique people or evidence of population-wide opinion.

Sentiment percentages use scored comments only. No scores are substituted for
excluded rows. The dated comparison uses the first and last dates with valid
scores; undated rows are disclosed and excluded. Hearing labels alone do not
establish chronology. Missing references disable representation claims. Hidden
groups and unmatched categories are not reconstructed or reported as gaps.
Question priorities remain suggestions; similarity does not prove an answer,
and absent response text cannot establish that a question was unanswered.

Selected text, including displayed subgroup labels, passes through the existing
local redactor. Automatic redaction can miss identifiers, so inspect the document
before sharing. The export does not include respondent IDs, original file names,
raw response text or review checkbox state. Neither format adds a personal author
name to its metadata.

File bytes stay in the current session only. Changing the upload, mapping,
reference, response, analysis run, or selected quotes removes the old download.
Generation failure removes the previous download for that format rather than
offering a stale or partial document. The other format remains available when
its inputs are unchanged. Local model weights can be reused; brief text and results are
not globally cached. The application does not save the document to disk.

The layout bounds content rather than shrinking the body text below 11 points.
Word pagination still depends on the viewer and installed fonts; check the page
layout after editing or replacing text. PDF generation refuses multi-page output
or characters unsupported by its bundled Bitstream Vera fonts instead of
silently dropping text or shrinking it. In that case, use Word. A successful export is
not evidence that the automated labels or selected themes are accurate.
