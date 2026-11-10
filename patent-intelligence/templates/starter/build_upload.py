#!/usr/bin/env python3
"""patent-intelligence 스킬을 플랫폼별 업로드 묶음으로 만든다 (핸드북 34). 표준 라이브러리만.

  dist/patent-intelligence.zip       폴더가 ZIP 최상위 (Claude·ChatGPT·Copilot Cowork)
  dist/patent-intelligence-flat.zip  SKILL.md가 ZIP 최상위
  dist/patent-intelligence/          펼친 폴더 (Gemini 업로드·내용 보기)

  python build_upload.py
"""
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"
NAME = "patent-intelligence"
TOOLS = ["pi_common.py", "pi_intake.py", "pi_stats.py", "pi_gate.py", "report_lint.py",
         "render_report.py", "export_for_copilot.py", "make_sample.py", "test_pi_tools.py"]
CONFIG = ["column_aliases.csv", "applicant_aliases.csv", "project.json"]


def collect():
    src = HERE / ".agents" / "skills" / NAME
    files = {p.relative_to(src).as_posix(): p for p in sorted(src.rglob("*")) if p.is_file()}
    for t in TOOLS:
        files["tools/" + t] = HERE / "tools" / t
    for c in CONFIG:
        files["config/" + c] = HERE / "config" / c
    files["PROJECT_INSTRUCTIONS.md"] = HERE / "PROJECT_INSTRUCTIONS.md"
    files["COPILOT_AGENT_INSTRUCTIONS.md"] = HERE / "COPILOT_AGENT_INSTRUCTIONS.md"
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
        if f.is_file() and f.parent == DIST:
            print("  -", f.name)


if __name__ == "__main__":
    main()
