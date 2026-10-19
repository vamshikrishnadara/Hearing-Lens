# Community Word brief

After running analysis, select **Prepare Word brief**, then **Download Word
brief** below the dashboard. The editable document uses 11-point body text and
a compact, single-page layout. Generation uses the current analysis and selected
quotes; it does not rerun clustering or sentiment models. PDF export is not yet
available.

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
raw response text, personal work records, or review checkbox state. Word metadata
does not add a personal author name.

File bytes stay in the current session only. Changing the upload, mapping,
reference, response, analysis run, or selected quotes removes the old download.
Generation failure removes any previous brief rather than offering a stale or
partial document. Local model weights can be reused; brief text and results are
not globally cached. The application does not save the document to disk.

The layout bounds content rather than shrinking the body text below 11 points.
Pagination still depends on the Word-compatible viewer and installed fonts;
check the page layout after editing or replacing text. A successful export is
not evidence that the automated labels or selected themes are accurate.
