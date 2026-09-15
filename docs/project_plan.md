# Hearing Lens Delivery Plan

The MVP is organized around five live review gates. Week 8 is reserved for slippage and post-launch fixes rather than new features.

## Gate 0 Scope and schema

Target: end of Week 1.

- Review the product statement, schema, wireframe, and privacy boundary.
- Demonstrate CSV and XLSX loading plus readable validation errors.
- Confirm the repository license and ownership language.
- Confirm weekly check-in time and the Gate 1 date.
- Identify the federal, CFPB, and synthetic development datasets and document their licenses.

## Gate 1 Analytical core

Target: end of Week 3.

- Demonstrate redaction, theme clustering, representative quotes, sentiment, emotion, and timeline on three development corpora.
- Record performance and manual-validation results.
- Write a remediation or limitation note for any agreement result below the target.

## Gate 2 End-to-end pipeline

Target: end of Week 4.

- Demonstrate representation-gap calculations against a hand check.
- Measure question-detector recall and false-positive rate.
- Run every analytical stage from one command and write structured outputs.

## Gate 3 Pilot ready

Target: end of Week 6.

- Demonstrate the complete upload-to-download flow at a public URL.
- Verify the one-page DOCX and PDF brief.
- Publish the methodology and limitations page.
- Confirm two pilot partners and their data arrangements.

## Gate 4 Launch and handoff

Target: end of Week 7.

- Complete two pilots and address critical findings.
- Complete privacy and accessibility checks.
- Publish version 1.0, the demo video, facilitator runbook, and final report.
- Leave no open critical bugs and disclose known limitations.

## Week 1 working backlog

| Priority | Item | Evidence | Status |
| --- | --- | --- | --- |
| P0 | Define input and normalized schemas | `docs/schema.md` | Draft complete |
| P0 | Create upload and column-mapping loader | `pipeline/ingest.py` | Initial implementation complete |
| P0 | Test validation, limits, and deduplication | `tests/test_ingest.py` | Initial tests complete |
| P0 | Define dashboard flow | `docs/wireframe.md` | Draft complete |
| P0 | Confirm license and ownership wording | Written decision from ChiEAC | Blocked on confirmation |
| P1 | Create 1,000-row synthetic hearing generator | Script and data dictionary | Planned |
| P1 | Select and document two public corpora | Source notes and licenses | Planned |
| P1 | Create a project board | Issues aligned to gates | Planned |
