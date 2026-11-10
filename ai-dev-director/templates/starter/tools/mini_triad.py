#!/usr/bin/env python3
"""mini_triad — '지휘·구현·검수' 삼권분립을 200줄 남짓으로 보여 주는 학습·소규모용 오케스트레이터.

AI DEV DIRECTOR의 핵심 원칙만 남겼다(표준 라이브러리만 사용).
  1) 원본 무수정 : git worktree(.mini_triad/<run>)에서만 작업, 원본 반영은 사람이 merge
  2) 스코프 가드 : ORDER의 allowed_paths·max_files 밖 변경이면 FAIL
  3) 반영 관문   : apply_gate로 AI 설정·테스트 설정 파일이 섞이면 멈춤
  4) 실제 테스트 : 검증 명령은 프로젝트가 아니라 이 명령줄(--test)에서 받음
  5) 독립 검수   : REVIEWER는 작업본 '밖' 빈 폴더에서 diff를 표준 입력으로만 받음
                   → 작업본에 심어진 .claude/.mcp.json 같은 설정이 검수 CLI에 실리지 않음
  6) fail-closed : 검수 응답이 없거나 JSON이 깨지면 PASS가 아니라 FAIL
  7) 종량제 차단 : 알려진 API 키 변수를 지운 환경으로 CLI 호출

사용(예: BUILDER=Antigravity, REVIEWER=Codex)
  python mini_triad.py --project D:/work/app --order order.json \
      --builder '["agy", "-p", "{prompt}"]' \
      --reviewer '["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", "-"]' \
      --test "python -m pytest -q"
  명령 배열 안의 {prompt} 는 프롬프트로 바뀌고, 없으면 프롬프트를 표준 입력으로 넘긴다.
  CLI 플래그는 버전마다 다를 수 있으니 각 CLI의 --help로 먼저 확인한다.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
import uuid
from fnmatch import fnmatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apply_gate  # noqa: E402

STRIP_ENV = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
             "AZURE_OPENAI_API_KEY", "CODEX_API_KEY", "ANTHROPIC_AUTH_TOKEN",
             "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
             "GOOGLE_GENAI_USE_VERTEXAI"]
REVIEW_FORMAT = ('마지막 줄에 JSON 한 줄만 쓰세요: {"verdict": "PASS" 또는 "FAIL", "reasons": ["..."]}. '
                 '확실하지 않으면 FAIL입니다.')


def clean_env():
    env = os.environ.copy()
    for k in STRIP_ENV:
        env.pop(k, None)
    return env


def git(cwd, *args, check=True):
    r = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=cwd,
                       capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 실패: {r.stderr.strip()}")
    return r.stdout


def call_cli(cmd, prompt, cwd, timeout):
    argv = [a.replace("{prompt}", prompt) for a in cmd]
    stdin = None if any("{prompt}" in a for a in cmd) else prompt
    try:
        r = subprocess.run(argv, cwd=cwd, input=stdin, capture_output=True, text=True,
                           encoding="utf-8", env=clean_env(), timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as e:
        return 124, f"CLI 실행 실패: {e}"


def split_cmd(cmd):
    """윈도우 경로(역슬래시)를 지키면서 따옴표만 벗겨 명령을 나눈다."""
    toks = shlex.split(cmd, posix=os.name != "nt")
    return [t[1:-1] if len(t) > 1 and t[0] == t[-1] and t[0] in "\"'" else t for t in toks]


def parse_verdict(text):
    """출력 끝에서부터 verdict JSON 한 줄을 찾는다. 못 찾으면 FAIL(fail-closed)."""
    for line in reversed((text or "").strip().splitlines()):
        line = line.strip().strip("`")
        if line.startswith("{") and "verdict" in line:
            try:
                obj = json.loads(line)
            except ValueError:
                break
            v = str(obj.get("verdict", "")).upper()
            if v in ("PASS", "FAIL"):
                return v, [str(x) for x in obj.get("reasons", [])][:20]
            break
    return "FAIL", ["검수 응답에서 verdict JSON을 찾지 못함(fail-closed)"]


def scope_check(changed, order):
    allowed = order.get("allowed_paths") or []
    max_files = int(order.get("max_files", 10))
    bad = [p for p in changed if not any(fnmatch(p.replace("\\", "/"), pat) for pat in allowed)]
    reasons = [f"허용 경로 밖 변경: {p}" for p in bad]
    if len(changed) > max_files:
        reasons.append(f"바뀐 파일 {len(changed)}개 > 상한 {max_files}개")
    if not changed:
        reasons.append("바뀐 파일이 없음")
    return reasons


def run(project, order, builder, reviewer, test_cmd, timeout=600, log=print):
    project = Path(project).resolve()
    run_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    wt = project / ".mini_triad" / run_id
    branch = f"mini-triad/{run_id}"
    report = {"run_id": run_id, "worktree": str(wt), "branch": branch, "steps": []}

    def step(name, ok, detail):
        report["steps"].append({"step": name, "ok": ok, "detail": detail})
        log(f"[{'통과' if ok else '실패'}] {name}: {detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)[:300]}")
        return ok

    def finish(verdict):
        report["verdict"] = verdict
        out = project / ".mini_triad" / f"{run_id}.report.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["report_file"] = str(out)
        return report

    # .mini_triad/ 는 원본 git이 보지 않게 한다
    excl = project / ".git" / "info" / "exclude"
    if excl.parent.is_dir() and ".mini_triad/" not in (excl.read_text(encoding="utf-8") if excl.exists() else ""):
        with open(excl, "a", encoding="utf-8") as f:
            f.write("\n.mini_triad/\n")
    git(project, "worktree", "add", "-q", "-b", branch, str(wt), "HEAD")
    step("격리 작업본", True, str(wt))

    prompt = (f"목표: {order['goal']}\n허용 경로: {order.get('allowed_paths')}\n"
              f"파일 수 상한: {order.get('max_files', 10)}\n"
              "허용 경로 안의 파일만 만들거나 고치세요. 테스트 파일을 약하게 바꾸지 마세요. 셸 명령은 쓰지 마세요.")
    code, out = call_cli(builder, prompt, str(wt), timeout)
    if not step("BUILDER", code == 0, f"종료 코드 {code}"):
        return finish("FAIL")

    changed = sorted(set(git(wt, "diff", "--name-only", "HEAD").split("\n") +
                         git(wt, "ls-files", "--others", "--exclude-standard").split("\n")) - {""})
    reasons = scope_check(changed, order)
    if not step("스코프 가드", not reasons, reasons or changed):
        return finish("FAIL")
    gate = apply_gate.classify(changed)
    verdict = apply_gate.decide(gate)
    if not step("반영 관문", verdict == "PASS", verdict if verdict == "PASS" else gate["block"] + gate["review"]):
        return finish("HUMAN_REVIEW")

    tr = subprocess.run(split_cmd(test_cmd), cwd=wt, capture_output=True, text=True,
                        encoding="utf-8", env=clean_env(), timeout=timeout)
    test_log = ((tr.stdout or "") + (tr.stderr or ""))[-4000:]
    if not step("테스트", tr.returncode == 0, f"종료 코드 {tr.returncode}"):
        report["test_log"] = test_log
        return finish("FAIL")

    git(wt, "add", "-A")
    diff = git(wt, "diff", "--cached")[:60000]
    review_prompt = (f"당신은 독립 검수자입니다. 목표와 diff, 테스트 결과를 읽고 판정하세요.\n목표: {order['goal']}\n"
                     f"[테스트 출력 끝부분]\n{test_log[-1500:]}\n[DIFF]\n{diff}\n{REVIEW_FORMAT}")
    with tempfile.TemporaryDirectory(prefix="mini-triad-review-") as empty:  # 작업본 밖 빈 폴더
        code, out = call_cli(reviewer, review_prompt, empty, timeout)
    v, why = parse_verdict(out) if code == 0 else ("FAIL", [f"검수 CLI 종료 코드 {code}"])
    if not step("REVIEWER", v == "PASS", why or "PASS"):
        return finish("FAIL")

    git(wt, "-c", "user.name=mini-triad", "-c", "user.email=mini-triad@localhost",
        "commit", "-q", "-m", f"mini-triad {run_id}: {order['goal'][:60]}")
    step("작업본 커밋", True, f"브랜치 {branch} — 원본 반영은 사람이: git merge {branch}")
    return finish("PASS")


def main(argv=None):
    ap = argparse.ArgumentParser(description="지휘·구현·검수 최소 오케스트레이터")
    ap.add_argument("--project", required=True)
    ap.add_argument("--order", required=True, help='ORDER JSON 파일: {"goal", "allowed_paths", "max_files"}')
    ap.add_argument("--builder", required=True, help="BUILDER 명령(JSON 배열)")
    ap.add_argument("--reviewer", required=True, help="REVIEWER 명령(JSON 배열)")
    ap.add_argument("--test", required=True, help="검증 명령")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args(argv)
    order = json.loads(Path(a.order).read_text(encoding="utf-8"))
    if not order.get("goal") or not order.get("allowed_paths"):
        print("[중단] ORDER에 goal과 allowed_paths가 필요합니다.")
        return 1
    rep = run(a.project, order, json.loads(a.builder), json.loads(a.reviewer), a.test, a.timeout)
    print(f"최종 판정: {rep['verdict']}  보고서: {rep['report_file']}")
    return 0 if rep["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
