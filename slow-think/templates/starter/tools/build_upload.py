#!/usr/bin/env python3
"""웹 앱 업로드용 스킬 묶음 만들기 (핸드북 19).

  python tools/build_upload.py            # dist/ 에 스킬별 묶음 생성

스킬마다 세 가지를 만듭니다(스킬 이름 = 폴더 이름).
  <이름>.zip        ZIP 최상위가 <이름>/ 폴더   → Claude.ai(Customize → Skills), ChatGPT(Skills)
  <이름>-flat.zip   ZIP 최상위에 SKILL.md       → Microsoft 365 Copilot Cowork(Upload skill)
  <이름>/           압축하지 않은 폴더           → Gemini 앱(Skills 폴더 업로드)
ai-meeting 에는 역할 예시(roles/)와 루브릭(prompts/rubric.md)을 references/ 로 넣습니다.
"""
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ("ask-better", "slow-think", "ai-meeting", "paper-brief")
EXTRAS = {
    "ai-meeting": [("prompts/rubric.md", "references/rubric.md"),
                   ("roles/default.md", "references/roles-default.md"),
                   ("roles/patent.md", "references/roles-patent.md"),
                   ("roles/paper-review.md", "references/roles-paper-review.md")],
    "paper-brief": [("prompts/07-verify.md", "references/verify.md")],
    "slow-think": [("prompts/05-premortem.md", "references/premortem.md")],
}


def build(root, dist):
    dist.mkdir(parents=True, exist_ok=True)
    made = []
    for name in SKILLS:
        src = root / ".agents" / "skills" / name
        if not (src / "SKILL.md").is_file():
            raise SystemExit("스킬이 없습니다: " + str(src))
        folder = dist / name
        if folder.exists():
            shutil.rmtree(folder)
        shutil.copytree(src, folder)
        for rel, dst in EXTRAS.get(name, []):
            p = root / rel
            if p.is_file():
                (folder / dst).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, folder / dst)
        files = sorted(f for f in folder.rglob("*") if f.is_file())
        with zipfile.ZipFile(dist / (name + ".zip"), "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                z.write(f, name + "/" + f.relative_to(folder).as_posix())
        with zipfile.ZipFile(dist / (name + "-flat.zip"), "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                z.write(f, f.relative_to(folder).as_posix())
        made.append(name)
    return made


def main(argv=None):
    ap = argparse.ArgumentParser(description="웹 앱 업로드용 스킬 묶음 만들기")
    ap.add_argument("--out", default=str(ROOT / "dist"))
    a = ap.parse_args(argv)
    made = build(ROOT, Path(a.out))
    sys.stdout.write("만듦 ({}): {}\n".format(a.out, ", ".join(made)))
    sys.stdout.write("Claude.ai·ChatGPT → <이름>.zip · Copilot Cowork → <이름>-flat.zip · Gemini → <이름>/ 폴더\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
