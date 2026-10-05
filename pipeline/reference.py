"""Validate a user-supplied population distribution without guessing its units."""
from dataclasses import dataclass
from decimal import Decimal, DecimalException
from collections.abc import Mapping
import math

import pandas as pd


class ReferenceError(ValueError):
    """A reference problem safe to show without echoing uploaded values."""


@dataclass(frozen=True)
class ReferenceGroup:
    key: str
    label: str
    share: Decimal


def group_label(value):
    """Preserve supplied categories; blank values are unknown, never inferred."""
    if not pd.api.types.is_scalar(value):
        raise ReferenceError('Group values must be single categories, not lists or objects.')
    if pd.isna(value):
        return ''
    return str(value).strip()


def parse_reference(reference, *, group_column='group', share_column='share'):
    """Accept a mapped two-column table or manual {group: share} entries.

    Bare numbers use 0-1 proportions. A percent sign explicitly selects 0-100
    units. Shares must sum to one within 0.000001; no rescaling or guessed units.
    """
    if isinstance(reference, Mapping):
        pairs = list(reference.items())
    elif isinstance(reference, pd.DataFrame):
        if (not reference.columns.is_unique or group_column == share_column
                or group_column not in reference or share_column not in reference):
            raise ReferenceError('Select different group and share columns in the reference table.')
        pairs = list(reference[[group_column, share_column]].itertuples(index=False, name=None))
    else:
        raise ReferenceError('Supply a reference table or manual group/share entries.')
    if not pairs:
        raise ReferenceError('The reference distribution has no groups.')
    groups, seen = [], set()
    for raw_label, value in pairs:
        label = group_label(raw_label)
        key = label.casefold()
        if not label:
            raise ReferenceError('Every reference row needs a group label.')
        if key in seen:
            raise ReferenceError('Reference group labels must be unique after trimming and case matching.')
        seen.add(key)
        if isinstance(value, bool) or not pd.api.types.is_scalar(value):
            raise ReferenceError('Reference shares must be proportions from 0 to 1 or explicit percentages.')
        try:
            raw = str(value).strip()
            share = Decimal(raw[:-1].strip()) / 100 if raw.endswith('%') else Decimal(raw)
        except (DecimalException, ValueError):
            raise ReferenceError('Reference shares must be proportions from 0 to 1 or explicit percentages.') from None
        if not share.is_finite() or not 0 <= share <= 1:
            raise ReferenceError('Reference shares must be finite and between 0 and 1; use a percent sign for percentages.')
        numeric = float(share)
        if share > 0 and (numeric == 0 or not math.isfinite(1 / numeric)):
            raise ReferenceError('Reference shares are too small for a finite representation ratio.')
        groups.append(ReferenceGroup(key, label, share))
    if abs(sum((g.share for g in groups), Decimal(0)) - 1) > Decimal('0.000001'):
        raise ReferenceError('Reference shares must sum to 1 (100%); complete or correct the distribution.')
    return tuple(groups)


def load_reference_csv(source, *, group_column='group', share_column='share'):
    """Read an explicit development/upload stream; preserve labels such as 001.

    No source filename or raw parser error is included in the public exception.
    The caller maps headers explicitly; CSV loading never guesses population data.
    """
    try:
        if hasattr(source, 'seek'): source.seek(0)
        frame = pd.read_csv(source, dtype=str, keep_default_na=False,
                            encoding='utf-8-sig', nrows=5001)
    except (OSError, ValueError, UnicodeError):
        raise ReferenceError('The reference CSV could not be read. Use a UTF-8 CSV with group and share columns.') from None
    finally:
        if hasattr(source, 'seek'): source.seek(0)
    if len(frame) > 5000:
        raise ReferenceError('The reference CSV exceeds 5,000 groups; reduce it before comparison.')
    parse_reference(frame, group_column=group_column, share_column=share_column)
    return frame[[group_column, share_column]].rename(columns={group_column: 'group', share_column: 'share'}).copy()
