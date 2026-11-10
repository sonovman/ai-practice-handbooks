# AGENTS.md — 이 폴더에서 에이전트가 항상 지킬 것

이 폴더는 핸드북 34편 '공개특허로 읽는 경쟁기술 동향과 C레벨 보고서' 키트입니다.
스킬: `.agents/skills/patent-intelligence` · 다음 단계(정밀분석)는 30~33편 claim-suite.

## 항상
- 한국어, 초보자도 따라 하기 쉽게 단계별로.
- 숫자(문헌·패밀리·기술신호·연도·점수)는 `tools/`가 만든 `work/01_intake.json`·`02_stats.json`에서만 가져온다. 직접 세지 않는다.
- 관문(ANALYSIS·REPORT·CANDIDATES)에서 멈춘다. 무응답은 승인이 아니다. `계속`은 묵시 승인으로 '기록했다고 말하고' 진행. 상태는 `python tools/pi_gate.py status`.
- 특허를 말할 때마다 공개·등록번호 + `원문 출원인 (영문명 또는 상태)`. 출원번호로 대체하지 않는다. 'Corpus'라는 말을 쓰지 않는다.
- 최근 18개월 출원(공개 지연 구간)을 감소로 읽지 않는다. 출원 수를 점유율로 바꿔 말하지 않는다.
- 당사 청구항 대조 없이 침해·비침해·FTO를 단정하지 않는다. 도구 결과·점수는 판단 재료이며 최종 판단은 사람이 한다.

## 폴더
- `inbox/` 원자료(읽기만) · `inbox/pdf/` 공보 · `config/` 회차 설정·열 별칭·출원인 별칭 · `work/` 산출물 · `out/` 최종본

## 기밀·보안
- 당사 청구항·제품자료·경쟁사 관심 목록은 회사가 승인한 환경에서만. 개인 운영 공개 중계 서버로 보내지 않는다.

## 도구(표준 라이브러리, Python 3.9+)
- `tools/pi_intake.py` 자료 검증 · `tools/pi_stats.py` 집계·등급 후보·점수·차트 · `tools/pi_gate.py` 관문 상태
- `tools/report_lint.py` 보고서 점검 · `tools/render_report.py` 인쇄용 HTML · `tools/make_sample.py` 가상 시범 자료
- `tools/export_for_copilot.py` Copilot(SharePoint 지식)용 .html·.xlsx·.txt 내보내기
- 시험: `python tools/test_pi_tools.py` (33개)
