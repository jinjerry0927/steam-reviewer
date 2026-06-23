"""긍/부정 리뷰별 빈출 키워드 추출 — AI 없이 순수 파이썬으로 동작한다.

라틴 문자(영어 등) 토큰을 소문자화·불용어 제거 후 빈도 집계한다.
한국어·일본어 등 비라틴 스크립트는 토큰 경계가 달라 신뢰도가 낮으므로,
키워드 분석은 `-l english` 처럼 단일 언어 표본에서 가장 의미 있다.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

# 라틴 단어 토큰: 알파벳(+내부 아포스트로피). 숫자/기호 제외.
_TOKEN_RE = re.compile(r"[a-z]+(?:'[a-z]+)?")

# 영어 불용어 + 리뷰에서 정보량 낮은 도메인 단어.
_STOPWORDS: frozenset[str] = frozenset(
    """
    a an the this that these those and or but if then so as of to in on at by for from with without
    is are was were be been being am do does did doing have has had having will would can could should
    i you he she it we they me him her us them my your his its our their mine yours not no nor too very
    just only also even still much many more most some any all both each few other such own same than
    about into over under again once here there when where why how what which who whom whose
    s t re ve ll d m o re up out off down out
    game games play played playing player players steam review reviews really get got like one time
    """.split()
)


def analyze_keywords(
    df,
    *,
    top_n: int = 15,
    min_length: int = 3,
    extra_stopwords: set[str] | None = None,
) -> dict[str, Any]:
    """긍/부정 리뷰별 빈출 키워드를 집계한다.

    Args:
        df: reviews_dataframe() 결과 (review, voted_up 컬럼 사용).
        top_n: 각 그룹에서 반환할 키워드 수.
        min_length: 최소 토큰 길이(짧은 단어 잡음 제거).
        extra_stopwords: 추가로 제외할 단어.

    Returns:
        {"positive": [{"word", "count"}...], "negative": [...]} 형태.
        리뷰 텍스트가 없으면 {"empty": True}.
    """
    if df is None or df.empty or "review" not in df or "voted_up" not in df:
        return {"empty": True, "positive": [], "negative": []}

    stop = set(_STOPWORDS)
    if extra_stopwords:
        stop |= {w.lower() for w in extra_stopwords}

    def _count(texts) -> Counter:
        counter: Counter = Counter()
        for text in texts:
            if not isinstance(text, str):
                continue
            for tok in _TOKEN_RE.findall(text.lower()):
                if len(tok) >= min_length and tok not in stop:
                    counter[tok] += 1
        return counter

    voted = df["voted_up"]
    pos_counter = _count(df[voted == True]["review"])  # noqa: E712
    neg_counter = _count(df[voted == False]["review"])  # noqa: E712

    def _top(counter: Counter) -> list[dict[str, Any]]:
        return [{"word": w, "count": c} for w, c in counter.most_common(top_n)]

    return {
        "positive": _top(pos_counter),
        "negative": _top(neg_counter),
    }
