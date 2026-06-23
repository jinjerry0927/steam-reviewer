"""차트 저장 테스트 — matplotlib 없으면 skip."""

import pytest

pytest.importorskip("matplotlib")

from steam_reviewer.analyzers.keywords import analyze_keywords  # noqa: E402
from steam_reviewer.analyzers.trends import analyze_trends  # noqa: E402
from steam_reviewer.loaders.steam import reviews_dataframe  # noqa: E402
from steam_reviewer.report.charts import save_charts  # noqa: E402

_DAY = 86_400
_BASE = 1_700_000_000


def _reviews():
    rows = []
    for i in range(6):
        rows.append({"review": "great combat music", "voted_up": True, "votes_up": 2, "language": "english",
                     "timestamp_created": _BASE + i * 3600,
                     "author": {"playtime_forever": 600 + i * 100}})
    for i in range(4):
        rows.append({"review": "crashes bad performance", "voted_up": False, "votes_up": 1, "language": "english",
                     "timestamp_created": _BASE + 14 * _DAY + i * 3600,
                     "author": {"playtime_forever": 120 + i * 30}})
    return rows


def test_save_charts_creates_pngs(tmp_path):
    df = reviews_dataframe(_reviews())
    trends = analyze_trends(df)
    keywords = analyze_keywords(df)
    saved = save_charts(df, out_dir=tmp_path, trends=trends, keywords=keywords, game_name="Test")
    assert len(saved) == 3  # trend + keywords + playtime
    for p in saved:
        assert p.exists()
        assert p.stat().st_size > 0
        assert p.suffix == ".png"


def test_save_charts_skips_missing_sections(tmp_path):
    df = reviews_dataframe(_reviews())
    # 추세/키워드 없이 호출 → 플레이타임 차트만
    saved = save_charts(df, out_dir=tmp_path)
    names = {p.name for p in saved}
    assert names == {"playtime.png"}
