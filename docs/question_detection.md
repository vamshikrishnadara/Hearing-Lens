# Question detection and validation

`pipeline/questions.py` implements the detection stage of Week 4. Its October 7
`mine_questions` API also supports [grouping, ranking, response matching and
potentially unanswered priorities](question_mining.md). The detection API and
frozen 200-sentence review remain unchanged. The upload UI and full-pipeline
command are separate integration work.

## Library use

```python
from pipeline.questions import analyze_questions

result = analyze_questions(mapped_frame)
candidates = [row for row in result['sentences'] if row['is_question']]
```

Call after `ingest.map_columns` to apply blank-comment removal and respondent-ID
deduplication. Only `comment_text` is used. The function copies and redacts text
through the existing privacy boundary before sentence splitting. Metadata and
identifiers are not returned. A redaction failure stops processing rather than
falling back to raw text. The function has no file writes or network calls.

English spaCy tokenization and its rule-based sentencizer supply sentence spans.
No new downloaded model is needed for splitting. Only the language resource is
cached; comments and analysis results are not cached. Each sentence carries:

- Position in the supplied table, sentence index and exact redacted-source offsets.
- Verbatim redacted sentence, its SHA-256, a candidate boolean and detection reasons.
- The parent result includes sentence/candidate totals and a count per input row.

The detector version is `interrogatives-v1`. The baseline from the brief flags a
terminal question mark, initial wh-word, or initial auxiliary. Matching ignores
case and leading quotation/list punctuation. Quoted terminal question marks work.
Whitespace, punctuation-only input and missing text do not create candidates.
Repeated sentences retain their separate source occurrences.

## Limits

These are candidate questions, not proof of an information request or an answer.
Relative clauses such as “What we need is more time” and names such as “Will
Smith” can trigger a false positive. Rhetorical questions are another source of
false positives. Indirect requests without a matching starter or terminal `?`
can be missed. English rules are not validated for other languages.

spaCy preserves many abbreviations and decimals, but sentence boundaries can be
wrong in malformed punctuation, lists and redaction-marker contexts. Spans refer
to the redacted original; no paraphrasing or sentence repair is performed.
Automatic redaction can miss identifiers or remove meaningful context. Review
files must remain local. No accuracy percentage is inferred from unit tests.

## Blind human sample

Prepare the packet outside the repository:

```sh
python -m scripts.prepare_question_review \
  --synthetic data/samples/synthetic_theme_benchmark.csv \
  --cfpb-dir data/public_samples/cfpb_2017_300 \
  --federal-dir data/public_samples/federal_mirror_300 \
  --output-dir /path/to/local/question-review
```

The sample uses seed `20261006`, drawing 200 sentence occurrences uniformly
without replacement from the complete pooled sentence set. It does not filter
on detector predictions; false negatives remain eligible. Longer comments
contribute more sentences, and repeated wording remains in the sampling frame.
This is a development-corpus estimate, not a representative community sample.

The October 6 run sampled 6,464 sentences: 89 review sentences from CFPB, 77
from the federal sample, and 34 fictional sentences. Corpus fingerprints and
source positions are frozen with the sample. Source texts and predictions are
kept out of Git. The blind page and answer file contain no model predictions.

Open `Hearing_Lens_Question_Review.html` locally. Choose yes/no/unsure, add a
reviewer name and save answers as JSON. Resume by selecting that saved file.
Answers remain in memory until saved. A reload does not save them. Existing
packets cannot be overwritten by the preparation command. The page renders
uploaded sentence text safely as text, not executable HTML, and uses no external
assets, network submission or browser storage.

Review rubric: “yes” means an information or clarification request, even without
a question mark; “no” means a statement, non-informational command or purely
rhetorical wording. Resolve uncertain cases before the final measurement.

```sh
python -m scripts.evaluate_question_review \
  --review /path/to/Hearing_Lens_Question_Answers.json \
  --manifest /path/to/local/question-review/question-review-manifest.json \
  --output /path/to/local/question-validation.json
```

The evaluator rejects changed source text/positions, stale samples, duplicate or
missing rows, invalid labels and labels without a reviewer name. The manifest
fingerprint binds the saved predictions. Reviewer identity is self-reported; this
does not authenticate that a person supplied the labels.

Recall is TP / (TP + FN). False-positive rate is FP / (FP + TN), using actual
non-questions as the denominator. Recall must be at least 80%; false-positive
rate must be strictly below 10%. Both classes and 200 resolved labels are needed
for acceptance. Partial metrics are provisional. Empty denominators remain
unavailable. Blank or unsure labels cannot produce an acceptance pass.

**Human question review completed on October 10, 2026 for the fictional sample.**
All 200 labels were supplied, with no blanks or unsure answers. Initial scoring
found 19 true positives, two false negatives, 179 true negatives and zero false
positives: 90.48% recall and 0% false-positive rate, meeting the numerical targets.
The reviewer subsequently changed two service-request labels from Yes to No after
assistant clarification. The adjudicated result is 19 true positives and 181 true
negatives (100% recall, 0% false-positive rate); this is not a new independent
blind evaluation. Both submissions and scores are preserved locally. The packet
contains 200 occurrences but only 48 distinct wordings, so results are limited
to this fictional development sample. Earlier sentiment/emotion review remains incomplete.

## Development checks

On October 6, all 190 Python tests passed, including 17 new detection/review
checks. `node tests/question_review_ui.mjs` separately checks blank defaults,
answer counts, reviewer-name validation, JSON saving/restoring and preservation
of current answers after an invalid import, using fictional in-memory inputs.
Browser inspection confirmed 200 blank answer controls and the unsure/reset
counter. A native browser download/resume round trip was not verified because
the preview browser session expired; the JavaScript save/resume unit checks passed.
