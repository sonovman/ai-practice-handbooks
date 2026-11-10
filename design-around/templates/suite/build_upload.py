#!/usr/bin/env python3
"""다섯 스킬을 플랫폼별 업로드 묶음으로 만든다 (핸드북 32 통합 키트). 표준 라이브러리만.

  dist/<이름>.zip       폴더가 ZIP 최상위 (Claude·ChatGPT)
  dist/<이름>-flat.zip  SKILL.md가 ZIP 최상위 (Copilot 등)
  dist/<이름>/          펼친 폴더 (Gemini)

  python build_upload.py
"""
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"
SKILLS = {
    "claim-suite": ["suite_status.py", "claim_parse.py", "chart_lint.py", "render_chart.py",
                    "construe_check.py", "apply_to_ledger.py", "design_around_eval.py"],
    "claim-decompose": ["claim_parse.py"],
    "claim-chart": ["chart_lint.py", "render_chart.py"],
    "claim-construe": ["construe_check.py", "apply_to_ledger.py"],
    "design-around": ["design_around_eval.py"],
}


def collect(name, tools):
    src = HERE / ".agents" / "skills" / name
    files = {p.relative_to(src).as_posix(): p for p in sorted(src.rglob("*")) if p.is_file()}
    for t in tools:
        f = HERE / "tools" / t
        if f.exists():
            files["tools/" + t] = f
    if name == "claim-suite":
        files["PROJECT_INSTRUCTIONS.md"] = HERE / "PROJECT_INSTRUCTIONS.md"
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
    for f in sorted(DIST.glob("*.zip")):
        print("  -", f.name)


if __name__ == "__main__":
    main()
