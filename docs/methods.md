# Methodology and limitations - draft

Hearing Lens groups comment text statistically; it does not infer demographics
or determine what a community unanimously believes. Supplied subgroup fields are
not used to predict personal characteristics. Upload processing is memory-only.
This draft describes the local analytical core, not a deployed five-panel app.

Themes use local MiniLM embeddings, K-means for small inputs, and BERTopic for
larger ones. Keyword labels use KeyBERT/MMR. Theme ID 0 means outlier. Quotes are
redacted original comments selected near a group center, subject to length and
duplicate filters. A selected quote illustrates the group, not agreement by all
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
| Federal | 20 | 0; sample pending | Pending | Pending |

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
9. The federal corpus and human validation are incomplete. Measured performance
   covers two local development corpora, not the deployed app or all required data.

Representation gaps, question mining, product brief export, and deployment are
later scheduled stages and are not represented as completed here.
