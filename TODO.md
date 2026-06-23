# 🎮 steam-reviewer — 전체 작업 목록 (Loop 진행용)

> **Loop 규칙**: 위에서부터 미완료(`[ ]`) 항목을 하나 집어 완료하고 `[x]`로 체크한다.
> 한 항목 = 한 루프에서 끝낼 수 있는 단위. 완료 시 무엇을 했는지 짧게 기록.
> 막히면 그 항목에 `⚠️ 메모`를 남기고 다음으로 넘어가지 말고 사용자에게 보고.
> **되돌릴 수 없는 외부 공개(PyPI 배포·git push·릴리스 태그)는 실행 직전 사용자 확인.**

기획서: [docs/기획서.md](docs/기획서.md)

---

## 🟢 v0.1 — 골격 + 리뷰 수집 + 기본 통계 (캐싱 기본 / AI ❌)
> 목표: `steam-reviewer analyze "Hades"` → 긍부정·플레이타임 통계가 텍스트로 출력

### 안전 바닥
- [x] `.gitignore` 생성 (`.env`, `__pycache__/`, `.cache/`, 빌드 산출물)
- [x] `.env.example` 생성 (`GEMINI_API_KEY=` 양식만, v0.3용)

### 패키지 골격
- [x] `pyproject.toml` (배포명 `steam-reviewer`, import `steam_reviewer`, deps: requests/typer/pandas, hatchling)
- [x] `steam_reviewer/__init__.py` + 버전(0.1.0) + 공개 API export
- [x] 폴더 골격 (`loaders/`, `analyzers/`, `ai/`, `report/`)

### 리뷰 수집 (Loaders)
- [x] `loaders/steam.py` — `resolve_appid(name)` (store search API, 키 불필요, 숫자면 App ID 바로 사용)
- [x] `loaders/steam.py` — `fetch_reviews(appid, max_count, language, filter)` 커서 페이지네이션 (커서 중복 시 종료)
- [x] `loaders/steam.py` — `reviews_dataframe()` 표준 변환 (작성자 steamid 제외, playtime만 추출)
- [x] 레이트리밋 매너 (요청 간 `delay`) + 에러/빈결과 처리 (`SteamAPIError`)

### 기본 분석 (Analyzers)
- [x] `analyzers/basic.py` — 긍/부정 비율, 리뷰 수, 언어 분포
- [x] `analyzers/basic.py` — 평균/중앙 플레이타임, 추천자 vs 비추천자 비교
- [x] `analyzers/basic.py` — 도움됨(votes_up) 상위 리뷰 식별 + Steam 전체 요약 패스스루

### 출력 + 마무리
- [x] `report/text.py` — 분석 결과를 보기 좋은 텍스트로 (면책 문구 포함)
- [x] `cli.py` — `steam-reviewer analyze <이름|appid>` → 텍스트 리포트
  - ⚠️ 메모: ① 단일 명령이면 typer가 서브커맨드명을 생략시켜 `@app.callback()`로 그룹 고정. ② Windows cp949 콘솔이 이모지 출력 시 크래시 → CLI 시작 시 stdout/stderr `reconfigure(utf-8, errors=replace)`.
- [x] `tests/test_basic.py` — 분석 핵심 동작 8개 (수집은 mock)
- [x] `README.md` 초안 (소개/설치/사용/면책·매너 문구)
- [x] `LICENSE` (MIT)
- [x] **git init + 첫 커밋** (`.env` 미포함 확인) — 커밋 `85c0d71`
- [x] **v0.1 동작 확인**: `steam-reviewer analyze "Hades" -n 60` 실데이터 수집→통계 출력 검증 완료 (Hades II, 긍정 92%)

---

## 🟡 v0.2 — 키워드 + 시간 추세 + 차트 + 캐싱 (AI ❌)
> 목표: "왜 좋아하고 싫어하는지" 키워드와 추세로 드러내기

