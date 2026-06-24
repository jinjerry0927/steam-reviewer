"""AI 요약 테스트 — 실제 API 호출 없이 generate 주입·환경변수 mock으로 검증."""

import pytest

from steam_reviewer.ai.summarize import (
    AISummaryUnavailable,
    ASPECTS,
    build_prompt,
    resolve_api_key,
    summarize_reviews,
)
from steam_reviewer.loaders.steam import reviews_dataframe


def _reviews():
    return [
        {"review": "Combat is amazing and the story is great.", "voted_up": True, "votes_up": 40,
         "language": "english", "timestamp_created": 1_700_000_000, "author": {}},
        {"review": "Fun gameplay, smooth performance.", "voted_up": True, "votes_up": 10,
         "language": "english", "timestamp_created": 1_700_100_000, "author": {}},
        {"review": "Crashes constantly, terrible performance and bad controls.", "voted_up": False, "votes_up": 25,
         "language": "english", "timestamp_created": 1_700_200_000, "author": {}},
    ]


def test_build_prompt_has_guardrails():
    prompt = build_prompt("Test Game", ["good combat"], ["crashes a lot"])
    assert "Test Game" in prompt
    assert "추천" in prompt  # 추천 금지 규칙 포함
    for aspect in ASPECTS:
        assert aspect in prompt
    assert "good combat" in prompt
    assert "crashes a lot" in prompt


def test_summarize_uses_injected_generate():
    df = reviews_dataframe(_reviews())
    captured = {}

    def fake_generate(prompt, *, model, api_key):
        captured["prompt"] = prompt
        captured["model"] = model
        return "■ 게임성\n  칭찬: 전투 호평\n  불만: 없음\n총평: 대체로 긍정"

    result = summarize_reviews(df, game_name="Test Game", model="gemini-x", generate=fake_generate)
    assert result["model"] == "gemini-x"
    assert "총평" in result["summary"]
    assert result["sample_size"]["positive"] == 2
    assert result["sample_size"]["negative"] == 1
    assert "Test Game" in captured["prompt"]


def test_summarize_no_key_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # 실제 .env가 키를 주입하지 못하도록 load_dotenv를 무력화(환경 독립).
    import dotenv

    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    df = reviews_dataframe(_reviews())
    with pytest.raises(AISummaryUnavailable):
        summarize_reviews(df, game_name="Test Game")  # generate 미주입 + 키 없음


def test_summarize_empty_reviews_raises():
    import pandas as pd

    def fake_generate(prompt, *, model, api_key):
        return "should not be called"

    with pytest.raises(AISummaryUnavailable):
        summarize_reviews(pd.DataFrame(), game_name="X", generate=fake_generate)


def test_resolve_api_key_explicit_wins(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "from_env")
    assert resolve_api_key("explicit_key") == "explicit_key"


def test_resolve_api_key_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env_key_123")
    assert resolve_api_key() == "env_key_123"


def test_sample_size_capped():
    # max_reviews 한도가 표본 수를 제한하는지
    many = []
    for i in range(50):
        many.append({"review": f"good {i}", "voted_up": True, "votes_up": i,
                     "language": "english", "timestamp_created": 1_700_000_000 + i, "author": {}})
    df = reviews_dataframe(many)

    def fake_generate(prompt, *, model, api_key):
        return "ok"

    result = summarize_reviews(df, game_name="X", max_reviews=10, generate=fake_generate)
    assert result["sample_size"]["positive"] <= 5  # half of 10
