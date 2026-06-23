"""기본 분석/변환 테스트 — 네트워크 없이 mock 리뷰로 검증."""

from steam_reviewer.analyzers.basic import analyze_basic
from steam_reviewer.loaders.steam import ReviewBatch, resolve_appid, reviews_dataframe
from steam_reviewer.report.text import render_text


def _sample_reviews():
    return [
        {
            "review": "Amazing gameplay loop, I keep coming back.",
            "voted_up": True,
            "votes_up": 120,
            "votes_funny": 3,
            "language": "english",
            "timestamp_created": 1_700_000_000,
            "author": {"steamid": "X1", "playtime_forever": 2400, "playtime_at_review": 1800, "num_games_owned": 50},
        },
        {
            "review": "Too difficult and the controller support is buggy.",
            "voted_up": False,
            "votes_up": 30,
            "votes_funny": 0,
            "language": "english",
            "timestamp_created": 1_700_100_000,
            "author": {"steamid": "X2", "playtime_forever": 300, "playtime_at_review": 120, "num_games_owned": 10},
        },
        {
            "review": "재미있어요. 다시 하고 싶음.",
            "voted_up": True,
            "votes_up": 8,
            "votes_funny": 1,
            "language": "koreana",
            "timestamp_created": 1_700_200_000,
            "author": {"steamid": "X3", "playtime_forever": 1200, "playtime_at_review": 900, "num_games_owned": 5},
        },
    ]


def test_resolve_appid_digit_shortcut():
    appid, name = resolve_appid("1145360")
    assert appid == 1145360


def test_reviews_dataframe_excludes_steamid():
    df = reviews_dataframe(_sample_reviews())
    assert len(df) == 3
    assert "steamid" not in df.columns  # 개인정보 제외
    assert "playtime_forever" in df.columns
    assert "created_date" in df.columns


def test_analyze_basic_counts():
    df = reviews_dataframe(_sample_reviews())
    stats = analyze_basic(df)
    assert stats["review_count"] == 3
    assert stats["positive"] == 2
    assert stats["negative"] == 1
    assert abs(stats["positive_ratio"] - 2 / 3) < 1e-3


def test_analyze_basic_playtime_and_languages():
    df = reviews_dataframe(_sample_reviews())
    stats = analyze_basic(df)
    assert "playtime_hours" in stats
    assert stats["languages"]["english"] == 2
    cmp = stats["playtime_recommender_vs_not"]
    assert cmp["recommender_hours"] is not None
    assert cmp["non_recommender_hours"] is not None


def test_analyze_basic_top_helpful_sorted():
    df = reviews_dataframe(_sample_reviews())
    stats = analyze_basic(df)
    votes = [t["votes_up"] for t in stats["top_helpful"]]
    assert votes == sorted(votes, reverse=True)
    assert votes[0] == 120


def test_analyze_basic_empty():
    import pandas as pd

    stats = analyze_basic(pd.DataFrame())
    assert stats["review_count"] == 0
    assert stats.get("empty") is True


def test_render_text_contains_disclaimer():
    df = reviews_dataframe(_sample_reviews())
    stats = analyze_basic(df, query_summary={"review_score_desc": "Very Positive", "total_reviews": 1000,
                                             "total_positive": 950, "total_negative": 50})
    out = render_text(stats, game_name="Test Game", appid=123)
    assert "Test Game" in out
    assert "추천이 아닙니다" in out
    assert "Very Positive" in out


def test_reviewbatch_len():
    batch = ReviewBatch(appid=1, reviews=_sample_reviews())
    assert len(batch) == 3
