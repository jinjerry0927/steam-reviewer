"""분석 결과를 PNG 차트로 저장한다 — matplotlib 선택 의존성(`[charts]`).

matplotlib가 없으면 import 시점이 아니라 호출 시점에 친절한 안내와 함께
ChartsUnavailable을 던진다(코어 동작은 차트 없이도 유지).
"""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any, Iterator


class ChartsUnavailable(RuntimeError):
    """matplotlib 미설치 등으로 차트를 만들 수 없음."""


def _require_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")  # 디스플레이 없는 환경에서도 PNG 저장.
        import matplotlib.pyplot as plt

        return plt
    except ImportError as exc:  # pragma: no cover - 환경 의존
        raise ChartsUnavailable(
            "차트 생성에는 matplotlib가 필요합니다. `pip install steam-reviewer[charts]` 로 설치하세요."
        ) from exc


def _iter_figures(
    plt,
    df,
    trends: dict[str, Any] | None,
    keywords: dict[str, Any] | None,
    suffix: str,
) -> Iterator[tuple[str, Any]]:
    """(이름, matplotlib Figure)를 순서대로 생성한다. save/embed가 공유한다."""
    # 1) 긍/부정 추세 라인
    if trends and trends.get("points"):
        points = trends["points"]
        dates = [p["date"] for p in points]
        ratios = [p["positive_ratio"] * 100 for p in points]
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(dates, ratios, marker="o", color="#66c0f4")
        ax.set_ylim(0, 100)
        ax.set_ylabel("Positive ratio (%)")
        ax.set_title(f"Review sentiment trend{suffix}")
        ax.grid(True, alpha=0.3)
        _thin_xticks(ax, len(dates))
        fig.autofmt_xdate()
        yield "trend", fig

    # 2) 키워드 막대 (긍/부정 나란히)
    if keywords and (keywords.get("positive") or keywords.get("negative")):
        fig, axes = plt.subplots(1, 2, figsize=(11, 5))
        _keyword_bar(axes[0], keywords.get("positive", []), "Positive keywords", "#5c9e3f")
        _keyword_bar(axes[1], keywords.get("negative", []), "Negative keywords", "#c0392b")
        fig.suptitle(f"Top keywords{suffix}")
        fig.tight_layout()
        yield "keywords", fig

    # 3) 플레이타임 분포 (시간 단위 히스토그램)
    if df is not None and not df.empty and "playtime_forever" in df:
        pt = df["playtime_forever"].dropna()
        pt = pt[pt > 0] / 60.0  # 분 → 시간, 0 제외
        if not pt.empty:
            fig, ax = plt.subplots(figsize=(8, 4))
            upper = pt.quantile(0.95)  # 극단값이 그래프를 망치지 않게 95분위로 클립
            ax.hist(pt.clip(upper=upper), bins=30, color="#66c0f4", edgecolor="white")
            ax.set_xlabel("Playtime (hours, top 5% clipped)")
            ax.set_ylabel("Reviews")
            ax.set_title(f"Playtime distribution{suffix}")
            ax.grid(True, alpha=0.3)
            yield "playtime", fig


def save_charts(
    df,
    *,
    out_dir: str | Path,
    trends: dict[str, Any] | None = None,
    keywords: dict[str, Any] | None = None,
    game_name: str = "",
) -> list[Path]:
    """플레이타임 분포·감성 추세·키워드 막대 차트를 PNG로 저장한다.

    Returns:
        저장된 PNG 경로 목록.
    """
    plt = _require_matplotlib()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    suffix = f" — {game_name}" if game_name else ""
    saved: list[Path] = []
    for name, fig in _iter_figures(plt, df, trends, keywords, suffix):
        saved.append(_save(fig, plt, out / f"{name}.png"))
    return saved


def charts_as_data_uris(
    df,
    *,
    trends: dict[str, Any] | None = None,
    keywords: dict[str, Any] | None = None,
    game_name: str = "",
) -> dict[str, str]:
    """차트를 base64 data URI(`data:image/png;base64,...`)로 만들어 반환한다.

    자기완결 HTML 리포트에 인라인 임베드하기 위함(외부 파일 의존 없음).
    matplotlib가 없으면 ChartsUnavailable.
    """
    plt = _require_matplotlib()
    suffix = f" — {game_name}" if game_name else ""
    uris: dict[str, str] = {}
    for name, fig in _iter_figures(plt, df, trends, keywords, suffix):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
        plt.close(fig)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        uris[name] = f"data:image/png;base64,{encoded}"
    return uris


def _keyword_bar(ax, items: list[dict[str, Any]], title: str, color: str) -> None:
    items = items[:10][::-1]  # 상위 10, 큰 값이 위로
    if not items:
        ax.set_title(f"{title} (없음)")
        ax.axis("off")
        return
    words = [it["word"] for it in items]
    counts = [it["count"] for it in items]
    ax.barh(words, counts, color=color)
    ax.set_title(title)


def _thin_xticks(ax, n: int, max_ticks: int = 12) -> None:
    if n <= max_ticks:
        return
    step = (n // max_ticks) + 1
    for i, label in enumerate(ax.get_xticklabels()):
        if i % step != 0:
            label.set_visible(False)


def _save(fig, plt, path: Path) -> Path:
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return path
