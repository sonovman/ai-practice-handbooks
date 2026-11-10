#!/usr/bin/env python3
"""원본 반영 직전 '추가 관문' — 격리 작업본에서 바뀐 파일 목록을 보고, 사람이 꼭 봐야 할 파일을 골라낸다.

왜 필요한가
  Director의 Scope Guard는 .git · .agents · .director_worktrees 를 막지만,
  작업 명세(ORDER)가 넓게(** 등) 열리면 다음 파일은 통과할 수 있다.
    - .claude/settings.json(훅), .mcp.json, .codex/, .gemini/  → 다음 CLI 호출 때 확인 창 없이 실행될 수 있음
    - conftest.py, pytest.ini, package.json(scripts) …          → 테스트를 돌리는 순간 실행·검증 방식이 바뀜
    - .github/workflows/, .vscode/tasks.json                     → 원격 CI·편집기에서 실행
  이 도구는 그런 파일이 섞이면 '사람 확인 필요'로 멈추게 하는 보조 관문이다(fail-closed).

사용
  # 작업본 폴더에서 바뀐 파일을 git으로 직접 읽기
  python apply_gate.py --worktree D:/work/my_app/.director_worktrees/<run_id>
  # 또는 파일 목록을 직접 넘기기(한 줄에 하나, '-'는 표준 입력)
  git diff --name-only HEAD | python apply_gate.py --files -

종료 코드: 0 = 반영해도 됨, 2 = 사람 확인 필요, 1 = 입력 오류(실패로 취급)
"""
import argparse
import json
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import PurePosixPath

# (패턴, 이유) — 소문자·슬래시 기준
REVIEW_RULES = [
    (".claude/*", "Claude Code 설정·훅: 다음 claude 호출 때 실행될 수 있음"),
    (".mcp.json", "MCP 서버 정의: 비대화 호출이 확인 없이 연결할 수 있음"),
    (".codex/*", "Codex 설정"),
    (".gemini/*", "Gemini/Antigravity 설정"),
    (".agents/*", "Antigravity 규칙·스킬·훅"),
    ("agents.md", "모든 에이전트가 읽는 상시 지침"),
    ("claude.md", "Claude Code 상시 지침"),
    ("gemini.md", "Gemini/Antigravity 상시 지침"),
    (".github/workflows/*", "원격 CI에서 실행됨"),
    (".vscode/tasks.json", "편집기에서 자동 실행될 수 있음"),
    (".vscode/settings.json", "편집기 설정"),
    ("conftest.py", "pytest가 테스트 전에 자동 실행"),
    ("*/conftest.py", "pytest가 테스트 전에 자동 실행"),
    ("pytest.ini", "테스트 수집·옵션이 바뀜(검증 약화 가능)"),
    ("tox.ini", "테스트 실행 방식이 바뀜"),
    ("setup.cfg", "테스트·패키지 설정이 바뀜"),
    ("pyproject.toml", "의존성·테스트 설정이 바뀜"),
    ("package.json", "npm scripts·의존성이 바뀜"),
    ("requirements*.txt", "의존성이 바뀜(공급망 확인)"),
    ("makefile", "빌드 명령이 바뀜"),
    ("dockerfile", "빌드 환경이 바뀜"),
    (".env", "비밀값 파일"),
    (".env.*", "비밀값 파일"),
    ("*.pem", "인증서·키 파일"),
    ("*.key", "키 파일"),
]
BLOCK_RULES = [
    (".git/*", "git 내부"),
    (".director_worktrees/*", "Director 제어 영역"),
]


def _norm(path):
    p = str(path).strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p.lower()


def _match(norm, pattern):
    if fnmatch(norm, pattern):
        return True
    # 디렉터리 규칙은 어느 깊이의 하위 파일에도 적용 (.claude/hooks/x.sh 등)
    if pattern.endswith("/*"):
        prefix = pattern[:-1]
        return norm.startswith(prefix) or ("/" + prefix) in ("/" + norm)
    return False


def classify(paths):
    """바뀐 파일 목록 → {'block': [...], 'review': [...], 'ok': [...]}"""
    result = {"block": [], "review": [], "ok": []}
    for raw in paths:
        if not str(raw).strip():
            continue
        n = _norm(raw)
        if ".." in PurePosixPath(n).parts or n.startswith("/") or (len(n) > 1 and n[1] == ":"):
            result["block"].append({"path": raw, "reason": "작업본 밖을 가리키는 경로"})
            continue
        hit = next((why for pat, why in BLOCK_RULES if _match(n, pat)), None)
        if hit:
            result["block"].append({"path": raw, "reason": hit})
            continue
        why = next((why for pat, why in REVIEW_RULES if _match(n, pat)), None)
        if why:
            result["review"].append({"path": raw, "reason": why})
        else:
            result["ok"].append(raw)
    return result


def decide(result):
    if result["block"]:
        return "BLOCK"
    if result["review"]:
        return "HUMAN_REVIEW"
    return "PASS"


def changed_files_in_worktree(worktree):
    """작업본에서 바뀐 파일(커밋 전 변경 + 새 파일)."""
    names = set()
    for args in (["git", "-c", "core.quotepath=false", "diff", "--name-only", "HEAD"],
                 ["git", "-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"]):
        r = subprocess.run(args, cwd=worktree, capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip() or "git 실행 실패")
        names.update(x for x in r.stdout.splitlines() if x.strip())
    return sorted(names)


def main(argv=None):
    ap = argparse.ArgumentParser(description="원본 반영 직전 보조 관문")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--worktree", help="격리 작업본 폴더")
    g.add_argument("--files", help="바뀐 파일 목록 파일('-'는 표준 입력)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.worktree:
            paths = changed_files_in_worktree(a.worktree)
        else:
            src = sys.stdin if a.files == "-" else open(a.files, encoding="utf-8")
            paths = [line.rstrip("\n") for line in src]
    except (OSError, RuntimeError) as e:
        print(f"[실패] 입력을 읽지 못했습니다: {e}  — 반영하지 마세요(fail-closed).")
        return 1
    res = classify(paths)
    verdict = decide(res)
    if a.json:
        print(json.dumps({"verdict": verdict, **res}, ensure_ascii=False, indent=2))
    else:
        print(f"판정: {verdict}  (바뀐 파일 {len(paths)}개)")
        for item in res["block"]:
            print(f"  [막음] {item['path']} — {item['reason']}")
        for item in res["review"]:
            print(f"  [확인] {item['path']} — {item['reason']}")
    return {"PASS": 0, "HUMAN_REVIEW": 2, "BLOCK": 2}[verdict]


if __name__ == "__main__":
    sys.exit(main())
