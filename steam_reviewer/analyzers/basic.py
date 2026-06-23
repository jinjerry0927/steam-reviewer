"""기본 통계 분석 — AI 없이 순수 pandas로 동작한다.

긍/부정 비율, 플레이타임, 추천자 vs 비추천자 비교, 영향력 큰 리뷰 식별.
"""

from __future__ import annotations

from typing import Any


def _minutes_to_hours(minutes: float | None) -> float | None:
    if minutes is None:
        return None
    try:
        return round(float(minutes) / 60.0, 1)
    except (TypeError, ValueError):
        return None


def analyze_basic(df, query_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    """리뷰 DataFrame에서 기본 통계를 계산한다.

    Args:
        df: reviews_dataframe() 결과.
        query_summary: Steam이 준 전체 요약(선택). 표본 외 전체 통계 참고용.

    Returns:
        리포트/AI 계층이 소비하는 통계 dict.
    """
    result: dict[str, Any] = {"review_count": int(len(df))}

    if df is None or df.empty:
        result["empty"] = True
        return result

    # 긍/부정 (표본 기준)
    voted = df["voted_up"].dropna().astype(bool)
    pos = int(voted.sum())
    neg = int((~voted).sum())
    total = pos + neg
    result["positive"] = pos
    result["negative"] = neg
    result["positive_ratio"] = round(pos / total, 4) if total else None

    # 언어 분포 (상위 5)
    if "language" in df:
        result["languages"] = df["language"].value_counts().head(5).to_dict()

    # 플레이타임 (분 → 시간)
    pt = df["playtime_forever"].dropna()
    if not pt.empty:
        result["playtime_hours"] = {
            "mean": _minutes_to_hours(pt.mean()),
            "median": _minutes_to_hours(pt.median()),
        }

    # 추천자 vs 비추천자 플레이타임(작성 시점 기준)
    if "playtime_at_review" in df and "voted_up" in df:
        sub = df[["voted_up", "playtime_at_review"]].dropna()
        if not sub.empty:
            rec = sub[sub["voted_up"] == True]["playtime_at_review"]  # noqa: E712
            non = sub[sub["voted_up"] == False]["playtime_at_review"]  # noqa: E712
            rec_h = _minutes_to_hours(rec.mean()) if not rec.empty else None
            non_h = _minutes_to_hours(non.mean()) if not non.empty else None
            ratio = None
            if rec_h and non_h and non_h > 0:
                ratio = round(rec_h / non_h, 1)
            result["playtime_recommender_vs_not"] = {
                "recommender_hours": rec_h,
                "non_recommender_hours": non_h,
                "ratio": ratio,
            }

    # 영향력 큰 리뷰 (votes_up 상위)
    if "votes_up" in df:
        top = df.sort_values("votes_up", ascending=False).head(3)
        result["top_helpful"] = [
            {
                "votes_up": int(row.votes_up) if row.votes_up is not None else 0,
                "voted_up": bool(row.voted_up) if row.voted_up is not None else None,
                "excerpt": _excerpt(row.review),
            }
            for row in top.itertuples()
        ]

    # Steam 전체 요약(표본이 아닌 모집단 참고)
    if query_summary:
        result["steam_summary"] = {
            "review_score_desc": query_summary.get("review_score_desc"),
            "total_positive": query_summary.get("total_positive"),
            "total_negative": query_summary.get("total_negative"),
            "total_reviews": query_summary.get("total_reviews"),
        }

    return result


def _excerpt(text: Any, limit: int = 160) -> str:
    if not isinstance(text, str):
        return ""
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rstrip() + "…"
