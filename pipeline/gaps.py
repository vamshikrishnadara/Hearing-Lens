"""Representation summaries from supplied categories only, with disclosure control.

No models, file writes, demographic inference, or population-data downloads.
"""
from collections import Counter
from collections.abc import Mapping
from decimal import Decimal

import pandas as pd

from pipeline.reference import ReferenceError, group_label, parse_reference


class GapError(ValueError):
    """An input/schema error safe to show without uploaded cell contents."""


def analyze_gaps(frame, *, subgroup_columns=None, references=None, minimum_group_size=10):
    """Return JSON-ready tidy rows and per-field coverage/status information.

    Call after ingest.map_columns to apply respondent-ID deduplication. Automatic
    selection considers only mapped subgroup__ columns, never raw demographics.
    Shares use nonmissing subgroup rows, including unmatched and suppressed rows.
    references maps selected column names to tables or manual group/share entries.
    Invalid references disable comparison for that field, not other analysis.
    """
    if not isinstance(frame, pd.DataFrame) or not frame.columns.is_unique:
        raise GapError('Provide a table with unique column names.')
    if type(minimum_group_size) is not int or minimum_group_size < 10:
        raise GapError('The minimum group size must be a whole number of at least 10.')
    if isinstance(subgroup_columns, str):
        raise GapError('Select subgroup columns as a list.')
    fields = (list(subgroup_columns) if subgroup_columns is not None else
              [c for c in frame.columns if isinstance(c, str) and c.startswith('subgroup__')])
    if (len(set(fields)) != len(fields) or any(not isinstance(c, str) or c not in frame for c in fields)
            or any(c in {'comment_text', 'respondent_id', 'date_or_hearing', 'source_row'} for c in fields)):
        raise GapError('Select distinct supplied subgroup columns, separate from comment and identifier fields.')
    references = {} if references is None else references
    if not isinstance(references, Mapping) or any(c not in fields for c in references):
        raise GapError('References must be assigned to selected subgroup columns.')
    if not fields:
        return {'status': 'unavailable', 'rows': [], 'fields': [],
                'notice': 'No subgroup field selected. Collect optional respondent-supplied categories to use this analysis.'}
    if 'comment_text' not in frame:
        raise GapError('Map a comment column before representation analysis.')
    eligible = frame.loc[frame.comment_text.fillna('').astype(str).str.strip().ne('')]
    rows, summaries = [], []
    for field in fields:
        try:
            labels = [group_label(v) for v in eligible[field]]
        except ReferenceError:
            raise GapError('Subgroup cells must contain single categories.') from None
        counts = Counter(label.casefold() for label in labels if label)
        display = {}
        for label in labels:
            if label: display.setdefault(label.casefold(), label)
        known = sum(counts.values())
        notices = []
        baseline = None
        ref_status = 'not_provided'
        if field in references:
            try:
                baseline = {g.key: g for g in parse_reference(references[field])}
                ref_status = 'valid'
            except ReferenceError as error:
                ref_status = 'invalid'
                notices.append(str(error))
        if not known:
            summaries.append({'field': field, 'status': 'unavailable', 'reference_status': ref_status,
                              'eligible_rows': len(eligible), 'known_rows': 0, 'missing_rows': len(eligible),
                              'minimum_group_size': minimum_group_size,
                              'notices': notices + ['No nonmissing supplied group values; comparison is unavailable.']})
            continue
        keys = set(counts) | set(baseline or {})
        # Also hide a second cell if one hidden cell could be reconstructed by
        # subtracting visible counts from the known total. Never drop hidden rows
        # from the share denominator or reveal their derived metrics.
        hidden = {key: 'small_group' for key in keys if counts[key] < minimum_group_size}
        if len(hidden) == 1:
            visible = keys - hidden.keys()
            if visible:
                secondary = min(visible, key=lambda k: (counts[k], k))
                hidden[secondary] = 'complementary'
        for key in sorted(keys):
            reference = baseline.get(key) if baseline is not None else None
            suppressed = key in hidden
            n = counts[key]
            share = Decimal(n) / Decimal(known)
            ref_share = reference.share if reference else None
            gap = (share - ref_share) * 100 if ref_share is not None else None
            ratio = share / ref_share if ref_share else None
            if suppressed:
                flag = 'suppressed'
            elif ref_status == 'invalid':
                flag = 'invalid_reference'
            elif ref_status == 'not_provided':
                flag = 'no_reference'
            elif reference is None:
                flag = 'unmatched'
            elif not ref_share:
                flag = 'zero_reference'
            elif Decimal(n) < Decimal('.75') * ref_share * Decimal(known):
                flag = 'underrepresented'
            elif Decimal(n) > Decimal('1.25') * ref_share * Decimal(known):
                flag = 'overrepresented'
            else:
                flag = 'within_range'
            rows.append({'field': field, 'group': reference.label if reference else display[key],
                         'count': None if suppressed else n,
                         'participation_share': None if suppressed else float(share),
                         'reference_share': float(ref_share) if ref_share is not None else None,
                         'gap_percentage_points': None if suppressed or gap is None else float(gap),
                         'representation_ratio': None if suppressed or ratio is None else float(ratio),
                         'flag': flag, 'suppressed': suppressed,
                         'suppression_reason': hidden.get(key)})
        if hidden:
            notices.append('Small-group counts and all derived metrics are hidden; an additional group may be hidden to prevent subtraction from totals. Group labels and supplied reference shares remain visible.')
        if ref_status == 'not_provided':
            notices.append('No reference supplied; counts and participation shares only. No representation claim is made.')
        elif baseline is not None and set(counts) - set(baseline):
            notices.append('Some supplied categories are absent from the reference. They remain in the denominator; unmatched categories have no gap or ratio.')
        if len(eligible) != known:
            notices.append('Missing group values are excluded from this field denominator. Shares describe only rows with known group values.')
        summaries.append({'field': field, 'status': 'comparison' if baseline is not None else 'counts_only',
                          'reference_status': ref_status, 'eligible_rows': len(eligible),
                          'known_rows': known, 'missing_rows': len(eligible) - known,
                          'minimum_group_size': minimum_group_size, 'notices': notices})
    return {'status': 'available' if rows else 'unavailable', 'rows': rows, 'fields': summaries,
            'notice': 'Counts describe comment rows after upstream cleaning, not necessarily unique people. Baselines must cover the same categories, geography and period. No missing attributes are inferred.'}
