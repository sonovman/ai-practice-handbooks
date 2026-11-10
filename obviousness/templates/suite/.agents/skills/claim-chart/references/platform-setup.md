# 플랫폼별 설치·설정 (Claude·ChatGPT·Gemini·Microsoft 365 Copilot·Antigravity)

원본은 `starter` 하나입니다. `python build_upload.py`가 웹 앱용 묶음을 만듭니다.
- `dist/claim-decompose.zip`, `dist/claim-chart.zip` — 폴더가 ZIP 최상위(Claude·ChatGPT 스킬 업로드)
- `dist/*-flat.zip` — SKILL.md가 ZIP 최상위(Copilot 등)
- `dist/claim-decompose/`, `dist/claim-chart/` — 펼친 폴더(Gemini 붙여넣기용)

| 플랫폼 | 등록 | 도구 실행(파이썬) | 비고 |
|---|---|---|---|
| Claude 웹·데스크톱 | 설정 → 기능에서 코드 실행·파일 생성 켬 → Skills에 zip 2개 업로드 | 가능 | 프로젝트 지침에 AGENTS.md, 지식에 사건 청구항·명세서 |
| Claude Code·Cowork | `.agents/skills/*`를 `.claude/skills/`로 복사, CLAUDE.md에 `@AGENTS.md` | 가능(로컬) | 사건 폴더에서 바로 실행 |
| ChatGPT | Skills(지원 요금제)에 zip 업로드, 또는 프로젝트 지침에 SKILL.md 붙여넣기 | 대체로 가능(Python) | 사건마다 새 대화·프로젝트 |
| Gemini 앱(Gem) | Gem 지침에 SKILL.md + AGENTS.md, 지식에 references | 제한적 | 분해·초안 보조용, 점검은 로컬 도구로 |
| Gemini CLI | starter 폴더에서 실행, GEMINI.md에 `@AGENTS.md` | 가능(로컬) | |
| M365 Copilot | 에이전트 만들기(지침에 SKILL.md 요약, 지식에 references) 또는 조직이 허용한 스킬 업로드(flat.zip) | 환경에 따라 확인 필요 | 사내 문서(명세서·대비표)를 SharePoint로 연결할 때 기밀 등급 확인 |
| GitHub Copilot(VS Code) | starter 폴더를 열면 AGENTS.md·`.agents/skills` 인식 | 가능(터미널) | |
| Google Antigravity | starter 폴더를 작업 공간으로 열기 | 가능(로컬) | `.agents/rules/claim-chart.md`(model_decision)가 요청 시 자동 적용 |

## 공통 첫 확인(5분)
1. 전체 ZIP을 받아 압축 해제(숨김 `.agents` 폴더가 보이게).
2. `python tools/test_claim_parse.py` → 8개, `python tools/test_chart_lint.py` → 12개 통과.
3. `python tools/claim_parse.py sample/claim_en.txt` → [1pre]~[1g] 10행.
4. `python tools/chart_lint.py sample/chart_good.json` → 오류 0, `sample/chart_bad.json` → 오류 12·경고 7.

## Antigravity에서 AI 도움으로 구축하기
1. Antigravity에서 빈 폴더를 열고 에이전트에게 요청: "핸드북 30편 키트 구조(AGENTS.md, .agents/rules, .agents/skills/claim-decompose·claim-chart, tools, prompts, sample)로 작업 폴더를 만들어 줘. 도구는 표준 라이브러리만, 시험 파일 포함."
   — 또는 키트 ZIP을 풀어 그 폴더를 엽니다(권장: 검증된 도구를 그대로 씀).
2. 에이전트에게 "tools 시험을 모두 실행하고 결과를 보여 줘"라고 시켜 20개 통과를 확인합니다. 터미널 명령 실행은 승인 후 진행되게 설정을 둡니다.
3. 사건 폴더를 만들고(`inbox/`에 청구항·명세서·대상물 자료) "claim-decompose로 원장 초안, 승인 후 claim-chart로 침해 차트, chart_lint 오류 0까지"라고 요청합니다.
4. 결과(`work/ledger.md`, `work/chart.json`, `work/lint.md`)를 사람이 검토합니다.

## 주의
- 메뉴 이름·요금제별 기능·관리자 정책은 자주 바뀝니다. 각 서비스의 현재 안내를 확인하세요.
- 의뢰인 자료·상대방 기밀은 조직이 승인한 환경(사내 테넌트·로컬)에서만. 개인 운영 중계 서버를 거치는 연동은 쓰지 않습니다.
