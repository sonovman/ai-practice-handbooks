#!/usr/bin/env python3
"""업로드 전 비밀정보·민감 파일 사전 점검 (핸드북 22). 표준 라이브러리만 사용.

깃허브에 올리기 '전에' 폴더를 훑어, 올라가면 안 되는 것을 미리 잡습니다.
  1) 소스·설정 파일 속 비밀로 보이는 값(API 키, 비밀번호, 개인키)
  2) 올리면 안 되는 민감 파일(.env, *.pem, id_rsa, credentials.json 등)
  3) 그 민감 파일이 .gitignore로 제외되어 있는지

  python tools/secret_scan.py                 # 현재 폴더
  python tools/secret_scan.py <폴더> --report work/secret.md
  python tools/secret_scan.py <폴더> --suggest-gitignore   # 추천 .gitignore 항목 출력

판정  FAIL 추적 대상에 비밀/민감 파일 → 올리기 전 반드시 조치
      WARN 민감해 보이나 .gitignore로 제외됨(값 자체는 폐기·회전 권장) 등
종료 코드 0(이상 없음) / 1(경고) / 2(실패)

주의: 값이 가려져(앞 몇 자만) 출력됩니다. 이 도구는 '사전 차단' 보조이며, 이미 올라간 이력은
      별도 조치가 필요합니다(폐기·재발급 + git filter-repo 등). 100% 탐지를 보장하지 않습니다.
"""
import argparse
import re
import sys
from pathlib import Path

# 높은 신뢰도의 비밀 패턴(이름 → 정규식). 값은 가려서 보고.
SECRET_PATTERNS = [
    ("OpenAI 키", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}")),
    ("Anthropic 키", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("AWS 액세스 키", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API 키", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("GitHub 토큰", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("Slack 토큰", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("개인키(PEM)", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("비밀번호·키 대입", re.compile(r"(?i)['\"]?(?:password|passwd|secret|api[_-]?key|access[_-]?token)['\"]?\s*[:=]\s*['\"][^'\"\n]{6,}['\"]")),
    ("DB 접속 문자열", re.compile(r"(?i)(?:postgres|postgresql|mysql|mongodb(?:\+srv)?|redis)://[^\s'\"<>]+:[^\s'\"<>]+@")),
]
# 올리면 안 되는 민감 파일 이름/패턴
RISKY_FILES = [
    ".env", ".env.local", ".env.development", ".env.production",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
    "credentials.json", "secrets.json", "service-account.json", "serviceaccount.json",
    ".npmrc", ".pypirc", ".netrc",
]
RISKY_SUFFIX = (".pem", ".key", ".pfx", ".p12", ".keystore", ".jks", ".ppk")
# 검사에서 제외할 폴더/확장자(잡음·바이너리)
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", ".cache"}
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".mp4",
               ".mp3", ".woff", ".woff2", ".ttf", ".so", ".dll", ".exe", ".bin", ".lock"}
MAX_BYTES = 1_000_000
RECOMMENDED_GITIGNORE = [
    "# 비밀·환경 (절대 올리지 않기)", ".env", ".env.*", "!.env.example",
    "*.pem", "*.key", "*.pfx", "*.p12", "id_rsa", "credentials.json", "secrets.json",
    ".npmrc", ".pypirc", ".netrc",
    "", "# 의존성·빌드·캐시", "node_modules/", ".venv/", "venv/", "__pycache__/", "*.pyc",
    "dist/", "build/", ".next/", ".cache/",
    "", "# OS·에디터", ".DS_Store", "Thumbs.db", ".idea/", ".vscode/",
]


def redact(s):
    s = s.strip().strip("'\"")
    return (s[:6] + "…" + s[-2:]) if len(s) > 10 else (s[:2] + "…")


def load_gitignore(root):
    """아주 단순한 .gitignore 매칭용 규칙 목록(완전하지 않음, 참고용)."""
    p = root / ".gitignore"
    rules = []
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                rules.append(line.rstrip("/"))
    return rules


