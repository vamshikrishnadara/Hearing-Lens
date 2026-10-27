"""Deployment-specific admission checks before expensive analysis work."""
import os

CLOUD_MAX_COMMENTS = 60
CLOUD_MAX_CHARACTERS = 24_000


class AnalysisLimitError(ValueError):
    """The hosted demonstration cannot accept this workload."""


def is_cloud_demo():
    return os.environ.get('HEARING_LENS_DEPLOYMENT') == 'community_cloud'


def check_analysis_size(frame):
    if not is_cloud_demo():
        return
    characters = int(frame['comment_text'].fillna('').astype(str).str.len().sum())
    if len(frame) > CLOUD_MAX_COMMENTS or characters > CLOUD_MAX_CHARACTERS:
        raise AnalysisLimitError(
            f'This free demo accepts up to {CLOUD_MAX_COMMENTS} cleaned comments '
            f'and {CLOUD_MAX_CHARACTERS:,} comment characters per file. '
            'This file exceeds that limit. Run the full file in the local dashboard '
            'using python -m scripts.start_local. No analysis was started and no '
            'comments were sampled or removed to meet the demo limit. Splitting files changes the overall '
            'themes and comparisons; use the complete file locally.')
