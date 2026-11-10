---
name: claim-suite
description: 청구항 분석 통합 오케스트레이터. 사건 목적(침해·무효·FTO·회피·해석)에 맞춰 claim-decompose·claim-construe·claim-chart·design-around를 순서대로 불러 쓰고, 사건 폴더·관문(G1~G5)을 관리.
---

# 청구항 분석 통합 오케스트레이터 (claim-suite)

네 스킬을 **한 사건 폴더, 같은 한정 원장 ID**로 이어 쓰게 하는 지휘 스킬이다. 직접 분석하지 않고, 단계마다 맞는 스킬을 불러 그 산출물을 다음 단계에 넘긴다.

| 스킬 | 맡는 일 | 산출(사건 폴더) |
|---|---|---|
| claim-decompose | 청구항 → 원자적 한정 명제 → 한정 원장 | `work/01_ledger.json` |
| claim-chart | 원장 위 Claim Chart(침해·비침해·신규성·진보성) | `work/02_chart.json` |
| claim-construe | 다툼 용어 해석, 원장 반영 | `work/03_construction.json`, `work/04_chart_construed.json` |
| design-around | 모든 독립항 대상 회피안 평가 | `work/05_design_input.json` |

## 0. 시작할 때 (항상)
1. 사건 폴더가 없으면 만든다: `case.json`, `inbox/`, `work/`, `out/`. (`cases/example` 참조)
2. `case.json`의 **purpose**를 확인한다 — infringement / invalidity / fto / design-around / construction. 모르면 하나만 묻는다.
3. 관할(forum: us / kr / us+kr), 특허·청구항, 우선일, 대상(제품명·버전 또는 선행문헌)을 채운다.
4. `python tools/suite_status.py <사건폴더>`로 현재 단계와 다음 할 일을 확인하고 그대로 따른다.

## 1. 목적별 순서
- **침해**: decompose → chart(초안) → construe → 반영·재점검 → 보고
- **무효**: decompose → construe(절차별 기준) → chart(신규성·진보성) → 반영·재점검 → 보고
- **FTO·회피설계**: decompose → chart(자사 제품) → construe → 반영·재점검 → design-around → 보고
- **해석만**: decompose → construe → 보고
상세 라우팅과 '되돌아가기' 규칙: `references/routing.md`.

## 2. 관문 (통과 전에는 다음 단계로 가지 않는다)
- **G1 원장 확정**: 사람이 3대 시험(삭제·대응·전체성)으로 원장을 확인 → `case.json`에 `"ledger_approved": true`.
- **G2 해석 점검**: `construe_check.py` 오류 0.
- **G3 차트 점검**: `chart_lint.py` 오류 0 **그리고** 해석 반영 뒤 '재검토' 행 0.
- **G4 회피**: 모든 독립항이 LOW인 회피안(결합안 포함) — FTO·회피 목적일 때.
- **G5 사람 최종 검토**: 변리사·변호사 검토 → `"human_signoff": true`, `out/`에 최종 보고.
`python tools/suite_status.py <사건폴더> --run`이 G2~G4 점검을 실제로 돌리고 `work/reports/`에 결과를 쓴다.

## 3. 넘겨주기 규칙 (스킬 사이 계약)
- 한정 ID는 원장에서 한 번 정하면 모든 파일에서 그대로 쓴다.
- 해석 문장은 03 → 04 → 05로 **글자 그대로** 복사한다(design_around_eval이 다르면 E10).
- 해석이 바뀌면 04를 지우고 다시 만든다(apply_to_ledger) → 차트를 다시 점검 → 회피안을 다시 평가.
- 넓힌 해석은 침해·무효·회피 모두에 같은 넓이로(대칭성).
상세: `references/handoffs.md`.

## 4. 늘 지킬 것
- 한국어, 초보자도 따라 하기 쉽게. 미국 실무 기준 + 한국 대응(각 스킬의 references).
- 결론부터 내지 않는다. 근거 위치 없는 판단은 쓰지 않는다.
- 의뢰인·상대방·개발 자료는 승인된 환경에서만. 개인 운영 중계 서버 경유 금지.
- 도구 결과·위험 등급은 법적 결론이 아니다. 최종 판단은 변리사·변호사.

## 5. 보고 (out/report.md)
사건 개요 → 원장 요약 → 해석표 → 차트(3열) → (FTO면) 회피안 비교표 → 남은 위험·확인하지 못한 것 → 사람 검토 기록.

## 참조
- `references/routing.md` — 목적별 단계·되돌아가기·스킬 호출 문구
- `references/handoffs.md` — 파일 형식 계약과 점검 도구 대응
- `references/platform-setup.md` — Claude·ChatGPT·Gemini·M365 Copilot 프로젝트 설정, Antigravity 구축
