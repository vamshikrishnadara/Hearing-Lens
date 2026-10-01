# Gate-status checklist - October 1, 2026

This is the repository's working milestone board. Status means **implemented**,
**verified**, **pending**, or **blocked**; none of these implies Benjamin's approval.
The fellow reported that no gate review has yet been submitted. Gate 0 and Gate 1
are therefore **pending review**, not approved. Weekly dates use September 14 as
the working kickoff and do not change the official brief's milestones.

## Gate 0 - scope and schema

| Requirement | Current evidence/status |
| --- | --- |
| Repository, loader, schema, wireframe | Implemented; loader regression checks pass; docs/schema.md and docs/wireframe.md available |
| Three development corpora | Synthetic and CFPB available locally; federal downloader implemented, complete sample blocked by official API HTTP 429 |
| Scope/schema demonstration and approval | Pending Benjamin's live review |
| License/ownership wording, hours, check-in time | Requires explicit confirmation with Benjamin; not inferred from code |
| Project tracking | This board and daily_delivery_schedule.md; no hosted GitHub Project board claimed |
| Required kickoff/public update | Publication unverified; drafts or repository updates do not count as posts |

## Week 2 theme-engine exit checks

| Requirement | Current evidence/status |
| --- | --- |
| Redaction before display | Existing implementation and regressions; known entity misses remain |
| BERTopic >=150 rows / K-means smaller inputs | Implemented in pipeline.core; routing and outlier tests pass |
| KeyBERT 1-3 grams / MMR labels | Implemented; candidate-vocabulary and configuration tests pass |
| Small-group handling / manual count | Implemented; density reduction is an upper target, K-means provides manual counts |
| Synthetic 5-15 themes and <20% outliers | Measured 6 themes, 0% outliers on the fixed 1,000-row sample |
| Three eligible distinct quotes per theme | Not met: synthetic counts 3,3,2,1,1,1; CFPB 3,3,1,2,2,1 |
| Quote swapping | Eligible alternative pool and library swap implemented; dashboard control pending Week 5 |
| Synthetic run under two minutes | Measured first core run 17.883s, including model loading but excluding imports/setup |
| Three-theme coherence review per corpus | Review packets prepared for two corpora; human review and federal corpus pending |
| Notebook showing all three corpora | Notebook review workspace and script/HTML reports prepared for two; executed three-corpus notebook deliverable not complete |

## Gate 1 - analytical core, target end Week 3

| Requirement | Current evidence/status |
| --- | --- |
| Sentiment and seven-class emotion inference | Implemented; local pinned models, batch size 32, explicit exclusions/truncation |
| Aggregation by theme and period | Implemented; denominator, missing-value and tie tests pass |
| Timeline rendering / missing-date behavior | Implemented; both chart types visually checked on synthetic data |
| Load model resources once | Bounded model cache; offline reuse test passes; no comment-result cache |
| Repeat run under 30 seconds | Synthetic 6.664s; CFPB 17.243s in the measured process |
| 60 human labels, 20 per corpus | 40 blind review rows prepared, 20 federal placeholders; zero human labels entered |
| Published agreement / remediation if below 70% | Evaluation script and methods draft implemented; actual agreement pending human labels |
| Live analytical demo on all three corpora | Two-corpus development flow verified; federal run and Benjamin's demo pending |
| Gate 1 approval | Pending; do not mark complete based on automated tests |

## Immediate remaining priorities

1. Obtain a complete federal sample after the official quota resets, through a
   properly configured key, or from a documented existing export. No quota bypass.
2. Prepare the remaining 20 review rows and run the third-corpus validation.
3. Have a person label all 60 comments, review excluded-language cases, then
   compute and publish real agreement rates and any required remediation.
4. Review theme coherence and resolve/discuss quote shortages. Do not meet the
   quote target by duplicating text, inventing quotes, or merging unrelated views.
5. Demonstrate the working outputs and open limitations to Benjamin for the gates.

Week 4 gaps/questions, Week 5 dashboard/deployment, Week 6 community brief, and
Week 7 pilot/launch work are not claimed complete. Weekly communication, partner
arrangements, and approval remain human responsibilities supported by the code.
