"""작성일별 리뷰 수·감성 추세 — 패치 전후 같은 시간 변화를 드러낸다.

`created_date`(reviews_dataframe가 생성)를 기간(일/주/월)으로 묶어
리뷰 수와 긍정 비율을 시계열로 만든다.
"""

from __future__ import annotations

from typing import Any

# CLI/사람이 쓰는 빈도 별칭 → pandas 리샘플 규칙.
_FREQ_ALIASES = {"day": "D", "week": "W", "month": "ME", "D": "D", "W": "W", "M": "ME", "ME": "ME"}


def analyze_trends(df, *, freq: str = "week") -> dict[str, Any]:
    """작성일 기준 리뷰 수·긍정 비율 추세를 계산한다.

    Args:
        df: reviews_dataframe() 결과 (created_date, voted_up 사용).
        freq: "day" | "week" | "month" (또는 pandas 규칙 D/W/ME).

    Returns:
        {"freq", "points": [{"date","count","positive","positive_ratio"}...],
         "first_ratio","last_ratio","direction"}. 데이터 없으면 {"empty": True}.
    """
    if df is None or df.empty or "created_date" not in df:
        return {"empty": True, "points": []}

    sub = df[["created_date", "voted_up"]].dropna(subset=["created_date"]).copy()
    if sub.empty:
        return {"empty": True, "points": []}

    rule = _FREQ_ALIASES.get(freq, freq)
    sub["voted_up"] = sub["voted_up"].astype(bool)

    grouped = sub.set_index("created_date").resample(rule)
    counts = grouped["voted_up"].count()
    positives = grouped["voted_up"].sum()

    points: list[dict[str, Any]] = []
    for period, count in counts.items():
        count = int(count)
        if count == 0:
            continue
        pos = int(positives.loc[period])
        points.append(
            {
                "date": period.date().isoformat(),
                "count": count,
                "positive": pos,
                "positive_ratio": round(pos / count, 4),
            }
        )

    result: dict[str, Any] = {"freq": rule, "points": points}
    if points:
        first_ratio = points[0]["positive_ratio"]
        last_ratio = points[-1]["positive_ratio"]
        result["first_ratio"] = first_ratio
        result["last_ratio"] = last_ratio
        delta = last_ratio - first_ratio
        # 5%p 이상 변동만 방향성으로 표시(잡음 제거).
        if delta > 0.05:
            result["direction"] = "up"
        elif delta < -0.05:
            result["direction"] = "down"
        else:
            result["direction"] = "flat"
    return result
