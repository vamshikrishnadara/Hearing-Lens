# Review fictional questions and calculations

This packet supports independent review of fictional school comments. Answers
start blank. A successful software run, matching spreadsheet formulas or an
assistant's assessment cannot substitute for a person's completed review.

## Prepare a local packet

With the local models installed, run from the repository root:

```sh
python -m scripts.prepare_fictional_review prepare --output-dir ../local-analysis/fictional-review-01
```

The command uses only the committed fictional school benchmark and response.
It refuses an existing destination to preserve previously entered answers.
Start with the generated `START_HERE.md`. Keep the packet and completed answers
outside Git. These files contain no prefilled human judgments.

1. Open `Hearing_Lens_Fictional_Question_Review.html`, enter your name and label
   each sentence Yes, No or Unsure. Save and resume using downloaded JSON.
   Resolve uncertain answers before final evaluation.
2. Read `Fictional_Top_Three_Review.md` and its fictional response. Independently
   select up to three question IDs in priority order, or explicitly confirm that
   none remain unanswered. Record your name and choices in `priority-review.json`
   and set `review_complete` only after reviewing all groups.
3. Check the eight fictional gap calculations using the separately generated
   workbook's source categories. Record your name/date and any discrepancies.

Do not inspect `question-review-manifest.json` or `priority-predictions.json`
before making your independent choices; they contain software predictions.
The response is an authored example, not evidence of any organization's answer.

## Evaluate supplied answers

```sh
python -m scripts.prepare_fictional_review score-questions \
  --answers COMPLETED_ANSWERS.json \
  --manifest ../local-analysis/fictional-review-01/question-review-manifest.json \
  --output ../local-analysis/fictional-question-score.json
```

The scorer rejects a changed sample, missing reviewer or mismatched scope.
Incomplete labels retain pending acceptance. Output files must be new. Labels
from a different packet cannot be reused. For top-three review, use the existing
priority evaluator described in the [question guide](question_mining.md), with
the new packet's predictions, response fixture and completed review. Explain
differing selections after making independent choices.

The optional `scripts/build_gap_spreadsheet.mjs` artifact-runtime builder takes
`gap-spreadsheet-input.json`, an output folder and an optional `YYYY-MM-DD`
preparation date. The date labels the workbook and filename; it does not fill
the human review date. The application's Python dependencies do not include
this optional spreadsheet-authoring runtime.

## October 9 packet and limits

The fixed packet samples 200 sentence occurrences from a pool of 1,337, with
48 distinct wordings. It includes six question groups and eight gap groups.
Repeated wording limits diversity: this is a development review, not an
independent held-out accuracy estimate. Predictions are hidden from the human
question page and priority list; software predictions remain in separate files.

The generated spreadsheet matched all eight pipeline rows, including exact
counts/flags and numeric differences below 1e-12. Zero-reference and changed-input
recalculation checks passed in the authoring runtime. Both sheets were visually
inspected. Native Excel recalculation was not tested. Human review remains pending.

Earlier theme and sentiment/emotion review remains separate. Completing this
fictional packet cannot establish accuracy on real community submissions or
automatically close the brief's broader validation requirements.
