# 넘겨주기 계약 — 파일 형식과 점검 도구

| 파일 | 만드는 스킬 | 읽는 스킬·도구 | 핵심 필드 |
|---|---|---|---|
| case.json | claim-suite | suite_status | purpose, forum, patent, claims, priority_date, target, ledger_approved, human_signoff, obviousness_combo |
| 01_ledger.json | claim-decompose (`claim_parse.py --json` 후 사람 확정) | claim-chart | limitations[].id·text·type·flags |
| 02_chart.json | claim-chart | chart_lint, render_chart, apply_to_ledger | meta(우선일·대상·유형·단계), limitations[], rows[](주장·사실·설명) |
| 03_construction.json | claim-construe | construe_check, apply_to_ledger | meta(forum·standard), terms[](ledger_id·construction·evidence·requires·used_for) |
| 04_chart_construed.json | apply_to_ledger | chart_lint, design_around_eval(--chart) | limitations[].construction, rows[].needs_review |
| 05_design_input.json | design-around | design_around_eval | claims[](모든 독립항, 한정별 출원경과), options[].changes[] |
| 06_obviousness.json | obviousness | obviousness_check(→ 02 생성) | meta(기준일·절차), posita, limitations[](원장 ID 전부), references[].map, cgk[], combinations[].steps[], secondary, effects |

## 규칙
1. **ID 고정** — 원장 ID(`1pre`, `1a`, `1c.1` …)는 바꾸지 않는다. 새 청구항은 번호 접두사(`7a`).
2. **해석 문장 복사** — 03의 construction → 04(자동) → 05의 limitations[].construction에 글자 그대로.
3. **재생성 순서** — 06의 결합이 바뀌면 02·04를 지우고 --run. 01이나 02가 바뀌면 04를 지우고 apply_to_ledger로 다시. 03이 바뀌어도 같다. 그다음 05 평가를 다시.
4. **관할 표시** — 03의 forum, 05는 미국·한국을 함께 평가. 한국 기능적 표현·제법한정물건은 미국과 방향이 다르다.
5. **원본 보존** — inbox/는 읽기만. 산출은 work/, 최종은 out/.

## 점검 도구 한눈에
| 도구 | 출처 | 코드 |
|---|---|---|
| claim_parse.py | 30편 | (분해 후보·주의 표시) |
| chart_lint.py · render_chart.py | 30편 | E01~E17 / W01~W16 |
| construe_check.py · apply_to_ledger.py | 31편 | C01~C16 / 재검토 |
| design_around_eval.py | 32편 | E01·E05·E10 / W06·W08·W11·W12 |
| obviousness_check.py | 33편 | O01~O25 / A·B·C·X 분류 / --chart |
| suite_status.py | 통합 v2 | 단계 S1~S6, 관문 G1~G6 |
