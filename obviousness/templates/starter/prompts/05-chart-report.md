# 05 차트·보고

1. 가장 설득력 있는 결합(예: C1)을 30편 진보성 차트로 바꿔 줘:
   `python tools/obviousness_check.py work/06_obviousness.json --chart C1 --chart-out work/02_chart.json`
   `python tools/chart_lint.py work/02_chart.json` → 오류 0.
2. out/obviousness_report.md: 기준(기준일·통상의 기술자) → 분류표 → 차이점×기술상식 → 결합 논리(관할별) → 2차적 고려사항·효과 → 반대 논리(상대방이 할 주장) → 사람이 판단할 것.
3. 공격(무효) 쪽이면 가장 약한 고리를, 방어(특허권자) 쪽이면 가장 강한 반박(not_found 차이점, 저해, nexus 있는 2차적 고려사항)을 먼저 적어.
