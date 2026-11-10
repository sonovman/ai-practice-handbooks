# 04 해석표 JSON으로 만들고 점검

지금까지의 해석을 references/schema.md 형식의 JSON(work/construction.json)으로 만들어 줘.
- ledger_id는 30편 원장 ID와 같게.
- 해석이 대응 사실에서 새로 확인해야 할 조건을 더하면 requires에 적어(evidence_hint 포함).
- used_for에 침해·유효성 양쪽 해석을 같게 적어(대칭성).
그다음 `python tools/construe_check.py work/construction.json`을 실행해 오류가 0이 될 때까지 고치고, 경고는 판단 이유를 한 줄씩 남겨.
