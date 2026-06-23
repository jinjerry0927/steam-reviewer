"""리뷰 길이·도움됨 분포 테스트 — 네트워크 없이 mock 리뷰로 검증."""

import pandas as pd

from steam_reviewer.analyzers.distributions import analyze_distributions
from steam_reviewer.loaders.steam import reviews_dataframe


def _reviews():
    return [
        {"review": "short", "voted_up": True, "votes_up": 0, "language": "english",
         "timestamp_created": 1_700_000_000, "author": {}},
        {"review": "a much longer review with many more characters here", "voted_up": True, "votes_up": 3,
         "language": "english", "timestamp_created": 1_700_100_000, "author": {}},
        {"review": "medium length review", "voted_up": False, "votes_up": 50,
         "language": "english", "timestamp_created": 1_700_200_000, "author": {}},
        {"review": "another one", "voted_up": True, "votes_up": 150,
         "language": "english", "timestamp_created": 1_700_300_000, "author": {}},
    ]


def test_distributions_length():
    df = reviews_dataframe(_reviews())
    dist = analyze_distributions(df)
    length = dist["length"]
    assert length["min"] == len("short")
    assert length["max"] == len("a much longer review with many more characters here")
    assert length["mean"] >= length["min"]


def test_distributions_votes_buckets():
    df = reviews_dataframe(_reviews())
    dist = analyze_distributions(df)
    votes = dist["votes_up"]
    assert votes["max"] == 150
    buckets = {b["range"]: b["count"] for b in votes["buckets"]}
    assert buckets["0"] == 1          # votes_up == 0
    assert buckets["1-4"] == 1        # 3
    assert buckets["20-99"] == 1      # 50
    assert buckets["100+"] == 1       # 150
    assert sum(b["count"] for b in votes["buckets"]) == 4


def test_distributions_empty():
    dist = analyze_distributions(pd.DataFrame())
    assert dist["empty"] is True
