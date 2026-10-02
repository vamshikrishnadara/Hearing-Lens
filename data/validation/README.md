# Human affect validation

The brief requires 60 genuinely hand-labeled comments: 20 each from the synthetic,
CFPB, and federal corpora. No model-generated or assistant-generated labels may
be presented as human ground truth. Agreement remains **pending** until this work
is done. The code can prepare a blind sheet and calculate metrics afterward.

Prepare a local sheet with `python -m scripts.prepare_hand_labels --cfpb-dir PATH
--federal-dir PATH --output /path/outside/git/hand-labels.csv`. If the federal
sample is unavailable, omit its option: the sheet will have 40 prepared comments
and 20 clearly marked pending rows. Do not label pending rows. The fixed seed is
20261001, with 20 distinct nonempty rows selected per supplied corpus.

A person reads each prepared redacted comment without consulting model outputs:

- `human_sentiment`: negative, neutral, or positive, representing expressed tone,
  not whether the person supports a policy. Use neutral for mainly factual text.
- `human_emotion`: anger, disgust, fear, joy, neutral, sadness, or surprise. Pick
  the dominant expressed emotion; use notes for ambiguity rather than inventing
  precise confidence. Concern may express fear; dissatisfaction is not always anger.
- `reviewer`: the human reviewer's name/initials. Add uncertainty and language
  problems to `notes`; discuss ambiguous cases before finalizing the sheet.
- Keep source positions, hashes, and text unchanged. Redaction may miss PII;
  keep the sheet local and review before any sharing.

Then run `python -m scripts.evaluate_hand_labels --labels PATH --predictions-dir
PATH --cfpb-dir PATH --federal-dir PATH`. It verifies source text and row identity,
rejects incomplete/invalid label pairs and duplicate rows, and reports agreement,
confusion matrices, coverage, and exclusions per corpus. A result below 70%
requires a written remediation plan or explicit limitation. Complete validation
requires 20 labeled, model-scored rows per corpus; no metric is invented for an
empty set. If language detection excludes a human-labeled English row, investigate
that exclusion; do not silently treat it as a neutral prediction.

Public review sheets and predictions remain local. Only aggregate measured
results, instructions, and fictional tests belong in Git. Human theme-coherence
review of three themes per corpus is a separate requirement.

## Current ready sheet — October 2

All three source corpora are now available, so preparation produces 60 real
review rows and no federal placeholders. For the current benchmark, pass
`--synthetic data/samples/synthetic_theme_benchmark.csv` to both preparation and
evaluation, along with the `cfpb_2017_300` and `federal_mirror_300` directories.
The fellow cannot review today; the sheet remains blank and agreement remains
pending. Keep prior sheets separate rather than mixing source samples.
