#!/usr/bin/env bash
# PreToolUse 훅: 파일 쓰기/수정 직전, 하드코딩된 비밀키를 차단한다.
# Claude Code는 훅에 JSON을 stdin으로 넘긴다. exit 2 면 도구 실행을 '차단'하고
# stderr 내용을 Claude에게 돌려줘 스스로 고치게 한다. exit 0 은 허용.
payload=$(cat)
# tool_input 에서 파일 내용(content/new_string 등)을 거칠게 추출해 검사
if printf '%s' "$payload" | grep -Eq 'sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}'; then
  echo "차단: 하드코딩된 비밀키로 보이는 값이 있습니다. 환경변수/시크릿 매니저를 쓰세요." >&2
  exit 2
fi
exit 0
