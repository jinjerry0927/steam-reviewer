"""측면별 칭찬·불만 AI 요약 (Gemini) — **선택 의존성** `[ai]`.

키가 없거나 `google-genai`가 없으면 동작하지 않으며(코어는 통계만으로 정상),
**기본값은 AI 끔**이다. 프롬프트는 "구매 추천 금지, 제공된 리뷰 근거 기반
측면별 요약만"을 가드레일로 강제한다.

개인정보: 작성자 식별자는 애초에 DataFrame에 없으며(steamid 제외), 프롬프트에는
리뷰 본문 표본만 들어간다.
"""

from __future__ import annotations

import os
from typing import Any, Callable

DEFAULT_MODEL = "gemini-2.0-flash"

# 요약 대상 측면(한국어 라벨). 프롬프트와 출력 스키마에 사용.
ASPECTS = ["게임성", "성능", "스토리", "가격", "조작"]

# 토큰 한도 보호용 기본값 — 표본 수와 리뷰당 글자 수 상한.
_MAX_REVIEWS = 120
_MAX_REVIEW_CHARS = 600


class AISummaryUnavailable(RuntimeError):
    """API 키 없음·라이브러리 없음 등으로 AI 요약을 실행할 수 없음."""


def resolve_api_key(explicit: str | None = None) -> str | None:
    """명시 인자 → 환경변수(`GEMINI_API_KEY`) 순으로 키를 찾는다.

    `.env`가 있으면 python-dotenv로 로드를 시도한다(있을 때만).
    """
    if explicit:
        return explicit
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    key = os.environ.get("GEMINI_API_KEY")
    return key or None


def _sample_reviews(df, *, max_reviews: int, max_chars: int) -> tuple[list[str], list[str]]:
    """도움됨(votes_up) 순으로 긍/부정 리뷰 본문을 균형 있게 표본 추출한다."""
    if df is None or df.empty or "review" not in df or "voted_up" not in df:
        return [], []

    work = df.copy()
    if "votes_up" in work:
        work = work.sort_values("votes_up", ascending=False)

    half = max(1, max_reviews // 2)

    def _pick(voted: bool) -> list[str]:
        rows = work[work["voted_up"] == voted]["review"].dropna()
        out: list[str] = []
        for text in rows:
            text = " ".join(str(text).split())
            if not text:
                continue
            out.append(text[:max_chars])
            if len(out) >= half:
                break
        return out

    return _pick(True), _pick(False)


def build_prompt(game_name: str, positive: list[str], negative: list[str]) -> str:
    """가드레일이 포함된 요약 프롬프트를 구성한다."""
    aspects = " / ".join(ASPECTS)
    pos_block = "\n".join(f"- {r}" for r in positive) or "(긍정 리뷰 표본 없음)"
    neg_block = "\n".join(f"- {r}" for r in negative) or "(부정 리뷰 표본 없음)"
    return f"""당신은 게임 리뷰 분석가입니다. 아래는 '{game_name}'의 Steam 리뷰 표본입니다.

[규칙]
- 구매를 추천/비추천하지 마세요. "사세요", "사지 마세요" 같은 표현 금지.
- 아래 제공된 리뷰에 실제로 나타난 내용만 근거로 요약하세요. 추측·창작 금지.
- 측면({aspects})별로 플레이어들의 칭찬과 불만을 각각 1~3개 짧은 한국어 항목으로 정리하세요.
- 표본에 근거가 없는 측면은 "언급 적음"으로 표시하세요.
- 마지막에 한 문장으로 전반적 평가 경향을 중립적으로 요약하세요(추천 아님).

[긍정 리뷰 표본]
{pos_block}

[부정 리뷰 표본]
{neg_block}

[출력 형식]
측면별로 다음처럼:
■ <측면>
  칭찬: ...
  불만: ...
(마지막) 총평: ...
"""


def _default_generate(prompt: str, *, model: str, api_key: str) -> str:
    """google-genai로 실제 호출. 라이브러리 없으면 AISummaryUnavailable."""
    try:
        from google import genai
    except ImportError as exc:  # pragma: no cover - 환경 의존
        raise AISummaryUnavailable(
            "AI 요약에는 google-genai가 필요합니다. `pip install steam-reviewer[ai]` 로 설치하세요."
        ) from exc

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(model=model, contents=prompt)
    text = getattr(resp, "text", None)
    if not text:
        raise AISummaryUnavailable("Gemini 응답이 비어 있습니다.")
    return text.strip()


def summarize_reviews(
    df,
    *,
    game_name: str,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    max_reviews: int = _MAX_REVIEWS,
    max_review_chars: int = _MAX_REVIEW_CHARS,
    generate: Callable[..., str] | None = None,
) -> dict[str, Any]:
    """측면별 칭찬·불만을 AI로 요약한다.

    Args:
        df: reviews_dataframe() 결과.
        game_name: 게임명(프롬프트 표기용).
        api_key: 명시 키. None이면 resolve_api_key()로 탐색.
        generate: 테스트/주입용 생성 함수. None이면 google-genai 사용.

    Returns:
        {"game_name","model","summary","sample_size":{"positive","negative"}}.

    Raises:
        AISummaryUnavailable: 키 없음·라이브러리 없음·빈 응답 등.
    """
    gen = generate or _default_generate
    key = api_key if generate is not None else resolve_api_key(api_key)
    if generate is None and not key:
        raise AISummaryUnavailable(
            "GEMINI_API_KEY가 없습니다. .env에 설정하거나 --ai 없이 통계만 사용하세요."
        )

    positive, negative = _sample_reviews(df, max_reviews=max_reviews, max_chars=max_review_chars)
    if not positive and not negative:
        raise AISummaryUnavailable("요약할 리뷰 본문이 없습니다.")

    prompt = build_prompt(game_name, positive, negative)
    summary = gen(prompt, model=model, api_key=key or "")
    return {
        "game_name": game_name,
        "model": model,
        "summary": summary,
        "sample_size": {"positive": len(positive), "negative": len(negative)},
    }
