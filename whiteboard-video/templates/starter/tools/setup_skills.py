#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_skills.py — srt-whiteboard-animation 스킬을 이 프로젝트의 .agents/skills/ 에 설치하고 한국어로 쓰게 고친다

하는 일
  1. https://github.com/geeklee/srt-whiteboard-animation 을 .agents/skills/srt-whiteboard-animation 으로 받기(git 필요)
     (이미 받은 폴더가 있으면 --source 로 지정)
  2. SKILL.md의 '모든 안내를 중국어로' 지시를 '사용자의 언어로'로 바꾸기 (MIT 라이선스, 원본은 SKILL.md.orig로 보관)
  3. HyperFrames 스킬 설치 명령 안내 (대화형이라 직접 실행)

사용법:  python tools/setup_skills.py [--source 받은폴더] [--dry-run]
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = "https://github.com/geeklee/srt-whiteboard-animation"
ZH = "所有面向用户的说明、分镜、配置和界面文字必须使用中文。"
FIX = "所有面向用户的说明、分镜、配置和界面文字使用用户所用的语言（用户使用韩语时一律用韩语）。"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="이미 받아 둔 srt-whiteboard-animation 폴더")
    ap.add_argument("--project", default=".")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    dest = Path(a.project) / ".agents" / "skills" / "srt-whiteboard-animation"
    if dest.exists():
        print("이미 있음: " + str(dest))
    elif a.dry_run:
        print("받을 예정: {} → {}".format(a.source or REPO, dest))
        return 0
    elif a.source:
        shutil.copytree(a.source, dest, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"))
        print("복사: {} → {}".format(a.source, dest))
    else:
        if not shutil.which("git"):
            print("git이 없습니다. GitHub에서 ZIP으로 받아 압축을 푼 뒤 --source 로 지정하세요: " + REPO)
            return 2
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", REPO, str(dest)], check=True)
    skill = dest / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    if ZH in text:
        if not a.dry_run:
            (dest / "SKILL.md.orig").write_text(text, encoding="utf-8")
            skill.write_text(text.replace(ZH, FIX), encoding="utf-8")
        print("SKILL.md: 중국어 전용 지시 → 사용자 언어 (원본 SKILL.md.orig)")
    else:
        print("SKILL.md: 바꿀 문장이 없음(이미 고쳤거나 원본이 바뀜) — 내용을 직접 확인하세요")
    print("\n다음(직접 실행):")
    print("  python {}/scripts/prepare_env.py --check   # 그리기 렌더러 환경".format(dest.as_posix()))
    print("  npx skills add heygen-com/hyperframes      # 선택: Core Skills + Antigravity 선택")
    return 0


if __name__ == "__main__":
    sys.exit(main())
