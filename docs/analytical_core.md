# Analytical core - October 1, 2026

## Run locally

Install the repository requirements, the existing spaCy model, and local weights:

```sh
python -m pip install -r requirements.txt
python -m scripts.setup_theme_model
python -m scripts.setup_affect_models
python -m unittest discover -s tests -v
```

The affect setup downloads only model/tokenizer resources, records resolved
revision hashes, and never downloads while analyzing a file. Model caches are
ignored by Git. Existing setup for `en_core_web_sm` remains required.

```python
from pipeline.core import analyze_core
from pipeline.timeline import timeline_figures

result = analyze_core(frame, period_column="hearing_date")
figures = timeline_figures(result["timeline"])
```

This returns themes, per-row affect, affect aggregated by theme, and period
summaries/volumes. It does not write data or contact inference services. The
Streamlit screen remains an upload/redaction preview; these Week 3 functions and
charts are library/command-line functionality, not the Week 5 five-panel app.

## Themes and quotes

The core routes by original input size: K-means below 150 rows, BERTopic at 150
or more. K-means uses the existing silhouette-selected 4-12 range and explicit
small-input fallback. BERTopic uses supplied local normalized embeddings, UMAP
(seed 42, cosine, random initialization, one worker), HDBSCAN, and c-TF-IDF.
It reduces density topics toward six by default; this is a fixed reduction
target, not a silhouette-selected count. HDBSCAN can yield fewer topics or all
outliers; no invented groups or forced outlier assignments are used to pass a
benchmark. Requests for manual counts in the BERTopic path are reduction targets;
use `backend="kmeans"` for manual K-means behavior. Core automatic K-means remains
limited to fewer than 150 rows, while manual counts support up to 5,000.

Unmatched rows use theme ID 0, with explicit count/share. Ordinary display IDs
start at 1. Theme shares use all analyzed comments, including outliers, as the
denominator; therefore ordinary shares may sum to less than one. An outlier
share of at least 20%, or a final count outside 5-15, produces a quality warning.
The option to merge qualifying small groups remains enabled in the core and
records its history. It does not merge density outliers.

Labels use KeyBERT, 1-3-word candidates, and MMR diversity 0.5. Candidate vocabulary
is built within individual comments so phrases do not cross comment boundaries;
normalized comment-group centers are used instead of embedding a truncated
concatenation of an entire cluster. The candidate vocabulary is capped at 5,000.
All label text comes from the existing redaction boundary. Empty vocabularies
retain generic labels. The legacy `analyze_themes()` defaults remain manual-six
K-means/TF-IDF for prior comparison scripts; choose the core for the new routing.

The core returns up to three selected quotes plus up to three eligible alternatives.
`pipeline.quote_review.swap_quote()` can replace a slot only with an alternative
from that same theme. It returns a copy and cannot inject arbitrary unredacted
text. Length and near-duplicate restrictions are unchanged. The library supports
review; the user-facing swap control remains dashboard work. Quote shortages
are reported rather than padded with duplicates or invented wording.

## Sentiment, emotion, language, and aggregation

`pipeline.affect` uses the brief's Cardiff sentiment model and Hartmann seven-class
emotion model. Resources load once per process through a bounded model cache;
models use CPU and evaluation/inference mode. Batch size is 32, maximum input is
512 tokens, and truncation is counted. Exact duplicate inputs are reused only
inside the current call, never cached across sessions or persisted. Model label
maps are validated rather than assuming class order. Only probabilities/labels,
row positions, language, status, and truncation flags leave the module.

Language detection uses langid normalized scores with an experimental 0.8
threshold. Non-English and uncertain rows are excluded from affect and counted,
not given neutral labels. Very short/mixed text and names can mislead detection.
This is not demographic inference and does not use supplied subgroup fields.
Theme analysis still includes such rows and warns that its models are English-only.
That limitation must remain visible during review.

Sentiment is negative/neutral/positive; emotion is anger, disgust, fear, joy,
neutral, sadness, or surprise. Aggregates count winning labels and divide by
scored rows only, with total/excluded counts alongside them. Mean sentiment is
mean P(positive) minus P(negative), between -1 and 1. A group without scores has
null values, not fabricated zero/neutral results. Tied dominant emotions are
reported as ties. These scores are not calibrated probabilities or evidence of
a respondent's intent, support for a proposal, or personal characteristics.

Pinned local revisions measured on October 1:

- Cardiff: `3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7`.
- Hartmann: `0e1cd914e3d46199ed785853e12b57304e04178b`.
- MiniLM: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.

## Timeline

Select a date/hearing column explicitly or let the module choose hearing_date,
date, then hearing_id. If every nonempty value parses, group by UTC calendar day,
using month-first interpretation for ambiguous dates. Missing values get a visible
missing-period group. If any nonempty value fails parsing, treat the entire column
as redacted categorical hearing labels in input order. With no period column,
return a single-period view and explanation.

Period affect summaries include all nonempty input rows with explicit exclusions;
theme volumes use theme assignments, including outliers. Blank comments are not
counted as submissions. Charts do not connect null sentiment gaps. Both chart
objects and their numerical summaries are returned, allowing a text alternative.

## Development validation

```sh
python -m scripts.validate_core --cfpb-dir PATH --federal-dir PATH --output-dir LOCAL_PATH
python -m scripts.prepare_hand_labels --cfpb-dir PATH --federal-dir PATH --output LOCAL_PATH/hand-labels.csv
```

Omit the federal option only while its sample is unavailable; output explicitly
marks that corpus pending. Validation checks repeatability, assignments, counts,
quotes, timing, and project targets. It saves review packets and self-contained
chart HTML only to the explicit local development output directory. This script
must not be wired to production uploads. Source-text fingerprints prevent
comparing human labels with predictions from a different corpus/order.

See [human-label instructions](../data/validation/README.md), [measured results](core_validation_2026-10-01.md),
and [gate status](gate_status.md). Code and tests are not supervisor approval.

Primary implementation references:
[BERTopic API](https://maartengr.github.io/BERTopic/api/bertopic.html),
[KeyBERT API](https://maartengr.github.io/KeyBERT/api/keybert.html),
[Cardiff model card](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest),
[Hartmann model card](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base).
