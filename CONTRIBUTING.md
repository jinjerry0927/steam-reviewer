# 기여 가이드 (Contributing)

steam-reviewer에 관심 가져주셔서 고맙습니다! 작은 수정부터 새 분석 기능까지 환영합니다.

## 개발 환경

```bash
git clone https://github.com/jinjerry0927/steam-reviewer.git
cd steam-reviewer
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[charts,ai,dev]"
pytest -q
```

- Python 3.10+ 필요.
- `charts`(matplotlib), `ai`(google-genai) 는 **선택 의존성**입니다. 코어(`loaders`/`analyzers`)는 이들 없이도 동작해야 합니다.

## 원칙 (꼭 지켜주세요)

1. **Steam API는 읽기 전용** — 리뷰 작성·투표 등 쓰기 동작 금지. 레이트리밋 매너(요청 간 간격) 유지.
2. **작성자 개인정보 비저장** — `steamid` 등 식별자는 분석·저장·재배포하지 않습니다. 집계·요약만.
3. **"추천"이 아니라 "진단·요약"** — 출력에 구매 추천/비추천 표현을 넣지 않습니다(AI 프롬프트 가드레일 포함).
4. **선택 의존성은 지연 임포트** — `import` 시점이 아니라 사용 시점에 로드하고, 없으면 친절한 안내로 폴백.

## 변경 절차

1. 이슈로 먼저 논의(특히 큰 변경).
2. 브랜치 생성 → 작은 단위 커밋.
3. **테스트 추가/갱신** — 네트워크 없이 동작하도록 mock 사용(기존 `tests/` 패턴 참고).
4. `pytest -q` 로컬 통과 확인.
5. PR 생성 — 무엇을/왜 바꿨는지 설명. CI(파이썬 매트릭스)가 초록이어야 머지됩니다.

## 코드 스타일

- 표준 라이브러리 우선, 의존성 추가는 신중히.
- 함수/모듈에 짧은 한국어 docstring (기존 코드 톤에 맞춤).
- 공개 API 변경 시 `steam_reviewer/__init__.py` 의 export 와 README 갱신.

감사합니다 🎮
