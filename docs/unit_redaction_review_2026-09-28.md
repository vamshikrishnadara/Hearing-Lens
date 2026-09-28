# Unit-number redaction correction - September 28, 2026

## Problem and change

Friday's public-data review found ordinary words being replaced with
`[UNIT_NUMBER]`. The old pattern allowed `STE` and the other unit labels to match
without a separator, then accepted any letters as the identifier. It could
therefore consume words such as `step`, `steal`, and `united`, or a phrase such
as `apartment clean`.

The corrected rule requires whitespace, a period, a hash separator, or an
immediately attached digit after the label. The identifier must contain a digit
or be a single letter. It checks the end of the complete token to avoid partially
matching longer words. Supported examples include `Apt 4B`, `Unit A`, `Suite B12`,
`Ste. 200`, `unit#B`, `Apt4B`, `STE200`, and `Suite 12-14`.

This changes the unit pattern only. It is not a name allowlist: a PERSON entity
such as Steve still goes through name redaction. Existing span merging, contact
patterns, metadata exclusion, and failure handling are unchanged.

## Validation

| Check | Previous rule | Corrected rule |
| --- | ---: | ---: |
| Exact outputs on 28 fictional pattern cases | 13/28 | 28/28 |
| Confirmed ordinary-text unit matches in the fixed 100-row CFPB sample | 17 | 0 |
| Public sample rows affected by those matches | 12 | 0 |
| Public sample PERSON / street-address replacements | 285 / 1 | 285 / 1 |
| Planted unit numbers detected in the 1,000-row fictional sample | 84 | 84 |
| Planted email / phone / street-address detections | 79 / 79 / 84 | 79 / 79 / 84 |
| Fully removed planted names in the fictional sample | 67/79 | 67/79 |

All **74 automated tests passed**, including five new regression tests covering
28 pattern cases, full-pipeline word/unit handling, token boundaries, independent
name detection, and the preview boundary. The existing six lighting cases still
match their expected outputs, and the original name fixture still removes
16 of 18 expected mentions. Known name misses remain.

The first targeted scan counted 13 known errors across nine public rows. Review
of the remaining four matches confirmed additional ordinary wording (`steady`,
`stellar`, and `apartment clean`). The final report covers all 17 errors across
12 rows. No actual unit identifiers were found among these 17 old matches;
positive unit coverage was checked separately with fictional addresses.

The public sample is unchanged, with SHA-256
`e7faa7957fe104113c2e145b7c65b36100025d6a4550cf31eb0ebcae6b362318`.
The final before report replays the unit expression from commit `08d7a92` in
memory against the same 28 cases and sample. It does not replace repository
files. The after report uses the corrected production rule.

## Effect on the public theme run

Restoring ordinary words changes the modeling input. The unchanged theme engine
still analyzed all 100 comments into six groups. Counts changed from
`38, 29, 16, 13, 3, 1` to `34, 30, 18, 14, 3, 1`. Candidate quotes changed from
10 to 12; this is a consequence of changed assignments, not a quote-selection
feature or evidence of better theme quality. Only two groups still have all
three quotes, and a singleton remains. All-X placeholders still affect four
keyword lists and labels.

Inspection of all 12 selected redacted quotes found no obvious personal names,
raw emails, phone numbers, or full street addresses. This is a limited,
assistant-assisted development check, not a privacy guarantee or independent
coding. One newly selected quote about a vehicle-lease overpayment appears in
the loan/bankruptcy group, illustrating the remaining label/coherence problem.
All 12 satisfy the existing 12-60-word filter; the number of initially eligible
comments remains 19. The measured run took 6.615 seconds including model loading,
excluding imports and review-packet preparation; it is not a speed comparison.

## Boundaries and next work

- Multi-letter-only identifiers such as `Unit PH`, named units, and compact
  letter-first forms such as `AptB` are outside this rule. Do not claim universal
  address coverage. These need context-aware treatment rather than restoring
  unrestricted prefix matching.
- A phrase such as `unit 3` can still refer to something other than an address.
  This pattern has no full address-context classifier.
- Public source masking prevents a reliable estimate of redaction recall.
  Name-detection gaps and broader address/phone formats remain.
- Source-placeholder keywords, quote handling for long comments, tiny clusters,
  the federal corpus, and the remaining analytical-core requirements are pending.
  Today's change does not complete the theme milestone or a supervisor gate.
- No interface behavior was added and no browser test was run. Automated preview
  checks exercised the changed redaction path.

## Reproduce and evidence

```sh
python -m scripts.validate_unit_redaction
python -m scripts.validate_unit_redaction --sample-dir data/public_samples/cfpb_2017
python -m scripts.validate_person_redaction
python -m scripts.validate_cfpb_themes --sample-dir data/public_samples/cfpb_2017
python -m unittest discover -s tests -v
```

The unit validation command prints fictional cases and public aggregate counts;
it never prints public narratives or complaint IDs. The known-word list is for
evaluation only, not an exception list in the pipeline. See the
[CFPB source guide](cfpb_source.md) to recreate the public sample.

Local evidence is in `daily-evidence/2026-09-28/`: `unit-before.json`,
`unit-after.json`, `replay_original_unit_rule.py`, `person-after.json`,
`cfpb-theme-validation.json`, `automated-tests.txt`, and the daily PDF.
Detailed public review text stays local. No new dependencies or models were added.
