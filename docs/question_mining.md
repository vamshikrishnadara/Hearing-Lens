# Question grouping, ranking and response matching

`mine_questions` extends the [candidate detector](question_detection.md) without
changing its API or the frozen 200-sentence review. It runs locally on CPU and
returns JSON-ready results. It is not yet connected to the dashboard or the full
pipeline command.

```python
from pipeline.questions import mine_questions

result = mine_questions(
    mapped_frame,
    grouping_distance=0.35,
    agency_response=optional_response_text,
    response_threshold=0.6,
)
groups_by_id = {g['question_group_id']: g for g in result['groups']}
priorities = [groups_by_id[key] for key in result['top_unanswered']]
```

## Grouping and source traceability

The existing detector redacts input before sentence splitting. Only candidate
questions are embedded, using the locally cached MiniLM model already used for
themes. No model download or new dependency is introduced. Normalized identical
wording is embedded once, while all source occurrences are retained.

Agglomerative clustering uses cosine distance and complete linkage, with a
default distance threshold of 0.35. Complete linkage avoids merging two distant
questions through a chain of intermediate matches. The threshold is a development
default, not a calibrated probability. It can leave related questions separate.

Each group's representative is a verbatim source question: the unique wording
with the greatest mean cosine similarity to the other unique wordings in that
group. Lexical ties are deterministic. Representatives carry offsets and hashes
into the redacted source. No question is paraphrased or generated. Group IDs use
sorted wording, independent of incidental clustering label numbers. They are
stable for repeated identical inputs, not permanent IDs across different corpora.

Every candidate gets one assignment containing its input row position, sentence
index and group ID. Frequency is the number of distinct comment rows supporting
the group. Repeating the same question within one comment does not increase that
frequency. `sentence_count` separately preserves all occurrences. Reliable
respondent-ID deduplication belongs upstream in `map_columns`; row counts do not
prove counts of unique people.

## Ranking and subgroup privacy

Ranking sorts by distinct comment count, then visible subgroup spread, both
descending. Representative wording and group ID break ties. It is a transparent
ordering rule, not an inferred importance or urgency score.

Only mapped `subgroup__` fields are selected automatically. Other supplied
category fields require explicit selection. Text, IDs and period fields are
excluded. Category values are trimmed and case-folded, never inferred.

For each question group, a category contributes to spread only if at least ten
distinct supporting comment rows supply it. A stricter minimum can be selected.
Spread sums qualifying field/category pairs: role=Parent and tenure=Renter are
two pairs, not two different people. This means scores depend on which fields
were selected and must not be compared across incompatible field selections.

Outputs include visible breadth per field, missing/partial coverage, and whether
small categories were suppressed. They contain no category names, category
counts or per-comment subgroup membership. Suppressed categories do not influence
ranking. Missing values and small categories make spread a lower bound. With no
known categories, spread is `null`; zero means known values exist but none met
the minimum. This does not guarantee anonymity or prevent every inference from
the original input, distinctive text, external knowledge or repeated releases.

## Optional response matching

The caller supplies agency response text as a string. It is separately redacted
and split into sentences. Each unique question wording is compared with every
response sentence. The best cosine match at or above 0.6 is returned with a
redacted response excerpt and source offsets. No official response is fetched,
inferred from a comment, or fabricated. Score is similarity, not confidence.

Group statuses are:

| Status | Meaning |
| --- | --- |
| `possible_match` | Every unique question wording has a response sentence meeting the threshold. |
| `partial_match` | Some wordings match, while others do not. |
| `no_match` | None of the wordings has a qualifying match. |
| `not_checked` | No usable response was supplied. |

The top three are the highest-ranked groups other than `possible_match`. Partial
groups stay eligible, so a response to one wording does not hide another one.
Fewer than three groups are returned when fewer qualify; none are invented.
Without a response, they are unverified follow-up priorities, not proven
unanswered questions. Empty and absent responses are distinguished in metadata.

