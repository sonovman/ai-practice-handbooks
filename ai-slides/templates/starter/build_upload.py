#!/usr/bin/env python3
"""slide-workshop 스킬을 플랫폼별 업로드 묶음으로 만든다 (핸드북 24). 표준 라이브러리만.

  dist/slide-workshop.zip       폴더가 ZIP 최상위 (Claude.ai·ChatGPT)
  dist/slide-workshop-flat.zip  SKILL.md가 ZIP 최상위 (Copilot)
  dist/slide-workshop/          펼친 폴더 (Gemini)

  python build_upload.py
"""
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_SRC = HERE / ".agents" / "skills" / "slide-workshop"
TOOLS_SRC = HERE / "tools"
DIST = HERE / "dist"
NAME = "slide-workshop"
TOOL_FILES = ["slide_lint.py", "deck_html.py"]


def collect():
    files = {}
    for p in sorted(SKILL_SRC.rglob("*")):
        if p.is_file():
            files[p.relative_to(SKILL_SRC).as_posix()] = p
    for t in TOOL_FILES:
        src = TOOLS_SRC / t
        if src.exists():
            files["tools/" + t] = src
    return files


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    files = collect()
    with zipfile.ZipFile(DIST / (NAME + ".zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for rel, src in files.items():
            z.write(src, NAME + "/" + rel)
    with zipfile.ZipFile(DIST / (NAME + "-flat.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for rel, src in files.items():
            z.write(src, rel)
    out = DIST / NAME
    for rel, src in files.items():
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print("생성:", DIST)
    for f in sorted(DIST.rglob("*")):
        if f.is_file():
            print("  -", f.relative_to(DIST).as_posix())


if __name__ == "__main__":
    main()
