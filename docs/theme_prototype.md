# Theme-analysis prototype - September 23, 2026

This is a command-line/library development prototype. The Streamlit upload
screen still ends at the redacted preview; it has no theme-analysis button yet.
Use fictional data. Theme quality and privacy review are not complete.

## Setup and run

Complete the [README setup](../README.md#local-setup), then run from the repository
root in the same environment:

```sh
python -m scripts.setup_theme_model
python -m unittest discover -s tests -v
python -m scripts.validate_themes
```

The setup command downloads `sentence-transformers/all-MiniLM-L6-v2` from
Hugging Face into the ignored `model_cache/all-MiniLM-L6-v2` directory and records
the resolved revision in `hearing_lens_source.json`. It does not upload comments.
The analysis code loads this local directory with `local_files_only=True` and
`trust_remote_code=False`. No model downloads take place while analyzing comments.
Only model resources are cached; comments, vectors, and results are not cached
or written to disk by the pipeline.

The validation command reads only fixed fictional fixtures and prints JSON.
Redirect that report to a local evidence folder if desired. Model downloads and
reports must not be committed. Without the downloaded model, one real-embedding
integration test is explicitly skipped; other tests use controlled vectors.

Library entry point: `pipeline.themes.analyze_themes(frame, theme_count=6)`.
The input needs `comment_text`; all other columns are ignored. The result contains
theme IDs, keyword labels, counts, shares, candidate quotes, warnings, and
assignments indexed by zero-based input row position. It returns no raw comments
or respondent metadata. Optional respondent deduplication belongs to the existing
ingestion step; this module does not deduplicate respondent IDs itself.

## How the first version works

1. Reject more than 5,000 rows and invalid theme counts (allowed range: 1-15).
   Remove empty comments; preserve input row positions for assignments.
2. Run existing name/contact redaction before deriving any textual output.
   Remove typed markers from modeling text. Ignore standalone contact/address
   sentences only when they contain detected markers and otherwise consist of
   contact boilerplate. Keep the redacted original for candidate quotes.
3. Encode comments locally on CPU with MiniLM and normalize vectors. Comments
   with no analyzable text after redaction are excluded with a notice.
4. Run K-means with a fixed seed and 10 initializations. Reduce the requested
   count when there are fewer distinct vectors. Assign every analyzed comment;
   there is no outlier detector in this version.
5. Rank TF-IDF keywords and phrases (one to three words) within each theme,
   suppress nested keyword duplicates, and build a label from up to three terms.
6. Rank members by cosine similarity to their theme center. Select up to three
   redacted quotes of 12-60 whitespace-delimited words, filtering duplicates and
   near-duplicates using modeling text and vector similarity. If fewer qualify,
   return fewer with an explicit warning instead of padding the result.

This uses K-means for all sizes as an initial baseline. The brief's BERTopic
path, small-file fallback distinction, tiny-cluster merging, quote-swap review,
and language detection are not implemented yet. English is assumed. Long input
may be truncated at the embedding model's context limit, even though the full
redacted comment remains available for quote length checks. These limitations
need to be addressed before calling the Week 2 milestone complete.

## Measured results

Tested with Sentence Transformers 5.7.0, scikit-learn 1.9.1, PyTorch 2.14.0,
spaCy 3.8.16, and MiniLM revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
All 55 automated tests passed, including 12 new theme tests and the real local
embedding integration check. Dependency consistency and whitespace checks passed.

The unchanged 1,000-row fictional sample produced six groups and 15 candidate
quotes. One local run took 4.075 seconds including model loading, excluding setup
downloads and Python imports; this is not a deployed-performance benchmark.

| Generated keyword label | Comments | Candidate quotes |
| --- | ---: | ---: |
| students / classroom / long | 260 | 3 |
| proposal / school / accessibility | 238 | 3 |
| families / need / district fund | 206 | 3 |
| hearing / easier / follow | 161 | 3 |
| data / publish / missed | 85 | 2 |
| broken / exterior / lighting | 50 | 1 |

Adjusted Rand index against the sample's planted categories was **0.1861**
(1 means identical grouping; 0 is approximately chance-adjusted agreement).
This is not classification accuracy. Ground-truth categories were used only for
evaluation, not to generate clusters or labels. Inspection confirms mixed topics
in multiple groups: the largest combines resources, health, transportation, and
safety; the fifth mixes transportation and communication. The lighting group is
coherent but narrow. The two quote shortages reflect duplicate/length filtering.
Zero outliers is a consequence of K-means, not evidence of quality.

The separate six-comment library/bus fixture produced two coherent groups of
three comments and three quotes each. This tiny fixture is a smoke check, not
an independent evaluation set. Manual inspection of the 15 larger-sample quotes
found no visible names, emails, phones, or street/unit values; the scripted
checks found no residual planted name tokens or raw email strings among those
selected quotes. The known broader redaction misses remain and this selected
set does not prove privacy for other comments or uploads.

## Next work

Improve grouping coherence and keyword labels before dashboard integration.
Evaluate the brief's BERTopic approach and review three themes per required
corpus. The two required public corpora remain outstanding; today's evidence
does not satisfy validation on all three corpora. No browser test was performed
because no interface behavior changed.

Reproducible JSON and test output are saved locally in
`daily-evidence/2026-09-23/`. The initial exploratory `theme-results.json` there
predates the contact-boilerplate/deduplication refinement; `theme-validation.json`
is the final validation report for this version.

Implementation references: [Sentence Transformers model API](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html)
and [scikit-learn K-means](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html).
