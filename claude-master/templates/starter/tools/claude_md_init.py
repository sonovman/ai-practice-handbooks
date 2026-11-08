#!/usr/bin/env python3
"""CLAUDE.md 길잡이 초안 만들기 (핸드북 23). 표준 라이브러리만 사용.

폴더를 훑어, 내 작업 폴더의 '안내 책자(CLAUDE.md)' 초안과 폴더 색인(index)을 만들어 줍니다.
SSR Plus의 'Second Brain(세컨드 브레인)' 단계를 손으로 짜지 않고 자동 초안으로 시작하기 위한 도구입니다.

  python tools/claude_md_init.py <폴더>                 # 화면으로 미리보기
  python tools/claude_md_init.py <폴더> --write         # <폴더>/CLAUDE.md, <폴더>/INDEX.md 생성(덮어쓰기 안 함)
  python tools/claude_md_init.py <폴더> --write --force  # 있으면 덮어쓰기
  python tools/claude_md_init.py <폴더> --name "특허 리서치" --max-depth 2

왜 자동 초안인가(초기 접근 → 개선):
  처음엔 CLAUDE.md에 모든 규칙·자료를 다 적는 경우가 많습니다. 그러면 파일이 수백 줄로 비대해지고,
  CLAUDE.md는 '강제 명령'이 아니라 '참고 맥락'으로 작동하기 때문에 핵심 지침이 묻혀 무시됩니다.
  그래서 이 도구는 CLAUDE.md를 150~200줄 안쪽의 '안내 책자(색인)'로 유지하고,
  자세한 내용은 INDEX.md나 세부 문서로 넘기도록 초안을 잡아 줍니다. 생성 후 ✏️ 자리를 직접 채우세요.

주의: 폴더의 '구조'만 읽어 색인을 만듭니다. 파일 '내용'은 읽지 않으므로 비밀정보가 새어 나가지 않습니다.
      생성물은 초안입니다. 규칙·완료 기준 같은 판단이 필요한 칸은 사람이 채워야 합니다.
"""
import argparse
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist",
             "build", ".next", ".cache", ".idea", ".vscode", "work"}
# 프로젝트 성격 추정용 표지 파일(있으면 해당 작업 흐름을 안내에 반영)
MARKERS = {
    "package.json": "자바스크립트/노드",
    "pyproject.toml": "파이썬",
    "requirements.txt": "파이썬",
    "pom.xml": "자바(Maven)",
    "Cargo.toml": "러스트",
    "go.mod": "Go",
    "index.html": "웹 페이지",
    "catalog.js": "핸드북 저장소",
}
LINE_BUDGET = 200  # 안내 책자 권장 상한(줄). 넘길 것 같으면 경고.


def walk(root, max_depth):
    """상대경로(posix) 목록을 depth 제한으로 수집. SKIP_DIRS 제외."""
    root = Path(root)
    dirs, files = [], []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        parts = rel.parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        if len(parts) > max_depth:
            continue
        if p.is_dir():
            dirs.append(rel.as_posix())
        else:
            files.append(rel.as_posix())
    return dirs, files


def detect_kind(root):
    root = Path(root)
    found = []
    for name, label in MARKERS.items():
        if (root / name).exists() or list(root.rglob(name))[:1]:
            found.append(label)
    # 중복 제거(순서 유지)
    seen, out = set(), []
    for f in found:
        if f not in seen:
            seen.add(f); out.append(f)
    return out


def top_level_dirs(dirs):
    return [d for d in dirs if "/" not in d]


def build_index(root, name, dirs, files):
    tops = top_level_dirs(dirs)
    lines = ["# {} — 폴더 색인(INDEX)".format(name), "",
             "> CLAUDE.md가 가리키는 '자세한 지도'입니다. 각 폴더가 무슨 일을 하는지 한 줄로 적어 두세요.",
             ""]
    if tops:
        lines.append("## 폴더")
        for d in tops:
            lines.append("- `{}/` — ✏️ 이 폴더의 역할 한 줄".format(d))
        lines.append("")
    # 최상위 파일 몇 개만 안내
    top_files = [f for f in files if "/" not in f][:12]
    if top_files:
        lines.append("## 최상위 파일")
        for f in top_files:
            lines.append("- `{}` — ✏️ 설명".format(f))
        lines.append("")
    lines += ["## 자주 쓰는 명령·링크",
              "- ✏️ 예: `python tools/...` / 자주 여는 문서 링크", ""]
    return "\n".join(lines) + "\n"


