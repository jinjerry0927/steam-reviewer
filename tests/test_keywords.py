"""키워드 분석 테스트 — 네트워크 없이 mock 리뷰로 검증."""

import pandas as pd

from steam_reviewer.analyzers.keywords import analyze_keywords
from steam_reviewer.loaders.steam import reviews_dataframe


def _reviews():
    return [
        {"review": "Amazing combat and combat feels great. Combat combat.", "voted_up": True, "votes_up": 5,
         "language": "english", "timestamp_created": 1_700_000_000, "author": {}},
        {"review": "The combat is fun and the music is wonderful.", "voted_up": True, "votes_up": 3,
         "language": "english", "timestamp_created": 1_700_100_000, "author": {}},
        {"review": "Terrible performance, constant crashes and stutter.", "voted_up": False, "votes_up": 8,
         "language": "english", "timestamp_created": 1_700_200_000, "author": {}},
        {"review": "Crashes ruined it. Performance crashes everywhere.", "voted_up": False, "votes_up": 2,
         "language": "english", "timestamp_created": 1_700_300_000, "author": {}},
    ]


def test_keywords_split_positive_negative():
    df = reviews_dataframe(_reviews())
    kw = analyze_keywords(df)
    pos_words = [k["word"] for k in kw["positive"]]
    neg_words = [k["word"] for k in kw["negative"]]
    assert "combat" in pos_words
    assert "crashes" in neg_words
    assert "combat" not in neg_words


def test_keywords_counts_and_sorted():
    df = reviews_dataframe(_reviews())
    kw = analyze_keywords(df, top_n=5)
    # combat: 3 + 1 + 1(in second review) = positive 그룹에서 최상위
    top_pos = kw["positive"][0]
    assert top_pos["word"] == "combat"
    counts = [k["count"] for k in kw["positive"]]
    assert counts == sorted(counts, reverse=True)


def test_keywords_stopwords_removed():
    df = reviews_dataframe(_reviews())
    kw = analyze_keywords(df)
    all_words = [k["word"] for k in kw["positive"]] + [k["word"] for k in kw["negative"]]
    for stop in ("the", "and", "is", "game", "it"):
        assert stop not in all_words


def test_keywords_extra_stopwords():
    df = reviews_dataframe(_reviews())
    kw = analyze_keywords(df, extra_stopwords={"combat"})
    assert "combat" not in [k["word"] for k in kw["positive"]]


def test_keywords_empty():
    kw = analyze_keywords(pd.DataFrame())
    assert kw["empty"] is True
    assert kw["positive"] == []
