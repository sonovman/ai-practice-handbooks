---
name: patent-intelligence
description: 공개특허(WIPSON 엑셀·공보)로 동종업계 특정 제품의 기술개발동향과 시장 흐름을 분석하고, 승인 관문을 거쳐 C레벨 보고서와 정밀분석 후보(최대 5건)를 만든다. KR·US·JP·CN·EP, 정기·수시 모니터링.
---

# 공개특허 기반 경쟁기술 인텔리전스 (patent-intelligence)

정기(월·분기) 또는 수시(경쟁사 신제품·소송·투자 검토)로 받은 공개 출원군을 검증·분석해, 경영진이 결정할 수 있는 보고서를 만든다.
이미 고른 몇 건의 정밀분석·특정 청구항 회피설계만 필요하면 이 스킬이 아니라 청구항 분석 스킬(30~33편 claim-suite)을 쓴다.

## 기본 원칙
1. **세는 일은 도구, 판단은 사람·AI.** 문헌 수·연도·출원인·패밀리·점수 환산은 `tools/`로 계산하고 그 숫자만 쓴다. 눈대중으로 세지 않는다.
2. **분석과 보고를 나눈다.** 분석결과서가 승인되면 그것이 `승인된 분석 기준선`이다. 보고서는 기준선에 있는 결론만 쓰고, 결론마다 `[B##]` 태그를 단다. 새 사실·점수·결론은 `신규 분석사항`으로 분리해 재승인.
3. **관문에서 멈춘다.** 분석결과(ANALYSIS)·보고서 초안(REPORT)·정밀분석 후보(CANDIDATES) 세 곳. 무응답은 승인이 아니다. `승인`은 명시 승인, `계속`만 있으면 묵시 승인으로 **기록했다고 말하고** 넘어간다(프로젝트 설정에서 끌 수 있음). 수정·추가 지시는 반영해 같은 관문에 재제출. 상태는 `work/state.json`에 남긴다(`tools/pi_gate.py`).
4. **번호와 이름.** 특허·실용신안을 말할 때마다 공개번호 또는 등록번호, 출원인은 `원문명 (공식 영문명)`. 영문명이 확인되지 않으면 `영문명 미확인`, 기계번역이면 `비공식 번역`. 출원번호를 공개번호처럼 쓰지 않는다.
5. 사용자 문서에 `Corpus`라는 말을 쓰지 않는다 → `공개특허 모집단`, `기술동향 분석대상`, `조사대상 문헌`.
6. 당사 청구항 대조 없이 침해·비침해·FTO를 단정하지 않는다. 단독출원 하나를 업계 트렌드로 올리지 않는다.

## 필수 참고자료 (작업 시작 때 모두 읽기)
- 자료 받기·열 맞추기·국가별 문헌종류·공개 지연 → [references/data-intake.md](references/data-intake.md)
- 분석·분류·등급·점수·최종 검증 → [references/analysis-rules.md](references/analysis-rules.md)
- 특허로 읽는 시장 신호와 한계 → [references/market-signals.md](references/market-signals.md)
- 승인 상태·단계별 산출물·기준선 → [references/approval-workflow.md](references/approval-workflow.md)
- 보고서 구성·표현·최종 QA → [references/report-spec.md](references/report-spec.md)
- 정밀분석 인계 패킷 → [references/handoff.md](references/handoff.md)
- 플랫폼별 설치·정기 실행 → [references/platform-setup.md](references/platform-setup.md)
- Microsoft 365 Copilot: SharePoint 경로에 모아 분석 → [references/copilot-sharepoint.md](references/copilot-sharepoint.md)

## 실행 흐름
### 0. 회차 설정
`config/project.json`에 회차명, 주기(정기/수시), 국가, 자료일, 기술동향 기준일, 주력·인접·확장 기술영역, 관심 경쟁사, 당사명, 당사 청구항 유무를 적는다. 이미 받은 정보는 다시 묻지 않는다. 결론을 바꾸는 누락만 구체적으로 요청하고, 나머지는 한계로 적고 진행한다. `pi_gate.py init`.

