# Label validation tools

Prepare a blind fictional review packet using:

```sh
python -m scripts.prepare_fictional_core_review prepare --output-dir ../local-analysis/core-review-01
```

The local HTML page supports sentiment, emotion and theme inspection. Answers
begin blank and can be saved and resumed. Keep review files outside Git and
leave source identifiers and text unchanged so scoring can verify the packet.

Sentiment choices are negative, neutral and positive. Emotion choices are anger,
disgust, fear, joy, neutral, sadness and surprise. Judge expressed tone rather
than agreement with a topic. Use unsure for unresolved judgments.

The evaluator checks row identity, allowed labels, source fingerprints and
coverage, then reports agreement, confusion tables and model exclusions. Empty
or unresolved inputs do not produce a completed result. Machine predictions
must not be substituted for independent reviewer judgments.

See [review-tool instructions](../../docs/fictional_review.md) for scoring commands.
