# 목적별 라우팅과 되돌아가기

## 단계 표
| 단계 | 스킬 | 할 일 | 산출 | 점검 |
|---|---|---|---|---|
| S1 | claim-decompose | `claim_parse.py`로 후보 → 7단계·3대 시험으로 확정 | 01_ledger.json | 사람(G1) |
| S2 | claim-chart | 행마다 주장–사실–설명, 특수 법리 모듈 | 02_chart.json | chart_lint |
| S3 | claim-construe | 다툼 용어만, 증거 순서·특수 형식 | 03_construction.json | construe_check(G2) |
| S4 | claim-construe | `apply_to_ledger.py`로 반영, 재검토 행 처리 | 04_chart_construed.json | chart_lint + 재검토 0(G3) |
| S5 | design-around | 모든 독립항, 회피안 3~5개, 결합안 | 05_design_input.json | design_around_eval(G4) |
| S6 | obviousness | 기준일·통상의 기술자 → ●◐○ 대비 → A/B/C/X → 차이점마다 기준일 기술상식 → 결합(C1…)·2차적 고려사항 | 06_obviousness.json | obviousness_check(G6) |
| R | claim-suite | 보고 | out/report.md | 사람(G5) |

## 목적별 순서
| 목적 | 순서 | 이유 |
|---|---|---|
| infringement | S1 → S2 → S3 → S4 → R | 차트를 써 봐야 다툼 용어가 드러남 |
| invalidity·obviousness | S1 → S3 → S6 → S2 → S4 → R | 절차별 기준으로 먼저 해석하고, 최근접 문헌·차이점·기술상식을 정한 뒤 그 결합으로 차트를 만든다 |
| fto / design-around | S1 → S2 → S3 → S4 → S5 → R | 자사 제품 기준 차트 → 해석 → 회피 |
| construction | S1 → S3 → R | 해석 의견만 |

## 되돌아가기
| 신호 | 돌아갈 곳 |
|---|---|
| chart_lint E01(대응 행 없음)·E12(가짜 요소) | S1 원장 |
| apply_to_ledger '재검토' | S2 사실 보강 또는 결론 변경 → S4 다시 |
| construe_check C10(대칭성)·C03(실시예 수입) | S3 |
| design_around_eval E10(해석 불일치)·W12(재검토 한정) | S3·S4를 먼저 끝냄 |
| 모든 회피안이 어떤 독립항에서 HIGH | S5에서 다른 한정·결합안 |
| obviousness_check O04(기술상식 조사 없음)·O05(증거 날짜) | S6 기술상식 조사 |
| obviousness_check O10(빠진 한정)·O11(동기 근거)·O14(유사 분야) | S6 결합안 다시 |
| 해석 반영 뒤 진보성 차트에 '재검토' | S6 대비(●◐○)를 새 해석으로 다시 → 02 지우고 --run |
| 제품·특허(계속출원·정정) 변경 | 해당 단계부터 다시, 이후 단계 전부 재실행 |

## 스킬 부르는 말(예)
- "claim-decompose로 inbox/claims.txt를 분해해 work/01_ledger.json 초안을 만들어 줘."
- "claim-chart로 원장과 inbox/product/ 자료로 침해 차트(work/02_chart.json)를 써 줘."
- "claim-construe로 다툼 용어를 골라 work/03_construction.json을 만들고 construe_check 오류 0까지."
- "apply_to_ledger로 04를 만들고 재검토 행 목록을 보여 줘."
- "obviousness로 inbox/prior_art의 문헌을 대비해 A/B/C로 나누고, 최근접 문헌과의 차이점마다 기준일 기술상식을 조사해 work/06_obviousness.json을 만든 뒤 obviousness_check 오류 0까지."
- "design-around로 모든 독립항 대상 회피안을 work/05_design_input.json에, design_around_eval로 평가."
- "suite_status --run 결과대로 다음 할 일을 진행해."
