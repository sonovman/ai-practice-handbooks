# AGENTS.md — 삼권분립 개발 작업 폴더 (항상 적용)

이 폴더는 "지휘(HEAD) · 구현(BUILDER) · 검수(REVIEWER)"를 나눠 코드를 만드는 작업 공간입니다.
어느 AI가 읽든 아래 규칙을 지킵니다.

## 역할을 섞지 않는다
- HEAD는 목표를 **ORDER**(허용 경로·파일 수 상한·완료 기준)로 바꾸고, 직접 코드를 쓰지 않는다.
- BUILDER는 ORDER의 허용 경로 안에서만 파일을 만들고 고친다. 테스트를 약하게 바꾸지 않는다.
- REVIEWER는 BUILDER와 **다른 회사 모델**이 맡고, diff와 테스트 출력만 보고 판정한다.
- 판정이 애매하거나 응답 형식이 깨지면 **FAIL**로 본다(fail-closed).

## 원본을 지킨다
- 작업은 git worktree(격리 작업본)에서만 한다. 원본 반영은 사람이 확인한 뒤 한다.
- 다음 파일이 바뀌면 반영 전에 반드시 사람에게 보인다:
  `.claude/` `.mcp.json` `.codex/` `.gemini/` `.agents/` `AGENTS.md` `CLAUDE.md` `GEMINI.md`
  `.github/workflows/` `.vscode/tasks.json` `conftest.py` `pytest.ini` `package.json` `requirements*.txt` `.env*`
  → `python tools/apply_gate.py --worktree <작업본>` 으로 확인한다.

## 사람에게 반드시 묻는 것
결제·유료 서비스 가입, 실계좌 주문, 실제 비밀번호·키·토큰, 되돌릴 수 없는 외부 행동(메일 발송, 배포, 삭제).

## 하지 않는 것
- 종량제 API 키 사용(구독 로그인 CLI만). 키가 환경에 있으면 `tools/director_preflight.py`로 먼저 확인.
- 권한 우회 플래그(`--dangerously-skip-permissions`, `--yolo`, `danger-full-access` 등) 사용.
- 개인이 운영하는 외부 중계 서버·비공식 MCP를 거치는 연결.

## 폴더
- `inbox/` 목표 메모·ORDER 초안 · `work/` 산출물·보고서 · `tools/` 점검 도구 · `prompts/` 붙여 넣는 프롬프트
