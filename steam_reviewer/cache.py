"""수집한 리뷰를 로컬 JSON으로 캐싱한다.

같은 조합(appid·언어·필터·구매유형·개수)으로 재실행하면 Steam에 다시 요청하지
않고 캐시에서 복원한다 — 레이트리밋 매너 + 빠른 재실행.

**개인정보 비저장**: 캐시에는 ``sanitize_review``로 작성자 식별자를 제거한
안전 리뷰만 저장한다(상시 원칙 #2). 캐시 항목에는 ``cached_at`` 타임스탬프가
있어 TTL이 지나면 자동으로 무효가 된다.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .loaders.steam import ReviewBatch, fetch_reviews, sanitize_review

DEFAULT_CACHE_DIR = ".cache"
DEFAULT_TTL_HOURS = 24.0


class ReviewCache:
    """리뷰 ReviewBatch를 디렉터리 안 JSON 파일로 저장/복원한다."""

    def __init__(self, cache_dir: str | Path = DEFAULT_CACHE_DIR, *, ttl_hours: float = DEFAULT_TTL_HOURS) -> None:
        self.dir = Path(cache_dir)
        # ttl_hours <= 0 이면 만료 없음(항상 유효).
        self.ttl_seconds = ttl_hours * 3600 if ttl_hours and ttl_hours > 0 else None

    def _path(self, appid: int, language: str, review_filter: str, purchase_type: str, max_count: int) -> Path:
        raw = f"{appid}|{language}|{review_filter}|{purchase_type}|{max_count}"
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
        return self.dir / f"reviews_{appid}_{digest}.json"

    def get(
        self,
        appid: int,
        *,
        language: str,
        review_filter: str,
        purchase_type: str = "all",
        max_count: int,
    ) -> ReviewBatch | None:
        """캐시 적중 시 ReviewBatch, 미스/만료/손상 시 None."""
        path = self._path(appid, language, review_filter, purchase_type, max_count)
        if not path.exists():
            return None
        try:
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None  # 손상된 캐시는 미스로 취급(다음 set에서 덮어씀).

        if self.ttl_seconds is not None:
            cached_at = data.get("cached_at", 0)
            if time.time() - cached_at > self.ttl_seconds:
                return None

        return ReviewBatch(
            appid=int(data.get("appid", appid)),
            reviews=list(data.get("reviews") or []),
            query_summary=dict(data.get("query_summary") or {}),
        )

    def set(
        self,
        batch: ReviewBatch,
        *,
        language: str,
        review_filter: str,
        purchase_type: str = "all",
        max_count: int,
    ) -> Path:
        """ReviewBatch를 안전 리뷰만 추려 캐시에 저장한다."""
        self.dir.mkdir(parents=True, exist_ok=True)
        path = self._path(batch.appid, language, review_filter, purchase_type, max_count)
        payload = {
            "cached_at": time.time(),
            "appid": batch.appid,
            "language": language,
            "review_filter": review_filter,
            "purchase_type": purchase_type,
            "max_count": max_count,
            "query_summary": batch.query_summary,
            "reviews": [sanitize_review(r) for r in batch.reviews],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path


def fetch_reviews_cached(
    appid: int,
    *,
    max_count: int = 500,
    language: str = "all",
    review_filter: str = "recent",
    purchase_type: str = "all",
    cache: ReviewCache | None = None,
    refresh: bool = False,
    **fetch_kwargs: Any,
) -> tuple[ReviewBatch, bool]:
    """캐시를 거쳐 리뷰를 가져온다.

    Returns:
        (batch, from_cache). ``refresh=True`` 면 캐시를 무시하고 새로 받아 덮어쓴다.
    """
    cache = cache or ReviewCache()

    if not refresh:
        hit = cache.get(
            appid,
            language=language,
            review_filter=review_filter,
            purchase_type=purchase_type,
            max_count=max_count,
        )
        if hit is not None:
            return hit, True

    batch = fetch_reviews(
        appid,
        max_count=max_count,
        language=language,
        review_filter=review_filter,
        purchase_type=purchase_type,
        **fetch_kwargs,
    )
    cache.set(
        batch,
        language=language,
        review_filter=review_filter,
        purchase_type=purchase_type,
        max_count=max_count,
    )
    return batch, False
