#!/usr/bin/env python3
"""design-around 스킬을 플랫폼별 업로드 묶음으로 만든다 (핸드북 32). 표준 라이브러리만.

  dist/design-around.zip       폴더가 ZIP 최상위 (Claude.ai·ChatGPT)
  dist/design-around-flat.zip  SKILL.md가 ZIP 최상위 (Copilot 등)
  dist/design-around/          펼친 폴더 (Gemini)

  python build_upload.py
"""
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"
NAME = "design-around"
TOOLS = ["design_around_eval.py"]


def collect():
    src = HERE / ".agents" / "skills" / NAME
    files = {p.relative_to(src).as_posix(): p for p in sorted(src.rglob("*")) if p.is_file()}
    for t in TOOLS:
        f = HERE / "tools" / t
        if f.exists():
            files["tools/" + t] = f
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
    for rel, src in files.items():
        dst = DIST / NAME / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print("생성:", DIST)
    for f in sorted(DIST.rglob("*")):
        if f.is_file():
            print("  -", f.relative_to(DIST).as_posix())


if __name__ == "__main__":
    main()
