"""분석 결과를 자기완결(self-contained) HTML 한 장으로 렌더링한다.

차트는 base64 data URI로 인라인 임베드하므로 외부 파일 의존이 없다(파일 하나만
열면 됨). Steam 다크 테마. 외부 의존성 없음(표준 라이브러리 `html`만 사용).
"""

from __future__ import annotations

from html import escape
from typing import Any

_DISCLAIMER = (
    "이 리포트는 공개 리뷰의 집계·요약이며 구매 추천이 아닙니다. "
    "플레이어들의 평가 경향을 보여줄 뿐입니다."
)

_CSS = """
:root { --bg:#1b2838; --panel:#2a475e; --panel2:#1f3a4d; --accent:#66c0f4;
  --text:#c7d5e0; --muted:#8f98a0; --pos:#a4d007; --neg:#c0392b; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text);
  font-family:'Segoe UI',Roboto,'Malgun Gothic',sans-serif; line-height:1.5; }
.wrap { max-width:960px; margin:0 auto; padding:24px; }
.header { display:flex; gap:20px; align-items:center; flex-wrap:wrap;
  background:var(--panel); border-radius:8px; padding:20px; margin-bottom:20px; }
.header img { width:292px; max-width:100%; border-radius:6px; }
.header h1 { margin:0 0 6px; font-size:26px; color:#fff; }
.meta { color:var(--muted); font-size:14px; }
.genres span { display:inline-block; background:var(--panel2); color:var(--accent);
  border-radius:4px; padding:2px 8px; margin:3px 4px 0 0; font-size:12px; }
.card { background:var(--panel); border-radius:8px; padding:18px 20px; margin-bottom:18px; }
.card h2 { margin:0 0 12px; font-size:18px; color:var(--accent); }
.big { font-size:22px; color:#fff; }
.bar { height:14px; border-radius:7px; background:var(--neg); overflow:hidden; margin:8px 0; }
.bar > div { height:100%; background:var(--pos); }
.kv { display:flex; flex-wrap:wrap; gap:18px; }
.kv div { min-width:130px; }
.kv .label { color:var(--muted); font-size:12px; }
.kw { display:flex; gap:24px; flex-wrap:wrap; }
.kw ul { list-style:none; padding:0; margin:0; flex:1; min-width:220px; }
.kw li { padding:3px 0; border-bottom:1px solid var(--panel2); }
.kw .count { color:var(--muted); float:right; }
.pos-h { color:var(--pos); } .neg-h { color:var(--neg); }
.review { background:var(--panel2); border-radius:6px; padding:10px 12px; margin:8px 0; font-size:14px; }
img.chart { width:100%; border-radius:6px; margin:8px 0; background:#fff; }
pre.ai { white-space:pre-wrap; background:var(--panel2); border-radius:6px; padding:14px;
  font-family:inherit; font-size:14px; margin:0; }
.foot { color:var(--muted); font-size:12px; margin-top:24px; text-align:center; }
"""


def _ratio_pct(stats: dict[str, Any]) -> str:
    r = stats.get("positive_ratio")
    return f"{r * 100:.0f}%" if r is not None else "N/A"


