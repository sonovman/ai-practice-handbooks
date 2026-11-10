#!/usr/bin/env python3
"""스킬을 웹 앱 업로드용 묶음 세 가지로 만든다(표준 라이브러리만).

  <name>.zip       폴더가 ZIP 최상위        → Claude(스킬 업로드), ChatGPT(폴더 업로드)용
  <name>-flat.zip  SKILL.md가 ZIP 최상위    → Microsoft 365 Copilot(Agent Builder)용
  <name>/          폴더 그대로              → Gemini(폴더 업로드)·Antigravity·Claude Code용

사용: python tools/build_upload.py [--skill .agents/skills/triad-dev-review] [--out ../upload]
"""
import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def validate(skill_dir):
    md = Path(skill_dir) / "SKILL.md"
    if not md.is_file():
        raise ValueError(f"{md} 가 없습니다")
    text = md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError("SKILL.md 첫 줄은 '---' 로 시작하는 frontmatter여야 합니다")
    meta = dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1), re.M))
    name, desc = meta.get("name", ""), meta.get("description", "")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        raise ValueError(f"name 형식 오류: {name!r} (소문자·숫자·하이픈, 64자 이하)")
    if name != Path(skill_dir).name:
        raise ValueError(f"name({name})과 폴더 이름({Path(skill_dir).name})이 달라요")
    if not desc or len(desc) > 200:
        raise ValueError(f"description은 1~200자여야 합니다(현재 {len(desc)}자)")
    if "<" in desc or ">" in desc:
        raise ValueError("description에 꺾쇠(<, >)를 쓰지 마세요")
    return name


def build(skill_dir, out_dir):
    skill_dir, out_dir = Path(skill_dir).resolve(), Path(out_dir).resolve()
    name = validate(skill_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in skill_dir.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    with zipfile.ZipFile(out_dir / f"{name}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, f"{name}/{p.relative_to(skill_dir).as_posix()}")
    with zipfile.ZipFile(out_dir / f"{name}-flat.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(skill_dir).as_posix())
    folder = out_dir / name
    if folder.exists():
        shutil.rmtree(folder)
    shutil.copytree(skill_dir, folder, ignore=shutil.ignore_patterns("__pycache__"))
    return [out_dir / f"{name}.zip", out_dir / f"{name}-flat.zip", folder]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", default=str(HERE.parent / ".agents" / "skills" / "triad-dev-review"))
    ap.add_argument("--out", default=str(HERE.parent.parent / "upload"))
    a = ap.parse_args(argv)
    try:
        for p in build(a.skill, a.out):
            print(f"만듦: {p}")
    except ValueError as e:
        print(f"[오류] {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
