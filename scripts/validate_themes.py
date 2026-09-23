"""Run themes on fixed fictional fixtures and print a reproducible JSON report.

No user file is read and no output file is written by this command. Redirect
stdout to a local evidence file if wanted. Run: python -m scripts.validate_themes
"""

import importlib.metadata
import json
from pathlib import Path
import re
from time import perf_counter

import pandas as pd
from sklearn.metrics import adjusted_rand_score

from pipeline.themes import MODEL_PATH, analyze_themes


def main():
    root = Path(__file__).resolve().parents[1]
    sample = pd.read_csv(root / 'data/samples/synthetic_chicago_hearing.csv')
    start = perf_counter()
    # Ground-truth labels are used below only for evaluation, never clustering.
    result = analyze_themes(sample[['comment_text']], theme_count=6)
    elapsed = perf_counter() - start
    actual = [item['theme_id'] for item in result['assignments']]
    truth = [sample.iloc[item['row_position']]['validation_theme'] for item in result['assignments']]
    composition = {}
    for item in result['assignments']:
        counts = composition.setdefault(str(item['theme_id']), {})
        name = sample.iloc[item['row_position']]['validation_theme']
        counts[name] = counts.get(name, 0) + 1
    quote_checks = []
    for theme in result['themes']:
        for quote in theme['quotes']:
            source = sample.iloc[quote['row_position']]['comment_text']
            name = re.search(r'Contact (.+?) at sample\.person\d+@example\.org', source)
            residual = bool(name and any(
                re.search(r'\b' + re.escape(token) + r'\b', quote['text'], re.IGNORECASE)
                for token in name[1].split()
            ))
            quote_checks.append({
                'row_position': quote['row_position'], 'word_count': len(quote['text'].split()),
                'planted_name_not_fully_removed': residual,
                'raw_email_present': bool(re.search(r'\S+@\S+', quote['text'])),
            })
    small = pd.DataFrame({'comment_text': [
        'The neighborhood library needs new books so children can discover more stories after school.',
        'Please extend library opening hours so working parents can borrow books with their children.',
        'More library books and reading programs would help students practice reading throughout the summer.',
        'Bus services are unreliable and students keep arriving late because their routes take too long.',
        'Please improve bus routes and schedules so children have a reliable journey to school every morning.',
        'School buses should arrive on time and families need clear updates about any route changes.',
    ]})
    small_start = perf_counter()
    small_result = analyze_themes(small, theme_count=2)
    source_path = MODEL_PATH / 'hearing_lens_source.json'
    print(json.dumps({
        'notice': 'Fictional development fixtures, not an independent benchmark or privacy certification.',
        'model_source': json.loads(source_path.read_text()) if source_path.exists() else {},
        'versions': {p: importlib.metadata.version(p) for p in ['sentence-transformers', 'scikit-learn', 'torch', 'spacy']},
        'synthetic_sample': {
            'elapsed_seconds_including_model_load': round(elapsed, 3),
            'adjusted_rand_index': round(float(adjusted_rand_score(truth, actual)), 4),
            'theme_composition': composition, 'quote_checks': quote_checks, 'result': result,
        },
        'small_fixture': {'elapsed_seconds_warm': round(perf_counter() - small_start, 3), 'result': small_result},
    }, indent=2))


if __name__ == '__main__':
    main()
