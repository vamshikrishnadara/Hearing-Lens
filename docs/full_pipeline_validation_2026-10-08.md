# Complete-pipeline development checks - October 8, 2026

The complete local workflow now runs through `pipeline.full.analyze_all` and
`run_all.py`. These checks verify automated operation, not human acceptance.
The dashboard is still the existing upload/redaction preview.

## Scope and results

All **243 automated tests passed** (11.055 seconds), including 21 new tests for
integration, row alignment, canonical dates, redaction at combined boundaries,
missing inputs, reference/response sidecars, preserved textual codes, export
hashes, nonfinite output rejection, failure handling and overwrite protection.
Model-heavy inference is replaced by controlled fixtures in unit tests; the
three-corpus runs below use the actual installed local models.

Each complete command body was run twice. Strict JSON results were identical
between runs for each corpus. Export hashes, row counts, theme/affect/timeline
totals, quote and question source spans, question ranking eligibility and
suppressed gap metrics passed all structural checks. Fictional gap results also
matched the existing independent rational-arithmetic check exactly.

| Dataset | Comments | Themes | Periods | Question groups | First analysis | Repeat analysis |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Fictional benchmark | 1,000 | 6 | 3 | 6 | 19.67 s | 7.38 s |
| CFPB fixed sample | 300 | 6 | 191 | 119 | 35.46 s | 34.11 s |
| Federal/FAA fixed sample | 300 | 6 | 4 | 228 | 24.09 s | 25.20 s |

All three retained 5–15 themes, fewer than 20% outliers and three selected quotes
per theme. The first/repeat command-body timings, including loading/mapping,
serialization and export, were 19.73/7.41 s, 35.50/34.15 s and 24.12/25.23 s.

Timings use four CPU threads on this local machine. The first fictional analysis
includes model loading; later corpora and repeats reuse loaded model weights but
recompute results. Process startup and imports already performed by the validator
are excluded. General system load affects timings; this is not a deployment SLA.

The expanded CFPB workflow exceeds the **30-second repeat target**. This includes
the newly added gap/question stages; it is not directly comparable to the prior
core-only 29.044-second measurement. The expanded full-pipeline target is reported
as failed and remains a refinement item; passing structural checks does not hide
it. All first analyses were under two minutes. The 2,000-row deployment benchmark
remains separate dashboard/deployment work.

## Complete command and missing fields

A fresh-process invocation of `run_all.py` also completed on the first 24 rows of
the fictional benchmark, with no selected dates, subgroups, references or response.
The JSON correctly reported a single-period timeline, unavailable gaps, an absent
response, and the row-limit notice. This exercised the real argument parser,
file loading, local models and local output files, beyond the unit-test fixtures.

The three larger runs preserve supplied dates through the canonical mapping.
The public samples deliberately have no subgroup/reference/response inputs:
their unavailable/unverified states are explicit. Fictional responses and
baselines were supplied only for the fictional benchmark; no real agency answer
or population distribution was inferred.

## Limitations and remaining validation

- Source integrity and repeatability do not establish theme coherence or affect
  correctness. Earlier human theme/quote review and 60 sentiment/emotion labels
  remain pending.
- The eight-row gap spreadsheet has not received its required human hand-check.
- All 200 human question labels and independent top-three choices are still
  pending. Recall of at least 80% and false-positive rate below 10% cannot be
  claimed without those labels. No acceptance rates were manufactured.
- Question groups can be singletons; a cosine response match is not proof of an
  adequate answer. Long input truncation and English-model limits still apply.
- Public sample provenance is checked before validation. Their detailed text,
  JSON and charts stay local outside Git; only this aggregate report is published
  when the user approves a push.
- Full dashboard integration, community brief exports and deployment remain
  subsequent scheduled work. The technical command does not complete those tasks.

See the [command guide](full_pipeline.md) for reproduction, output interpretation,
privacy boundaries and failure handling. Human validation remains distinct from
Benjamin's reported waiver of formal gate approval meetings.
