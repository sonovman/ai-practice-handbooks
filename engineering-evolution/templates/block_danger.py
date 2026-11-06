"""위험한 명령을 실행 전에 막는 Hook (Claude Code PreToolUse 용)

에이전트가 터미널 명령을 실행하기 직전에 Claude Code가 이 파일을 부릅니다.
아래 목록에 걸리면 종료 코드 2로 끝나고, 그 명령은 실행되지 않습니다.
CLAUDE.md의 "삭제 금지"는 안내일 뿐이라 무시될 수 있지만, 이 차단은 무시되지 않습니다.
Python 표준 라이브러리만 씁니다.
"""
import json
import re
import sys

BLOCK = [
    (r"\brm\s+-[a-z]*r", "폴더 통째 삭제"),
    (r"\b(del|rmdir|Remove-Item)\b", "파일 삭제"),
    (r"\bdrop\s+(table|database)\b", "DB 삭제"),
    (r"\b(mv|move|sed\s+-i)\b.*input[/\\]|>\s*input[/\\]", "원본 자료 폴더(input/) 수정"),
    (r"\b(curl|wget|Invoke-WebRequest|scp)\b", "외부 전송"),
]


def main():
    raw = sys.stdin.buffer.read().decode("utf-8", "ignore")
    try:
        data = json.loads(raw[raw.find("{"):])
    except Exception:
        return 0
    command = (data.get("tool_input") or {}).get("command", "")
    for pattern, reason in BLOCK:
        if re.search(pattern, command, re.IGNORECASE):
            sys.stderr.write(f"[차단] {reason} 명령은 실행할 수 없습니다. 필요하면 사용자에게 요청하세요.\n명령: {command}")
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
