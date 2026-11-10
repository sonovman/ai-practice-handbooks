# 프로젝트에서 다섯 스킬 켜기 (Claude·ChatGPT·Gemini·Microsoft 365 Copilot·Antigravity)

`python build_upload.py` → `dist/`에 다섯 스킬(claim-suite, claim-decompose, claim-chart, claim-construe, design-around)의
`이름.zip`(폴더가 최상위), `이름-flat.zip`(SKILL.md가 최상위), 펼친 폴더가 만들어집니다.
프로젝트 지침에는 `PROJECT_INSTRUCTIONS.md`를 그대로 붙여 넣습니다.

## Claude (웹·데스크톱)
1. 설정에서 코드 실행·파일 생성을 켭니다.
2. 스킬 화면에서 zip 다섯 개를 올리고 모두 켭니다(스킬은 계정 단위라 모든 프로젝트에서 보입니다).
3. 새 프로젝트를 만들고 **프로젝트 지침**에 `PROJECT_INSTRUCTIONS.md` 내용을 붙여 넣습니다.
4. 프로젝트 지식(파일)에 사건 자료를 올리고, 대화를 "claim-suite로 이 사건을 시작해 줘. 목적은 FTO"처럼 시작합니다.
5. 도구는 대화의 코드 실행 환경에서 돌아갑니다. 사건 폴더가 대화마다 새로 만들어질 수 있으니 결과 파일은 내려받아 보관합니다.

## Claude Code·Cowork (로컬)
- `suite/` 폴더를 사건 작업 공간으로 열고 `.agents/skills/*`를 `.claude/skills/`로 복사, CLAUDE.md에 `@AGENTS.md`와 `@PROJECT_INSTRUCTIONS.md`.
- 사건마다 `cases/<사건명>/`을 만들고 `python tools/suite_status.py cases/<사건명> --run`.

## ChatGPT
- 스킬을 지원하는 요금제면 zip 다섯 개를 올리고, 프로젝트 지침에 `PROJECT_INSTRUCTIONS.md`.
- 스킬을 쓸 수 없으면 프로젝트 파일에 각 SKILL.md와 references를 올리고 지침에 "필요한 단계에서 해당 SKILL.md를 따르라"를 넣습니다.

## Gemini
- Gem: 지침에 `PROJECT_INSTRUCTIONS.md`, 지식에 다섯 SKILL.md와 핵심 references. 도구 실행은 제한적이므로 점검은 로컬에서.
- Gemini CLI: `suite/`에서 실행, GEMINI.md에 `@AGENTS.md` `@PROJECT_INSTRUCTIONS.md`.

## Microsoft 365 Copilot
- 에이전트를 만들어 지침에 `PROJECT_INSTRUCTIONS.md`(길이 제한이 있으면 '0. 시작'·'1. 순서'·'2. 관문'만), 지식에 다섯 SKILL.md·references·사건 문서(SharePoint).
- 조직이 스킬 업로드를 허용하면 `-flat.zip`을 올립니다. Python 실행 가능 여부는 환경에 따라 다르니 점검은 로컬 도구로 확인합니다.

## Google Antigravity (AI 도움으로 구축)
1. 통합 키트를 풀어 `suite/` 폴더를 작업 공간으로 엽니다. `AGENTS.md`(항상 규칙)와 `.agents/rules/claim-suite.md`(요청 시 적용)가 자동으로 읽힙니다.
2. 에이전트에게: "tools의 시험을 모두 실행해 결과를 보여 줘" → 57개 통과(명령 실행은 승인 후).
3. "cases/example을 복사해 cases/사건A를 만들고, inbox에 자료를 넣었어. claim-suite 순서대로 진행하고 각 관문에서 멈춰서 나에게 확인받아."
4. 단계마다 `suite_status.py --run` 결과를 보고 다음 단계로. 관문 G1·G5는 사람이 `case.json`에 직접 표시합니다.

## 주의
- 메뉴 이름·요금제별 기능·관리자 정책은 바뀝니다. 각 서비스의 현재 안내를 확인하세요.
- 의뢰인·상대방·개발 자료는 조직이 승인한 환경에서만. 개인 운영 중계 서버 연동은 쓰지 않습니다.
