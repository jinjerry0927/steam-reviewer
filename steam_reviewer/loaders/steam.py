"""Steam 공개 API에서 리뷰와 게임 정보를 수집한다.

모든 엔드포인트는 공개(키 불필요)이며 **읽기 전용**이다.
작성자 식별 정보(steamid 등)는 분석에 쓰지 않으며 저장/재배포하지 않는다.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import requests

STORE_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
APPREVIEWS_URL = "https://store.steampowered.com/appreviews/{appid}"
APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"

_DEFAULT_HEADERS = {"User-Agent": "steam-reviewer/0.1 (+https://github.com/jinjerry0927/steam-reviewer)"}
_TIMEOUT = 15


class SteamAPIError(RuntimeError):
    """Steam API 호출 실패."""


@dataclass
class ReviewBatch:
    """수집한 리뷰와 Steam이 제공하는 요약 통계."""

    appid: int
    reviews: list[dict[str, Any]] = field(default_factory=list)
    query_summary: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.reviews)


def resolve_appid(name: str, *, country: str = "us", language: str = "en") -> tuple[int, str]:
    """게임 이름으로 Steam App ID를 찾는다.

    Returns:
        (appid, 정식 게임명). 매칭 실패 시 SteamAPIError.
    """
    if name.strip().isdigit():
        return int(name.strip()), name.strip()

    params = {"term": name, "cc": country, "l": language}
    try:
        resp = requests.get(STORE_SEARCH_URL, params=params, headers=_DEFAULT_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise SteamAPIError(f"이름 검색 실패: {name!r} ({exc})") from exc

    items = data.get("items") or []
    if not items:
        raise SteamAPIError(f"'{name}'(으)로 게임을 찾지 못했습니다. 정확한 이름이나 App ID를 써보세요.")
    top = items[0]
    return int(top["id"]), str(top.get("name", name))


def fetch_appdetails(appid: int, *, country: str = "us", language: str = "english") -> dict[str, Any]:
    """게임 상세(이름·장르·헤더이미지·가격 등)를 가져온다. 공개·읽기 전용.

    Returns:
        정규화된 dict: name, header_image, genres(list[str]), price, is_free,
        short_description, developers(list[str]), release_date.
        실패/미공개 앱이면 SteamAPIError.
    """
    params = {"appids": appid, "cc": country, "l": language}
    try:
        resp = requests.get(APPDETAILS_URL, params=params, headers=_DEFAULT_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise SteamAPIError(f"앱 상세 수집 실패 (appid={appid}): {exc}") from exc

    entry = (data or {}).get(str(appid)) or {}
    if not entry.get("success") or not entry.get("data"):
        raise SteamAPIError(f"앱 상세를 가져올 수 없습니다 (appid={appid}). 비공개이거나 지역 제한일 수 있습니다.")

    d = entry["data"]
    price = None
    if d.get("is_free"):
        price = "무료"
    elif d.get("price_overview"):
        price = d["price_overview"].get("final_formatted")

    return {
        "appid": appid,
        "name": d.get("name"),
        "header_image": d.get("header_image"),
        "genres": [g.get("description") for g in (d.get("genres") or []) if g.get("description")],
        "price": price,
        "is_free": bool(d.get("is_free")),
        "short_description": d.get("short_description"),
        "developers": d.get("developers") or [],
        "release_date": (d.get("release_date") or {}).get("date"),
    }


def fetch_reviews(
    appid: int,
    *,
    max_count: int = 1000,
    language: str = "all",
    review_filter: str = "recent",
    purchase_type: str = "all",
    delay: float = 0.4,
    session: requests.Session | None = None,
) -> ReviewBatch:
    """커서 페이지네이션으로 리뷰를 최대 max_count개 수집한다.

    Args:
        appid: Steam App ID.
        max_count: 가져올 최대 리뷰 수.
        language: "all" 또는 Steam 언어 코드("english", "koreana" 등).
        review_filter: "recent" | "updated" | "all".
        purchase_type: "all" | "steam" | "non_steam_purchase".
        delay: 요청 간 대기(초). 레이트리밋 매너.
        session: 재사용할 requests 세션(선택).
    """
    sess = session or requests.Session()
    sess.headers.update(_DEFAULT_HEADERS)

    collected: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}
    cursor = "*"
    seen_cursors: set[str] = set()

    while len(collected) < max_count:
        params = {
            "json": 1,
            "filter": review_filter,
            "language": language,
            "purchase_type": purchase_type,
            "num_per_page": min(100, max_count - len(collected)),
            "cursor": cursor,
        }
        try:
            resp = sess.get(APPREVIEWS_URL.format(appid=appid), params=params, timeout=_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            raise SteamAPIError(f"리뷰 수집 실패 (appid={appid}): {exc}") from exc

        if data.get("success") != 1:
            raise SteamAPIError(f"Steam이 success!=1 응답 (appid={appid}).")

        if not summary:
            summary = data.get("query_summary", {})

        page = data.get("reviews") or []
        if not page:
            break
        collected.extend(page)

        next_cursor = data.get("cursor", "")
        if not next_cursor or next_cursor in seen_cursors:
            break
        seen_cursors.add(next_cursor)
        cursor = next_cursor

        if len(collected) < max_count:
            time.sleep(delay)

    return ReviewBatch(appid=appid, reviews=collected[:max_count], query_summary=summary)


# 분석에 사용할 안전한 필드만 추린다(작성자 식별자 제외).
_SAFE_FIELDS = {
    "voted_up": "voted_up",
    "votes_up": "votes_up",
    "votes_funny": "votes_funny",
    "weighted_vote_score": "weighted_vote_score",
    "comment_count": "comment_count",
    "language": "language",
    "review": "review",
    "timestamp_created": "timestamp_created",
    "timestamp_updated": "timestamp_updated",
    "steam_purchase": "steam_purchase",
    "received_for_free": "received_for_free",
}


def sanitize_review(r: dict[str, Any]) -> dict[str, Any]:
    """저장·캐시용으로 작성자 식별자를 제거한 안전 리뷰 dict를 만든다.

    원본 응답의 ``author.steamid`` 등은 버리고, 분석에 필요한 안전 필드와
    플레이타임만 남긴다. 결과는 ``reviews_dataframe``이 그대로 처리할 수 있다.
    """
    row: dict[str, Any] = {src: r.get(src) for src in _SAFE_FIELDS}
    author = r.get("author") or {}
    row["author"] = {
        "playtime_forever": author.get("playtime_forever"),
        "playtime_at_review": author.get("playtime_at_review"),
        "num_games_owned": author.get("num_games_owned"),
    }
    return row


def reviews_dataframe(batch: ReviewBatch | list[dict[str, Any]]):
    """ReviewBatch(또는 리뷰 리스트)를 pandas DataFrame으로 변환한다.

    작성자 개인정보는 제외하고, author.playtime_forever / playtime_at_review만 추출한다.
    """
    import pandas as pd

    reviews = batch.reviews if isinstance(batch, ReviewBatch) else batch
    rows = []
    for r in reviews:
        row = {dst: r.get(src) for src, dst in _SAFE_FIELDS.items()}
        author = r.get("author") or {}
        # 플레이타임은 분석에 필요 — 식별자(steamid)는 제외
        row["playtime_forever"] = author.get("playtime_forever")
        row["playtime_at_review"] = author.get("playtime_at_review")
        row["num_games_owned"] = author.get("num_games_owned")
        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty and "timestamp_created" in df:
        df["created_date"] = pd.to_datetime(df["timestamp_created"], unit="s", errors="coerce")
    return df
