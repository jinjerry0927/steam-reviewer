"""기본 통계 dict를 보기 좋은 텍스트 리포트로 렌더링한다."""

from __future__ import annotations

from typing import Any

_DISCLAIMER = (
    "ℹ️  이 리포트는 공개 리뷰의 집계·요약이며 구매 추천이 아닙니다. "
    "플레이어들의 평가 경향을 보여줄 뿐입니다."
)


def render_text(stats: dict[str, Any], *, game_name: str, appid: int) -> str:
    lines: list[str] = []
    lines.append(f"🎮 {game_name} (App {appid}) — 리뷰 분석")
    lines.append("=" * 48)

    if stats.get("empty") or stats.get("review_count", 0) == 0:
        lines.append("수집된 리뷰가 없습니다.")
        return "\n".join(lines)

    n = stats["review_count"]
    pos = stats.get("positive", 0)
    neg = stats.get("negative", 0)
    ratio = stats.get("positive_ratio")
    ratio_str = f"{ratio * 100:.0f}%" if ratio is not None else "N/A"
    lines.append(f"표본 리뷰 {n:,}개 · 긍정 {ratio_str}  (👍 {pos:,} / 👎 {neg:,})")

    steam = stats.get("steam_summary")
    if steam and steam.get("total_reviews"):
        desc = steam.get("review_score_desc") or ""
        lines.append(
            f"전체(Steam): {desc} · 리뷰 {steam['total_reviews']:,}개 "
            f"(👍 {steam.get('total_positive', 0):,} / 👎 {steam.get('total_negative', 0):,})"
        )

    pt = stats.get("playtime_hours")
    if pt:
        lines.append("")
        lines.append(f"⏱️  평균 플레이타임 {pt.get('mean')}h · 중앙값 {pt.get('median')}h")

    cmp = stats.get("playtime_recommender_vs_not")
    if cmp:
        rec = cmp.get("recommender_hours")
        non = cmp.get("non_recommender_hours")
        ratio_pt = cmp.get("ratio")
        msg = f"   추천자 {rec}h vs 비추천자 {non}h"
        if ratio_pt:
            msg += f"  → 추천자가 {ratio_pt}배 더 오래 플레이"
        lines.append(msg)

    langs = stats.get("languages")
    if langs:
        lines.append("")
        lang_str = ", ".join(f"{k} {v}" for k, v in langs.items())
        lines.append(f"🌐 언어 분포(상위): {lang_str}")

    dist = stats.get("distributions")
    if dist and not dist.get("empty"):
        length = dist.get("length")
        votes = dist.get("votes_up")
        if length:
            lines.append("")
            lines.append(
                f"📝 리뷰 길이(문자): 평균 {length['mean']} · 중앙값 {length['median']} "
                f"(최소 {length['min']} / 최대 {length['max']})"
            )
        if votes:
            bucket_str = ", ".join(f"{b['range']}:{b['count']}" for b in votes.get("buckets", []))
            lines.append(f"👍 도움됨(votes_up) 분포: {bucket_str}  · 중앙값 {votes['median']} / 최대 {votes['max']}")

    kw = stats.get("keywords")
    if kw and not kw.get("empty"):
        pos_kw = kw.get("positive") or []
        neg_kw = kw.get("negative") or []
        if pos_kw or neg_kw:
            lines.append("")
            lines.append("🔑 빈출 키워드 (라틴 문자 기준)")
            if pos_kw:
                lines.append("  👍 " + ", ".join(f"{k['word']}({k['count']})" for k in pos_kw[:10]))
            if neg_kw:
                lines.append("  👎 " + ", ".join(f"{k['word']}({k['count']})" for k in neg_kw[:10]))

    trends = stats.get("trends")
    if trends and not trends.get("empty") and trends.get("points"):
        pts = trends["points"]
        lines.append("")
        first, last = pts[0], pts[-1]
        arrow = {"up": "📈 상승", "down": "📉 하락", "flat": "➡️ 보합"}.get(trends.get("direction"), "")
        lines.append(
            f"📅 감성 추세({trends.get('freq')}): "
            f"{first['date']} 긍정 {first['positive_ratio'] * 100:.0f}% "
            f"→ {last['date']} 긍정 {last['positive_ratio'] * 100:.0f}%  {arrow}"
        )

    top = stats.get("top_helpful")
    if top:
        lines.append("")
        lines.append("🔝 도움이 된 리뷰 (votes_up 상위)")
        for i, t in enumerate(top, 1):
            mark = "👍" if t.get("voted_up") else "👎"
            lines.append(f"  {i}. {mark} (+{t.get('votes_up', 0)}) {t.get('excerpt', '')}")

    lines.append("")
    lines.append(_DISCLAIMER)
    return "\n".join(lines)
