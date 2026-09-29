# Automatic theme-count selection - September 29, 2026

## Scope and behavior

Added opt-in `analyze_themes(frame, theme_count="auto")` for input files with
fewer than 150 rows. The limit includes blanks and is checked before embeddings.
Manual 1-15 selection and the default six-group behavior remain unchanged.
This is a library feature; the upload screen still has no theme controls.

The brief specifies silhouette-selected K-means counts between 4 and 12 for
small files. The implementation scores feasible candidates using Euclidean
silhouette on normalized comment vectors, matching K-means' Euclidean geometry.
A candidate must be no larger than the distinct-vector count and strictly smaller
than the analyzed row count. Each uses seed 42 and 10 initializations. Highest
score wins; exact ties prefer smaller counts. Recorded metadata exposes every
valid candidate's score and any skipped count. Collapsed or nonfinite candidates
are skipped; unexpected failures produce a sanitized error rather than results.

When no candidate is feasible or scoreable, the result is one group with an
explicit warning and no silhouette score. This covers tiny and duplicate-heavy
inputs; it is not evidence that they contain only one topic. Users can choose a
manual count. No minimum-size merging, BERTopic routing, or language detection
was added today. The remaining theme requirements are still incomplete.

## Reproducible comparison

From the repository root with the existing local model installed:

```sh
python -m unittest discover -s tests -v
python -m scripts.compare_theme_selection --sample-dir data/public_samples/cfpb_2017
```

Optionally add `--baseline-report /path/to/cfpb-keyword-validation.json` to check
the earlier manual result after verifying its sample hash. The comparison emits
aggregates, never public narrative text, complaint IDs, or quote text. It checks
the same fixed 100-row CFPB sample and the existing 24-row fictional fixture.
Only comment text enters analysis; fictional category labels are used afterward.

Sample SHA-256: `e7faa7957fe104113c2e145b7c65b36100025d6a4550cf31eb0ebcae6b362318`.
MiniLM revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
Environment: Sentence Transformers 5.7.0, scikit-learn 1.9.1, PyTorch 2.14.0,
spaCy 3.8.16. This run reused the existing model; no dependency was added.

## Measured results

| Dataset and mode | Selected groups | Group sizes | Candidate quotes | Groups with 3 quotes |
| --- | ---: | --- | ---: | ---: |
| CFPB manual six | 6 | 34, 30, 18, 14, 3, 1 | 12 | 2 |
| CFPB automatic | 6 | 34, 30, 18, 14, 3, 1 | 12 | 2 |
| Fictional manual three | 3 | 8, 8, 8 | 9 | 3 |
| Fictional automatic | 12 | Twelve groups of 2 | 12 | 0 |

CFPB silhouette scores for k=4 through 12, respectively:
0.032558, 0.035319, **0.040712**, 0.030486, 0.032513, 0.028559,
0.024920, 0.024571, 0.019109. No candidate was skipped. The best score is low;
selecting six does not establish good topic separation or semantic accuracy.
The manual result's complete themes (including labels, shares, and redacted
quotes), assignments, and removal/exclusion counts exactly match September 28.
There is no hand-coded theme truth for the CFPB sample and no new human review
or supervisor sign-off is claimed. Existing mixed groups and quote gaps remain.

The fictional fixture has three planted topics and introduction/no-introduction
pairs. Its true count is below the brief's automatic minimum. Automatic mode
selected 12 at silhouette 0.469765, separating pairs into small groups. Agreement
with planted categories (adjusted Rand index) dropped from 1.0 for manual three
to 0.188235 for automatic selection. ARI is not an accuracy percentage. This
explicitly demonstrates a limitation of the count range and duplicate-sensitive
geometry; the extra quotes do not establish better themes. Keep manual selection
available and review results rather than assuming automatic is better.

## Verification and remaining work

All 90 automated tests passed. The 13 added checks cover candidate range and
maximum score, exact ties, tiny/duplicate-heavy inputs, skipped scores, sanitized
failures, 149/150-row boundaries, manual regression, original row positions,
redacted quotes, and text-free comparison reports. All reported candidate quote
lengths were within 12-60 words. This does not certify privacy or semantic quality.
No interface behavior changed, so no browser test was performed.

Next priorities remain tiny-cluster handling, the larger-file BERTopic path,
keyword quality, and validation on the required federal corpus. The automatic
mode is an incremental implementation of the small-file requirement, not
completion of the analytical core.

References: [scikit-learn silhouette score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html)
and [silhouette analysis for K-means](https://scikit-learn.org/stable/auto_examples/cluster/plot_kmeans_silhouette_analysis.html).
