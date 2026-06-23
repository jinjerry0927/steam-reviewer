"""steam-reviewer 커맨드라인 인터페이스."""

from __future__ import annotations

import sys

import typer

# Windows 레거시 콘솔(cp949 등)에서 이모지 출력 시 크래시 방지.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

from .analyzers.basic import analyze_basic
from .analyzers.distributions import analyze_distributions
from .analyzers.keywords import analyze_keywords
from .analyzers.trends import analyze_trends
from .cache import ReviewCache, fetch_reviews_cached
from .loaders.steam import SteamAPIError, resolve_appid, reviews_dataframe
from .report.text import render_text

app = typer.Typer(add_completion=False, help="Steam 리뷰를 수집·분석해 리포트를 생성합니다.")


@app.callback()
def _root() -> None:
    """Steam 리뷰 분석 CLI. 하위 명령: analyze"""


@app.command()
def analyze(
    game: str = typer.Argument(..., help="게임 이름 또는 Steam App ID"),
    max_count: int = typer.Option(500, "--max", "-n", help="수집할 최대 리뷰 수"),
    language: str = typer.Option("all", "--language", "-l", help='리뷰 언어 ("all", "english", "koreana" 등)'),
    review_filter: str = typer.Option("recent", "--filter", "-f", help='정렬 ("recent" | "updated" | "all")'),
    refresh: bool = typer.Option(False, "--refresh", help="캐시를 무시하고 새로 수집"),
    no_cache: bool = typer.Option(False, "--no-cache", help="로컬 캐시를 쓰지도 만들지도 않음"),
    cache_ttl: float = typer.Option(24.0, "--cache-ttl", help="캐시 유효 시간(시간). 0이면 만료 없음"),
    trend_freq: str = typer.Option("week", "--trend", help='감성 추세 단위 ("day" | "week" | "month")'),
    charts_dir: str = typer.Option(None, "--charts", help="차트 PNG를 저장할 디렉터리 (matplotlib 필요)"),
) -> None:
    """게임의 Steam 리뷰를 분석해 텍스트 리포트를 출력합니다."""
    try:
        appid, name = resolve_appid(game)
    except SteamAPIError as exc:
        typer.secho(f"❌ {exc}", fg=typer.colors.RED)
        raise typer.Exit(1)

    typer.secho(f"⏳ '{name}' (App {appid}) 리뷰 수집 중… (최대 {max_count:,}개)", fg=typer.colors.CYAN)
    try:
        if no_cache:
            from .loaders.steam import fetch_reviews

            batch = fetch_reviews(appid, max_count=max_count, language=language, review_filter=review_filter)
            from_cache = False
        else:
            batch, from_cache = fetch_reviews_cached(
                appid,
                max_count=max_count,
                language=language,
                review_filter=review_filter,
                cache=ReviewCache(ttl_hours=cache_ttl),
                refresh=refresh,
            )
    except SteamAPIError as exc:
        typer.secho(f"❌ {exc}", fg=typer.colors.RED)
        raise typer.Exit(1)

    if from_cache:
        typer.secho("💾 로컬 캐시에서 불러왔습니다 (--refresh 로 새로 수집).", fg=typer.colors.GREEN)

    if len(batch) == 0:
        typer.secho("수집된 리뷰가 없습니다. 언어/필터 옵션을 바꿔보세요.", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    df = reviews_dataframe(batch)
    stats = analyze_basic(df, query_summary=batch.query_summary)
    keywords = analyze_keywords(df)
    trends = analyze_trends(df, freq=trend_freq)
    stats["keywords"] = keywords
    stats["trends"] = trends
    stats["distributions"] = analyze_distributions(df)
    typer.echo("")
    typer.echo(render_text(stats, game_name=name, appid=appid))

    if charts_dir:
        from .report.charts import ChartsUnavailable, save_charts

        try:
            saved = save_charts(df, out_dir=charts_dir, trends=trends, keywords=keywords, game_name=name)
        except ChartsUnavailable as exc:
            typer.secho(f"⚠️  {exc}", fg=typer.colors.YELLOW)
        else:
            typer.echo("")
            typer.secho(f"📊 차트 {len(saved)}개 저장: {charts_dir}", fg=typer.colors.CYAN)
            for p in saved:
                typer.echo(f"   - {p}")


def main() -> None:  # 콘솔 스크립트 진입점 대체용
    app()


if __name__ == "__main__":
    app()
