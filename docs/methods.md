# Methodology

Hearing Lens summarizes supplied comment text using local natural-language
processing models. It does not infer demographic traits or treat a comment
sample as a representative measure of community opinion.

## Input and cleaning

CSV and XLSX columns are mapped to a common schema. Empty comments are removed;
when respondent IDs are supplied, duplicate nonempty IDs keep the first usable
comment. Dates and subgroup values remain supplied metadata. The application
processes uploads in session memory; the separate command-line tool explicitly
exports requested results.

## Redaction and themes

Names, contact details and address patterns are redacted before displayed labels
and quotes are derived. MiniLM embeddings represent comment meaning. The core
uses K-means below 150 rows and BERTopic for larger inputs, with explicit outliers.
KeyBERT/MMR supplies keyword labels. Theme shares include ungrouped comments in
the denominator.

Supporting quotes are original redacted comments or contiguous sentence excerpts
with source positions. Length and duplicate filters limit each theme to suitable
distinct quotes. Eligible alternatives can replace a selected quote. Missing
quotes are never invented. A quote illustrates a theme; it does not imply that
all members of the group share the same position.

## Sentiment, emotion and time

English transformer models classify negative, neutral or positive sentiment and
seven emotion categories. Aggregates use scored rows, with exclusions and
truncation counts shown separately. Mean sentiment is the average of positive
minus negative model probability. These scores are not calibrated certainty or
an assessment of a person's intent.

Dates are grouped by UTC calendar day when all nonempty values parse. Otherwise,
the supplied column becomes categorical hearing labels. With no period field,
the output contains a single period. Missing and unscored values are explicit.

## Representation and questions

Participation shares are compared with reference distributions supplied by the
user. Small groups and complementary cells are suppressed to reduce disclosure.
No baseline or personal characteristic is inferred from comment text.

Question rules identify candidate sentences, semantic grouping combines related
questions, and ranking uses frequency and visible subgroup spread. Optional
response matching identifies possible matches; similarity alone cannot prove
that a question has been answered. Outputs therefore describe potentially
unanswered priorities.

## Interpretation limits

- Automatic redaction can miss identifiers or remove ordinary wording.
- Sarcasm, mixed tone and domain-specific language can confuse classifiers.
- Language detection may exclude short or mixed-language comments; long inputs
  are subject to model context limits.
- Theme membership depends on the input and settings; related wording does not
  guarantee a shared concern or viewpoint.
- Repeated fictional examples support software checks, not population claims or
  independent real-world accuracy estimates.
- Automated consistency checks do not establish semantic accuracy. Evaluate
  predictions against independently supplied judgments before relying on them.

See the [analytical core](analytical_core.md), [representation calculations](representation_gaps.md)
and [question methods](question_mining.md) for implementation details.
