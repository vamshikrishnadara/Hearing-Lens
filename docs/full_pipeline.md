# Complete local analysis

`run_all.py` combines themes, sentiment/emotion, timelines, representation gaps
and questions. It cleans a user-supplied CSV or XLSX once and uses the same
zero-based cleaned row positions throughout. The Streamlit interface remains
an upload/redaction preview; the five-panel dashboard is separate work.

## Setup and command

Follow [analytical-core setup](analytical_core.md), including the spaCy name
model, MiniLM and both affect models. Analysis uses already installed local
models; it does not download resources or retrieve an agency response.

From the repository root, run the fictional benchmark into a new local folder
outside the repository:

```sh
python run_all.py data/samples/synthetic_theme_benchmark.csv \
  --comment-column comment_text --id-column respondent_id \
  --date-column hearing_date --subgroup role --subgroup housing_tenure \
  --output-dir ../local-analysis/example-01
```

Only the input file, comment mapping and destination are required.

| Option | Meaning |
| --- | --- |
| `--sheet NAME` | XLSX sheet; defaults to the first sheet. Not accepted for CSV. |
| `--id-column NAME` | Keep the first nonblank occurrence of each respondent ID. Without this, counts represent comment rows. |
| `--date-column NAME` | Supplied date or hearing label; never inferred from comments. |
| `--subgroup NAME` | Supplied category column; repeat for additional fields. No demographic inference. |
| `--references FILE.json` | Explicit reference distributions for selected source subgroup fields. |
| `--agency-response FILE.txt` | Supplied UTF-8 response text; absent responses are never guessed or fetched. |
| `--minimum-group-size N` | At least 10; shared by gap suppression and question subgroup ranking. |
| `--row-limit N` | First 1–5,000 input rows, default 5,000, before cleaning. |
| `--cpu-threads N` | 1, 2 or 4 local CPU threads; default 4. |

Textual CSV codes such as `001` and literal `NA` categories are preserved. Excel
cells stored as text are preserved too; formatting a numeric cell with leading
zeros does not change its underlying value. Empty comments are removed; IDs are
trimmed for deduplication and empty IDs do not deduplicate. Cleaning decisions
appear under `ingestion`. The capped reader checks one extra row, so
`rows_omitted_at_least` is a lower bound, not an exact omitted total.

## Optional references and responses

Reference JSON uses **source column names**, not internal `subgroup__` names.
For example, this is an explicitly fictional distribution:

```json
{"role": {"Parent": "40%", "Teacher": "20%", "Resident": "20%", "Student": "10%", "Community organizer": "10%"}}
```

Pass the saved file with `--subgroup role --references FILE.json`. Plain numbers
are proportions from 0 to 1; percent strings use 0 to 100. Shares must total 100%.
Missing/invalid distributions produce counts-only results with notices, never a
guessed population. Malformed JSON, duplicate keys, non-object distributions and
unselected reference fields fail before analysis. Reference files are capped at
1 MB. See the [gap guide](representation_gaps.md) for category matching and limits.

Response files are capped at 400 KB, with a further limit of 100,000 characters
and 1,000 sentences. Oversized inputs fail rather than returning a partial result.
Matches are possible answers only: they can be incomplete, contradictory or
off-topic. Human review is required. See the [question guide](question_mining.md).

## Results and safe handling

The destination must not exist. Successful runs create:

- `analysis.json`: all module results, notices, assignments and cleaning counts.
- `timeline-sentiment.html`: self-contained sentiment chart, usable offline.
- `timeline-theme_volume.html`: self-contained theme-volume chart, usable offline.
- `manifest.json`: completion status, analysis time, CPU threads and SHA-256
  hashes of the three result files. Written last.

The JSON contains `themes`, `affect`, `affect_by_theme`, `timeline`, `gaps`, and
`questions`, alongside schema version and row counts. Timeline numerical tables
provide a text alternative to charts. Question representatives have source spans
into redacted comments; `top_unanswered` contains group IDs.

The library does not write files. This CLI explicitly exports local results and
must not be wired to a production upload handler. Raw input tables, respondent
IDs and unused metadata are not exported. Redacted quotes/questions, hearing
labels and supplied subgroup labels may still be sensitive: automatic redaction
does not guarantee anonymity. Review before sharing and keep private data out
of Git. Result files and the new destination directory have owner-only permissions;
this does not control backups, synchronization or later sharing.

Input/model/serialization failures create no result folder. A disk failure may
leave an incomplete folder; without `manifest.json` it is not a completed run.
Retry into a new folder. Existing results are never overwritten. Errors do not
print raw parser/model exception messages or uploaded cell values. Exit status
is 0 for success, 1 for run failure and 2 for argument errors.

“Complete” means the automated run finished, not human acceptance or approval
for publication. Review of themes, quotes, affect, gap arithmetic, question
recall/false positives and top-three priorities remains separate.

## Missing optional information

| Missing or unsuitable input | Result |
| --- | --- |
| No date/hearing field | Single-period timeline with an explanation. |
| Mixed dates/unparseable labels | Redacted hearing labels; rows retained. |
| Subgroups absent/all blank | Gaps explicitly unavailable. |
| Reference absent/invalid | Counts/shares where permitted; no representation comparison. |
| Small subgroup | Counts/derived gaps suppressed; question ranking uses visible categories only. |
| Response absent/blank | Unverified follow-up priorities, not proven unanswered questions. |
| No detected questions | Empty groups/priorities, explicit no-questions state. |
| Unsupported/uncertain affect language | Counted exclusion, never fabricated neutral scores. |
| Required model missing | Failure, not apparently complete partial analysis. |

## In-memory API

```python
from pipeline.ingest import map_columns
from pipeline.full import analyze_all

mapped = map_columns(raw_frame, comment_column="Comment",
                     date_or_hearing_column="Hearing", subgroup_columns=["Role"])
result = analyze_all(mapped.frame)
```

API reference keys use mapped names, such as `subgroup__Role`; CLI keys use the
source header. The API retains the core's `theme_count` and `backend` options.
Legacy `analyze_core()` still returns its four original results. Both entry
points recognize `date_or_hearing`. No user results are cached between calls.

## Reproduce development checks

```sh
python -m unittest discover -s tests -v
python -m scripts.validate_full_pipeline \
  --cfpb-dir data/public_samples/cfpb_2017_300 \
  --federal-dir data/public_samples/federal_mirror_300 \
  --output-dir ../local-analysis/validation-01
```

The validator checks sample provenance, runs the command body twice per corpus,
verifies output hashes, compares JSON results, checks cross-module totals and
quote/question source spans, and compares fictional gaps with independent
rational arithmetic. Detailed data/charts stay in the chosen local directory.
Structural checks and quality/performance targets are reported separately.
These runs do not replace human review or establish deployment performance.
