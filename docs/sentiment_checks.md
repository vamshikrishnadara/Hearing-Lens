# Checking sentiment results

Sentiment labels summarize expressed tone as negative, neutral or positive.
They do not establish whether someone supports a proposal, whether a complaint
is valid, or how the wider community feels. Each comment receives one model
label, even when it contains several different views.

## Inspect a result

1. Open **Sentiment and emotion**, then **Inspect sentiment scores**. The table
   puts the smallest top-two score gaps first.
2. Download the labeled CSV and match **Cleaned comment number** to
   `cleaned_comment_number`. These numbers refer to the cleaned table, not the
   original spreadsheet row or a person's identity.
3. Read the complete `redacted_comment`, including praise, complaints,
   qualifications and requests. Check `affect_status` and `affect_truncated`.
   Excluded comments have no substitute neutral label; truncated model inputs
   may omit part of a long comment.
4. Compare the label with all three sentiment scores. Also check some comments
   with larger gaps: close scores are not the only source of mistakes.
5. If recording corrections, keep them in a separate column in a local copy,
   with a short reason. Preserve the automatic label for comparison. Editing
   the CSV does not update the dashboard, totals or previously downloaded
   briefs; the app does not import corrected labels.

## Read the scores

The following values are illustrative arithmetic, not measured model results.

| Negative | Neutral | Positive | Winning label | Top-two gap |
| --- | --- | --- | --- | --- |
| 0.49 | 0.50 | 0.01 | Neutral | 0.01 (1 percentage point) |
| 0.10 | 0.20 | 0.70 | Positive | 0.50 (50 percentage points) |

The CSV uses scores from 0 to 1; the dashboard displays percentages. The gap is
the highest score minus the second-highest score. It differs from
`sentiment_score`, which is positive minus negative: the examples above have
sentiment scores of -0.48 and +0.60. A neutral winning label can therefore have
a negative mean-tone contribution. Tied top scores have a zero gap; the model's
fixed label order resolves the displayed label, not evidence that one view wins.

Model scores are not calibrated certainty. A 0.70 score is not a guarantee of
70% accuracy, and a large gap does not prove correctness. Missing score details
stay blank; they are not zero. The inspection table does not change any labels.

## Fictional examples to discuss

These are reading examples, not a scored benchmark or model predictions.

| Comment | What to check |
| --- | --- |
| "The new evening class is excellent, and the instructor made everyone feel welcome." | Explicit praise suggests positive tone. |
| "The class was cancelled again without notice, and I am frustrated." | Explicit dissatisfaction suggests negative tone. |
| "What time does registration open on Monday?" | An information request alone does not express positive or negative tone. |
| "The instructor was helpful, but the room was inaccessible and I missed half the session." | Praise and criticism coexist; a single label loses some meaning. Read the full comment before using it in a summary. |

Do not automatically label every question neutral or every requested change
negative. Consider the tone and context of the full comment. If testing a new
classifier, use separate examples with independent labels and compare each
dataset, not just one overall percentage. Do not change reference answers or
choose thresholds solely to make an existing sample pass.

See the [user guide](user_guide.md#7-explore-sentiment-and-emotion) for dashboard
controls and [analytical methods](analytical_core.md) for model limitations.
