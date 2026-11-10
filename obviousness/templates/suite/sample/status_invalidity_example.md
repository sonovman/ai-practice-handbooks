# 사건 상태 — 가상 착즙기 특허 A — 무효심판 진보성 공격(교육용 예시)

- 목적: invalidity · 관할: us+kr · 특허: 가상특허 A · 대상: D1~D4 선행문헌(가상)

## 단계
| 단계 | 스킬 | 할 일 | 파일 | 상태 |
|---|---|---|---|---|
| S1 | claim-decompose | 청구항 분해 → 한정 원장 | `work/01_ledger.json` | 있음 |
| S3 | claim-construe | 해석(절차별 기준) — 무효 차트 전에 | `work/03_construction.json` | 있음 |
| S6 | obviousness | A/B/C 분류 → 차이점×기준일 기술상식 → 결합 논리 | `work/06_obviousness.json` | 있음 |
| S2 | claim-chart | 신규성·진보성 차트(--run이 06의 결합에서 생성) | `work/02_chart.json` | 있음 |
| S4 | claim-construe | 해석 반영·차트 재점검 | `work/04_chart_construed.json` | 있음 |

## 관문
- 통과 G1 원장 확정
- 통과 G2 해석 점검 오류 0
- 통과 G6 진보성 점검 오류 0
- 미통과 G3 차트 오류 0 · 재검토 0
- 미통과 G5 사람 최종 검토

## 점검 결과
- 해석 점검: 오류 0 · 경고 0
- 차트 점검: 오류 0 · 경고 0 · 재검토 행 1
- 진보성 점검: 오류 0 · 경고 8 · 오류 없는 결합: C1, C2

## 메모
- 02_chart.json을 06의 결합 C1에서 새로 만들었습니다(obviousness_check --chart).
- 04_chart_construed.json을 새로 만들었습니다(apply_to_ledger).

## 다음 할 일
**[G3] 차트 오류·'재검토' 행을 고치세요(work/reports/chart_lint.md, impact.md)** — 스킬 `claim-chart` · 파일 `work/04_chart_construed.json`
