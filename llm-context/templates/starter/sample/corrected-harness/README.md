# 하네스 예시 — 실제 Claude Code 훅 형식으로 교정

흔한 초기 접근은 `preToolUse`/`preCommit`/`turnFinish` 같은 이름과 단순한 settings.json을 쓰는 것입니다.
실제 Claude Code의 훅은 아래 이벤트 이름과 구조를 씁니다(공식 문서 기준).

## 실제 훅 이벤트
- PreToolUse / PostToolUse — 도구 실행 직전/직후 (matcher 로 도구 지정)
- UserPromptSubmit — 사용자 입력 제출 시
- Stop / SubagentStop — (서브)에이전트가 응답을 끝내려 할 때  ← '완료 차단'은 여기
- PreCompact — 대화 압축 직전
- SessionStart / SessionEnd / Notification

## 바뀐 점(초기 접근 → 개선)
- `preCommit` 은 Claude Code 훅이 아니라 **git 훅**입니다. 커밋 차단은 git의 pre-commit 훅으로,
  또는 "커밋 명령 실행 직전"을 PreToolUse(matcher: Bash)로 잡아 처리합니다.
- `turnFinish` 라는 이벤트는 없습니다. "작업 완료 차단"은 **Stop** 훅으로 합니다.
- 차단 방식: 훅이 **exit 2** 를 반환하면 동작을 막고 stderr 를 Claude에게 돌려줍니다. exit 0 은 허용.
  (JSON 출력으로 더 세밀하게 제어할 수도 있습니다.)

적용: 이 `.claude/` 를 프로젝트 루트에 두고, 스크립트에 실행 권한(chmod +x)을 줍니다.