**A semantic match does not establish that a response answers a question.** It
can repeat, evade or contradict it. Inspect every possible match and the top-three
selection before making a public claim. The detector can also misclassify
statements, and its human accuracy remains unmeasured. Long sentences may be
truncated by MiniLM. English-only assumptions and redaction limits still apply.

## Resource and failure behavior

Complete-linkage clustering has quadratic memory requirements. More than 2,000
unique question wordings are rejected before embedding/clustering. Responses
over 100,000 characters or 1,000 sentences are rejected rather than silently
truncated. These are resource limits, not performance guarantees. Missing models,
invalid vectors and incompatible question/response vectors fail with safe error
messages; failures do not turn questions into purportedly unanswered results.
No question candidates require no embedding calls. The module does not write
uploads or cache user analysis results.

## October 7 development validation

The fixed fictional benchmark contains 130 candidate sentences, grouped into six
questions. Three explicitly fictional response sentences produced three possible
matches. The highest-ranked remaining questions concerned:

1. Disability accommodations and an accessibility contact (26 comments).
2. Hiring licensed psychologists (25 comments).
3. A public response log (19 comments).

These agree with the authored fictional response scenario, **not a human
reviewer's independent picks**. Thresholds 0.55, 0.60, 0.65 and 0.70 yielded the
same six group classifications and priorities. Default 0.60 was retained. This
small, deliberately constructed scenario is not held-out quality evidence.
Three additional authored paraphrase pairs grouped as expected using the real
local model; those are development examples, not an accuracy benchmark.

| Sample | Comments | Candidate sentences | Groups | First / repeat seconds |
| --- | ---: | ---: | ---: | ---: |
| Fictional | 1,000 | 130 | 6 | 5.987 / 2.060 |
| CFPB | 300 | 126 | 119 | 5.627 / 5.457 |
| Federal | 300 | 286 | 228 | 3.665 / 3.651 |

Each run used four CPU threads. The first fictional run includes embedding-model
load; later corpora reuse it. Repeats recompute results. Imports, source loading,
report writes and the separate validation assertions are outside the timer.
All repeats were identical. Counts, one-assignment-per-candidate, representative
spans and eligibility of top-three results passed. Public samples have many
single-question groups; no human coherence claim is made. Neither public sample
has an agency response supplied, so its answer status is unverified.

All 222 automated tests passed, including 32 new grouping, ranking, matching and
validation checks. These cover repetition within comments, incomplete matches,
missing responses/metadata, suppression, safe failures and review integrity.

```sh
python -m scripts.validate_questions \
  --cfpb-dir data/public_samples/cfpb_2017_300 \
  --federal-dir data/public_samples/federal_mirror_300 \
  --output-dir /path/to/new/local/question-validation
```

Public narratives and detailed outputs remain local, outside Git. The fictional
response fixture is clearly labeled in `data/samples/synthetic_agency_responses.json`.

## Independent top-three review

The local packet shows the fictional response, all six questions, frequencies
and visible spread, but hides the algorithm's ordering and match guesses. A human
chooses up to three questions and explicitly confirms completing the review. If
none remain, that must be stated explicitly. Fields start blank, not preapproved.

```sh
python -m scripts.evaluate_question_priorities \
  --review /path/to/completed/top-three-human-review.json \
  --result /path/to/local/synthetic-questions.json \
  --response-fixture data/samples/synthetic_agency_responses.json \
  --output /path/to/new/local/top-three-validation.json
```

The evaluator checks the exact review source, response, unique known IDs, reviewer
name and explicit completion. A different selection or ordering needs a short
explanation for each differing question. Identity/judgments are self-reported,
not authenticated. **Human priority review completed on October 10, 2026 for the
fictional sample.** The reviewer selected `q004`, `q001`, `q003` in that order
before being shown the system's selections; the evaluator confirmed an exact
match. Task instructions were clarified without supplying the choices. The
fictional question-label review and eight-group manual calculation check are
also complete. Earlier sentiment/emotion and theme/quote reviews remain incomplete.
