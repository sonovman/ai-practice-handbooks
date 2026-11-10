# 04 평가 도구로 집계

03의 회피안을 references/schema.md 형식의 work/design_input.json으로 만들어 줘.
- 한정 ID·해석은 30·31편과 똑같이(해석 문장은 그대로 복사).
- 그다음 `python tools/design_around_eval.py work/design_input.json --chart <31편 chart_construed.json> --out work/da_report.md` 실행.
- 입력 오류(E)는 고치고, 경고(W)는 각각 어떻게 처리할지 한 줄씩.
- 모든 독립항이 LOW인 안이 없으면, 결합안을 만들어 다시 평가해.
