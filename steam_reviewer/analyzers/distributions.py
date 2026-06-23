"""리뷰 길이·도움됨(votes_up) 분포 통계 — AI 없이 순수 pandas로 동작한다."""

from __future__ import annotations

from typing import Any

# 도움됨(votes_up) 구간 경계. (하한 포함, 상한 미만) — 마지막은 무한대.
_VOTE_BINS = [(0, 1), (1, 5), (5, 20), (20, 100), (100, None)]


def analyze_distributions(df) -> dict[str, Any]:
    """리뷰 길이와 votes_up 분포를 계산한다.

    Args:
        df: reviews_dataframe() 결과 (review, votes_up 사용).

    Returns:
        {"length": {...}, "votes_up": {...}}. 데이터 없으면 {"empty": True}.
    """
    if df is None or df.empty:
        return {"empty": True}

    result: dict[str, Any] = {}

    if "review" in df:
        lengths = df["review"].dropna().map(lambda t: len(str(t)))
        if not lengths.empty:
            result["length"] = {
                "mean": round(float(lengths.mean()), 1),
                "median": int(lengths.median()),
                "min": int(lengths.min()),
                "max": int(lengths.max()),
            }

    if "votes_up" in df:
        votes = df["votes_up"].dropna().astype(int)
        if not votes.empty:
            buckets: list[dict[str, Any]] = []
            for low, high in _VOTE_BINS:
                if high is None:
                    mask = votes >= low
                    label = f"{low}+"
                else:
                    mask = (votes >= low) & (votes < high)
                    label = f"{low}-{high - 1}" if high - low > 1 else str(low)
                buckets.append({"range": label, "count": int(mask.sum())})
            result["votes_up"] = {
                "mean": round(float(votes.mean()), 1),
                "median": int(votes.median()),
                "max": int(votes.max()),
                "buckets": buckets,
            }

    return result
