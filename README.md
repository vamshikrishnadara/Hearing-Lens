# Hearing Lens

Hearing Lens is a privacy-conscious analyzer for public comments, community survey responses, and meeting sign-up exports. The planned application accepts CSV or XLSX files, lets a user map their columns, and produces transparent summaries of themes, sentiment, representation gaps, timelines, and unanswered questions.

This repository contains the upload-and-preview foundation and a complete local command-line workflow for themes, sentiment, emotion, timelines, representation gaps and questions. Human validation remains incomplete; see the methodology for technical limitations.

## Project principles

- The production application will analyze only data supplied by the user.
- Uploaded content must remain in memory and must not be written to server logs or storage.
- Personally identifying information must be redacted before quotes are displayed or exported.
- Demographic traits must never be inferred from names or comment text.
- Methods, validation results, and limitations must be explained in plain language.

## Current functionality

- Accepts CSV and XLSX files.
- Lists workbook sheets and allows sheet selection.
- Enforces a configurable row limit.
- Supports mapping the required comment column and optional date, respondent ID, and subgroup columns.
- Initially selects `comment_text` when that exact header exists; the selection remains editable.
- Drops empty comments and can remove repeated respondent IDs.
- Reports validation problems in readable language.
- Redacts common email, web, phone, street-address, and unit-number patterns from display text.
- Replaces person names detected by the local English spaCy model with `[PERSON]`.
- Blocks the preview if name detection is unavailable or fails.
- Provides a development-only theme pipeline with local embeddings, keyword labels, counts, shares, and redacted candidate quotes.
- Offers optional automatic theme counts for fewer than 150 input rows, with recorded candidate scores and manual selection retained.
- Offers experimental small-theme merging with a similarity threshold, merge history, and warnings for unmatched groups; disabled by default.
- Uses experimental sentence weighting to reduce repeated wording's influence, with the original whole-comment method retained for comparison.

- Routes the analytical core to BERTopic for at least 150 input rows and automatic K-means for smaller files, with KeyBERT/MMR labels and explicit outliers.
- Provides local sentiment/emotion models, counted language exclusions, theme/period summaries, and timeline chart objects.
- Prepares blind human-label sheets and repeatable comparison reports without inventing agreement results.
- Computes representation gaps from supplied categories and explicit baselines, with small-group suppression and missing-data notices. See the [gap guide](docs/representation_gaps.md).
- Groups and ranks question candidates, compares supplied responses and selects potentially unanswered priorities with explicit review notices.
- Runs all modules from one command with local JSON results and offline timeline charts. See the [complete pipeline guide](docs/full_pipeline.md).
- Provides [fictional-only workflow checks](docs/fictional_validation.md) for repeatability, missing fields, cleaning and small-group handling.

Name detection is an initial implementation with measured misses and false
positives; it does not guarantee that a comment is anonymous. The analytical workflow is not yet connected to the upload interface. Community brief exports and the final dashboard panels remain unfinished.
Representation gaps and question mining are available through the local workflow, with dashboard integration pending.
All three development corpus types are available locally. Numerical theme checks pass on the main samples; human validation and qualitative review remain pending. The original short/repetitive stress sample still exposes quote shortages.

## Local setup

1. Create and activate a Python 3.11 or later virtual environment.
2. Install the dependencies with `python -m pip install -r requirements.txt`.
3. Install the English name model with `python -m spacy download en_core_web_sm` (tested with model 3.8.0 and spaCy 3.8.16).
4. Run the tests with `python -m unittest discover -s tests -v`.
5. From the repository root, start the interface with `python -m streamlit run app/streamlit_app.py`.

Using `python -m streamlit` keeps the repository root available for the app's
pipeline imports. Use fictional data while testing: automatic redaction can
miss personal names and other identifiers. The preview displays only
the comment column after automatic redaction; mapped identifiers and metadata remain
in memory for processing and are excluded from the preview.

The name model is downloaded during setup, not while handling a file. Inference
runs locally. If the model is missing, reinstall it using step 3 and restart
the app. Run `python -m scripts.validate_person_redaction` for a reproducible
report on the fictional name cases and existing 1,000-row sample. See
`docs/redaction_design.md` for the measured limitations.

## User help

- [Theme prototype setup, usage, and measured limitations](docs/theme_prototype.md)
- [September 24 theme-grouping comparison](docs/theme_grouping_review_2026-09-24.md)
- [CFPB public sample source and preparation](docs/cfpb_source.md)
- [September 25 public-data validation findings](docs/cfpb_validation_2026-09-25.md)
- [September 28 unit-redaction correction and checks](docs/unit_redaction_review_2026-09-28.md)
- [September 29 automatic theme-count comparison and limits](docs/theme_selection_review_2026-09-29.md)
- [September 30 small-theme merging policy and comparison](docs/small_theme_review_2026-09-30.md)

- [Upload and preview user guide](docs/user_guide.md)
- [Upload and setup troubleshooting](docs/troubleshooting.md)
- [Reusable upload and preview testing checklist](docs/manual_test_checklist.md)

## Repository layout

```text
hearing-lens/
  app/streamlit_app.py       Current upload and mapping interface
  pipeline/ingest.py         File loading, validation, and column mapping
  pipeline/redact.py         Person, contact, and address redaction
  pipeline/themes.py         Initial local theme analysis and quote selection
  docs/schema.md             Canonical input and internal schemas
  docs/redaction_design.md   Redaction boundary, limitations, and validation plan
  docs/wireframe.md          First dashboard wireframe
  data/samples/              Reproducible development fixture and data dictionary
  scripts/                   Development-data utilities
  tests/test_ingest.py       Unit tests for the loader
```


## Development samples

The repository includes a reproducible 1,000-row fictional hearing dataset with six planted themes, three hearing dates, skewed subgroup distributions, and controlled redaction examples. It contains no collected resident data. Run `python scripts/generate_synthetic_sample.py` to recreate it.

Offline utilities prepare fixed 300-row CFPB and federal public samples for development. The earlier 100-row CFPB sample is retained for regression checks. An additional richer 1,000-row fictional theme benchmark is included; the original fixture remains unchanged. Public source text and detailed reports stay local;
the repository contains source notes, preparation/validation scripts, fictional
tests, and aggregate findings. See the CFPB links above. This does not change
the application's in-memory handling of user uploads.

## Analytical-core setup and validation

See [setup and API usage](docs/analytical_core.md), [measured results](docs/core_validation_2026-10-02.md),
and [methodology](docs/methods.md). Install local affect weights
with `python -m scripts.setup_affect_models`; analysis never downloads them.
The Streamlit page remains a preview, while the analytical core is exercised
through `pipeline.core.analyze_core`. Use `pipeline.full.analyze_all` or
`run_all.py` for the complete workflow, including gaps and questions.

## Week 1–3 verification

- [Executed three-corpus theme notebook](notebooks/week2_theme_validation.ipynb)
- [Week 2 findings and limitations](docs/week2_validation_2026-10-02.md)
- [Federal archive provenance and preparation](docs/federal_source.md)
- [Human labeling instructions](data/validation/README.md)

Install `requirements-dev.txt` to rerun notebooks. Public sample files and detailed
review packets stay local; notebooks publish aggregate checks only. Human labels
and agreement rates are not produced by the assistant.
