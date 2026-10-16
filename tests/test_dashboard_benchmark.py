import pytest
from scripts.benchmark_dashboard import make_benchmark


def test_fictional_benchmark_has_distinct_text_and_ids():
    frame = make_benchmark()
    assert len(frame) == frame.comment_text.nunique() == frame.respondent_id.nunique() == 2000
    assert frame.equals(make_benchmark())
    with pytest.raises(ValueError):
        make_benchmark(2401)


