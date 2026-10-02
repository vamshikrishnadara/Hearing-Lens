# Week 2 validation — October 2, 2026

## Main benchmark and reproducibility

The local main benchmark now contains a richer fictional 1,000-row hearing file,
300 fixed CFPB narratives, and 300 FAA comments from the public Mirrulations
archive of Regulations.gov. Original samples are retained separately. No public
comment was edited, length-filtered, or selected for its model outcome. Public
text, review packets, and manifests remain local; source preparation and hashes
are documented in the corpus source notes.

The additional fictional fixture has 48 substantive authored templates rather
than the original 24 short templates. It is development data, not an independent
held-out test. Configuration comparisons were explored on these corpora; a better
score is not evidence of generalization. The old fixture's quote shortages are
still reported and must not be concealed by the new benchmark.

```sh
python -m scripts.validate_week2 --output-dir data/results/week2
```

The executed `notebooks/week2_theme_validation.ipynb` reruns the three main
corpora and the original synthetic stress fixture, publishing aggregate output
only. The selected source hashes and row identities accompany local packets.

## Implementation changes

BERTopic fits distinct embedding vectors once, then restores all original rows
and counts. This reduces disconnected neighborhoods caused by repeated wording.
The reduction target excludes the outlier bucket. Conservative centroid
refinement uses original embedding space: similarity >=0.45 and margin >=0.03
are required for reassignment. Ambiguous rows retain their density assignment;
original density outliers remain outliers. No ground-truth category is supplied
to these steps. These thresholds are experimental, not calibrated confidence.

Long comments can contribute contiguous complete-sentence excerpts of 12–60
words. Source offsets and an explicit excerpt flag make them traceable. Contact-
bearing sentences are avoided, duplicate wording is filtered, and insufficient
material leaves visible shortages. Excerpts never concatenate different authors,
paraphrase text, or add words. The legacy full-comment-only option remains.
Quote embeddings are computed only for nearest-first candidates actually needed.

An explicit contact-name rule catches capitalized full names immediately before
a detected email/phone address where the small NER model missed them. It is not
a general privacy guarantee. Known over-redaction, such as a conference-call
phrase mistaken for an address, remains disclosed.

## Measured findings

All three main samples produce six themes, three distinct source-valid quotes
per theme, and fewer than 20% density outliers: synthetic 4.4%, CFPB 16.67%, FAA
19%. The fictional development ARI is 0.705765. Each theme-only run completes
under two minutes on the tested laptop CPU. The original synthetic stress file
still produces quote counts 3,2,2,2,2,2; that unmet case is retained explicitly.
Consult the executed notebook and current core report for the exact run timings.
These are local measurements; production deployment is scheduled later.

## AI-assisted qualitative inspection, not human acceptance

The assistant inspected selected quotes and a systematic sample of members of
the three largest themes per corpus. Some long public comments were inspected
as excerpts. This is preliminary development inspection, not independent human
coding or a completed human coherence/privacy review. Local packets preserve
complete redacted comments for the eventual reviewer.

| Corpus/theme | Observation | Follow-up |
| --- | --- | --- |
| Fictional 1 | Mostly hearing accessibility; includes late notices and unanswered questions | Broad participation grouping; distinguish accessibility from communication during review |
| Fictional 2 | Mostly counseling/mental health; includes emergency evacuation at row 259 | Mixed member needs reviewer attention |
| Fictional 3 | Classroom resources, books, supplies, teaching support | Sampled members were substantively aligned |
| CFPB 1 | Broad payment/loan servicing group; includes identity-theft loan concerns | Review breadth and overlapping issues |
| CFPB 2 | Credit-report disputes, inaccurate records, verification problems | Broadly related; tone and alleged causes vary |
| CFPB 3 | Unauthorized inquiries/security concerns, with website-access complaint at row 254 | Mixed member; avoid presenting label as exhaustive |
| FAA 1 | Objections to effectiveness/burden of external aircraft markings | Broadly related; multiple reasons and perspectives |
| FAA 2 | Registration-number display, privacy, format and cost; some very short support statements | Topic membership does not imply shared stance |
| FAA 3 | Scope/enforcement/security of drone marking; overlaps other groups | Weak separation; review before public use |

Selected quotes were inspected for obvious name/email/phone remnants. Contact-tail
avoidance was added after an FAA quote included location context alongside masks.
Automated source checks and AI inspection do not certify complete anonymization.
Human review remains pending, and these findings do not establish that every
comment in every group belongs together.

## Remaining closeout

The software and numerical checks are available, but Week 2's qualitative
acceptance cannot be claimed complete without the human review. The fellow cannot
review today. Formal supervisor gate meetings have been waived as a prerequisite;
that is separate from the quality requirement. Code licensing is undecided and
weekly public updates are drafts, not claimed publications.
