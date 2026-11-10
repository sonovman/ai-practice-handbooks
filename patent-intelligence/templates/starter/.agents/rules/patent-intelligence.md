---
trigger: model_decision
description: 사용자가 공개특허·출원 리스트(WIPSON 엑셀 등)로 경쟁사·업계 기술동향, 기술의 시장 흐름, 특허 동향 보고서, 경영진(C레벨) 보고, 정기·수시 특허 모니터링, 관심특허 후보 선정을 요청할 때 적용.
---

# 경쟁기술 인텔리전스 작업 흐름(모델 판단 시 적용)

1. `pi_gate.py status`로 회차 상태 확인(없으면 init). `config/project.json` 확인·보완.
2. `pi_intake.py` → 오류·경고 보고(번호 없음·누락 공보·영문명·패밀리·병행 후보·공개 지연).
3. 1차 선별 → `work/clusters.csv`·`work/scores.csv` → `pi_stats.py` → 등급 후보를 정독으로 확정.
4. `work/03_analysis.md`([B##] 태그) → ANALYSIS 관문에서 멈춤.
5. 승인 후 `work/reports/report.md` → `report_lint.py` 오류 0 → REPORT 관문에서 멈춤.
6. 최종본(render_report·DOCX) → 정밀분석 후보 ≤5 → CANDIDATES 관문에서 멈춤 → `work/05_handoff.json` → claim-suite 안내.
