---
trigger: model_decision
description: 사용자가 LLM이 지침을 잊거나 규칙을 무시하는 문제, 컨텍스트 윈도우·CLAUDE.md·훅·세션 관리(/clear·/compact)·하네스 구축을 물을 때 적용.
---

# 컨텍스트 관리 작업 흐름(모델 판단 시 적용)

1. 원인부터: 재입력 구조·어텐션 희석·CLAUDE.md는 부탁·압축 손실.
2. CLAUDE.md 슬림화: claude_md_lint.py로 200줄·4~10규칙·모호표현 점검.
3. 훅으로 강제: 위험작업=PreToolUse, 완료차단=Stop, 압축전=PreCompact. exit 2로 차단.
4. 분원화: 절차=스킬, 무거운 작업=서브에이전트(요약만 수신).
5. 성공 기준·TDD: 합격/금지 범위 먼저, 테스트는 수정 금지.
6. 세션: /compact 대신 /clear, 반복 교정은 메모리, context_budget.py로 점유율 확인.

주의: 'preCommit/turnFinish'는 실제 훅 이벤트가 아님. 훅 이름·형식은 공식 문서로 확인.
