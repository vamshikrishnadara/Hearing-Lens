"""Compare fixed theme methods on fictional fixtures; print JSON, never read uploads.

Run: python -m scripts.compare_theme_grouping
The new fixture is a development smoke check, not held-out public-corpus evidence.
"""

import importlib.metadata
import json
from pathlib import Path
import re
from time import perf_counter

import pandas as pd
from sklearn.metrics import adjusted_rand_score

from pipeline.themes import MODEL_PATH, analyze_themes


# Authored separately from the generator. Both copies of each statement keep
# their evaluation category; those categories never enter the analysis pipeline.
NEW_COMMENTS = {
    'library': [
        'Our public library needs more picture books so young children can practice reading at home.',
        'Please extend library opening hours into the evening so working families can borrow books.',
        'The library reading room needs quiet study tables and shelves for the growing book collection.',
        'Funding library staff would let children join more reading clubs and get help choosing books.',
    ],
    'bus_service': [
        'The city bus often arrives late and commuters miss connections on their way to work.',
        'Please run buses more frequently at weekends so residents can reach shops without long waits.',
        'Bus passengers need reliable timetables at stops and updates when their usual route is delayed.',
        'The first morning bus should arrive earlier so workers can reach their jobs on time.',
    ],
    'drainage': [
        'Blocked storm drains leave our streets flooded whenever heavy rain falls across the neighborhood.',
        'Please clear leaves from roadside drains before storms so rainwater can flow into the sewers.',
        'The drainage pipes overflow during heavy rainfall and flood the road outside our homes.',
        'Repairing damaged storm sewers would stop rainwater pooling at intersections after every summer storm.',
    ],
}
INTRO = 'Thank you for giving residents the opportunity to speak today. '


def new_fixture():
    comments = [text for texts in NEW_COMMENTS.values() for text in texts]
    categories = [category for category, texts in NEW_COMMENTS.items() for _ in texts]
    return pd.DataFrame({
        'comment_text': comments + [INTRO + text for text in comments],
        'validation_theme': categories * 2,
    })


def summarize(frame, result, *, paired=False):
    assignments = result['assignments']
    truth = [frame.iloc[item['row_position']]['validation_theme'] for item in assignments]
    actual = [item['theme_id'] for item in assignments]
    composition = {}
    for item, category in zip(assignments, truth):
        group = composition.setdefault(str(item['theme_id']), {})
        group[category] = group.get(category, 0) + 1
    quote_checks = []
    for theme in result['themes']:
        for quote in theme['quotes']:
            source = frame.iloc[quote['row_position']]['comment_text']
            name = re.search(r'Contact (.+?) at sample\.person\d+@example\.org', source)
            quote_checks.append({
                'row_position': quote['row_position'],
                'length_valid': 12 <= len(quote['text'].split()) <= 60,
                'raw_email_present': bool(re.search(r'\S+@\S+', quote['text'])),
                'planted_name_not_fully_removed': bool(name and any(
                    re.search(r'\b' + re.escape(token) + r'\b', quote['text'], re.IGNORECASE)
                    for token in name[1].split()
                )),
            })
    output = {
        'adjusted_rand_index': round(float(adjusted_rand_score(truth, actual)), 4),
        'theme_composition': composition,
        'candidate_quote_count': len(quote_checks),
        'quote_checks': quote_checks,
        'result': result,
    }
    if paired:
        by_row = {item['row_position']: item['theme_id'] for item in assignments}
        half = len(frame) // 2
        output['same_theme_with_and_without_intro'] = {
            'matching_pairs': sum(by_row[i] == by_row[i + half] for i in range(half)),
            'total_pairs': half,
        }
    return output


def main():
    root = Path(__file__).resolve().parents[1]
    sample = pd.read_csv(root / 'data/samples/synthetic_chicago_hearing.csv')
    source = MODEL_PATH / 'hearing_lens_source.json'
    report = {
        'notice': 'Development-only comparisons. ARI is not accuracy; no public-corpus or privacy certification.',
        'timing_note': 'Baseline runs first and includes initial model loading; later runs are warm. Do not compare speeds.',
        'model_source': json.loads(source.read_text()) if source.exists() else {},
        'versions': {p: importlib.metadata.version(p) for p in ['sentence-transformers', 'scikit-learn', 'torch', 'spacy']},
        'fixtures': {},
    }
    for name, frame, count, paired in [
        ('synthetic_1000', sample, 6, False),
        ('separate_24', new_fixture(), 3, True),
    ]:
        methods = {}
        for mode in ['whole_comment', 'sentence_weighted']:
            start = perf_counter()
            result = analyze_themes(frame[['comment_text']], theme_count=count, embedding_mode=mode)
            elapsed = perf_counter() - start
            methods[mode] = summarize(frame, result, paired=paired)
            methods[mode]['elapsed_seconds'] = round(elapsed, 3)
        report['fixtures'][name] = methods
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
