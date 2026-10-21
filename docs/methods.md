# Methodology

Hearing Lens summarizes community feedback supplied as CSV or XLSX. It supports
exploration and discussion, not automatic decisions about people. Analysis runs
with local model weights; comments are not sent to an external inference API.

## Input, cleaning and denominators

The app reads at most the first 5,000 rows and warns when additional rows are
omitted. Uploads are limited to 10 MB. The comment column is required; dates,
respondent IDs and subgroup fields are optional. Blank comments are removed.
With an ID column, duplicate nonblank IDs keep the first usable comment; missing
IDs are retained. Without reliable IDs, counts describe comments, not people.

| Measure | Denominator / treatment |
| --- | --- |
| Theme share | All theme-analyzed comments, including outliers; excluded text is reported separately |
| Sentiment and emotion percentages | Scored English comments only; excluded rows are not treated as neutral |
| Mean sentiment | Mean of P(positive) minus P(negative) over scored rows; no scores gives a missing value |
| Subgroup participation | Cleaned rows with a known value for that field, including suppressed and unmatched categories |
| Question frequency | Distinct source comments supporting a question group, not repeated question sentences |

Input order supplies internal row positions. Respondent IDs are used for optional
cleaning but are excluded from the displayed comment preview and labeled export.

## Models and reproducibility

| Component | Model / implementation | Role |
| --- | --- | --- |
| Name detection | spaCy `en_core_web_sm` plus rules | Redaction of detected names, contacts and address patterns |
| Semantic embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Themes, quote ranking and question similarity |
| Sentiment | `cardiffnlp/twitter-roberta-base-sentiment-latest` | Negative, neutral and positive labels |
| Emotion | `j-hartmann/emotion-english-distilroberta-base` | Anger, disgust, fear, joy, neutral, sadness and surprise |
| Language | `langid`, normalized score threshold 0.8 | Eligibility for English affect scoring |

Immutable analytical model revisions and required files are defined in
[`scripts/model_setup.py`](../scripts/model_setup.py). Installation records model
provenance locally. File-presence checks do not verify cryptographic integrity.
Record the code revision, package versions, model revisions, input fingerprint
and settings with an evaluation. Seeded clustering improves repeatability but
does not guarantee identical behavior across library or hardware changes.

## Redaction, themes and supporting quotes

Redaction precedes theme labels, displayed quotes and question text. Sentiment
and emotion use the mapped comment text locally. Automatic redaction can miss
identifiers or replace ordinary words; inspect excerpts before sharing them.

The core chooses K-means for fewer than 150 input rows and BERTopic at 150 or
more. K-means selects among 4-12 candidate groups where the data support it.
BERTopic uses normalized MiniLM vectors, UMAP with seed 42, HDBSCAN and c-TF-IDF.
It fits distinct vectors once and restores all original rows and counts.
Automatic density grouping preserves natural topics up to 15; larger counts
are reduced. Manual density counts are reduction targets, not guarantees.

A conservative refinement can move assigned comments in the original embedding
space when similarity is at least 0.45 and the winning margin is at least 0.03.
Original outliers stay outliers. Qualifying small themes may merge; changes are
recorded. These development settings have not established general accuracy.

KeyBERT supplies 1-3-word labels with MMR diversity 0.5. Candidate phrases come
from within individual redacted comments. Theme ID 0 denotes ungrouped comments;
ordinary themes start at 1. Counts, excluded rows and outliers remain visible.

Quotes are original redacted text or contiguous sentence excerpts with source
positions. Candidates must satisfy length and duplication filters. The dashboard
offers up to three selected quotes and eligible alternatives from the same theme.
If fewer are suitable, it shows the shortage rather than inventing text. A quote
illustrates a theme; it does not establish that every comment shares its meaning.

## Sentiment, emotion and time

Affect models use CPU inference, batches of up to 32 and a 512-token limit.
Truncated rows are flagged. Non-English or uncertain-language rows are excluded
from affect scoring and counted explicitly. Theme analysis can still include
these rows, although its model is also English-oriented. Exact duplicate inputs
are reused within a call; user text and predictions are not globally cached.

Scores are model outputs, not calibrated certainty or an assessment of intent.
Mixed praise and criticism, implied dissatisfaction, sarcasm and short questions
can disagree with human interpretation. Emotion ties remain explicit.

When every nonblank period value parses as a date, the timeline uses UTC calendar
days (month-first for ambiguous dates). Otherwise it uses supplied categorical
labels in input order. Missing periods remain visible. Without a period column,
there is one aggregate period. Charts do not bridge missing sentiment scores.

## Representation and questions

Representation compares supplied categories against an explicit reference.
Gap = participation percentage minus reference percentage. Ratio = participation
share / reference share. Ratios below 0.75 or above 1.25 are flagged; exact boundary
values are within range. A zero reference has no defined ratio. Small groups and
complementary cells are suppressed; hidden cells remain in the denominator.
No demographic trait or baseline is inferred from names or comment text.

Question rules detect candidate sentences with a question mark or initial
interrogative/auxiliary. Semantic clustering combines related candidates; ranking
uses frequency and visible subgroup spread. Optional response matching finds
possible passages. Similarity does not establish an answer, and missing response
text does not prove that a question went unanswered. Rhetorical questions and
ordinary statements can trigger the rules.

## Reports and data handling

Word and PDF briefs share the same bounded prose: at most three leading themes,
one excerpt each, sentiment, first/last scored-date comparison, up to two visible
representation gaps and three question priorities. Ellipses mark shortened text.
The full dashboard and labeled CSV provide more detail. PDF generation checks a
single page, uses embedded fonts and keeps body text at 11 points. Unsupported
characters or overflow produce an error with Word as an alternative.

Uploads, results and generated downloads remain in the app session. Changed
inputs or quotes invalidate prior downloads. Only model resources are shared.
Analysis jobs serialize within a process; a new request waits at most 30 seconds
for the current job. This is not a timeout for the active analysis. The separate
command-line tool writes exports only to its explicitly selected destination.

## Validation and use limits

Read the [validation summary](validation.md) for measured results and scope.
Fictional fixtures exercise software behavior; their repeated authored patterns
do not establish accuracy on real community responses. Human agreement on a
small development sample is also not a representative accuracy estimate.

Check source excerpts, excluded rows, quote shortages, reference suitability and
possible response matches before using findings. Review charts and reports as
descriptive aids. The app does not establish representative participation,
causation, policy support, individual intent or complete anonymization.

For detailed algorithms, see the [analytical core](analytical_core.md),
[representation calculations](representation_gaps.md), [question methods](question_mining.md)
and [brief selection rules](community_brief.md).
