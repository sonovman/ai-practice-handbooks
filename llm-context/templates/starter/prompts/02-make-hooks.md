# 하네스 훅 구성 요청

이 프로젝트에 결정론적 훅을 구성해 줘(실제 Claude Code 이벤트 이름으로).
- 비밀키·위험 명령 차단: PreToolUse(matcher로 Write/Edit/Bash) 훅, 감지 시 exit 2.
- 완료 차단: Stop 훅에서 테스트 실행, 실패 시 exit 2로 종료 거부.
- 압축 전 상태 보존: PreCompact 훅.
- .claude/settings.json 과 각 스크립트를 만들어 주고, 'preCommit/turnFinish'는 쓰지 마(실제 이벤트 아님).