### 캐싱
- [x] `cache.py` — 수집한 리뷰 로컬 JSON 캐시 (재실행 시 재요청 안 함). `ReviewCache`(appid·언어·필터·구매유형·개수 조합별 키) + `fetch_reviews_cached`. **개인정보 비저장**: `sanitize_review`로 steamid 등 작성자 식별자 제거 후 안전 필드만 저장(상시 원칙 #2).
- [x] 캐시 만료/강제갱신(`--refresh`) 옵션 — `cached_at` 기반 TTL(기본 24h, 0이면 무제한), CLI `--refresh`/`--no-cache`/`--cache-ttl`. `tests/test_cache.py` 7개 통과.

### 분석 심화
- [x] `analyzers/keywords.py` — 긍/부정 리뷰별 빈출 키워드 (라틴 토큰·불용어 제거, `analyze_keywords`). 비라틴 스크립트는 `-l english` 권장.
- [x] `analyzers/trends.py` — 작성일별 리뷰 수·긍정 비율 추세 (`analyze_trends`, day/week/month 리샘플 + first/last/direction).
- [x] 리뷰 길이/도움됨 분포 통계 — `analyzers/distributions.py` (`analyze_distributions`, 길이 평균/중앙/최소/최대 + votes_up 구간 버킷).

### 차트
- [x] `report/charts.py` — 감성 추세 라인 + 긍/부정 키워드 막대 + 플레이타임 분포 (matplotlib 선택 의존성, Agg 백엔드, 라벨은 폰트 안전하게 영어).
- [x] 차트 PNG 저장 + CLI `--charts DIR` (+ `--trend` 단위 옵션). matplotlib 없으면 `ChartsUnavailable` 안내 후 코어는 정상.

### 마무리
- [x] `tests/test_keywords.py`, `tests/test_trends.py` (+ `test_distributions.py`, `test_charts.py`). 전체 30개 통과.
- [x] README에 분석 예시·차트·옵션 추가.
- [x] **v0.2 동작 확인**: `analyze "Hades" -n 80 -l english --charts …` 실데이터로 키워드/추세/분포/캐시 적중/PNG 3종 생성 검증. 버전 0.2.0.

---

## 🟠 v0.3 — AI 측면별 요약 (AI ✅)
> 목표: 수천 리뷰 → 측면별 칭찬·불만 자연어 요약

- [ ] `google-genai` 선택 의존성(`[ai]`) + `.env` `GEMINI_API_KEY`
- [ ] `ai/summarize.py` — 리뷰 샘플링·집계 → 프롬프트 구성 (토큰 한도 고려)
- [ ] `ai/summarize.py` — 측면별(게임성/성능/스토리/가격/조작) 칭찬·불만 요약
- [ ] 프롬프트 가드레일: "추천 금지, 리뷰 근거 기반 요약만"
- [ ] 키 없으면 통계만 (fallback), 기본값 = AI 끔
- [ ] `cli.py --ai` 옵션
- [ ] `tests/test_ai.py` (mock)
- [ ] README에 AI 요약 예시
- [ ] **v0.3 동작 확인** (키 없는 fallback 포함)

---

## 🔵 v0.4 — App 상세 + HTML 리포트 (AI ✅)
> 목표: 헤더 이미지·장르 포함 완성형 리포트

- [ ] `loaders/steam.py` — `fetch_appdetails(appid)` (게임명/장르/헤더이미지/가격)
- [ ] `report/html.py` — 헤더 이미지 + 통계 + 차트 + AI 요약을 HTML 한 장으로
- [ ] HTML 템플릿 디자인 (Steam 다크 테마)
- [ ] `--html` CLI 옵션
- [ ] 차트 인라인 임베드(자기완결 HTML)
- [ ] `tests/test_html.py`
- [ ] README에 HTML 리포트 예시
- [ ] **v0.4 동작 확인**

---

## 🟣 v1.0 — 배포 + 브랜딩
> 목표: `pip install steam-reviewer`

- [ ] PyPI에 `steam-reviewer` 이름 사용 가능 여부 확인 (불가 시 대체명)
- [ ] 패키지 메타데이터 (분류자/키워드/URL)
- [ ] 로고/브랜딩 + 태그라인
- [ ] README 완성 (배지, 데모, 면책·매너)
- [ ] `CONTRIBUTING.md` + 이슈/PR 템플릿
- [ ] GitHub Actions CI (pytest 매트릭스)
- [ ] 🛑 TestPyPI 업로드 (사용자 확인 후)
- [ ] 🛑 **PyPI 정식 배포** (사용자 확인 후)
- [ ] 🛑 GitHub 릴리스 v1.0 태그 (사용자 확인 후)

> 🛑 **STOP — 루프 정지선**: v1.0의 외부 공개 항목(🛑)은 자동 진행하지 않고 사용자 확인을 받는다.

---

## 📌 상시 원칙 (매 작업 점검)
1. Steam API는 **읽기만** + 레이트리밋 준수·캐싱
2. 작성자 개인정보 저장·재배포 금지 (집계·요약만)
3. "추천" 아니라 "진단·요약"
4. `loaders`/`analyzers`는 AI 없이도 동작
5. 키는 `.env`에만 — 커밋 전 `git status` 확인
