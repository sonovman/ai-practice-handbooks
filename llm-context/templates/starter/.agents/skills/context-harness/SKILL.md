---
name: context-harness
description: LLM이 대화·지침이 길어질 때 맥락을 잃는 이유를 이해하고, 확률적 부탁(프롬프트) 대신 결정론적 하네스(훅·테스트·슬림 지침·세션 분리)로 통제하는 법. CLAUDE.md 슬림화, 훅, 스킬/서브에이전트 분원화, /clear·메모리 전략.
---

# 컨텍스트 관리와 하네스

LLM은 매 턴 [시스템 지침 + 규칙 + 데이터 + 대화 전체]를 처음부터 다시 읽는다. 길어지면 어텐션이
분산돼 초기 규칙을 놓친다. 그래서 '말로 부탁'하지 말고 '시스템이 어길 수 없는 장치'로 바꾼다.

## 왜 맥락을 잃나 (원인)
- 재입력 구조: 대화 이력을 가중치에 저장하지 않고 매번 전체를 다시 입력받는다 → 길수록 창이 참.
- 어텐션 희석·위치적 유실: 양이 늘면 비중이 분산되고, 초기 규칙은 끝(현재 생성 시점)에서 멀어져 무시된다.
- CLAUDE.md는 '부탁': 강제 설정이 아니라 참고 텍스트다. 길고 모호하면 진짜 규칙이 잡음에 묻힌다.
- 압축(/compact)의 손실: 요약 과정에서 스킬 목록·세부 규칙을 잃을 수 있다.

## 통제 전략
1. **확률적 지시 → 결정론적 훅**: 위험 작업·완료 선언을 훅으로 막는다(실제 이벤트: PreToolUse, Stop, PreCompact…).
   - exit 2 로 차단하고 stderr 를 Claude에게 돌려 스스로 고치게 한다. 'preCommit/turnFinish'는 실제 이벤트가 아니다(각각 git 훅 / Stop).
2. **CLAUDE.md 슬림화**: `claude_md_lint.py` 로 200줄·상시 규칙 4~10개·모호 표현을 점검. 과거 2번 이상 틀린 것만, 0/1로 판별 가능한 문장으로.
3. **분원화(스킬·서브에이전트)**: 절차는 스킬로(호출 시 로딩), 무거운 분석은 서브에이전트(독립 창)로 맡기고 요약만 받는다.
4. **성공 기준·TDD**: "무엇이 되면 합격 / 무엇은 안 건드림"을 먼저 테스트로 고정. 테스트는 수정 금지, 이행 코드만.
5. **세션 정화**: 주제가 바뀌면 /compact 대신 /clear. 반복 교정은 메모리로 재주입. `context_budget.py` 로 점유율 확인.

## 도구
- `tools/claude_md_lint.py` — CLAUDE.md 슬림화 점검(PASS/WARN/FAIL).
- `tools/context_budget.py` — 컨텍스트 창 점유율 추정(OK/WARN/HIGH).
- `sample/corrected-harness/` — 실제 훅 형식(settings.json·PreToolUse·Stop·PreCompact) 예시.

## 참조
- `references/checklist.md` — 하네스 개편 체크리스트(교정판)
- `references/platforms.md` — Claude·ChatGPT·Gemini·Copilot·Antigravity에서의 컨텍스트 관리
