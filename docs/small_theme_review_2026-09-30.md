# Small-theme merging - September 30, 2026

## Scope

The brief asks for tiny-cluster merging. This implements a conservative,
experimental library option; it does not claim that small themes are unimportant
or that removing them improves semantic quality. Default behavior is unchanged:

```python
result = analyze_themes(frame, theme_count="auto", merge_small_themes=True)
```

The option also works with manual counts. It can reduce the final number below
the manual request or below the automatic range of 4-12. The count selection
and its silhouette scores describe the initial groups, not the merged result.
There is no new Streamlit control, dependency, or model download.

## Fixed policy

- Small means fewer than three comments. The minimum cosine similarity is 0.75.
  Both are fixed experimental choices made before this comparison, not calibrated
  thresholds or values specified by the official brief.
- Compute each original group's mean vector and normalize it. A near-zero mean
  (norm at most 1e-12) cannot provide a qualifying match.
- At least one current group in a proposed pair must still be small. Two groups
  already at size three or above never merge under this policy.
- For groups that already include earlier merges, require every cross-pair
  original centroid similarity to meet the threshold. Choose the candidate with
  the highest minimum similarity. Exact ties use original display-group order.
- Merge whole memberships, then repeat until no eligible pair remains. The
  original-center requirement prevents single-link similarity chains from
  joining dissimilar original groups. It does not establish semantic equivalence
  or ensure that an original group was coherent.
- Preserve unmatched small groups and warn about them. Never discard a comment.
  The final display order is largest group first, then earliest input position.
- Rebuild keyword labels, counts, shares, assignments, centers, and quote choices
  from final memberships. Existing redaction, length, and duplicate rules apply.

`theme_merging` records enabled state and initial/final counts. When enabled it
also records thresholds, merge history with original theme IDs and similarity,
final-theme source IDs, and retained small-theme IDs. IDs refer to the original
size/position-sorted display groups, not raw K-means labels. Unexpected merger
failures stop results with a sanitized error. Selection metadata is not relabeled
as a post-merge quality score.

## Comparison

The same 100-row CFPB sample and 24-row fictional fixture from September 29
were used, with the same installed MiniLM model and no threshold tuning.

| Dataset/mode | Groups off / on | Small groups off / on | Quotes off / on | ARI off / on |
| --- | --- | --- | --- | --- |
| CFPB automatic | 6 / 6 | 1 / 1 | 12 / 12 | No theme ground truth |
| CFPB manual six | 6 / 6 | 1 / 1 | 12 / 12 | No theme ground truth |
| Fictional automatic | 12 / 11 | 12 / 10 | 12 / 12 | 0.188235 / 0.246628 |
| Fictional manual three | 3 / 3 | 0 / 0 | 9 / 9 | 1.0 / 1.0 |

The public sample's group sizes stayed 34, 30, 18, 14, 3, 1. The singleton did
not meet the threshold for any partner and remains visible with a warning.
Complete themes and assignments are identical with merging on/off. The disabled
manual result also matches the stored September 28 result's themes, assignments,
warnings, analyzed count, and removal/exclusion counts. The earlier result lacks
the newer selection metadata, so no historical equality is claimed for that field.

The fictional automatic result merged original groups 9 and 11 at similarity
0.767400 into one group of four. Final sizes were 4 followed by ten groups of 2.
It still substantially over-splits the three planted categories, and no group
has three eligible quotes (the merged group has two). Manual three remains the
better match on this fixture. The ARI increase is development-fixture agreement,
not accuracy or proof of improved public-data quality. No new public-corpus human
coding or supervisor sign-off is claimed.

All four comparisons preserved analyzed row positions. Each row was assigned
once; counts and shares matched assignments; each quote belonged to its final
theme, matched its redacted source text, and met the 12-60-word rule. These are
consistency checks, not privacy certification. CFPB still has only two themes
with three eligible quotes; fictional manual three has three, automatic has zero.

## Validation and reproduction

All 106 automated tests passed, including 16 added tests covering qualifying and
unmatched groups, two-small-group merging, no merging of already-sized groups,
chain prevention, deterministic choices, threshold boundaries, zero centers,
nonmutation and membership conservation, opt-in behavior, rebuilt output,
final IDs, fallback warnings, sanitized failures, and aggregate reports that detect
inconsistent counts or quotes without printing source text. Dependency and
whitespace checks passed. No UI behavior changed, so no browser test was run.

```sh
python -m unittest discover -s tests -v
python -m scripts.compare_small_themes --sample-dir data/public_samples/cfpb_2017
```

Optionally add `--baseline-report /path/to/cfpb-keyword-validation.json` to compare
with the stored public manual-six result. The sample manifest is verified first,
and the optional baseline must have the same sample hash. The report contains
only aggregate checks and theme-number merge metadata, not public narrative
text, complaint identifiers, labels, or quote text. Only comment text enters
analysis; fictional labels are used afterward for ARI.

Sample SHA-256: `e7faa7957fe104113c2e145b7c65b36100025d6a4550cf31eb0ebcae6b362318`.
MiniLM revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
Versions: Sentence Transformers 5.7.0, scikit-learn 1.9.1, PyTorch 2.14.0,
spaCy 3.8.16. Local detailed aggregates and test output are stored outside Git.

## Remaining limits

Centroid similarity can combine different meanings, including a minority view
with a larger topic. The rule does not classify agreement, disagreement, or
importance. The threshold has not been calibrated on an independent corpus.
Keeping unmatched groups is intentional; fewer groups alone is not success.
The initial count and embeddings still dominate the result. This feature is
not a general solution to over-splitting, mixed themes, quote shortages, or the
unfinished BERTopic path. Broader validation, including the required federal
corpus, remains necessary before completing the theme-engine milestone.
