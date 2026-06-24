<p align="center">
  <img src="https://raw.githubusercontent.com/jinjerry0927/steam-reviewer/main/docs/images/logo.png" width="320" alt="steam-reviewer logo">
</p>

# 🎮 steam-reviewer

[![CI](https://github.com/jinjerry0927/steam-reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/jinjerry0927/steam-reviewer/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/steam-reviewer.svg)](https://pypi.org/project/steam-reviewer/)
[![Python](https://img.shields.io/pypi/pyversions/steam-reviewer.svg)](https://pypi.org/project/steam-reviewer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 게임 이름만 넣으면 Steam 리뷰 수천 개를 분석해 **통계 + AI 요약 리포트**를 뽑아주는 도구
>
> *Read 1,000 reviews in 1 second.* · 별점 너머의 진짜 이유를 봅니다.

별점·추천%만으로는 "왜" 좋아하고 싫어하는지 알 수 없습니다. `steam-reviewer`는 공개 Steam 리뷰를 대량 수집해 긍/부정 경향, 플레이타임, 키워드, 시간 추세를 분석하고, (선택적으로) AI가 측면별 칭찬·불만을 요약합니다.

## 설치

```bash
pip install steam-reviewer            # 핵심 기능
pip install "steam-reviewer[ai]"      # AI 요약 포함 (v0.3+)
pip install "steam-reviewer[charts]"  # 차트 (v0.2+)
```

## 사용법

```bash
steam-reviewer analyze "Hades"            # 이름으로
steam-reviewer analyze 1145360            # App ID로
steam-reviewer analyze "Elden Ring" -n 1000 -l english
steam-reviewer analyze "Hades" -l english --charts ./charts   # 차트 PNG까지
steam-reviewer analyze "Hades" -l english --ai               # AI 측면별 요약 (키 필요)
steam-reviewer analyze "Hades" -l english --html report.html # 자기완결 HTML 리포트
```

옵션:
- `--max, -n` 수집할 최대 리뷰 수 (기본 500)
- `--language, -l` 리뷰 언어 (`all`, `english`, `koreana` 등)
- `--filter, -f` 정렬 (`recent` | `updated` | `all`)
- `--trend` 감성 추세 단위 (`day` | `week` | `month`, 기본 `week`)
- `--charts DIR` 추세·키워드·플레이타임 차트 PNG를 `DIR`에 저장 (matplotlib 필요)
- `--ai` 측면별(게임성/성능/스토리/가격/조작) 칭찬·불만 AI 요약 (`--ai-model` 로 모델 지정)
- `--html FILE` 헤더 이미지·통계·차트·AI 요약을 한 장의 자기완결 HTML로 저장 (차트는 인라인 임베드)
- `--refresh` 캐시를 무시하고 새로 수집 / `--no-cache` 캐시 미사용 / `--cache-ttl H` 캐시 유효시간(시간)

### HTML 리포트 (v0.4+)

`--html report.html` 은 게임 헤더 이미지·장르·가격(App 상세 API)과 통계·차트·AI 요약을 **한 장의 HTML**로 묶습니다. 차트는 base64로 인라인 임베드되어 파일 하나만 열면 되고(외부 의존 없음), Steam 다크 테마로 표시됩니다. `--ai`/`--charts` 와 함께 쓰면 그 결과도 포함됩니다.

### AI 요약 (선택, v0.3+)

`--ai` 는 측면별 칭찬·불만을 Gemini로 요약합니다. **기본은 꺼져 있고**, 키가 없으면 통계만 출력합니다(요약은 건너뜀).

```bash
pip install "steam-reviewer[ai]"
echo "GEMINI_API_KEY=발급받은_키" > .env     # 또는 환경변수로 export
steam-reviewer analyze "Hades" -l english --ai
```

> AI 요약은 "구매 추천 금지, 제공된 리뷰 근거 기반 요약만" 가드레일 아래 동작하며, 출력은 추천이 아니라 평가 경향 진단입니다. 키는 `.env`(깃 제외)에만 둡니다.

### 출력 예시 (`analyze "Hades" -l english`)

```text
🎮 Hades II (App 1145350) — 리뷰 분석
================================================
표본 리뷰 80개 · 긍정 94%  (👍 75 / 👎 5)
전체(Steam): Overwhelmingly Positive · 리뷰 68,273개 (👍 66,087 / 👎 2,186)

⏱️  평균 플레이타임 89.4h · 중앙값 69.3h
   추천자 86.7h vs 비추천자 61.3h  → 추천자가 1.4배 더 오래 플레이

📝 리뷰 길이(문자): 평균 281.2 · 중앙값 82 (최소 2 / 최대 6450)
👍 도움됨(votes_up) 분포: 0:74, 1-4:6, 5-19:0, 20-99:0, 100+:0

🔑 빈출 키워드 (라틴 문자 기준)
  👍 hades(58), good(27), great(25), story(23), fun(16), gameplay(11)
  👎 attack(4), weapons(3), boss(3), runs(3), story(3)

📅 감성 추세(W): 2026-06-21 긍정 95% → 2026-06-28 긍정 92%  ➡️ 보합
```

> 키워드 분석은 라틴 문자 토큰 기준이라 `-l english` 처럼 단일 언어 표본에서 가장 의미 있습니다.
> `--charts` 는 `trend.png`(감성 추세), `keywords.png`(긍/부정 키워드 막대), `playtime.png`(플레이타임 분포)를 생성합니다.

## 라이브러리로

```python
from steam_reviewer import (
    resolve_appid, fetch_reviews_cached, reviews_dataframe,
    analyze_basic, analyze_keywords, analyze_trends,
)

appid, name = resolve_appid("Hades")
batch, from_cache = fetch_reviews_cached(appid, max_count=500, language="english")
df = reviews_dataframe(batch)

stats = analyze_basic(df, query_summary=batch.query_summary)
print(stats["positive_ratio"])
print(analyze_keywords(df)["negative"][:5])   # 불만 키워드 상위 5
print(analyze_trends(df, freq="week")["direction"])  # up | down | flat
```

## 원칙 / 면책

- **읽기 전용**: Steam 공개 API를 조회만 하며, 리뷰 작성·투표 등 쓰기 동작은 하지 않습니다.
- **레이트리밋 매너**: 요청 간 간격을 두고 수집하며, 결과를 캐시합니다 (v0.2+).
- **개인정보 미저장**: 작성자 식별자(steamid 등)는 분석에 쓰지 않고 저장/재배포하지 않습니다. 집계·요약만 다룹니다.
- **추천이 아님**: 이 도구의 출력은 구매 추천이 아니라 *플레이어 평가 경향의 진단·요약*입니다.

## 로드맵

- [x] v0.1 — 리뷰 수집 + 기본 통계 + 텍스트 리포트
- [x] v0.2 — 키워드 + 시간 추세 + 분포 + 차트 + 캐싱
- [x] v0.3 — AI 측면별 요약 (Gemini, 키 없으면 통계만)
- [x] v0.4 — App 상세 + 자기완결 HTML 리포트 (차트 인라인)
- [ ] v1.0 — PyPI 배포

자세한 진행: [TODO.md](TODO.md) · 기획: [docs/기획서.md](docs/기획서.md)

## 라이선스

MIT
