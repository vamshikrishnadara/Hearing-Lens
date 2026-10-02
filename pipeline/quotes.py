"""Traceable verbatim quote spans. Never pad, paraphrase, or combine commenters."""
import re
from difflib import SequenceMatcher

_CONTACT = re.compile(r'\[(?:EMAIL_ADDRESS|PHONE_NUMBER|STREET_ADDRESS|UNIT_NUMBER)\]')

def quote_spans(text, mode='full_comment'):
    """Offsets refer to the complete redacted source, before excerpt selection."""
    if 12 <= len(text.split()) <= 60 and (mode == 'full_comment' or not _CONTACT.search(text)):
        return [(0, len(text))]
    if mode != 'sentences' or len(text.split()) < 12:
        return []
    boundaries = [0] + [m.end() for m in re.finditer(r'(?<=[.!?])\s+', text)]
    spans = []
    # Keep complete adjacent sentences, allowing short sentences to gain context.
    # A single sentence longer than 60 words is omitted rather than cut mid-thought.
    for index, start in enumerate(boundaries):
        candidate = None
        for end in boundaries[index + 1:] + [len(text)]:
            stop = len(text[:end].rstrip())
            count = len(text[start:stop].split())
            if count > 60: break
            # Contact-bearing sentences can leave city/ZIP or other context next
            # to a masked address. Prefer substantive sentences without that tail.
            if _CONTACT.search(text[start:stop]): break
            if count >= 12:
                candidate = (start, stop)
        if candidate is not None: spans.append(candidate)
    return list(dict.fromkeys(spans))


def nearly_identical(left, right):
    """Compare wording, not sentiment similarity: opposing views can embed closely."""
    left, right = (' '.join(x.casefold().split()) for x in (left, right))
    return (left == right or left in right or right in left
            or SequenceMatcher(None, left, right).ratio() >= .85)


def valid_source_quote(quote, redacted_source):
    text = quote['text']
    if not 12 <= len(text.split()) <= 60: return False
    if 'source_start' not in quote: return text == redacted_source
    start, end = quote['source_start'], quote['source_end']
    return (type(start) is int and type(end) is int
            and 0 <= start < end <= len(redacted_source)
            and text == redacted_source[start:end]
            and quote['is_excerpt'] == (start != 0 or end != len(redacted_source)))
