"""Compare automatic counts with manual baselines; print aggregate results only.

Run: python -m scripts.compare_theme_selection --sample-dir PATH
Optional --baseline-report PATH checks an earlier validate_cfpb_themes JSON.
No downloads, public narratives, identifiers, or quote text are printed.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path

from sklearn.metrics import adjusted_rand_score

from pipeline.themes import MODEL_PATH, analyze_themes
from scripts.compare_theme_grouping import new_fixture
from scripts.validate_cfpb_themes import load_sample


def summarize(result):
    quotes = [quote for theme in result['themes'] for quote in theme['quotes']]
    return {
        'selection': result['theme_selection'],
        'analyzed_comments': result['analyzed_comments'],
        'group_sizes': [theme['count'] for theme in result['themes']],
        'candidate_quote_count': len(quotes),
        'themes_with_three_quotes': sum(len(theme['quotes']) == 3 for theme in result['themes']),
        'all_quote_lengths_valid': all(12 <= len(quote['text'].split()) <= 60 for quote in quotes),
    }


def compare(frame, manual_count):
    # Only text enters the engine. Fictional categories are used afterward.
    results = {str(count): analyze_themes(frame[['comment_text']], theme_count=count)
               for count in [manual_count, 'auto']}
    summaries = {mode: summarize(result) for mode, result in results.items()}
    if 'validation_theme' in frame:
        for mode, result in results.items():
            truth = [frame.iloc[a['row_position']]['validation_theme'] for a in result['assignments']]
            labels = [a['theme_id'] for a in result['assignments']]
            summaries[mode]['adjusted_rand_index'] = float(adjusted_rand_score(truth, labels))
    return summaries, results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample-dir', required=True, type=Path)
    parser.add_argument('--baseline-report', type=Path)
    args = parser.parse_args()
    frame, manifest = load_sample(args.sample_dir)
    public, results = compare(frame, 6)
    if args.baseline_report:
        old = json.loads(args.baseline_report.read_text())
        if old['sample_provenance']['sample_sha256'] != manifest['sample_sha256']:
            raise ValueError('Baseline uses a different sample.')
        previous = old['validation']['result']
        public['manual_baseline_unchanged'] = {
            key: results['6'][key] == previous[key]
            for key in ['themes', 'assignments', 'analyzed_comments', 'empty_comments_removed', 'excluded_row_positions']
        }
    fictional, _ = compare(new_fixture(), 3)
    source = MODEL_PATH / 'hearing_lens_source.json'
    print(json.dumps({
        'notice': 'Silhouette measures vector separation, not semantic accuracy. The fictional fixture has three planted topics, below the automatic minimum of four; this deliberately checks a known limitation.',
        'sample_sha256': manifest['sample_sha256'],
        'model_source': json.loads(source.read_text()) if source.exists() else {},
        'versions': {p: importlib.metadata.version(p) for p in ['sentence-transformers', 'scikit-learn', 'torch', 'spacy']},
        'cfpb_100': public,
        'fictional_24_three_topics': fictional,
    }, indent=2))


if __name__ == '__main__':
    main()
