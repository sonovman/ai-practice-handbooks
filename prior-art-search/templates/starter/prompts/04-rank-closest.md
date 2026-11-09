# 최근접 선행문헌 산정

mapping.json으로 최근접 선행문헌을 산정해 줘.
`python tools/rank_closest.py plan.json mapping.json --report work/closest.md`
- A 신규성 부정 / B 주인용 / C 보조 / X 기준일 이후로 분류하고 결합 경로를 제시.
- 주인용 후보는 상위 2~3건을 각각 출발점으로. 점수는 집계일 뿐 법적 결론이 아님을 명시.
- 효과의 현저성·청구항 해석은 따로 검토 항목으로.
