#!/usr/bin/env python3
"""AI DEV DIRECTOR 설치 전·첫 실행 전 사전 점검 (표준 라이브러리만 사용).

무엇을 보나
  1. Python 3.9 이상, git 설치 여부
  2. 세 CLI(claude / codex / agy) 중 몇 개가 PATH에 있는지 (최소 2개 필요)
  3. 종량제 과금으로 이어질 수 있는 환경 변수 (Director가 지우는 5개 밖의 것까지)
  4. config.yaml 의 위험 기본값 (auto_apply, head_proxy, solomon.allowed_roots)
  5. companion.json 의 허용 프로젝트 목록
  6. 대상 프로젝트에 '열기만 해도 실행되는' AI 설정 파일이 있는지
     (.claude/settings.json 훅, .mcp.json, .codex/, .gemini/, .vscode/tasks.json)

사용
  python director_preflight.py --director D:/tools/ai-dev-director --project D:/work/my_app
  python director_preflight.py --json ...      # 결과를 JSON으로

종료 코드: 0 = 통과(주의만 있음), 1 = 막아야 할 문제 있음
"""
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

# Director 원본(core/env_utils.py)이 지우는 키
DIRECTOR_STRIPS = {"OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
                   "GOOGLE_API_KEY", "AZURE_OPENAI_API_KEY"}
# 그 밖에 종량제·다른 결제 경로로 바뀔 수 있는 변수
BILLING_RISK_ENV = {
    "CODEX_API_KEY": "Codex가 구독 대신 API 키로 과금될 수 있음",
    "ANTHROPIC_AUTH_TOKEN": "Claude Code가 구독 대신 다른 인증으로 과금될 수 있음",
    "CLAUDE_CODE_USE_BEDROCK": "Claude Code가 AWS Bedrock(종량제)으로 호출됨",
    "CLAUDE_CODE_USE_VERTEX": "Claude Code가 Google Cloud(종량제)로 호출됨",
    "CLAUDE_CODE_USE_FOUNDRY": "Claude Code가 Microsoft Foundry(종량제)로 호출됨",
    "GOOGLE_GENAI_USE_VERTEXAI": "Google 계열 CLI가 Vertex AI(종량제)로 호출될 수 있음",
    "GOOGLE_CLOUD_PROJECT": "agy가 Cloud 프로젝트 과금으로 로그인돼 있을 수 있음(확인 필요)",
}
CLIS = ("claude", "codex", "agy")
# 열기만 해도(또는 테스트만 돌려도) 코드가 실행될 수 있는 프로젝트 파일
AUTO_EXEC_FILES = [".claude/settings.json", ".claude/settings.local.json", ".mcp.json",
                   ".codex/config.toml", ".gemini/settings.json", ".vscode/tasks.json",
                   "conftest.py"]


def _finding(level, code, msg):
    return {"level": level, "code": code, "message": msg}


def check_runtime(which=shutil.which, version=sys.version_info):
    out = []
    if tuple(version[:2]) < (3, 9):
        out.append(_finding("BLOCK", "PYTHON_OLD", f"Python {version[0]}.{version[1]} — 3.9 이상이 필요합니다."))
    else:
        out.append(_finding("OK", "PYTHON", f"Python {version[0]}.{version[1]}"))
    if not which("git"):
        out.append(_finding("BLOCK", "GIT_MISSING", "git이 없습니다. 격리 작업본(worktree)을 만들 수 없습니다."))
    else:
        out.append(_finding("OK", "GIT", "git 확인"))
    found = [c for c in CLIS if which(c)]
    if len(found) < 2:
        out.append(_finding("BLOCK", "CLI_TOO_FEW",
                            f"로그인된 CLI가 최소 2개 필요합니다. 찾은 것: {found or '없음'} (claude / codex / agy)"))
    else:
        out.append(_finding("OK", "CLI", f"찾은 CLI: {', '.join(found)}"))
    if len(found) == 2:
        out.append(_finding("WARN", "CLI_TWO_ONLY",
                            "CLI가 2개뿐이면 한 회사 모델이 두 역할을 맡게 되어 '독립성 낮음'이 될 수 있습니다."))
    return out


def check_env(env=None):
    env = os.environ if env is None else env
    out = []
    for k in sorted(DIRECTOR_STRIPS):
        if env.get(k):
            out.append(_finding("INFO", "KEY_STRIPPED", f"{k} 는 Director가 호출 직전에 지웁니다(문제 없음)."))
    for k, why in BILLING_RISK_ENV.items():
        if env.get(k):
            out.append(_finding("WARN", "BILLING_ENV", f"{k} 가 설정돼 있습니다 — {why}. Director는 이 변수를 지우지 않습니다."))
    return out


