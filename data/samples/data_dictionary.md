# Synthetic Hearing Sample Data Dictionary

`synthetic_chicago_hearing.csv` is a reproducible development fixture containing 1,000 fictional public comments. It contains no collected resident data and must not be described as evidence from a real hearing.

## Fields

| Field | Type | Description |
| --- | --- | --- |
| `respondent_id` | String | Unique synthetic identifier in `SYN-0001` format |
| `comment_text` | String | Template-based fictional comment; a controlled subset contains fictional contact or address patterns for redaction tests |
| `hearing_date` | Date | One of three fictional hearing dates |
| `ward` | Integer | Skewed categorical ward value used to test participation summaries |
| `role` | String | Fictional respondent role with a deliberately uneven distribution |
| `language` | String | Fictional respondent-supplied language category |
| `housing_tenure` | String | Fictional respondent-supplied tenure category |
| `school` | String | Fictional school label |
| `validation_theme` | String | One of six planted themes used to evaluate clustering results |

## Planted themes

- Classroom resources
- School safety
- Mental health
- Transportation
- Accessibility
- Communication

## Intended use

- Validate CSV loading and column mapping.
- Exercise contact and address redaction.
- Measure whether clustering recovers the six planted themes.
- Test timeline output across three hearings.
- Test representation calculations with deliberately skewed subgroup distributions.

The sample may be regenerated with:

```text
python scripts/generate_synthetic_sample.py
```

The default seed makes repeated runs identical so regression tests remain stable.

## Additional theme benchmark

`synthetic_theme_benchmark.csv` contains a second, explicitly fictional 1,000-row
fixture with the same fields, six planted categories, three hearing dates, skewed
subgroups, and contact/address probes. Its 48 authored substantive templates are
21–25 words each, with deterministic optional context and contact additions.
Generate it with `python -m scripts.generate_theme_benchmark` (seed 20261001).

The original fixture remains unchanged as a short/repetitive-comment stress test.
The new fixture was added because short repetitive templates cannot always supply
three distinct eligible quotes. Results on these different fixtures must not be
presented as a like-for-like model improvement. Neither fixture is independent
held-out evaluation or collected resident testimony. Category metadata is never
passed into analysis. Development settings were explored on these fixtures, so
ARI is a development diagnostic, not a generalization claim.

## Public development files

CFPB: 300 narratives, fields `complaint_id`, `comment_text`, `date_received`,
`product`, `issue`. Federal: 300 comments, fields `source_id`, `comment_text`,
`hearing_date`. IDs and metadata are used for preparation/provenance only; themes
use text. See `docs/cfpb_source.md` and `docs/federal_source.md` for source rules,
hashes, and reproduction commands. Public text lives in ignored
`data/public_samples/`, rather than publishing submitter narratives under
`data/samples/`. This is a documented departure from the brief's suggested
three-committed-files layout; all three corpus types are available locally.
