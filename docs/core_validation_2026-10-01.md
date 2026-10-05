# Analytical-core validation - October 1, 2026

## What was run

The local core now runs themes, sentiment, emotion, theme/period aggregates,
and timeline generation. The fixed synthetic sample (1,000 rows) and fixed CFPB
sample (100 narratives, existing SHA-256
`e7faa7957fe104113c2e145b7c65b36100025d6a4550cf31eb0ebcae6b362318`)
were each analyzed twice in one process with two PyTorch CPU threads. Only model
resources are cached; data and analysis results are recomputed on the second run.
Timings exclude Python imports, setup/downloads, and output serialization. The
synthetic first run includes initial model loading; the CFPB first run reuses
those resources. These are local measurements, not deployed-service benchmarks.

| Check | Synthetic | CFPB |
| --- | --- | --- |
| Backend | BERTopic | Automatic K-means |
| Themes / outliers | 6 / 0% | 6 / 0% |
| Sizes | 503, 269, 90, 49, 48, 41 | 34, 30, 18, 14, 3, 1 |
| Selected quote counts | 3, 3, 2, 1, 1, 1 | 3, 3, 1, 2, 2, 1 |
| First measured run | 17.883 seconds | 18.188 seconds |
| Repeat run | 6.664 seconds | 17.243 seconds |
| Affect-scored / language-uncertain or non-English | 980 / 20 | 98 / 2 |
| Rows truncated for affect | 0 | 9 |
| Timeline periods | 3 | 86 |
| Repeated structured outputs identical | Yes | Yes |

Assignments were unique, counts plus outliers matched the analyzed rows, and all
selected quotes belonged to their assigned theme, exactly matched the redacted
original text, and were 12-60 words. Both synthetic timeline chart types were
visually checked in a browser. These consistency checks do not certify privacy
or topic coherence. The three-quotes-per-theme requirement is not met.

The initial BERTopic trial reduced toward 15 groups and left many one-quote
groups. The final configuration reduces density topics toward six by default,
retaining warnings and explicit outliers. This change reduces fragmentation but
does not solve quality: development ARI against planted synthetic categories is
0.232002, below the earlier sentence-weighted K-means comparison's 0.2647. ARI is
not accuracy; the density method is not presented as a demonstrated improvement.
It implements the required algorithm while making its current limitations visible.

## Verification and provenance

All **133 automated tests passed**, including 27 new checks for routing, outliers,
keyword settings, quote review, language exclusions, inference batch size and
truncation, offline model reuse, aggregation, period fallback, blind review sheets,
invalid human-label records, and agreement reporting. Dependency consistency and
whitespace checks passed. The public sample and model files remain outside Git.

Versions: BERTopic 0.17.4, KeyBERT 0.9.0, langid 1.1.6, Transformers 5.17.0,
PyTorch 2.14.0, scikit-learn 1.9.1. Model revision hashes and API behavior are in
[analytical-core usage](analytical_core.md). Review packets include an ordered
comment-text fingerprint; agreement evaluation rejects predictions from a
mismatched source. Output never treats automated predictions as human labels.

The reproducible command is:

```sh
python -m scripts.validate_core --cfpb-dir PATH --output-dir LOCAL_PATH
```

Add `--federal-dir PATH` only after preparing and verifying that sample. The local
output contains aggregate JSON, redacted review packets, and self-contained HTML
charts. Only the aggregate findings in this document are published to Git.

## Incomplete acceptance requirements

The federal download hit the official API's public-key rate limit (HTTP 429);
no complete third-corpus sample or benchmark is claimed. The downloader now
checkpoints successful responses for a later retry. A supplied export or configured
key can unblock that work; the source is documented in [federal source notes](federal_source.md).

The human sheet currently has 40 prepared rows and 20 explicit federal placeholders.
Human sentiment/emotion agreement is **pending**, not 0% or 100%. Coherence review
of three themes per corpus also needs human review. Language detection excluded
20 known-English synthetic rows as uncertain, a measurable limitation requiring
review rather than silent neutral labels. Long CFPB comments were truncated for
affect and often do not qualify as full-comment quotes.

The current implementation does not satisfy every Week 2/3 benchmark and has not
passed Gate 1. See [methodology](methods.md) for validation limitations.