def _yaml_value(text, dotted):
    """아주 단순한 YAML 읽기: 'section:' 아래 들여쓴 'key: value' 하나를 찾는다(표준 라이브러리만)."""
    section, key = dotted.split(".")
    in_sec = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not raw.startswith((" ", "\t")):
            in_sec = line.strip() == f"{section}:"
            continue
        if in_sec:
            m = re.match(r"\s+" + re.escape(key) + r"\s*:\s*(.*)$", line)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    return None


def _yaml_list(text, dotted):
    section, key = dotted.split(".")
    items, in_sec, in_key = [], False, False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not raw.startswith((" ", "\t")):
            in_sec, in_key = line.strip() == f"{section}:", False
            continue
        if in_sec:
            if re.match(r"\s+" + re.escape(key) + r"\s*:", line):
                in_key = True
                continue
            m = re.match(r"\s+-\s*(.+)$", line)
            if in_key and m:
                items.append(m.group(1).strip().strip('"').strip("'"))
            elif in_key and re.match(r"\s+\w", line):
                in_key = False
    return items


def check_config(director_dir):
    out = []
    cfg = Path(director_dir) / "config.yaml"
    if not cfg.is_file():
        return [_finding("BLOCK", "CONFIG_MISSING", f"{cfg} 가 없습니다. Director 폴더 경로를 확인하세요.")]
    text = cfg.read_text(encoding="utf-8")
    auto_apply = _yaml_value(text, "autonomy.auto_apply")
    if auto_apply and auto_apply.lower() not in ("off", "on_done"):
        out.append(_finding("WARN", "AUTO_APPLY_ON",
                            f"autonomy.auto_apply = {auto_apply} — 처음 몇 번은 off 로 두고 결과를 직접 확인한 뒤 반영하세요."))
    if (_yaml_value(text, "autonomy.head_proxy") or "").lower() == "true":
        out.append(_finding("WARN", "HEAD_PROXY_ON",
                            "autonomy.head_proxy = true — HEAD가 사람 대신 결정합니다. 돈·자격증명·비가역 행동만 멈춥니다."))
    roots = _yaml_list(text, "solomon.allowed_roots")
    if roots:
        out.append(_finding("INFO", "SOLOMON_ROOTS", f"외부 발주(솔로몬) 허용 루트: {roots} — 쓰지 않으면 비워 두세요."))
    test_cmd = _yaml_value(text, "verification.test_command")
    if not test_cmd or test_cmd.lower() == "null":
        out.append(_finding("WARN", "NO_TEST_CMD", "verification.test_command 가 비어 있습니다. 실제 테스트 없이는 검증이 약해집니다."))
    comp = Path(director_dir) / "companion.json"
    if comp.is_file():
        try:
            data = json.loads(comp.read_text(encoding="utf-8"))
            if data.get("allowed_projects"):
                out.append(_finding("INFO", "BRIDGE_PROJECTS",
                                    f"브리지로 발주 가능한 프로젝트: {data['allowed_projects']}"))
        except (ValueError, OSError):
            out.append(_finding("WARN", "COMPANION_JSON", "companion.json 을 읽지 못했습니다."))
    if not out:
        out.append(_finding("OK", "CONFIG", "config.yaml 기본값 점검 완료"))
    return out


def check_project(project_dir):
    out = []
    root = Path(project_dir)
    if not root.is_dir():
        return [_finding("BLOCK", "PROJECT_MISSING", f"{root} 폴더가 없습니다.")]
    if not (root / ".git").exists():
        out.append(_finding("INFO", "NOT_GIT", "git 저장소가 아닙니다. Director가 빈 폴더처럼 자동 준비합니다(첫 커밋 생성)."))
    for rel in AUTO_EXEC_FILES:
        if (root / rel).is_file():
            out.append(_finding("WARN", "AUTO_EXEC_FILE",
                                f"{rel} 가 있습니다 — 비대화 CLI가 이 파일의 훅·서버를 확인 창 없이 실행할 수 있습니다. 내용을 먼저 읽어 보세요."))
    if (root / ".env").is_file():
        out.append(_finding("WARN", "DOTENV", ".env 가 있습니다 — 세 AI 모두 작업본을 읽을 수 있으니 실제 비밀값은 빼 두세요."))
    if not out:
        out.append(_finding("OK", "PROJECT", "프로젝트에 자동 실행 설정 파일 없음"))
    return out


def run(director=None, project=None, env=None, which=shutil.which):
    findings = check_runtime(which=which) + check_env(env)
    if director:
        findings += check_config(director)
    if project:
        findings += check_project(project)
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="AI DEV DIRECTOR 사전 점검")
    ap.add_argument("--director", help="ai-dev-director 폴더")
    ap.add_argument("--project", help="작업할 프로젝트 폴더")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    findings = run(a.director, a.project)
    if a.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        mark = {"OK": "[통과]", "INFO": "[참고]", "WARN": "[주의]", "BLOCK": "[중단]"}
        for f in findings:
            print(f"{mark[f['level']]} {f['message']}")
    return 1 if any(f["level"] == "BLOCK" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
