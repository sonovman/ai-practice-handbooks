# AGENTS.md — 청구항 분석 통합 작업 공간 v2 (핸드북 30~33)

이 폴더는 claim-suite(지휘)·claim-decompose·claim-chart·claim-construe·obviousness·design-around 여섯 스킬과 점검 도구를 한곳에 모은 통합 키트입니다.
항상 `PROJECT_INSTRUCTIONS.md`를 따릅니다. 요약:

- 새 사건은 `cases/example`(FTO) 또는 `cases/invalidity-example`(무효·진보성)을 복사해 `cases/<사건명>/`으로 시작하고, `case.json`의 purpose·forum을 채운다.
- 매 단계 뒤 `python tools/suite_status.py cases/<사건명> --run` → "다음 할 일"대로. 관문(G1~G6)에서 멈추고 사람에게 확인받는다.
- 한정 ID·해석 문장은 모든 파일에서 동일. 같은 해석을 침해·무효·회피에.
- 근거 위치 없는 판단 금지. 결과는 법적 결론이 아니며 최종 판단은 변리사·변호사.
- 기밀 자료는 승인된 환경에서만, 개인 운영 공개 중계 서버 경유 금지.

## 도구(표준 라이브러리)
claim_parse.py · chart_lint.py · render_chart.py(30편) / construe_check.py · apply_to_ledger.py(31편) / design_around_eval.py(32편) / obviousness_check.py(33편) / suite_status.py(통합)
시험: `for f in tools/test_*.py; do python $f; done` (Windows: `Get-ChildItem tools\test_*.py | % { python $_ }`)
