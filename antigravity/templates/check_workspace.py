#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_workspace.py — Antigravity 작업 폴더의 규칙·스킬·MCP 설정을 올리기 전에 점검 (핸드북 16편)

점검하는 것
  규칙   AGENTS.md / GEMINI.md, .agents/rules/*.md — trigger 값, glob이면 globs, model_decision이면 description,
         파일 크기(24,000바이트 넘으면 잘림)
  스킬   .agents/skills/<폴더>/SKILL.md — description 필수, name은 소문자·하이픈이고 폴더 이름과 같게
  MCP    mcp_config.json(작업 폴더 .agents/ 또는 지정 파일) — JSON 문법, 서버마다 command 또는 serverUrl,
         옛 필드 httpUrl, 상대 경로 실행 파일, 비밀값 직접 기록
  권한   permissions(allow/ask/deny) — 위험한 allow(command(*), sudo, rm), .ssh 보호 누락

사용법
  python check_workspace.py 작업폴더
  python check_workspace.py 작업폴더 --mcp ~/.gemini/config/mcp_config.json --permissions settings.json

필요한 것: Python 3.8 이상 (추가 설치 없음). 경로·형식은 2026-11 Antigravity 공식 문서 기준입니다.
"""
import argparse
import json
import re
import sys
from pathlib import Path

TRIGGERS = {"always_on", "model_decision", "glob", "manual"}
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SECRET = re.compile(r"(api[_-]?key|token|secret|password|authorization)", re.I)
SECRET_VALUE = re.compile(r"^(sk-|ghp_|AIza|xox[bp]-|Bearer\s+\S{12,})")
MAX_RULE_BYTES = 24000


def frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip("'\"")
    return meta, text[m.end():]


def check_rules(root, add):
    for name in ("AGENTS.md", "GEMINI.md"):
        f = root / name
        if f.exists():
            size = f.stat().st_size
            add("주의" if size > 6000 else "통과", "규칙", "{} — 항상 적용, {:,}바이트{}".format(
                name, size, " · 매 턴 들어가므로 짧게(전역+always_on 합계 2만 토큰 예산)" if size > 6000 else ""))
    rdir = root / ".agents" / "rules"
    if not rdir.exists() and (root / ".agent" / "rules").exists():
        rdir = root / ".agent" / "rules"
        add("주의", "규칙", "옛 폴더 .agent/rules 사용 중 — 새 기본값은 .agents/rules")
    for f in sorted(rdir.glob("*.md")) if rdir.exists() else []:
        text = f.read_text(encoding="utf-8")
        meta, body = frontmatter(text)
        size = len(text.encode("utf-8"))
        if size > MAX_RULE_BYTES:
            add("실패", "규칙", "{} — {:,}바이트, 24,000바이트를 넘는 부분은 잘립니다.".format(f.name, size))
        if meta is None:
            add("실패", "규칙", "{} — rules 폴더의 파일은 trigger가 있는 frontmatter가 필요합니다.".format(f.name))
            continue
        t = meta.get("trigger", "")
        if t not in TRIGGERS:
            add("실패", "규칙", "{} — trigger '{}' (가능: {})".format(f.name, t, ", ".join(sorted(TRIGGERS))))
        elif t == "glob" and not meta.get("globs"):
            add("실패", "규칙", "{} — trigger: glob인데 globs가 없습니다.".format(f.name))
        elif t == "model_decision" and not meta.get("description"):
            add("실패", "규칙", "{} — model_decision은 description을 보고 불러오므로 description이 필요합니다.".format(f.name))
        else:
            add("통과", "규칙", "{} — {}{}".format(f.name, t, " ({})".format(meta.get("globs")) if t == "glob" else ""))
        if not body.strip():
            add("주의", "규칙", "{} — 본문이 비어 있습니다.".format(f.name))


def check_skills(root, add):
    sdir = root / ".agents" / "skills"
    if not sdir.exists():
        add("정보", "스킬", ".agents/skills 없음")
        return
    for d in sorted(p for p in sdir.iterdir() if p.is_dir()):
        f = d / "SKILL.md"
        if not f.exists():
            add("실패", "스킬", "{}/ — SKILL.md가 없습니다.".format(d.name))
            continue
        meta, body = frontmatter(f.read_text(encoding="utf-8"))
        if not meta or not meta.get("description"):
            add("실패", "스킬", "{} — description이 없습니다(에이전트가 언제 쓸지 판단하는 유일한 단서).".format(d.name))
            continue
        name = meta.get("name", d.name)
        if not NAME.match(name):
            add("실패", "스킬", "{} — name '{}'은 소문자·숫자·하이픈만".format(d.name, name))
        elif name != d.name:
            add("주의", "스킬", "{} — name '{}'이 폴더 이름과 다릅니다. /{}로 불릴 수 있습니다.".format(d.name, name, name))
        else:
            add("통과", "스킬", "/{} — description {}자".format(name, len(meta["description"])))
        if len(meta["description"]) < 30:
            add("주의", "스킬", "{} — description이 짧습니다. 무엇을 하고 언제 쓰는지 한두 문장으로.".format(d.name))


def rows_ref(add):
    return add.rows


def check_mcp(path, add):
    try:
        cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        add("실패", "MCP", "{} — JSON 문법 오류({}행). 주석(//)은 쓸 수 없습니다.".format(path, e.lineno))
        return
    servers = cfg.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        add("실패", "MCP", "{} — 최상위에 mcpServers 객체가 필요합니다.".format(path))
        return
    for name, s in servers.items():
        before = len(rows_ref(add))
        if "httpUrl" in s:
            add("실패", "MCP", "{} — httpUrl은 지원되지 않습니다. serverUrl(Streamable HTTP)을 쓰세요.".format(name))
        has_cmd, has_url = "command" in s, "serverUrl" in s
        if has_cmd == has_url:
            add("실패", "MCP", "{} — command(로컬) 또는 serverUrl(원격) 중 하나만 있어야 합니다.".format(name))
            continue
        if has_cmd:
            args = s.get("args", [])
            rel = [a for a in args if re.search(r"\.(js|py|mjs|ts)$", a) and not (a.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", a))]
            if rel:
                add("주의", "MCP", "{} — 상대 경로 {} : Antigravity는 다른 폴더에서 실행하므로 절대 경로로 쓰세요.".format(name, rel[0]))
            if "절대경로" in " ".join(args):
                add("실패", "MCP", "{} — 예시 경로('/절대경로/…')를 실제 경로로 바꾸세요.".format(name))
        else:
            if not s["serverUrl"].startswith("https://") and "localhost" not in s["serverUrl"]:
                add("주의", "MCP", "{} — https가 아닌 원격 주소입니다.".format(name))
        leaked = []
        for k, v in list(s.get("env", {}).items()) + list(s.get("headers", {}).items()):
            if SECRET.search(k) and isinstance(v, str) and v and not v.startswith("${") and (SECRET_VALUE.match(v) or len(v) >= 16):
                leaked.append(k)
        if leaked:
            add("주의", "MCP", "{} — {}에 비밀값이 그대로 적혀 있습니다. 파일 권한을 잠그고 저장소에 올리지 마세요.".format(name, ", ".join(leaked)))
        if s.get("disabled"):
            add("정보", "MCP", "{} — 꺼짐(disabled)".format(name))
        elif not leaked and not any(r[0] == "실패" and r[2].startswith(name + " ") for r in rows_ref(add)[before:]):
            add("통과", "MCP", "{} — {}".format(name, "로컬 " + s["command"] if has_cmd else "원격 " + s["serverUrl"]))


def check_permissions(path, add):
    try:
        cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        add("실패", "권한", "{} — JSON 문법 오류({}행)".format(path, e.lineno))
        return
    p = cfg.get("permissions", cfg)
    allow, deny = p.get("allow", []), p.get("deny", [])
    risky = [r for r in allow if r in ("command(*)", "write_file(/)", "mcp(*)", "execute_url(*)") or re.match(r"command\((sudo|rm)\b", r)]
    for r in risky:
        add("실패", "권한", "allow에 {} — 모든(또는 파괴적) 동작을 묻지 않고 허용합니다.".format(r))
    if not any(".ssh" in r for r in deny):
        add("주의", "권한", "deny에 ~/.ssh 보호가 없습니다(예: write_file(~/.ssh), read_file(~/.ssh)).")
    if not any(r.startswith("command(sudo") for r in deny):
        add("주의", "권한", "deny에 command(sudo)가 없습니다.")
    if not risky:
        add("통과", "권한", "allow {}개 · ask {}개 · deny {}개 (우선순위 Deny > Ask > Allow)".format(len(allow), len(p.get("ask", [])), len(deny)))
    if json.dumps(cfg).find("always-proceed") >= 0 or json.dumps(cfg).lower().find("turbo") >= 0:
        add("주의", "권한", "always-proceed / Turbo — 모든 명령을 제한 없이 실행합니다. 격리된 환경에서만 쓰세요.")


def check(root, mcp=None, permissions=None):
    rows = []

    def add(level, area, detail):
        rows.append((level, area, detail))
    add.rows = rows
    root = Path(root)
    check_rules(root, add)
    check_skills(root, add)
    mcp_path = mcp or (root / ".agents" / "mcp_config.json")
    if Path(mcp_path).exists():
        check_mcp(mcp_path, add)
    else:
        add("정보", "MCP", "작업 폴더 MCP 설정 없음(전역 ~/.gemini/config/mcp_config.json은 --mcp로 점검)")
    if permissions:
        check_permissions(permissions, add)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Antigravity 작업 폴더 점검")
    ap.add_argument("root")
    ap.add_argument("--mcp")
    ap.add_argument("--permissions")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    rows = check(a.root, a.mcp, a.permissions)
    print("Antigravity 작업 폴더 점검 — {}\n".format(a.root))
    for level, area, detail in rows:
        print("[{}] {:<4} {}".format(level, area, detail))
    fails = sum(1 for r in rows if r[0] == "실패")
    warns = sum(1 for r in rows if r[0] == "주의")
    print("\n실패 {}건 · 주의 {}건".format(fails, warns))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
