# Fictional workflow checks

The fixed fictional school benchmark and authored edge cases can exercise the
complete local workflow without providing any other dataset. These checks test
software behavior, repeatability and timing. They do not establish accuracy on
real community submissions or complete independent human review.

## Run the checks

Install the local models as described in the [complete pipeline guide](full_pipeline.md).
From the repository root, choose a new output folder outside Git:

```sh
python -m scripts.validate_fictional --output-dir ../local-analysis/fictional-check-01
```

The command fixes its inputs to the committed fictional benchmark, fictional
response and authored examples. It runs each scenario twice through the full
command body, including JSON, both offline charts and hash manifests. No input
dataset argument is accepted. Existing destinations are preserved. Exit status
is nonzero if a structural check or benchmark target fails.

Checks cover shared row positions and totals, theme and timeline counts,
redacted quote and question source spans, question-group frequencies, priority
eligibility, suppressed metrics, export hashes and repeated JSON equality.
Scenario-specific checks cover independent gap arithmetic, three dates, omitted
fields, cleaning, hearing labels, complementary suppression and empty questions.

## Measured result — October 9, 2026

All five scenarios passed every structural check and produced identical repeated
JSON. Times below measure analysis with four CPU threads; loading the input,
writing exports and process startup are excluded. The first benchmark includes
model loading. Subsequent runs reuse model weights but recompute results.

| Scenario | Input / cleaned rows | First / repeat seconds | Result |
| --- | --- | --- | --- |
| Fictional school benchmark | 1,000 / 1,000 | 19.96 / 7.48 | Six themes, six question groups, three dates; independent gap arithmetic agrees |
| Missing optional columns | 24 / 24 | 0.57 / 0.53 | Single period, unavailable gaps, no supplied response |
| Cleaning and hearing labels | 5 / 3 | 0.07 / 0.07 | Blank comment and repeated ID removed; labels retained |
| Small categories | 31 / 31 | 0.12 / 0.12 | Small and complementary groups suppressed |
| Statements only | 24 / 24 | 0.10 / 0.10 | No question groups; blank categories and response handled |

The benchmark also met the 5–15-theme, under-20%-outlier, three-quotes-per-theme,
under-two-minute first-analysis and under-30-second repeat targets. Small edge
cases deliberately do not aim for those theme/quote targets. Timing is one local
measurement, not a general performance guarantee or a repair of earlier findings.

188 targeted regression tests passed, including 17 new fictional-validation and
review-packet tests. The separate question-review interface checks passed for
blank answers, progress counts, reviewer requirements, download, resume, invalid
import preservation and reset. This is a selected regression run, not a claim
that every repository test was rerun.

The run's `fictional-validation.json` records source hashes, individual checks
and timing scope. Detailed outputs belong outside Git.

For blank human labels, independent priorities and the calculation workbook,
see the [fictional review instructions](fictional_review.md).

## Upload-to-Themes app check - October 12, 2026

The real Streamlit app was executed with its in-process AppTest runner and the
1,000-comment fictional theme benchmark, with network model access disabled.
Actual installed local models ran through the complete analytical pipeline;
no analytical outputs were mocked in this check. Date and ID fields were mapped.
The UI showed six themes, three quotes and three alternatives per theme, and
44 ungrouped comments. Clicking Analyze to returning the rendered app took
17.90 seconds locally. This includes the analysis-button run and UI construction,
excludes the earlier preview step, and is not a deployment or browser-latency test.
A review tick survived a normal UI rerun without rerunning analysis.

50 targeted tests and six subtests passed across dashboard, upload/mapping,
redaction UI, ingestion, pipeline orchestration and theme-backend checks.
Dashboard lifecycle tests use small fictional inputs and mocked expensive
inference to isolate upload replacement/removal, sheet and mapping changes,
failed validation and analysis, retry, session isolation, preserved text codes,
quote swapping, review reset and empty/shortage states. The real-model check
above separately exercises the connected workflow. Browser visual inspection
and the deployed 2,000-row benchmark are not claimed by these tests.

Session review ticks are UI controls and do not establish independently measured
model accuracy.
