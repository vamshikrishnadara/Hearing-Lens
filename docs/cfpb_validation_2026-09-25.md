# First CFPB theme validation - September 25, 2026

## Scope and repeatability

Ran the existing sentence-weighted MiniLM/K-means prototype, with six requested
themes, on the [100-narrative public sample](cfpb_source.md). No theme, keyword,
redaction, or quote-selection code changed today. This checks transfer to public
text; it is not a completed quality benchmark or supervisor gate approval.

After preparing the sample and installing the models from the README:

```sh
python -m scripts.validate_cfpb_themes --sample-dir data/public_samples/cfpb_2017
python -m unittest discover -s tests -v
```

The validation command checks sample/manifest consistency before analysis, prints
JSON, and makes no network request or file writes itself. Redirect stdout to a
local evidence file if desired. The report includes full redacted review text;
it should stay local. Metadata goes only into contextual product counts, never
into the embeddings. Public product categories are not a hand-coded theme truth.

## Observed results

| Check | Result |
| --- | --- |
| Input / analyzed | 100 / 100 narratives; none empty or excluded |
| Theme sizes | 38, 29, 16, 13, 3, 1 |
| Redacted word count | Minimum 5; median 133.5; maximum 735 |
| Comments within the 12-60-word quote range | 19 of 100 |
| Selected candidate quotes | 10; only two themes have all three |
| Themes with an all-X placeholder keyword | 4 of 6 |
| Selected quote lengths | All 10 within 12-60 words |
| Raw email pattern among selected quotes | Zero matches; not a complete identifier check |
| Theme-analysis runtime | 6.774 seconds in one local run, including model load |
| Automated tests | 69 passed, including seven new public-sample/validation tests |

Runtime excludes Python imports, source downloading, sample preparation, CSV
loading, and preparation of the separate review packet. This small local run
is not a production-performance benchmark. All comments are assigned because
K-means has no outlier detector; that does not establish theme quality.

The tests use fictional data only. Five preparation tests cover deterministic
sampling, filters/long text, bad records, manifest hashes/overwrite protection,
and ambiguous archives. Two validation tests cover mismatched sample metadata
and the separation of model input, review redaction, and contextual fields.
Existing pipeline tests, including the real local model check, still pass.

## Review of three groups

Assistant-assisted inspection covered the first five input positions in each
of the three largest groups (15 full redacted narratives), plus all 10 selected
candidate quotes. This selection is deterministic, but not random or exhaustive.
These observations are not independent human coding or supervisor sign-off.
No consumer text or public complaint IDs are reproduced in this report.

| Group and generated label | Review findings |
| --- | --- |
| 1: `xxxx / account / payment` (38 comments; 3 quotes) | Rows 4, 7, 9, 13, 15 concern card closure fees, a changing loan payoff amount, debt-collection harassment, an unauthorized account, and payment allocation. Broad account/payment overlap exists, but this is not one narrow theme. |
| 2: `xxxx / credit / equifax` (29 comments; 3 quotes) | Rows 5, 8, 12, 33, 46 cover a disputed card application, an unknown account, credit inquiries, a disputed collection contract, and suspected scam calls. Credit/dispute overlap exists; the company keyword does not adequately describe all reviewed narratives. |
| 3: `xxxx / loan / bankruptcy` (16 comments; 0 quotes) | Rows 6, 10, 24, 25, 29 include four bankruptcy/discharge concerns and one goodwill request for removing late-payment marks. The loan/bankruptcy label is more informative, but not an exact description of every member. No member meets current quote eligibility. |

Other groups are `debt / company / xxxx` (13 comments, 2 quotes),
`paid agreed / account paid / credit` (3 comments, 2 quotes), and
`box / chase / deposit` (1 comment, no quotes). The singleton reinforces the
unfinished tiny-cluster handling requirement.

## Concrete findings for follow-up

1. **Source placeholders pollute keywords.** All-X masking tokens appear in four
   groups' keywords and four displayed labels. Introduce a carefully scoped
   modeling/keyword normalization rule that preserves the original redacted quote.
2. **Long comments leave quote gaps.** Only 19 comments are initially short
   enough; the selected ten cannot supply three quotes to every group. Evaluate
   how to support faithful short excerpts with traceability, or a review workflow,
   against the brief's verbatim-quote requirement. Do not silently truncate or pad.
3. **Redaction removes ordinary text.** In reviewed rows, the unit-number pattern
   masks words beginning with `ste`, including `step`, `steps`, and `steal`.
   The pattern currently allows no separator after `STE`.
   Add focused fictional regressions before changing it; retain real unit coverage.
4. **Labels and cluster sizes need work.** A company name can dominate a label,
   unrelated concerns can share a broad group, and a singleton remains. The
   brief's automatic choice of cluster count and tiny-cluster merging are pending.

Inspection of the ten candidate quotes found no obvious unmasked personal names,
emails, phone numbers, or full street addresses. Organization names, state codes,
and financial details remain, as do the source's masks. This limited check is not
a privacy guarantee; source masking prevents a reliable measurement of our
redaction recall. False positives in the longer review text are confirmed.

## Remaining scope and evidence

This is the first small public corpus run. The federal public-comment corpus,
expanded CFPB review, BERTopic path, silhouette-selected small-file clustering,
KeyBERT/MMR labels, quote review, language handling, and dashboard integration
remain unfinished. No browser test was performed because the interface did not
change. Keep working against the existing conditional end-of-Week-7 plan.

Local evidence in `daily-evidence/2026-09-25/`: `public-sample/cfpb_sample.csv`,
`public-sample/cfpb_manifest.json`, `cfpb-theme-validation.json`,
`automated-tests.txt`, and the daily PDF. Detailed JSON contains redacted text
for local review; only aggregate findings and fictional tests go into Git.

Model: MiniLM revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
Environment: Sentence Transformers 5.7.0, scikit-learn 1.9.1, PyTorch 2.14.0,
spaCy 3.8.16. No new dependencies were installed.
