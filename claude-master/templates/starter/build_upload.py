#!/usr/bin/env python3
"""claude-starter 스킬을 플랫폼별 업로드 묶음으로 만든다 (핸드북 23). 표준 라이브러리만.

세 가지 형태를 만든다.
  dist/claude-starter.zip       폴더가 ZIP 최상위 (Claude.ai·ChatGPT 등 '폴더째' 업로드용)
  dist/claude-starter-flat.zip  SKILL.md가 ZIP 최상위 (Copilot 등 '파일째' 업로드용)
  dist/claude-starter/          펼친 폴더 (Gemini 등 폴더 그대로 쓰는 경우)

  python build_upload.py
"""
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_SRC = HERE / ".agents" / "skills" / "claude-starter"
TOOLS_SRC = HERE / "tools"
DIST = HERE / "dist"
NAME = "claude-starter"
# 스킬과 함께 넣을 도구(스킬이 참조하는 스크립트들)
TOOL_FILES = ["claude_md_init.py", "skill_init.py"]


def collect():
    """{아카이브 내 상대경로: 원본 경로}"""
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

    # 1) 폴더가 최상위
    with zipfile.ZipFile(DIST / (NAME + ".zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for rel, src in files.items():
            z.write(src, NAME + "/" + rel)
    # 2) SKILL.md가 최상위(평평)
    with zipfile.ZipFile(DIST / (NAME + "-flat.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for rel, src in files.items():
            z.write(src, rel)
    # 3) 펼친 폴더
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
