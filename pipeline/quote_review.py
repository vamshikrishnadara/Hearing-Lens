"""Swap only between previously redacted, eligible candidates for a theme."""
from copy import deepcopy


def swap_quote(result, theme_id, quote_index, replacement_row_position):
    updated = deepcopy(result)
    theme = next((t for t in updated['themes'] if t['theme_id'] == theme_id), None)
    if theme is None or isinstance(quote_index, bool) or not isinstance(quote_index, int) or not 0 <= quote_index < len(theme['quotes']):
        raise ValueError('Choose an existing theme and quote slot.')
    alternatives = theme.get('quote_alternatives', [])
    replacement = next((q for q in alternatives if q['row_position'] == replacement_row_position), None)
    if replacement is None:
        raise ValueError('Choose an eligible redacted alternative from this theme.')
    old = theme['quotes'][quote_index]
    theme['quotes'][quote_index] = replacement
    theme['quote_alternatives'] = [q for q in alternatives if q['row_position'] != replacement_row_position] + [old]
    return updated
