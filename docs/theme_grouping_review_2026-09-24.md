# Theme grouping review - September 24, 2026

## Focus and method

Improve the initial theme grouping without changing the sample, redaction rules,
K-means settings, keyword algorithm, or quote eligibility rules. The sample has
177 copies of the same hearing-attendance introduction across multiple topics.
That motivated testing a sentence-based representation that gives common
sentences less influence, while retaining full redacted quotes.

Two limited exploratory alternatives were checked: centering and renormalizing
whole-comment vectors (ARI 0.2278), and sentence-frequency weighting (0.2647),
against the original 0.1861. Sentence weighting was selected for this experimental
prototype. This choice used development results; it is not held-out evidence or
proof of improvement on real uploads. No hand-written topic rules or planted
category labels are passed into clustering. The separate fixture below was
added as a smoke check after selecting the method, not as a public benchmark.

The [prototype guide](theme_prototype.md) describes the weighting formula and
its limitations. The default is now `sentence_weighted`; `whole_comment` remains
available to reproduce the baseline. Both use the same local MiniLM model and
K-means configuration. No dependency or model download was required today.

## Reproducible comparison

Run from the repository root after completing model setup:

```sh
python -m scripts.compare_theme_grouping
python -m scripts.validate_themes
python -m unittest discover -s tests -v
```

The comparison command prints a JSON report from fixed fictional inputs. It
includes model revision, library versions, theme composition, full results,
quote checks, and the mode for each run. Evaluation labels are read only after
analysis of the comment column. Reports are saved locally, outside the repository.

| Check | Original whole-comment mode | Sentence-weighted mode |
| --- | ---: | ---: |
| Unchanged sample comments analyzed | 1,000 | 1,000 |
| Groups | 6 | 6 |
| Adjusted Rand index (ARI) | 0.1861 | 0.2647 |
| Candidate quotes | 15 | 15 |
| Selected quotes within 12-60 words | 15/15 | 15/15 |
| Residual planted-name/raw-email flags in selected quotes | 0 | 0 |
| Separate fixture: 24 comments, 3 topics, ARI | 1.0000 | 1.0000 |
| Separate fixture: pairs staying together with/without an introduction | 12/12 | 12/12 |
| Separate fixture: candidate quotes | 9 | 9 |

ARI is chance-adjusted agreement between groupings, not classification accuracy.
The development-sample increase is 0.0786. Its categories have semantic overlap
and comments repeat a small number of templates. Do not interpret 1,000 rows as
1,000 independent examples, or the gain as evidence that every theme improved.

The new 24-comment fixture uses 12 separately authored statements about libraries,
bus service, and drainage, each repeated with a generic thank-you introduction.
Both methods formed three groups of eight. This shows preservation on an easy,
small example; it does not distinguish the methods' quality on real-world data.
The original six-comment library/bus fixture also still forms two groups of
three, with three quotes each.

All **62 automated tests passed**, including the real local model check. Seven
new tests cover common-introduction influence, repetition within a comment,
single-sentence vectors and row order, the original embedding path, full redacted
quote preservation, invalid mode handling, and degenerate averaged vectors.
The earlier name/contact boundary check now examines every embedded sentence.

## Manual review and remaining problems

| New keyword label | Comments | Quotes | Review |
| --- | ---: | ---: | --- |
| students / classroom / long | 300 | 3 | Still mixes transport, classroom resources, health, and safety. |
| school / proposal / counselors | 235 | 3 | Health and classroom staffing overlap; includes safety comments. |
| families / included / accessibility | 209 | 3 | Accessibility is prominent, but safety, transport, and communication remain mixed. |
| hearing / meeting / dates | 115 | 3 | Accessibility and communication overlap; includes six transport comments. |
| easier / follow / make | 91 | 2 | Combines communication with online accessibility; label remains vague. |
| broken / exterior / lighting | 50 | 1 | Coherent but narrow; repeated template limits distinct quotes. |

Read all 15 selected large-sample quotes and nine new-fixture quotes. No visible
personal names or raw contact/address values were found. Automated checks cover
length, planted name tokens, and raw emails, not every identifier type. Existing
redaction misses remain; these checks do not certify privacy. The unchanged
quote eligibility rules still leave two groups short of three quotes.

One sequential comparison measured 4.104 seconds for the first baseline run and
1.240 seconds for the subsequent weighted run on the large sample. The first
loads model resources and the later run is warm, so this is **not a fair speed
comparison**. A separate fresh-process weighted run took 3.737 seconds including
model loading, excluding imports/setup. No production-performance claim is made.

No interface changes or browser tests were performed. K-means still assigns all
comments, with no outlier detector. Public-corpus evaluation, the brief's BERTopic
path, tiny-cluster merging, language handling, quote review, and dashboard
integration remain unfinished. Continue Week 2 work within the existing delivery
plan; this change does not complete or approve a supervisor review gate.

## Local evidence

`daily-evidence/2026-09-24/` (beside the repository) contains:

- `theme-before.json` and `theme-after.json`: original and updated validation runs.
- `theme-comparison.json`: side-by-side comparison on both fixed fixtures.
- `exploration.json` and `explore_grouping.py`: the limited exploratory comparison.
- `automated-tests.txt`: the full 62-test result.
- Daily evidence PDF: a short shareable record of completed work and limitations.

Versions remain Sentence Transformers 5.7.0, scikit-learn 1.9.1, PyTorch 2.14.0,
and spaCy 3.8.16. MiniLM revision:
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
