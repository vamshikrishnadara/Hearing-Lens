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
            f'This file contains {len(frame):,} cleaned comments and {characters:,} '
            f'comment characters. The free online demo supports up to '
            f'{CLOUD_MAX_COMMENTS} comments and {CLOUD_MAX_CHARACTERS:,} characters. '
            'No analysis was started. Use the local version to analyze the complete '
            'file and download its reports, or upload a smaller sample for an online demonstration.')