def build_claude_md(root, name, dirs, files, kinds):
    tops = top_level_dirs(dirs)
    kind_line = ", ".join(kinds) if kinds else "✏️ (일반 작업 폴더)"
    L = []
    a = L.append
    a("# {}".format(name))
    a("")
    a("> 이 파일은 Claude에게 주는 '안내 책자'입니다. 강제 명령이 아니라 참고 맥락으로 작동하니,")
    a("> 150~200줄 안쪽으로 짧게 유지하고 자세한 내용은 INDEX.md나 세부 문서로 넘기세요.")
    a("")
    a("## 1. 이 폴더는 무엇인가")
    a("- 성격(추정): {}".format(kind_line))
    a("- 목적: ✏️ 한두 문장으로. (예: 특허 사건 리서치 자료와 초안을 모으는 폴더)")
    a("- 읽는 사람: ✏️ 나 / 동료 / 의뢰인")
    a("")
    a("## 2. 항상 지킬 원칙")
    a("- ✏️ 예: 결과에는 근거(출처)를 함께 남긴다.")
    a("- ✏️ 예: 비밀정보·개인정보가 담긴 파일은 밖으로 올리지 않는다.")
    a("- ✏️ 예: 새 작업은 새 대화로 시작한다(책상 정리).")
    a("")
    a("## 3. 폴더 안내(자세한 지도는 INDEX.md)")
    if tops:
        for d in tops:
            a("- `{}/` — ✏️ 한 줄".format(d))
    else:
        a("- ✏️ (하위 폴더가 생기면 여기에 한 줄씩)")
    a("- 전체 색인: `INDEX.md`")
    a("")
    a("## 4. 작업 방식·완료 기준")
    a("- ✏️ 예: 코드를 고치면 반드시 테스트를 돌려 통과 증거를 남긴다.")
    a("- ✏️ 예: 길어진 대화는 /compact 로 줄이고, 주제가 바뀌면 /clear 한다.")
    a("")
    a("## 5. 참조(길잡이)")
    a("- `INDEX.md` — 폴더·파일 색인")
    a("- ✏️ 그 밖에 자주 참조할 문서 링크")
    a("")
    a("<!-- 생성: claude_md_init.py · 초안입니다. ✏️ 자리를 채우고, 길어지면 세부 문서로 쪼개세요. -->")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="CLAUDE.md 길잡이 초안 만들기")
    ap.add_argument("path", nargs="?", default=".", help="대상 폴더")
    ap.add_argument("--name", help="문서 제목(기본: 폴더 이름)")
    ap.add_argument("--max-depth", type=int, default=2, help="색인에 담을 폴더 깊이(기본 2)")
    ap.add_argument("--write", action="store_true", help="CLAUDE.md / INDEX.md 파일로 저장")
    ap.add_argument("--force", action="store_true", help="이미 있어도 덮어쓰기")
    a = ap.parse_args(argv)

    root = Path(a.path).resolve()
    if not root.is_dir():
        sys.exit("폴더가 아닙니다: {}".format(root))
    name = a.name or root.name
    dirs, files = walk(root, max(1, a.max_depth))
    kinds = detect_kind(root)

    claude_md = build_claude_md(root, name, dirs, files, kinds)
    index_md = build_index(root, name, dirs, files)

    n_lines = claude_md.count("\n")
    if n_lines > LINE_BUDGET:
        sys.stderr.write("주의: CLAUDE.md 초안이 {}줄입니다. {}줄 안쪽으로 줄이세요(세부는 INDEX.md로).\n"
                         .format(n_lines, LINE_BUDGET))

    if not a.write:
        sys.stdout.write("===== CLAUDE.md (미리보기) =====\n")
        sys.stdout.write(claude_md)
        sys.stdout.write("\n===== INDEX.md (미리보기) =====\n")
        sys.stdout.write(index_md)
        sys.stdout.write("\n(저장하려면 --write 를 붙이세요)\n")
        return 0

    wrote = []
    for fname, text in (("CLAUDE.md", claude_md), ("INDEX.md", index_md)):
        target = root / fname
        if target.exists() and not a.force:
            sys.stderr.write("건너뜀(이미 있음): {}  — 덮어쓰려면 --force\n".format(target))
            continue
        target.write_text(text, encoding="utf-8")
        wrote.append(target.name)
    if wrote:
        sys.stdout.write("생성: {} (폴더: {})\n".format(", ".join(wrote), root))
        sys.stdout.write("다음: ✏️ 표시를 채우고, 길어지면 세부 문서로 쪼개세요.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
