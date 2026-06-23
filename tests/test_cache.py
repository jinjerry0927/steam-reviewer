"""리뷰 캐시 테스트 — 네트워크 없이 mock 리뷰로 검증."""

import json
import time

from steam_reviewer import cache as cache_mod
from steam_reviewer.cache import ReviewCache, fetch_reviews_cached
from steam_reviewer.loaders.steam import ReviewBatch


def _sample_reviews():
    return [
        {
            "review": "Great game.",
            "voted_up": True,
            "votes_up": 10,
            "language": "english",
            "timestamp_created": 1_700_000_000,
            "author": {"steamid": "SECRET123", "playtime_forever": 2400, "playtime_at_review": 1800, "num_games_owned": 50},
        },
        {
            "review": "Buggy.",
            "voted_up": False,
            "votes_up": 2,
            "language": "english",
            "timestamp_created": 1_700_100_000,
            "author": {"steamid": "SECRET456", "playtime_forever": 300, "playtime_at_review": 120, "num_games_owned": 10},
        },
    ]


def _batch():
    return ReviewBatch(appid=42, reviews=_sample_reviews(), query_summary={"review_score_desc": "Very Positive"})


_KEY = dict(language="all", review_filter="recent", purchase_type="all", max_count=500)


def test_cache_roundtrip(tmp_path):
    c = ReviewCache(tmp_path)
    assert c.get(42, **_KEY) is None  # 처음엔 미스
    c.set(_batch(), **_KEY)
    hit = c.get(42, **_KEY)
    assert hit is not None
    assert hit.appid == 42
    assert len(hit.reviews) == 2
    assert hit.query_summary["review_score_desc"] == "Very Positive"


def test_cache_does_not_persist_steamid(tmp_path):
    c = ReviewCache(tmp_path)
    path = c.set(_batch(), **_KEY)
    raw = path.read_text(encoding="utf-8")
    assert "SECRET123" not in raw  # 작성자 식별자 미저장(상시 원칙 #2)
    assert "steamid" not in raw
    assert "playtime_forever" in raw  # 분석용 플레이타임은 유지


def test_cache_expiry(tmp_path):
    c = ReviewCache(tmp_path, ttl_hours=1.0)
    path = c.set(_batch(), **_KEY)
    # cached_at 을 2시간 전으로 조작 → 만료
    data = json.loads(path.read_text(encoding="utf-8"))
    data["cached_at"] = time.time() - 2 * 3600
    path.write_text(json.dumps(data), encoding="utf-8")
    assert c.get(42, **_KEY) is None


def test_cache_no_expiry_when_ttl_zero(tmp_path):
    c = ReviewCache(tmp_path, ttl_hours=0)
    path = c.set(_batch(), **_KEY)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["cached_at"] = 0  # 아주 오래 전
    path.write_text(json.dumps(data), encoding="utf-8")
    assert c.get(42, **_KEY) is not None


def test_cache_key_varies_with_max_count(tmp_path):
    c = ReviewCache(tmp_path)
    c.set(_batch(), **_KEY)
    other = dict(_KEY, max_count=1000)
    assert c.get(42, **other) is None  # 다른 개수 → 다른 키 → 미스


def test_fetch_reviews_cached_uses_cache(tmp_path, monkeypatch):
    calls = {"n": 0}

    def fake_fetch(appid, **kwargs):
        calls["n"] += 1
        return _batch()

    monkeypatch.setattr(cache_mod, "fetch_reviews", fake_fetch)
    c = ReviewCache(tmp_path)

    b1, from_cache1 = fetch_reviews_cached(42, cache=c, **_KEY)
    b2, from_cache2 = fetch_reviews_cached(42, cache=c, **_KEY)
    assert calls["n"] == 1  # 두 번째는 캐시 사용 → 재요청 없음
    assert from_cache1 is False
    assert from_cache2 is True
    assert len(b2.reviews) == 2


def test_fetch_reviews_cached_refresh_bypasses(tmp_path, monkeypatch):
    calls = {"n": 0}

    def fake_fetch(appid, **kwargs):
        calls["n"] += 1
        return _batch()

    monkeypatch.setattr(cache_mod, "fetch_reviews", fake_fetch)
    c = ReviewCache(tmp_path)

    fetch_reviews_cached(42, cache=c, **_KEY)
    _, from_cache = fetch_reviews_cached(42, cache=c, refresh=True, **_KEY)
    assert calls["n"] == 2  # refresh 는 캐시 무시하고 재요청
    assert from_cache is False
