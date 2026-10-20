"""Fixed stage names for optional progress callbacks; never include input text."""

STAGES = {
    'waiting': 'Waiting for the current analysis to finish',
    'initializing': 'Preparing analysis libraries',
    'representation': 'Checking subgroup counts and reference values',
    'redaction': 'Checking comments for names and contact details',
    'embeddings': 'Preparing comment embeddings',
    'clustering': 'Grouping related comments into themes',
    'keywords': 'Preparing theme labels',
    'quotes': 'Selecting supporting quote excerpts',
    'language': 'Checking comment languages',
    'sentiment': 'Analyzing sentiment',
    'emotion': 'Analyzing emotion',
    'timeline': 'Summarizing themes and dates',
    'questions': 'Grouping questions and checking response matches',
    'complete': 'Analysis complete',
}


def notify(progress, stage):
    if stage not in STAGES:
        raise ValueError('Unknown analysis stage.')
    if progress is not None:
        progress(stage)
