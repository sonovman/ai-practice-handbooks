#!/usr/bin/env python3
"""두 스킬(claim-decompose, claim-chart)을 플랫폼별 업로드 묶음으로 만든다 (핸드북 30). 표준 라이브러리만.

  dist/<name>.zip       폴더가 ZIP 최상위 (Claude.ai·ChatGPT)
  dist/<name>-flat.zip  SKILL.md가 ZIP 최상위 (Copilot 등)
  dist/<name>/          펼친 폴더 (Gemini)

  python build_upload.py
"""
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"
SKILLS = {
    "claim-decompose": ["claim_parse.py"],
    "claim-chart": ["chart_lint.py", "render_chart.py"],
}


def collect(name, tools):
    src = HERE / ".agents" / "skills" / name
    files = {}
    for p in sorted(src.rglob("*")):
        if p.is_file():
            files[p.relative_to(src).as_posix()] = p
    for t in tools:
        f = HERE / "tools" / t
        if f.exists():
            files["tools/" + t] = f
    return files


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    for name, tools in SKILLS.items():
        files = collect(name, tools)
        with zipfile.ZipFile(DIST / (name + ".zip"), "w", zipfile.ZIP_DEFLATED) as z:
            for rel, src in files.items():
                z.write(src, name + "/" + rel)
        with zipfile.ZipFile(DIST / (name + "-flat.zip"), "w", zipfile.ZIP_DEFLATED) as z:
            for rel, src in files.items():
                z.write(src, rel)
        for rel, src in files.items():
            dst = DIST / name / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    print("생성:", DIST)
    for f in sorted(DIST.rglob("*")):
        if f.is_file():
            print("  -", f.relative_to(DIST).as_posix())


if __name__ == "__main__":
    main()
