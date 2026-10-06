# Representation gaps - October 5, 2026

The local gap module compares categories supplied in the uploaded data with an
explicit reference distribution. It makes no demographic inference and downloads
no population data. The dashboard and end-to-end command integration are later
Week 4/5 tasks; this module does not change today's upload preview.

## Meaning and denominator

Run after the existing ingestion/mapping step, which removes blank comments and
optionally deduplicates respondent IDs. Each subgroup field is calculated
independently. Its denominator is the number of usable comment rows with a
nonblank value for that field. Unknown values are reported separately and never
filled from names or comment text. Without reliable respondent IDs these are
shares of comment rows, not unique people. They are descriptive comparisons,
not proof that a self-selected comment sample represents a population.

- Participation share = group count / rows with a known value for that field.
- Gap in percentage points = 100 x (participation share - reference share).
- Representation ratio = participation share / reference share.
- Ratios strictly below 0.75 are underrepresented; strictly above 1.25 are
  overrepresented. Exactly 0.75 or 1.25 is within the specified range.
- A zero reference share has a gap but no defined ratio or ratio-based flag.

All known categories stay in the denominator, including suppressed categories
and categories absent from the baseline. Published shares must not be rescaled
to the remaining visible or matched rows.

## Reference input

Use manual group/share entries or a UTF-8 CSV with mapped group and share headers.
Bare values mean proportions from 0 to 1; percentages require a percent sign
(for example `0.62` or `62%`). Bare `62` is rejected, not guessed as a percentage.
Labels match after trimming whitespace and case-folding. Leading zero codes
are preserved by the dedicated CSV loader; `001` and `1` remain different labels.

Blank/duplicate labels, nonfinite/negative/out-of-range shares, extreme values
that cannot produce finite ratios, and empty distributions are rejected. The
reference must sum to one within 0.000001, with no silent rescaling. CSV files
above 5,000 groups are rejected, never sampled. The caller must supply a baseline
covering the appropriate geography, period and category definitions and retain
its provenance; the module does not certify it.

An invalid reference disables comparison for that field and returns an explicit
notice while retaining counts. A missing reference returns counts/shares only.
An unmatched observed category remains visible when it meets the size rule, but
has no baseline, gap or ratio. Baseline-only categories are retained and subject
to the same 0-9-row suppression rule. All-unknown or absent subgroup fields give
an unavailable state rather than a misleading zero-participation comparison.

## Small-group disclosure control

The default minimum is 10 rows; callers may increase it but cannot lower it.
For a suppressed category, count, participation share, gap, and ratio are all
null, and no under/overrepresentation flag is emitted. Labels and supplied
reference shares remain visible; this is count suppression, not anonymization
of arbitrary category labels. Select appropriate categorical fields, not names
or free-text identifiers, before displaying/sharing results.

If exactly one category would be suppressed, the smallest remaining category
is also suppressed (ties by normalized label). This prevents the simplest
subtraction of visible counts from the known total. There is no combined
"Other" count exposing the hidden value. Totals/coverage remain available.
This does not provide formal privacy guarantees against external knowledge,
overlapping fields, repeated filtered releases, or differencing attacks.
Further disclosure review is required for dashboard filters and public exports.

## API

```python
from pipeline.ingest import map_columns
from pipeline.gaps import analyze_gaps
from pipeline.reference import load_reference_csv

mapped = map_columns(raw_frame, comment_column="comments",
                     respondent_id_column="id", subgroup_columns=["tenure"])
reference = load_reference_csv(uploaded_reference,
                               group_column="group", share_column="share")
result = analyze_gaps(mapped.frame, references={"subgroup__tenure": reference})
# Manual alternative: references={"subgroup__tenure": {"Renter": "60%", "Owner": "40%"}}
# result["rows"] is a tidy, JSON-ready list for later charting.
# result["fields"] carries eligible/known/missing row counts and notices.
```

Only already-mapped `subgroup__` columns are selected automatically. Raw category
columns require explicit selection via `subgroup_columns`. Reserved comment,
identifier and date fields cannot be selected. Processing does not mutate its
inputs, persist uploads, call models, or infer missing values. `GapError` covers
invalid schema/options; invalid individual references are contained per field.

## October 5 development verification

Run `python -m scripts.validate_gaps --output-dir data/results/gaps` to reproduce
the fictional 1,000-row check. All reference shares below are deliberately
fictional test assumptions, not Census or Chicago population facts.

| Field/group | Count | Participation | Fictional reference | Gap (points) | Ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| Role: Community organizer | 50 | 5.0% | 10% | -5.0 | 0.5 |
| Role: Parent | 541 | 54.1% | 40% | +14.1 | 1.3525 |
| Role: Resident | 204 | 20.4% | 20% | +0.4 | 1.02 |
| Role: Student | 82 | 8.2% | 10% | -1.8 | 0.82 |
| Role: Teacher | 123 | 12.3% | 20% | -7.7 | 0.615 |
| Tenure: Other | 69 | 6.9% | 5% | +1.9 | 1.38 |
| Tenure: Owner | 273 | 27.3% | 35% | -7.7 | 0.78 |
| Tenure: Renter | 658 | 65.8% | 60% | +5.8 | 1.096667 |

All eight rows matched independent integer counting and rational arithmetic
exactly at the numeric output precision (ratios above are rounded for reading).
No groups in this fixture need suppression. Separate regression cases verify
9/10 boundaries, complementary suppression, unknown/mismatched categories,
missing data, zero baselines, valid threshold boundaries, CSV group codes and
malformed references. The complete suite passed 173 tests, including 23 new ones.

This is an independent code calculation, not the brief's human hand-computed
spreadsheet check. An independent formula workbook was prepared and automatically
verified on October 6; its [method and remaining human check](gap_spreadsheet_check.md)
are documented separately. Question detection is now implemented, while
its 200-sentence human evaluation and full-pipeline integration remain Week 4
work. Earlier theme and 60-comment affect human reviews remain pending.
