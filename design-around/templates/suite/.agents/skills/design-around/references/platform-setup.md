# 플랫폼별 설치·설정 (Claude·ChatGPT·Gemini·Microsoft 365 Copilot·Antigravity)

원본은 `starter` 하나입니다. `python build_upload.py` → `dist/design-around.zip`(Claude·ChatGPT), `dist/design-around-flat.zip`(Copilot 등), `dist/design-around/`(Gemini).
30편(claim-decompose·claim-chart)·31편(claim-construe) 스킬과 함께 등록하면 분해 → 해석 → 회피가 이어집니다.

| 플랫폼 | 등록 | 도구 실행 | 메모 |
|---|---|---|---|
| Claude 웹·데스크톱 | 설정에서 코드 실행·파일 생성 켜기 → Skills에 design-around.zip(+30·31편 zip) | 가능 | 프로젝트 지식에 특허·출원경과, 개발안은 사내 승인 범위에서 |
| Claude Code·Cowork | `.agents/skills/design-around`를 `.claude/skills/`로, CLAUDE.md에 `@AGENTS.md` | 가능(로컬) | 30·31편 starter와 같은 사건 폴더 |
| ChatGPT | Skills(지원 요금제)에 zip, 또는 프로젝트 지침에 SKILL.md | 대체로 가능 | |
| Gemini 앱(Gem) / CLI | Gem 지침에 SKILL.md+AGENTS.md / CLI는 GEMINI.md에 `@AGENTS.md` | Gem 제한적 / CLI 가능 | Gem은 회피안 아이디어 정리용 |
| M365 Copilot | 에이전트 지침에 SKILL.md 요약, 지식에 references·사내 도면 문서 / 조직이 허용하면 flat.zip | 환경에 따라 확인 | R&D 문서 접근 권한·공유 범위 확인 |
| Google Antigravity | starter 폴더를 작업 공간으로 | 가능(로컬) | `.agents/rules/design-around.md`가 요청 시 적용 |

## 공통 첫 확인
1. `python tools/test_design_around_eval.py` → 13개 통과.
2. `python tools/design_around_eval.py sample/design_input.json --chart sample/chart_construed_31.json` → O3·O6 LOW, 나머지 HIGH.

## Antigravity에서 AI 도움으로 구축하기
1. 30·31·32편 starter를 한 사건 폴더 아래 나란히 풀고 상위 폴더를 작업 공간으로 엽니다.
2. "세 키트의 시험을 모두 실행해 결과를 보여 줘" → 20 + 16 + 13개 통과(명령 실행은 승인 후).
3. `inbox/`에 특허·출원경과·개발안 사양을 넣고: "30편 원장 → 31편 해석 → 모든 독립항 목록 → design-around로 회피안 3~5개(접근법 ①~④) → design_input.json → design_around_eval로 미국·한국 평가 → 모든 독립항 LOW인 안과 사업 메모"를 요청합니다.
4. 사람이 결과와 근거(시험·도면·출원경과 위치)를 검토하고, 채택안은 설계 동결 전에 비침해 의견을 받습니다.

## 주의
- 메뉴·요금제별 기능은 바뀝니다. 각 서비스의 현재 안내를 확인하세요.
- 개발안·원가·도면은 영업비밀입니다. 승인된 환경에서만, 개인 운영 중계 서버 연동은 쓰지 않습니다.
