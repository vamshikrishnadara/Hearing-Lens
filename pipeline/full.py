"""Complete mapped-table analysis; no input/output files or result caches."""
import pandas as pd

from pipeline.core import analyze_core
from pipeline.gaps import analyze_gaps
from pipeline.questions import mine_questions


class PipelineError(ValueError):
    """Invalid mapped input, without echoing source cells."""


def analyze_all(frame, *, references=None, agency_response=None,
                minimum_group_size=10, theme_count='auto', backend='auto'):
    """Analyze the output of ingest.map_columns in a common row-position space.

    References use mapped subgroup__ names. Missing optional inputs retain each
    module's explicit unavailable/counts-only/unverified status. Model failures
    propagate: no partially complete result is returned. Human validation is
    separate and is never inferred from a successful run.
    """
    if (not isinstance(frame, pd.DataFrame) or not frame.columns.is_unique
            or 'comment_text' not in frame or not 1 <= len(frame) <= 5000):
        raise PipelineError('Supply a mapped table with 1–5,000 comments and unique column names.')
    if any(not isinstance(v, str) or not v.strip() for v in frame.comment_text):
        raise PipelineError('Map and clean comment text before running the complete pipeline.')
    # Validate categorical inputs before starting expensive model work.
    gaps = analyze_gaps(frame, references=references, minimum_group_size=minimum_group_size)
    core = analyze_core(frame, period_column='date_or_hearing' if 'date_or_hearing' in frame else None,
                        theme_count=theme_count, backend=backend)
    questions = mine_questions(frame, agency_response=agency_response,
                               minimum_group_size=minimum_group_size)
    return {'schema_version': '1.0', 'input_rows': len(frame), **core,
            'gaps': gaps, 'questions': questions,
            'notice': 'Automated analysis, not human-validated findings. Review themes, quotes, '
                      'affect labels, gaps and question priorities before using or sharing results. '
                      'Redaction can miss identifiers; supplied subgroup labels remain visible.'}
