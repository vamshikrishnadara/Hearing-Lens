# Targeted name-redaction validation - September 22, 2026

## Task and method

Reproduced the previously observed removal of the adjective `Broken` in the
opening phrase `Broken exterior lighting`. Baseline application revision:
`e6268d4`. Added a separate six-case fictional fixture and extended
`python -m scripts.validate_person_redaction` to report its expected outputs.
Kept the original 22-case and 1,000-row fixtures unchanged for comparison.

Applied a narrow post-detection exception only to the opening adjective phrase.
All reported results below were measured locally with spaCy 3.8.16 and
`en_core_web_sm` 3.8.0. The model was not retrained or replaced.

## Before and after

| Check | Before | After |
| --- | --- | --- |
| Incorrect `Broken` replacements in 1,000-row sample | 45 | 0 |
| Fully removed planted names in that sample | 67 / 79 | 67 / 79 |
| PERSON markers in that sample | 112 | 67 |
| Total replacement matches in that sample | 438 | 393 |
| Email / phone / street / unit replacements | 79 / 79 / 84 / 84 | 79 / 79 / 84 / 84 |
| Fully removed name mentions in original 22-case fixture | 16 / 18 | 16 / 18 |
| Name-free controls receiving PERSON markers | 1 / 6 | 0 / 6 |
| New focused cases matching exact expected output | 3 / 6 | 6 / 6 |

The lower replacement total is expected: the rule removes 45 incorrect PERSON
markers, not 45 successful name detections. The sample still has 12 planted
names that are not fully removed.

## Examples and regression checks

- `Broken exterior lighting near the entrance needs repair.` now remains intact.
- `Broken exterior lighting was reported by John Smith.` now preserves the
  adjective and still replaces `John Smith` with `[PERSON]`.
- Fictional name contexts such as `Broken Smith spoke at the hearing.`,
  `Contact Broken at resident@example.org.`, and `My name is Broken...` retain
  the expected name redaction. There is no global allowlist for the word.
- Longer PERSON spans and mentions away from the opening phrase are not
  exempted. Boundary tests supply controlled detections to verify these rules.
- Preview checks verify preserved original text in memory, excluded metadata,
  and retained name/email/phone redaction and counts in the same comment.

All 43 automated tests passed (39 existing plus four new tests). Existing
failure-blocking, overlap, ingestion, and app checks also passed. Tests used
fictional data and the real local model, with controlled detections for boundary
cases. No browser-level validation was performed today.

## Limitations and evidence

These fixtures were used during development and are not an independent privacy
benchmark. The correction is restricted to one adjective phrase; `Broken windows
need repair.` remains an observed false-positive context outside this change.
The original misses involving `Anne-Marie O'Neill` and `Elena` remain. An unusual
name at the start of the exempted phrase could be retained; the heuristic is not
proof that the text is anonymous. Continue using fictional data and reviewing
output before sharing it.

Before/after JSON reports, the automated-test output, and the daily evidence PDF
are kept locally in `daily-evidence/2026-09-22/`, outside the repository.
