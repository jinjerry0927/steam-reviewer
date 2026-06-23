"""시간 추세 분석 테스트 — 네트워크 없이 mock 리뷰로 검증."""

import pandas as pd

from steam_reviewer.analyzers.trends import analyze_trends
from steam_reviewer.loaders.steam import reviews_dataframe

_DAY = 86_400
_BASE = 1_700_000_000  # 2023-11-14 근처


def _reviews_over_time():
    # 1주차: 대부분 긍정 / 4주차: 대부분 부정 → 하향 추세
    rows = []
    for i in range(5):  # 1주차 긍정 5
        rows.append({"review": "good", "voted_up": True, "votes_up": 1, "language": "english",
                     "timestamp_created": _BASE + i * 3600, "author": {}})
    for i in range(5):  # 4주차 부정 4 + 긍정 1
        rows.append({"review": "bad", "voted_up": i == 0, "votes_up": 1, "language": "english",
                     "timestamp_created": _BASE + 21 * _DAY + i * 3600, "author": {}})
    return rows


def test_trends_buckets_and_counts():
    df = reviews_dataframe(_reviews_over_time())
    tr = analyze_trends(df, freq="week")
    assert tr["freq"] == "W"
    assert len(tr["points"]) >= 2
    total = sum(p["count"] for p in tr["points"])
    assert total == 10


def test_trends_direction_down():
    df = reviews_dataframe(_reviews_over_time())
    tr = analyze_trends(df, freq="week")
    assert tr["first_ratio"] > tr["last_ratio"]
    assert tr["direction"] == "down"


def test_trends_day_freq():
    df = reviews_dataframe(_reviews_over_time())
    tr = analyze_trends(df, freq="day")
    assert tr["freq"] == "D"
    # 빈 날짜는 제외되므로 점은 실제 데이터가 있는 2일치
    assert all(p["count"] > 0 for p in tr["points"])


def test_trends_empty():
    tr = analyze_trends(pd.DataFrame())
    assert tr["empty"] is True
    assert tr["points"] == []


def test_trends_points_have_ratio():
    df = reviews_dataframe(_reviews_over_time())
    tr = analyze_trends(df)
    for p in tr["points"]:
        assert 0.0 <= p["positive_ratio"] <= 1.0
        assert p["positive"] <= p["count"]
