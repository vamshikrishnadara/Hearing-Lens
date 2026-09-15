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
