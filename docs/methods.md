# Methodology and limitations - draft

Hearing Lens groups comment text statistically; it does not infer demographics
or determine what a community unanimously believes. Supplied subgroup fields are
not used to predict personal characteristics. Upload processing is memory-only.
This draft describes the local analytical core, not a deployed five-panel app.

Themes use local MiniLM embeddings, K-means for small inputs, and BERTopic for
larger ones. Keyword labels use KeyBERT/MMR. Theme ID 0 means outlier. Quotes are
redacted original comments or contiguous complete-sentence excerpts selected near a group center, subject to length and duplicate filters. Excerpts carry source offsets and are never padded or paraphrased. A selected quote illustrates the group, not agreement by all
its members. Review quote candidates before sharing them.

Sentiment is classified as negative, neutral, or positive. Emotion has seven
classes. Both are English models, run locally, then aggregated over scored rows;
counts and exclusions accompany proportions. Mean sentiment is the average of
positive minus negative model probability. Scores are not calibrated certainty.
Timeline periods use supplied dates or hearing labels, with a single-period view
when no period is supplied. See [implementation details and model cards](analytical_core.md).

## Human validation table

| Corpus | Required hand labels | Human labels completed | Sentiment agreement | Emotion agreement |
| --- | ---: | ---: | --- | --- |
| Synthetic | 20 | 0 | Pending | Pending |
| CFPB | 20 | 0 | Pending | Pending |
| Federal | 20 | 0 | Pending | Pending |

The sheet is blind and must be completed by a person. The evaluation command
checks source identity, label vocabulary, duplicate rows, coverage, and exclusions.
Every rate below 70% must have a written plan: inspect disagreements, test an
appropriate alternative model or threshold, or explicitly document the limitation.
No agreement rate is claimed from automated tests or synthetic category labels.

## Known limitations

1. Sarcasm, negation, mixed feelings, and domain-specific language can confuse
   sentiment/emotion models trained on other kinds of text.
2. Non-English and uncertain-language rows are excluded from affect. Detection
   can misclassify short, mixed, or even clearly English text; exclusions are shown.
3. Affect inputs beyond 512 tokens are truncated and counted. Sentence embeddings
   also have context limits; a long sentence can lose information.
4. Themes depend on input composition and parameter choices. Similarity is not
   shared meaning, and optional merging can combine distinct or minority views.
5. Redaction is imperfect. Known name/entity misses remain; tests are not a
   privacy guarantee and a human quote review remains necessary.
6. Quote shortages are real: short/long comments and repeated wording can leave
   fewer than three eligible distinct quotes. No duplicates are added to fill slots.
7. Dates can be ambiguous. UTC/month-first parsing is documented; mixed invalid
   dates become categorical hearing labels rather than being silently discarded.
8. Public development samples are convenience/development samples and do not
   establish population representation or performance on partner data.
9. All three development corpus types are prepared. Human agreement and independent theme/quote review remain pending. Local measurements do not establish deployed-service or partner-data performance.

Representation-gap calculations are implemented locally as of October 5. Shares
use known subgroup values after upstream cleaning, with missing coverage reported.
Baselines are supplied explicitly and categories are never inferred. Small-group
counts and derived metrics are suppressed, with complementary suppression when
needed. See [gap methods and limits](representation_gaps.md).

Question detection is implemented as of October 6. English spaCy sentence
splitting and terminal-question-mark/initial-wh-word/auxiliary rules identify
candidates in redacted text. Human review of the 200-sentence fictional packet
was completed October 10: initial recall 90.48%, false-positive rate 0%. Two
reviewer corrections after assistant clarification yield an adjudicated 100%
recall and 0% false-positive rate; original labels/results are retained. The
200 occurrences contain only 48 distinct wordings, limiting generalization. See
[question rules and evaluation](question_detection.md). Grouping, frequency and
protected subgroup-spread ranking, and supplied-response matching are implemented
as of October 7. Outputs say potentially unanswered; semantic similarity does not
prove that a response answers a question. The independent fictional top-three
review was completed October 10, with `q004`, `q001`, `q003` matching the system.
The reviewer also confirmed all eight manual gap calculations and supplied a
workbook. See [question mining and development checks](question_mining.md) and
[gap review](gap_spreadsheet_check.md). Full-pipeline integration is implemented;
product brief export and deployment remain unfinished.

## Current development evidence

The richer fictional fixture and larger public samples are documented in
[Week 2 validation](week2_validation_2026-10-02.md). Original samples remain as
stress/regression data. Development ARI is not sentiment/emotion agreement, and
changes in fixture content are not claimed as like-for-like accuracy gains.
All 60 blind review comments are ready; no human labels have been supplied.


## Complete local workflow (October 8)

The [complete pipeline](full_pipeline.md) maps and cleans input once, then combines
all five analysis areas using the same cleaned-row positions. Mapped dates are
recognized by the timeline. Optional reference/response inputs remain supplied,
never inferred. The API is memory-only; the separate local command explicitly
exports JSON and offline charts to a new folder, with a completion/hash manifest.
It is not connected to the production upload handler.

[Three-corpus integration checks](full_pipeline_validation_2026-10-08.md) pass for
structure, source integrity and repeatability, with 243 automated tests passing.
Expanded CFPB repeat analysis is 34.11 seconds, above the 30-second target. Human
theme/affect review remains incomplete. Fictional question, priority and manual
gap reviews were completed October 10; they do not establish real-submission accuracy.