### 1. 자료 검증 (INPUT_VALIDATION)
`python tools/pi_intake.py inbox/<이번회차>.xlsx --previous inbox/<직전회차>.xlsx --pdf-dir inbox/pdf`
→ `work/01_intake.md`의 오류·경고를 먼저 사용자에게 보여 준다(번호 없는 문헌, 누락 공보, 영문명 미확인, 패밀리 미확인, 중국 병행출원 후보, 공개 지연 구간). `이번 회차 신규 관측`과 `기술동향 분석대상`은 다른 집합이다.

### 2. 분석 (ANALYSIS)
1. 모든 분석대상 1차 선별: 요약·독립청구항·대표도면·출원인·최선일·권리유형으로 `Problem → Mechanism → Structure → Function → Effect`. 기술군을 정해 `work/clusters.csv`(id,cluster).
2. 2차 정독: 핵심 동향·반복출원·회피설계 신호·당사 구조 근접·신규 멀티기능·FTO 후보만 종속항·상세설명·패밀리까지. 증거 우선순위 `청구항 > 상세설명·도면 > 요약 > 명칭`.
3. 점수표 `work/scores.csv` → `python tools/pi_stats.py work/01_intake.json --clusters work/clusters.csv --scores work/scores.csv`. 도구의 등급은 '후보'다. 정독해 확정하고, 바꾸면 이유를 적는다.
4. `work/03_analysis.md`: 자료검증 → 확정사실·추론·미확인(판단마다 `[B##]`) → 신규 관측 → 기술동향 → 경쟁사 전략 → 회피설계 신호 → 시장 신호 → 정밀분석 예비후보 → 한계·신뢰도. 보고서 디자인은 하지 않는다.
5. `pi_gate.py submit ANALYSIS` → 승인 / 수정 후 재검토 / 추가자료 반영 중 선택을 요청하고 **멈춘다**.

### 3. 보고서 초안 (REPORT)
기준선만으로 `work/reports/report.md`(구성: report-spec). 결론마다 `[B##]`. `python tools/report_lint.py work/reports/report.md --stats work/02_stats.json --baseline work/03_analysis.md` 오류 0 → submit → 멈춤.

### 4. 최종본 (FINAL)
승인된 초안으로 최종본. 원본은 report.md 하나. HTML/PDF는 `tools/render_report.py`, DOCX는 플랫폼 문서 기능(Claude docx 스킬, ChatGPT 파일 생성, Word+Copilot). 렌더한 뒤 쪽마다 눈으로 확인(번호·영문명 잘림, 표 넘침). 단순·현대적·가독성, 장식보다 근거와 신뢰도.

### 5. 정밀분석 후보 (CANDIDATES)
정말 정밀검토가 필요한 문헌만, 최대 5건(채우려고 약한 후보를 넣지 않음). 점수가 낮아도 대체원리·강한 회피설계 신호·핵심 경쟁사 권리망이면 `Strategic Exception`. 번호·출원인(원문·영문)·선정 이유·분석목적·긴급도·필요 추가자료 → submit → 멈춤. 승인 전에는 정밀분석을 시작하지 않는다.

### 6. 인계 (HANDOFF)
승인된 대상만 `work/05_handoff.json`(필드: handoff.md). 다음 단계는 claim-suite(30~33편: 분해→해석→차트→진보성·회피)에 이 패킷과 공보 원문을 넘기라고 안내한다.

## 중단 조건
- 관문에서 응답이 없으면 다음 단계로 가지 않는다.
- 번호를 확인할 수 없는 문헌은 핵심근거로 쓰지 않는다.
- 공식 출처로 확인하지 못한 영문명을 공식명처럼 쓰지 않는다.
- 공개 지연 구간(최근 18개월)의 문헌 수 감소를 '감소·둔화'로 해석하지 않는다.
- 특허 출원 수를 매출·점유율로 바꿔 말하지 않는다.
