"""HTML 리포트 테스트 — 네트워크/렌더 의존 없이 문자열 검증."""

import pytest

from steam_reviewer.analyzers.basic import analyze_basic
from steam_reviewer.analyzers.keywords import analyze_keywords
from steam_reviewer.analyzers.trends import analyze_trends
from steam_reviewer.loaders.steam import reviews_dataframe
from steam_reviewer.report.html import render_html


def _reviews():
    return [
        {"review": "Great combat and story.", "voted_up": True, "votes_up": 30, "language": "english",
         "timestamp_created": 1_700_000_000, "author": {"playtime_forever": 1200}},
        {"review": "Crashes and bad performance.", "voted_up": False, "votes_up": 12, "language": "english",
         "timestamp_created": 1_700_200_000, "author": {"playtime_forever": 200}},
    ]


def _stats():
    df = reviews_dataframe(_reviews())
    stats = analyze_basic(df, query_summary={"review_score_desc": "Very Positive", "total_reviews": 1000,
                                             "total_positive": 900, "total_negative": 100})
    stats["keywords"] = analyze_keywords(df)
    stats["trends"] = analyze_trends(df)
    return stats


def test_render_html_basic_structure():
    html = render_html(_stats(), game_name="Test Game", appid=123)
    assert html.startswith("<!doctype html>")
    assert "Test Game" in html
    assert "App 123" in html
    assert "추천이 아닙니다" in html  # 면책
    assert "Very Positive" in html


def test_render_html_with_appdetails_and_image():
    details = {
        "name": "Hades II", "header_image": "https://example.com/h.jpg",
        "genres": ["Action", "Roguelike"], "price": "₩29,000",
        "developers": ["Supergiant"], "release_date": "2024",
        "short_description": "A rogue-like dungeon crawler.",
    }
    html = render_html(_stats(), game_name="Hades II", appid=1145350, appdetails=details)
    assert 'src="https://example.com/h.jpg"' in html
    assert "Action" in html and "Roguelike" in html
    assert "Supergiant" in html
    assert "₩29,000" in html


def test_render_html_embeds_chart_data_uri():
    uris = {"trend": "data:image/png;base64,AAAA", "playtime": "data:image/png;base64,BBBB"}
    html = render_html(_stats(), game_name="X", appid=1, chart_uris=uris)
    assert "data:image/png;base64,AAAA" in html
    assert 'class="chart"' in html


def test_render_html_includes_ai_summary():
    html = render_html(_stats(), game_name="X", appid=1, ai_summary="■ 게임성\n  칭찬: 전투")
    assert "AI 측면별 요약" in html
    assert "전투" in html


def test_render_html_escapes_user_text():
    details = {"name": "<script>alert(1)</script>", "genres": [], "developers": []}
    html = render_html(_stats(), game_name="x", appid=1, appdetails=details)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_render_html_no_optional_sections():
    # 키워드/추세/AI/차트/상세 없이도 깨지지 않음
    df = reviews_dataframe(_reviews())
    stats = analyze_basic(df)
    html = render_html(stats, game_name="Bare", appid=9)
    assert "Bare" in html
    assert html.rstrip().endswith("</html>")


def test_charts_as_data_uris():
    pytest.importorskip("matplotlib")
    from steam_reviewer.report.charts import charts_as_data_uris

    df = reviews_dataframe(_reviews())
    uris = charts_as_data_uris(df, trends=analyze_trends(df), keywords=analyze_keywords(df), game_name="X")
    assert "playtime" in uris
    for uri in uris.values():
        assert uri.startswith("data:image/png;base64,")
