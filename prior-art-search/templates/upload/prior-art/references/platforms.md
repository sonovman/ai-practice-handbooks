# 도구별 활용 (선택)

조사식 설계·구성대비 같은 '판단 보조'는 어느 AI에서도 되지만, 실제 검색·전문 확보는 각 DB 약관을 따른다.

| 단계 | Claude | ChatGPT | Gemini | Microsoft 365 Copilot |
|---|---|---|---|---|
| 개념 조사식(plan.json) 작성 | concept-plan 프롬프트 | 동일 프롬프트 | 동일 프롬프트 | 동일 프롬프트 |
| DB별 식 변환 | build_queries.py | 스크립트 실행 | 스크립트 실행 | 스크립트 실행 |
| 구성대비 판단 | 근거와 함께 mapping.json | 동일 | 동일 | 동일 |
| 산정·보고 | rank_closest.py | 스크립트 실행 | 스크립트 실행 | 스크립트 실행 |

## Google Antigravity로 구축(선택)
- Antigravity(핸드북 16편)에 "plan.json 스키마와 build_queries·rank_closest 스크립트, examples를 갖춘
  사건 폴더 구조를 만들어 줘"처럼 뼈대 작성을 맡기고, 실제 조사·판단은 변리사가 한다.

## 주의(공통)
- 웹 DB(Google·Espacenet·PATENTSCOPE·KIPRIS 웹)는 **브라우저 자동화로 반복 조회 금지**(약관). 사람이 실행.
- 공식 API만 자동(KIPRIS Plus·OPS·BigQuery). 개인이 운영하는 불명의 중계 서버로 데이터를 보내지 않는다.
- 최종 판단(신규성·진보성·FTO)은 변리사가 한다. AI 결과는 1차 초안이다.
