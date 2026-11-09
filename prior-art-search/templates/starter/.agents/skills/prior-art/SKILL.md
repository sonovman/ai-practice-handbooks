---
name: prior-art
description: 선행기술조사를 돕는다. 청구항에서 개념 조사식을 설계하고, DB별 검색식·바로열기 URL을 만들고, 검색 결과를 구성대비해 최근접 선행문헌(신규성 부정/주인용/보조/기준일 이후)을 산정한다. 공식 API는 자동, 웹 DB는 약관상 사람이 실행. 판단과 집계를 분리.
---

# 선행기술조사 (검색식 제안 → 검색 → 최근접 선행문헌 산정)

청구항을 받아 선행기술을 조사하고, 가장 유사하거나 가장 적은 수정으로 도달 가능한 '최근접 선행문헌'을 추린다.
핵심 원칙: **판단(근거와 함께 기록)과 집계(공개된 규칙으로 계산)를 분리**해 재현·검토가 가능하게 한다.

## 전체 흐름(승인 관문)
1. 접수: 청구항·우선일(cutoff)·목적 확인. 빠진 정보는 하나만 질문.
2. 검색식 제안(G1): 특징 분해(F1…Fn, 차별 특징 표시) → 개념 조사식(plan.json) → DB별 검색식. 승인받는다.
3. 검색(G2): 공식 API(KIPRIS Plus·EPO OPS·BigQuery)는 호출량 승인 후 자동. 웹 DB는 링크/식을 사람이 실행.
4. 통합·선별: 패밀리 병합, 적중으로 읽을 순서 결정.
5. 구성대비: 특징별 ●(명시)/◐(일부·상위개념)/○(불개시)을 **근거 위치와 함께** mapping.json에 기록.
6. 산정(G4): 점수·분류(A/B/C/X)·결합 경로 계산. 근거 없이 ●·◐면 산정 중단.
7. 보고: 조사 범위·후보·대비표·결합 경로·한계.
8. 보충 검색: 보완 문헌이 빈 특징만 겨냥해 재검색(최대 2회).

## 자동 vs 사람 실행 (이용약관)
- 자동(공식 API): KIPRIS Plus, EPO OPS(주당 한도·속도 제한), Google BigQuery(처리량 dry run 필수).
- 사람(웹 DB): KIPRIS 웹, Google Patents 웹, Espacenet, PATENTSCOPE. **브라우저 자동화로 반복 조회 금지**(약관 위반).
  스킬은 검색식·바로열기 URL을 만들고, 사람이 열어 결과 CSV를 `imports/`에 저장한다.

## 조사식: 개념 → DB별 변환
- 개념 조사식(plan.json) 하나를 만들어 DB별 문법으로 자동 변환한다(문법 오류↓, 결과 비교 가능).
- `build_queries.py` 가 KIPRIS·Google·Espacenet·PATENTSCOPE 식과 URL, KR 확대선출원용(cutoff 없는) 식을 생성.
- 언어: KIPRIS=한국어, 그 외=영어(미국·영국 철자, 단·복수 모두).

## 날짜 기준(법과 연결)
- 신규성·진보성: 공개일이 cutoff(우선일) '이전'인 문헌만. 각 DB 식에 자동 한정.
- 확대된 선출원(특허법 제29조 제3항)·선출원(제36조): cutoff보다 늦게 공개돼도 해당할 수 있어, cutoff 없는 KR 검색을 따로 돌린다.

## 산정 규칙(요지)
- 점수 = 100 × 관련성 × (1 − 수정부담/총가중치). 분류 A 신규성 부정 / B 주인용 / C 보조 / X 기준일 이후.
- `rank_closest.py` 가 mapping.json을 집계. 저해요인 문헌은 B에서 제외, 근거 없으면 중단.

## 도구
- `tools/build_queries.py` — 개념 조사식 → DB별 검색식·URL. (Google 여러 단어 표현은 따옴표, KIPRIS ta는 TL+AB로 요약까지 포함)
- `tools/rank_closest.py` — 구성대비(mapping.json) → 최근접 선행문헌 산정.
- `tools/kipris_bridge.py` — (선택·로컬 전용) 위 KIPRIS 식을 10편 `kipris_client.py`로 실제 호출해 CSV 저장.
  10편 `kipris_client.py`·`fixtures/`를 `tools/`에 복사해야 쓸 수 있습니다(웹 채팅 앱은 외부 API 차단).

## 참조
- `references/db-syntax.md` — DB별 문법 대응표
- `references/selection-criteria.md` — 최근접 선행기술 판단 기준(EPO·한국 심사기준 연계)
- `references/platform-setup.md` — Claude·ChatGPT·Copilot·Gemini별 스킬 등록·프로젝트 설정, 사건 폴더 표준
- `references/kipris-bridge.md` — 10편 KIPRIS Plus 클라이언트 연동(로컬), 입력값 이름·첫 사용 확인
- `references/platforms.md` — 도구별 활용 요약·약관 주의
