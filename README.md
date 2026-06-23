# 🎮 steam-reviewer

> 게임 이름만 넣으면 Steam 리뷰 수천 개를 분석해 **통계 + AI 요약 리포트**를 뽑아주는 도구
>
> *Read 1,000 reviews in 1 second.*

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
```

옵션:
- `--max, -n` 수집할 최대 리뷰 수 (기본 500)
- `--language, -l` 리뷰 언어 (`all`, `english`, `koreana` 등)
- `--filter, -f` 정렬 (`recent` | `updated` | `all`)

## 라이브러리로

```python
from steam_reviewer import resolve_appid, fetch_reviews, reviews_dataframe, analyze_basic

appid, name = resolve_appid("Hades")
batch = fetch_reviews(appid, max_count=500)
df = reviews_dataframe(batch)
stats = analyze_basic(df, query_summary=batch.query_summary)
print(stats["positive_ratio"])
```

## 원칙 / 면책

- **읽기 전용**: Steam 공개 API를 조회만 하며, 리뷰 작성·투표 등 쓰기 동작은 하지 않습니다.
- **레이트리밋 매너**: 요청 간 간격을 두고 수집하며, 결과를 캐시합니다 (v0.2+).
- **개인정보 미저장**: 작성자 식별자(steamid 등)는 분석에 쓰지 않고 저장/재배포하지 않습니다. 집계·요약만 다룹니다.
- **추천이 아님**: 이 도구의 출력은 구매 추천이 아니라 *플레이어 평가 경향의 진단·요약*입니다.

## 로드맵

- [x] v0.1 — 리뷰 수집 + 기본 통계 + 텍스트 리포트
- [ ] v0.2 — 키워드 + 시간 추세 + 차트 + 캐싱
- [ ] v0.3 — AI 측면별 요약 (Gemini)
- [ ] v0.4 — App 상세 + HTML 리포트
- [ ] v1.0 — PyPI 배포

자세한 진행: [TODO.md](TODO.md) · 기획: [docs/기획서.md](docs/기획서.md)

## 라이선스

MIT
