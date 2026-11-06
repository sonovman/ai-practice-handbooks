#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_setup.py — Claude Desktop에 Korean Law MCP가 제대로 등록됐는지 점검

하는 일
  1. 운영체제에 맞는 claude_desktop_config.json 위치를 찾습니다. (직접 경로를 줘도 됩니다)
  2. JSON 문법 오류(쉼표·괄호 누락)를 줄 번호와 함께 알려 줍니다.
  3. mcpServers 안에 korean-law 항목이 있는지, 방식(원격/로컬)이 무엇인지 봅니다.
  4. '본인의_인증키', 'honggildong' 같은 자리표시가 그대로 남았는지 봅니다.
  5. 공개 서버(mcp.gomdori.app)·mcp-remote를 거치는 설정이면 실패로 표시합니다.
  6. 'npx -y korean-law-mcp'처럼 실행할 때마다 최신판을 받는 설정이면 주의로 표시합니다.
  7. Node.js 20.19 이상이 설치됐는지 봅니다.

하지 않는 일
  - 인터넷에 접속하지 않습니다. 인증키가 유효한지, 서버가 응답하는지는
    Claude를 완전히 종료 후 다시 켜고 테스트 질문으로 확인합니다.
  - 설정 파일을 고치지 않습니다. 읽기만 합니다.

사용법
  python check_setup.py                 # 기본 위치의 설정 파일 점검
  python check_setup.py 설정파일.json   # 특정 파일 점검

필요한 것: Python 3.8 이상 (추가 설치 없음)
"""
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLACEHOLDERS = ["내사용자이름", "본인의_인증키", "본인_인증키", "본인키", "본인의인증키", "honggildong", "your_key", "YOUR_KEY", "내키", "<", "[suspicious"]
LOCAL_NODE = (20, 19, 0)

OK, WARN, FAIL = "통과", "주의", "실패"


def default_config_path():
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(base) / "Claude" / "claude_desktop_config.json"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def node_version():
    exe = shutil.which("node")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "-v"], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return None
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", out)
    return tuple(int(x) for x in m.groups()) if m else None


def fmt(v):
    return ".".join(str(x) for x in v)


def find_entry(servers):
    for name, cfg in servers.items():
        blob = json.dumps(cfg, ensure_ascii=False)
        if name == "korean-law" or "korean-law" in blob or "gomdori.app/law" in blob:
            return name, cfg
    return None, None


def check(path):
    rows = []
    add = lambda status, item, detail: rows.append((status, item, detail))

    if not path.exists():
        add(FAIL, "설정 파일", "파일이 없습니다: {}  → Claude Desktop을 한 번 실행하고 설정 > 개발자 > 설정 편집을 누르면 생깁니다.".format(path))
        return rows
    add(OK, "설정 파일", str(path))

    text = path.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        add(FAIL, "JSON 문법", "{}번째 줄 {}번째 칸 근처: {}  → 쉼표(,)·따옴표·중괄호를 확인하세요.".format(e.lineno, e.colno, e.msg))
        return rows
    add(OK, "JSON 문법", "오류 없음")

    servers = data.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        add(FAIL, "mcpServers", "\"mcpServers\": { ... } 묶음이 없습니다.")
        return rows
    name, cfg = find_entry(servers)
    if not cfg:
        add(FAIL, "korean-law 항목", "mcpServers 안에 korean-law 설정이 없습니다. (등록된 서버: {})".format(", ".join(servers) or "없음"))
        return rows
    add(OK, "korean-law 항목", "\"{}\" 로 등록됨 (MCP 서버 총 {}개)".format(name, len(servers)))

    blob = json.dumps(cfg, ensure_ascii=False)
    args = [str(a) for a in cfg.get("args", [])] if isinstance(cfg.get("args"), list) else []
    command = str(cfg.get("command", ""))
    need = LOCAL_NODE
    if "gomdori" in blob or "mcp-remote" in args or "url" in cfg:
        add(FAIL, "연결 방식", "공개 서버(개인 운영)를 거치는 설정입니다. 이 가이드는 내 컴퓨터에서 법제처로 바로 연결하는 로컬 설치만 씁니다.")
    elif command == "npx":
        add(WARN, "연결 방식", "로컬 실행이지만 'npx -y'는 실행할 때마다 npm의 최신판을 받습니다. 검증한 버전을 고정 설치하고 command를 korean-law-mcp(또는 node + 경로)로 바꾸길 권합니다.")
    elif "korean-law-mcp" in command or any("korean-law-mcp" in a for a in args):
        add(OK, "연결 방식", "로컬 설치 (내 컴퓨터 → 법제처 직접)")
    else:
        add(WARN, "연결 방식", "알 수 없는 형식입니다. 예시 설정과 비교하세요.")

    left = [p for p in PLACEHOLDERS if p in blob]
    env = cfg.get("env", {}) if isinstance(cfg.get("env"), dict) else {}
    if left:
        add(FAIL, "인증키", "자리표시가 그대로 남았습니다({}). 법제처에서 받은 본인 인증키(OC)로 바꾸세요.".format(", ".join(left)))
    elif env.get("LAW_OC"):
        add(OK, "인증키", "env LAW_OC 에 설정됨")
    else:
        add(FAIL, "인증키", "env 에 LAW_OC 가 없습니다. 로컬 설치는 본인 인증키가 꼭 필요합니다.")

    for a in args:
        if a.endswith(".js") and not Path(a).exists():
            add(FAIL, "실행 파일", "args의 경로에 파일이 없습니다: {}  → npm root -g 로 설치 위치를 확인하세요.".format(a))

    v = node_version()
    if v is None:
        add(FAIL, "Node.js", "node 명령을 찾지 못했습니다. nodejs.org 에서 LTS 버전을 설치하세요.")
    elif v < need:
        add(FAIL, "Node.js", "현재 {} — {} 이상이 필요합니다.".format(fmt(v), fmt(need)))
    else:
        add(OK, "Node.js", "{} (필요 {} 이상)".format(fmt(v), fmt(need)))
    return rows


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    path = Path(argv[0]) if argv else default_config_path()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    rows = check(path)
    print("Korean Law MCP 설정 점검\n")
    for status, item, detail in rows:
        print("[{}] {:<14} {}".format(status, item, detail))
    fails = sum(1 for r in rows if r[0] == FAIL)
    print()
    if fails:
        print("실패 {}건 — 위 안내대로 고친 뒤 다시 실행하세요.".format(fails))
    else:
        print("설정은 이상 없습니다. Claude Desktop을 '완전히 종료'(트레이 아이콘 우클릭 → Quit) 후 다시 켜고 테스트 질문을 던지세요.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
