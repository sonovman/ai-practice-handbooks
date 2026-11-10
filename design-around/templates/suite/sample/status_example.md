# 사건 상태 — 가상 착즙기 특허 A — JX-600 개발안 FTO·회피설계(교육용 예시)

- 목적: fto · 관할: us+kr · 특허: 가상특허 A · 대상: JX-500(현행) / JX-600(개발안)

## 단계
| 단계 | 스킬 | 할 일 | 파일 | 상태 |
|---|---|---|---|---|
| S1 | claim-decompose | 청구항 분해 → 한정 원장 | `work/01_ledger.json` | 있음 |
| S2 | claim-chart | 자사 제품 대비 차트 | `work/02_chart.json` | 있음 |
| S3 | claim-construe | 다툼 용어 해석 | `work/03_construction.json` | 있음 |
| S4 | claim-construe | 해석 반영·차트 재점검 | `work/04_chart_construed.json` | 있음 |
| S5 | design-around | 회피안 평가(모든 독립항) | `work/05_design_input.json` | 있음 |

## 관문
- 통과 G1 원장 확정
- 통과 G2 해석 점검 오류 0
- 미통과 G3 차트 오류 0 · 재검토 0
- 통과 G4 모든 독립항 LOW인 회피안
- 미통과 G5 사람 최종 검토

## 점검 결과
- 해석 점검: 오류 0 · 경고 0
- 차트 점검: 오류 0 · 경고 0 · 재검토 행 1
- 회피안: 입력 오류 0 · 미국·한국 모두 LOW: O3, O6

## 메모
- 04_chart_construed.json을 새로 만들었습니다(apply_to_ledger).

## 다음 할 일
**[G3] 차트 오류·'재검토' 행을 고치세요(work/reports/chart_lint.md, impact.md)** — 스킬 `claim-chart` · 파일 `work/04_chart_construed.json`
