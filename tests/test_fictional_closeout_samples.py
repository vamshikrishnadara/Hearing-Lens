"""Authored fixtures are stable, diverse in text length and contain no review labels."""
import pandas as pd
import pytest
from scripts.fictional_closeout_samples import make_sample


@pytest.mark.parametrize('name',['community_center','tenant_association'])
def test_reproducible_balanced_fictional_fixture(name):
    first=make_sample(name)
    pd.testing.assert_frame_equal(first,make_sample(name))
    assert len(first)==first.comment_text.nunique()==first.respondent_id.nunique()==300
    assert first.validation_theme.value_counts().tolist()==[50]*6
    assert first.hearing_date.nunique()==3
    lengths=first.comment_text.str.split().str.len()
    assert lengths.min()>=12 and lengths.max()>60
    assert not {'sentiment','emotion','human_label'} & set(first.columns)


def test_invalid_fixture_is_not_silently_substituted():
    with pytest.raises(KeyError):make_sample('unknown')
