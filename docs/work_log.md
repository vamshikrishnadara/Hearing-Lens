# Hearing Lens Work Log

This log records real project outputs and plans. It is not a payroll record. Actual hours should be entered by Vamshi from time personally spent working, reviewing, testing, meeting, or completing related project activity. Planned time must not be presented as completed time.

## September 14 2026

**Reporting week:** September 8 through September 14
**Status:** Foundation package prepared; Vamshi review and validation pending
**Actual time:** To be entered by Vamshi

### Completed outputs

- Converted the project brief into a concise product description and a list of privacy principles.
- Created the initial repository structure and dependency list.
- Defined the user-input schema, internal mapped fields, validation behavior, representation-reference format, and privacy boundary.
- Drafted the upload and results wireframes, including empty and error states.
- Implemented a CSV and XLSX loader with sheet selection, a 5,000-row cap, readable failures, and warnings.
- Implemented comment-column mapping, empty-comment removal, optional respondent deduplication, and optional subgroup mapping.
- Added an initial Streamlit upload and mapping screen.
- Added unit tests for CSV loading, row limits, mapping cleanup, missing fields, and unsupported files.
- Verified all five ingestion tests pass using Python's built-in test runner.
- Converted the eight-week project brief into a gate-based delivery plan and Week 1 backlog.

### Evidence

- `README.md`
- `pipeline/ingest.py`
- `app/streamlit_app.py`
- `tests/test_ingest.py`
- Test result on September 14: 5 tests run, 5 passed
- `docs/schema.md`
- `docs/wireframe.md`
- `docs/project_plan.md`

### Ten-hour focus plan

This is a planning allocation, not a statement that ten hours were completed.

| Activity | Planned time | Completion evidence |
| --- | ---: | --- |
| Review the brief and extract non-negotiables | 0.5 hour | Notes in README and schema |
| Translate gates and acceptance criteria into a backlog | 1.0 hour | Project plan |
| Establish the repository structure and dependencies | 1.0 hour | Project folders and requirements |
| Define the input and internal data schemas | 1.5 hours | Schema document |
| Draft upload, results, and empty-state wireframes | 1.0 hour | Wireframe document |
| Implement ingestion and column mapping | 2.5 hours | Loader module and interface |
| Test loader and mapping behavior | 1.5 hours | Automated tests and results |
| Review outputs, record decisions, and prepare status | 1.0 hour | Updated log and backlog |
| **Total planned** | **10.0 hours** | |

### Review checklist for Vamshi

- Read the schema and confirm the field names make sense.
- Run the tests and save the result.
- Launch the interface and test one small CSV and one XLSX workbook.
- Record corrections or questions in the backlog.
- Enter only the actual time spent on these activities.

## September 15 2026

**Reporting week:** September 15 through September 21
**Status:** Planned
**Actual time:** Enter after work is completed

### Eleven-hour plan

| Activity | Planned time | Intended evidence |
| --- | ---: | --- |
| Review Day 1 output and reproduce the test run | 0.5 hour | Test result and review notes |
| Define redaction rules, entities, and failure cases | 2.0 hours | Redaction design document |
| Implement the first redaction module | 3.0 hours | `pipeline/redact.py` |
| Write redaction unit tests and inspect examples | 1.5 hours | `tests/test_redact.py` and results |
| Implement a synthetic hearing-data generator | 1.5 hours | Generator script and data dictionary |
| Generate and validate a development sample | 1.0 hour | Sample dataset validation summary |
| Start the methods and limitations notes | 0.75 hour | Methods draft |
| Update the backlog and prepare the daily status | 0.75 hour | Work-log and plan updates |
| **Total planned** | **11.0 hours** | |

### End-of-day update rule

At the end of September 15, replace planned status only for tasks that were actually completed. Record actual time separately, note any blockers, and link each completed claim to a file, test result, meeting note, or decision.
