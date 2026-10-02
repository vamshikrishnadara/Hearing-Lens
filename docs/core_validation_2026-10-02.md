# Analytical-core validation - October 2, 2026

## Scope and method

The core was run twice per corpus in one process on the local laptop CPU, with
four PyTorch threads. First/repeat times include theme analysis, redaction,
affect inference, and timeline aggregation. Only the first corpus includes
initial model/JIT loading; later corpora reuse model resources. Imports, setup
downloads, and report serialization are excluded. The repeat reruns analysis;
it does not retrieve a persisted result. Model revisions are recorded in the
[core guide](analytical_core.md).

```sh
python -m scripts.validate_core \
  --synthetic data/samples/synthetic_theme_benchmark.csv \
  --cfpb-dir data/public_samples/cfpb_2017_300 \
  --federal-dir data/public_samples/federal_mirror_300 \
  --cpu-threads 4 --output-dir data/results/core-validation
```

## Measured results

| Corpus | Rows | Themes | Outliers | First (s) | Repeat (s) | Affect scored | Language excluded | Truncated |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fictional benchmark | 1000 | 6 | 4.40% | 14.766 | 5.369 | 1000 | 0 | 0 |
| CFPB | 300 | 6 | 16.67% | 28.896 | 29.044 | 297 | 3 | 33 |
| FAA archive | 300 | 6 | 19.00% | 20.648 | 20.636 | 296 | 4 | 9 |

Each main corpus returned three source-valid 12-60-word quotes per theme, valid
membership/count totals, and identical structured results on its repeat run.
All eight automated core checks passed for each corpus. The three main samples
also passed all eight theme-only checks in the executed notebook. These checks
do not establish thematic coherence or sentiment/emotion accuracy.

The repeat target is under 30 seconds. CFPB passed by less than one second in
this final run; this is a measured pass, not a robust performance margin or a
service guarantee. Earlier runs on the same 300-row input exceeded the target
(about 37 seconds before optimization, about 32 seconds with two threads after
optimization). Length-sorted affect batches reduce padding and restore original
row order; quote selection embeds only the candidates needed. No model was
changed, source comment shortened, or cross-call result cache introduced to
meet the target. Retest on the deployment environment in Week 5.

The richer fictional benchmark has development ARI 0.705765. It is newly authored
data with 48 templates, not a held-out test or a like-for-like improvement on the
original 24-template fixture. The original file remains unchanged and its
notebook stress run still has quote counts 3,2,2,2,2,2 (ARI 0.262017). Thresholds
were explored on development data. See [Week 2 findings](week2_validation_2026-10-02.md)
for mixed groups and qualitative limitations.

## Verification and human review

- All 150 automated tests passed; dependency consistency and whitespace checks passed.
- All six notebook code cells executed successfully on the final implementation.
- The notebook includes all three main corpora and the original stress fixture;
  saved outputs contain aggregate checks only, not public narratives.
- All 60 review rows are ready (20 per corpus), with no placeholder rows and no
  human answers. The local review page was visually checked: blank choices,
  complete comments, and 0/60 progress. JavaScript syntax was checked separately.
- The agreement evaluator verified source fingerprints with the final outputs.
  It reports zero labeled rows, null agreement, and completion=false. The fellow
  cannot review today; no model output is substituted for human ground truth.
- Human coherence/privacy inspection of three themes per corpus is also pending.
  AI inspection found broad/overlapping groups; see the Week 2 report.

## Sources and remaining limits

CFPB sample SHA-256: `d3f32e0f4db5dbcfeb98467368fde551594fa9ed78bc1067f48eb2c855f53ff2`.

FAA sample SHA-256: `c49045c8e56baf08f27c6f8926604c1dc35aea8d3656efd70d2b1dce877dc219`.

Source preparation, convenience-sampling limits, and provenance are in
[CFPB notes](cfpb_source.md) and [federal notes](federal_source.md). Public source
text, raw responses, review packets, and human-label sheets remain local.

Automatic redaction can miss identifiers and over-redact ordinary phrases.
Language detection excluded three CFPB and four FAA rows; excluded rows receive
no invented neutral score. Long model inputs are limited to 512 tokens and the
truncation counts above remain visible. Scores are not calibrated judgments of
intent or policy support. The full dashboard and deployment are later work.

Benjamin's formal gate approvals are no longer a prerequisite, per the fellow's
report. This does not complete human validation. The code license is undecided;
public-update drafts exist but publication is not claimed. Accordingly, all
Weeks 1-3 deliverables are not marked complete.