def is_ignored(relpath, name, rules):
    """relpath(posix), 파일명으로 간단 매칭: 정확 이름, *.ext, 디렉터리 조각."""
    for r in rules:
        if r.startswith("!"):
            continue
        if r == name or r == relpath:
            return True
        if r.startswith("*.") and name.endswith(r[1:]):
            return True
        if r.startswith(".env") and name.startswith(".env"):
            return True
        if "/" in r and (relpath == r or relpath.startswith(r + "/") or ("/" + r + "/") in ("/" + relpath)):
            return True
        if r and ("/" + r + "/") in ("/" + relpath + "/"):
            return True
    return False


def iter_files(root):
    for p in sorted(root.rglob("*")):
        if p.is_dir():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts[:-1]):
            continue
        yield p


def scan(root):
    root = Path(root).resolve()
    rules = load_gitignore(root)
    items = []

    def add(level, kind, path, detail):
        items.append({"level": level, "kind": kind, "path": path, "detail": detail})

    for p in iter_files(root):
        rel = p.relative_to(root).as_posix()
        name = p.name
        ignored = name == ".git" or is_ignored(rel, name, rules) or (".git/" in rel + "/")

        # 1) 민감 파일 이름
        risky = name in RISKY_FILES or p.suffix.lower() in RISKY_SUFFIX
        if risky and name != ".env.example":
            if ignored:
                add("WARN", "민감 파일(.gitignore로 제외됨)", rel, "제외돼 있지만 값 자체는 노출 위험이 없는지 확인")
            else:
                add("FAIL", "민감 파일(추적 대상)", rel, ".gitignore에 추가하거나 폴더 밖으로 옮기세요")

        # 2) 파일 내용의 비밀 패턴
        if p.suffix.lower() in SKIP_SUFFIX:
            continue
        try:
            if p.stat().st_size > MAX_BYTES:
                continue
            text = p.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue
        for label, rx in SECRET_PATTERNS:
            m = rx.search(text)
            if m:
                lvl = "WARN" if ignored else "FAIL"
                tail = " (단, .gitignore로 제외됨 — 값은 폐기·회전 권장)" if ignored else ""
                add(lvl, "비밀로 보이는 값: " + label, rel, "'{}'{}".format(redact(m.group(0)), tail))

    status = "FAIL" if any(i["level"] == "FAIL" for i in items) else "WARN" if items else "OK"
    return {"status": status, "items": items, "root": str(root)}


def to_markdown(res):
    mark = {"OK": "이상 없음", "WARN": "확인 필요", "FAIL": "올리기 전 조치"}
    lines = ["# 업로드 전 비밀정보 점검", "", "- 대상: `{}`".format(res["root"]),
             "- 판정: **{}**".format(mark[res["status"]]), ""]
    if res["items"]:
        lines += ["| 판정 | 항목 | 경로 | 조치 |", "|---|---|---|---|"]
        lab = {"OK": "통과", "WARN": "경고", "FAIL": "실패"}
        for i in res["items"]:
            lines.append("| {} | {} | `{}` | {} |".format(lab[i["level"]], i["kind"], i["path"], i["detail"]))
    else:
        lines.append("비밀로 보이는 값이나 민감 파일을 찾지 못했습니다. 그래도 눈으로 한 번 더 확인하세요.")
    lines += ["", "> 이 도구는 사전 차단 보조이며 100% 탐지를 보장하지 않습니다. 이미 올라간 비밀은 즉시 폐기·재발급하고,",
              "> 커밋 이력에서 제거하려면 git filter-repo 등 별도 조치가 필요합니다(본문 참고)."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="업로드 전 비밀정보·민감 파일 점검")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--report")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--suggest-gitignore", action="store_true", help="추천 .gitignore 항목 출력")
    a = ap.parse_args(argv)
    if a.suggest_gitignore:
        sys.stdout.write("\n".join(RECOMMENDED_GITIGNORE) + "\n")
        return 0
    res = scan(a.path)
    if a.json:
        import json
        sys.stdout.write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    else:
        md = to_markdown(res)
        sys.stdout.write(md)
        if a.report:
            Path(a.report).parent.mkdir(parents=True, exist_ok=True)
            Path(a.report).write_text(md, encoding="utf-8")
    return {"OK": 0, "WARN": 1, "FAIL": 2}[res["status"]]


if __name__ == "__main__":
    sys.exit(main())
