# Validation scope and measured limitations

This document describes technical evaluation of the software. Development
fixtures are fictional and contain repeated authored patterns. They are useful
for checking counts, source traceability and reproducibility, but are not a
representative sample of real community feedback.

## Human agreement on fictional comments

A fixed sample contained 20 comments from each of three contexts. One person
supplied sentiment and emotion judgments; source fingerprints matched the saved
predictions. Agreement means exact winning-label matches divided by 20. It is
not precision, recall, inter-rater agreement or a confidence score.

| Context | Comments | Sentiment matches | Emotion matches |
| --- | ---: | ---: | ---: |
| School feedback | 20 | 14/20 (70%) | 16/20 (80%) |
| Community center | 20 | 11/20 (55%) | 15/20 (75%) |
| Tenant association | 20 | 15/20 (75%) | 19/20 (95%) |

The community-center sentiment result is below the 70% development target.
The sample is small, class coverage is uneven, and one judgment per comment
cannot quantify disagreement between people. Mixed tone and implied sentiment
remain limitations. Re-running the same 60 texts reproduced the original model
labels with no truncation; that confirms consistency, not correctness. These
results apply to the pinned affect models in [model setup](../scripts/model_setup.py).

Nine original theme/quote groups were inspected; seven were accepted, while two
school groups had coherence or quote-representativeness concerns. Automatic
density grouping and quote selection subsequently changed. Those judgments do
not validate the revised groups. A revised school-fixture check produced 12
themes and 44/1,000 outliers; five groups had only two eligible distinct quotes.
Do not treat more themes, source-valid quotes or completed labeling as a quality
pass. Changed models or settings need fresh, independently supplied judgments;
do not tune decisions merely to pass the same labeled sample.

## Structural and output checks

| Area | What the checks establish | What they do not establish |
| --- | --- | --- |
| Cleaning and row accounting | Blank removal, ID deduplication, counts and source positions agree | Unmapped IDs cannot establish unique participants |
| Themes and quotes | Assignments reconcile; excerpts belong to their themes and match redacted source spans | Semantic coherence or representative quotes |
| Affect and timelines | Row order, scored denominators, missing values and plotted totals agree | Correct interpretation of each comment |
| Representation | Formula, threshold and suppression behavior matches independent arithmetic | A suitable or representative reference population |
| Questions | Rules, group membership, ranking and possible-match boundaries behave consistently | Every detected item is a genuine question or an answer is complete |
| Word/PDF | Shared prose, one-page PDF, readable fonts, safe failure and input-change invalidation | Correct automated labels or absence of all identifiers |
| Session controls | Automated lifecycle tests clear stale results and separate workspace state | Hosted multi-browser isolation or resource availability |

At code revision `edf89a4`, 129 targeted tests and six subtests passed for the
analysis runtime, progress, pipeline orchestration, dashboard and report paths.
Five PDF layouts and two Word layouts were visually checked. This is a selected
regression run, not an assertion that every repository test or browser passed.

## Performance scope

A local 300-comment community-center fixture at revision `edf89a4` completed
analysis in 20.47 seconds on its first process run and 8.08 seconds on repeat.
Preparing the PDF from the existing result added 0.071 and 0.032 seconds. The
analysis outputs matched the pre-instrumentation baseline exactly. These timings
exclude package installation, model downloads and browser/network latency.
A repeat reuses model resources; it does not reuse a prior analysis result.

Report-generation time and upload-to-results time are different measurements.
The export target is under 15 seconds from an existing analysis. The hosted
2,000-comment workflow target is under three minutes after startup. Local times
cannot establish either behavior on the hosted service. Free-host CPU/memory
limits, cold compilation and concurrent requests can affect the result; stage
logs help locate delays but do not by themselves prove the cause.

## Reproduce technical checks

Use Python 3.12, install requirements and models as described in the
[README](../README.md#install-and-run), then run:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m scripts.benchmark_dashboard \
  --entrypoint app/streamlit_app.py --rows 300 --repeats 2 \
  --output ../local-analysis/app-check.json \
  --fixture-output ../local-analysis/fictional-check.csv
```

The generated performance fixture differs from the community-center fixture
above, so it is a new measurement rather than a reproduction of those exact
timings. It exercises all five panels and labeled-CSV row accounting. Model
preparation uses pinned files and requires network access only if missing.
AppTest executes the app in process; it is not a browser or Linux cloud build.
To check the cloud entrypoint locally, use `--entrypoint deployment/cloud_app.py
--rows 60`. Its admission cap is 60 cleaned comments and 24,000 comment characters;
the larger workload above must use the local entrypoint.

Record the code, package/model versions, fixture fingerprint, timing boundaries
and errors with any comparison. Use the [deployment checks](deployment.md#performance-and-workflow-checks)
for actual browser timing, independent-session isolation and first-time use.
Keep detailed labels and evaluation records in the chosen local output folder.