def render_html(
    stats: dict[str, Any],
    *,
    game_name: str,
    appid: int,
    appdetails: dict[str, Any] | None = None,
    chart_uris: dict[str, str] | None = None,
    ai_summary: str | None = None,
) -> str:
    """분석 통계를 HTML 문자열로 렌더링한다."""
    chart_uris = chart_uris or {}
    parts: list[str] = []

    # ---- 헤더 (앱 상세) ----
    title = escape(str((appdetails or {}).get("name") or game_name))
    header_bits = [f"<h1>{title}</h1>", f'<div class="meta">App {appid}']
    if appdetails:
        if appdetails.get("developers"):
            header_bits.append(" · " + escape(", ".join(appdetails["developers"])))
        if appdetails.get("release_date"):
            header_bits.append(" · " + escape(str(appdetails["release_date"])))
        if appdetails.get("price"):
            header_bits.append(" · " + escape(str(appdetails["price"])))
    header_bits.append("</div>")
    if appdetails and appdetails.get("genres"):
        genres = "".join(f"<span>{escape(g)}</span>" for g in appdetails["genres"])
        header_bits.append(f'<div class="genres">{genres}</div>')
    if appdetails and appdetails.get("short_description"):
        header_bits.append(f'<p class="meta">{escape(appdetails["short_description"])}</p>')

    img = ""
    if appdetails and appdetails.get("header_image"):
        img = f'<img src="{escape(appdetails["header_image"])}" alt="{title}">'
    parts.append(f'<div class="header">{img}<div>{"".join(header_bits)}</div></div>')

    # ---- 핵심 통계 ----
    n = stats.get("review_count", 0)
    pos = stats.get("positive", 0)
    neg = stats.get("negative", 0)
    r = stats.get("positive_ratio") or 0
    overview = [
        '<div class="card"><h2>개요</h2>',
        f'<div class="big">표본 {n:,}개 · 긍정 {_ratio_pct(stats)}</div>',
        f'<div class="bar"><div style="width:{r * 100:.0f}%"></div></div>',
        f'<div class="meta">👍 {pos:,} · 👎 {neg:,}</div>',
    ]
    steam = stats.get("steam_summary")
    if steam and steam.get("total_reviews"):
        overview.append(
            f'<div class="meta">전체(Steam): {escape(str(steam.get("review_score_desc") or ""))} · '
            f'리뷰 {steam["total_reviews"]:,}개</div>'
        )
    overview.append("</div>")
    parts.append("".join(overview))

    # ---- 플레이타임 / 분포 ----
    kv_items: list[str] = []
    pt = stats.get("playtime_hours")
    if pt:
        kv_items.append(_kv("평균 플레이타임", f'{pt.get("mean")}h'))
        kv_items.append(_kv("중앙 플레이타임", f'{pt.get("median")}h'))
    cmp = stats.get("playtime_recommender_vs_not")
    if cmp and cmp.get("ratio"):
        kv_items.append(_kv("추천자/비추천자 플레이", f'{cmp["ratio"]}배'))
    dist = stats.get("distributions") or {}
    if dist.get("length"):
        kv_items.append(_kv("리뷰 길이(중앙, 문자)", str(dist["length"]["median"])))
    if kv_items:
        parts.append(f'<div class="card"><h2>플레이타임 · 분포</h2><div class="kv">{"".join(kv_items)}</div></div>')

    # ---- 차트 (인라인) ----
    chart_titles = {"trend": "감성 추세", "keywords": "키워드", "playtime": "플레이타임 분포"}
    chart_html = []
    for key in ("trend", "keywords", "playtime"):
        if key in chart_uris:
            chart_html.append(f'<img class="chart" src="{chart_uris[key]}" alt="{chart_titles[key]}">')
    if chart_html:
        parts.append(f'<div class="card"><h2>차트</h2>{"".join(chart_html)}</div>')

    # ---- 키워드 ----
    kw = stats.get("keywords") or {}
    if kw.get("positive") or kw.get("negative"):
        parts.append(
            '<div class="card"><h2>빈출 키워드</h2><div class="kw">'
            + _kw_list("👍 칭찬", kw.get("positive", []), "pos-h")
            + _kw_list("👎 불만", kw.get("negative", []), "neg-h")
            + "</div></div>"
        )

    # ---- 감성 추세 요약 ----
    trends = stats.get("trends") or {}
    if trends.get("points"):
        pts = trends["points"]
        first, last = pts[0], pts[-1]
        arrow = {"up": "📈 상승", "down": "📉 하락", "flat": "➡️ 보합"}.get(trends.get("direction"), "")
        parts.append(
            f'<div class="card"><h2>감성 추세</h2><div class="meta">{escape(first["date"])} '
            f'긍정 {first["positive_ratio"] * 100:.0f}% → {escape(last["date"])} '
            f'긍정 {last["positive_ratio"] * 100:.0f}% {arrow}</div></div>'
        )

    # ---- 도움된 리뷰 ----
    top = stats.get("top_helpful") or []
    if top:
        items = []
        for t in top:
            mark = "👍" if t.get("voted_up") else "👎"
            items.append(f'<div class="review">{mark} (+{t.get("votes_up", 0)}) {escape(t.get("excerpt", ""))}</div>')
        parts.append(f'<div class="card"><h2>도움이 된 리뷰</h2>{"".join(items)}</div>')

    # ---- AI 요약 ----
    if ai_summary:
        parts.append(f'<div class="card"><h2>🤖 AI 측면별 요약</h2><pre class="ai">{escape(ai_summary)}</pre></div>')

    body = "\n".join(parts)
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Steam 리뷰 분석</title>
<style>{_CSS}</style></head>
<body><div class="wrap">
{body}
<div class="foot">ℹ️ {escape(_DISCLAIMER)}<br>steam-reviewer · 공개 Steam 리뷰 기반</div>
</div></body></html>"""


def _kv(label: str, value: str) -> str:
    return f'<div><div class="label">{escape(label)}</div><div class="big">{escape(value)}</div></div>'


def _kw_list(title: str, items: list[dict[str, Any]], cls: str) -> str:
    lis = "".join(
        f'<li>{escape(str(it["word"]))}<span class="count">{it["count"]}</span></li>' for it in items[:10]
    )
    return f'<ul><li class="{cls}"><strong>{escape(title)}</strong></li>{lis}</ul>'
