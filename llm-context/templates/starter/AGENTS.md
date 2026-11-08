# AGENTS.md — 이 폴더에서 에이전트가 항상 지킬 것

이 폴더는 핸드북 26편 'LLM 원리와 컨텍스트 관리(하네스)' 키트입니다.

## 항상
- 한국어, 초보자도 따라 하기 쉽게 단계별로.
- 확률적 부탁보다 결정론적 장치(훅·테스트)를 우선. "다 됐습니다"는 자동 검사로 확인.
- 지침은 짧고 기계적으로. 긴 절차는 스킬로, 무거운 작업은 서브에이전트로 분리.

## 훅은 실제 이벤트 이름으로
- PreToolUse / PostToolUse / UserPromptSubmit / Stop / SubagentStop / PreCompact / SessionStart / SessionEnd.
- 완료 차단은 Stop, 압축 전은 PreCompact. 'preCommit'·'turnFinish'는 실제 이벤트가 아니다(git 훅 / Stop).
- 차단은 exit 2 + stderr. settings.json 구조를 지킨다.

## 도구(표준 라이브러리)
- `tools/claude_md_lint.py` — CLAUDE.md 슬림화 점검.
- `tools/context_budget.py` — 컨텍스트 창 점유율 추정.
- 시험: `python tools/test_claude_md_lint.py`, `python tools/test_context_budget.py`.
