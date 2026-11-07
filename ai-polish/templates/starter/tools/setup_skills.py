#!/usr/bin/env python3
"""윤문 스킬 설치 도우미 (핸드북 18).

두 공개 저장소에서 '스킬 파일만' 골라 작업 폴더의 스킬 위치로 복사합니다.
설치 스크립트(install.sh 등)는 실행하지 않습니다.

  한국어  epoko77-ai/im-not-ai  (MIT) → <대상>/humanize-korean/
  영어    blader/humanizer      (MIT) → <대상>/humanizer/

사용 예
  python tools/setup_skills.py                     # git으로 받아 .agents/skills/ 에 설치 (Antigravity·Codex)
  python tools/setup_skills.py --target claude     # .claude/skills/ 에 설치 (Claude Code)
  python tools/setup_skills.py --source-ko D:/zip/im-not-ai-main --source-en D:/zip/humanizer-main
                                                   # git 없이: GitHub에서 받은 ZIP을 푼 폴더 지정
  python tools/setup_skills.py --portable          # 웹 앱 업로드용 legal-polish.zip 만들기 (dist/)
"""
import argparse
import datetime
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPOS = {
    "ko": ("https://github.com/epoko77-ai/im-not-ai.git", "im-not-ai"),
    "en": ("https://github.com/blader/humanizer.git", "humanizer"),
}
# im-not-ai install.sh 의 RUNTIME_SCRIPTS 와 같은 목록(복사 설치용)
RUNTIME_SCRIPTS = (
    "prepare_monolith_input.py", "reassemble_chunks.py", "verify_change_rate.py",
    "verify_gates.py", "restore_modality.py", "strip_injected_commas.py", "sanitize_text.py",
    "checks.py", "console.py",
)
TARGETS = {"agents": ".agents/skills", "claude": ".claude/skills"}


def out(msg):
    sys.stdout.write(msg + "\n")


def clone(url, dest):
    if shutil.which("git") is None:
        sys.exit("git이 없습니다. GitHub에서 Code → Download ZIP으로 받아 압축을 푼 뒤 "
                 "--source-ko / --source-en 으로 폴더를 지정하세요.")
    subprocess.run(["git", "clone", "-q", "--depth", "1", url, str(dest)], check=True)
    rev = subprocess.run(["git", "-C", str(dest), "log", "-1", "--format=%h %cs"],
                         capture_output=True, text=True).stdout.strip()
    return rev or "unknown"


def resolve_dir(base, rel, fallback_rel):
    """심볼릭 링크가 Windows에서 '경로가 적힌 텍스트 파일'로 풀린 경우까지 처리."""
    p = base / rel
    if p.is_dir():
        return p
    alt = base / fallback_rel
    if alt.is_dir():
        return alt
    raise FileNotFoundError("{} 를 찾을 수 없습니다".format(p))


def copy_tree(src, dst):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=False,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def install_ko(repo, skills_dir, rev):
    """Codex용 자립형 스킬(스크립트 포함)을 쓰고, references 링크는 실제 폴더로 복사."""
    skill_src = repo / "codex" / "skills" / "humanize-korean"
    if not (skill_src / "SKILL.md").is_file():
        raise FileNotFoundError("im-not-ai 저장소 구조가 예상과 다릅니다: " + str(skill_src))
    dst = skills_dir / "humanize-korean"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    shutil.copy2(skill_src / "SKILL.md", dst / "SKILL.md")
    if (skill_src / "agents").is_dir():
        copy_tree(skill_src / "agents", dst / "agents")
    refs = resolve_dir(repo, "codex/skills/humanize-korean/references", "skills/humanize-korean/references")
    copy_tree(refs, dst / "references")
    # codex/skills/.../scripts 는 저장소 루트 scripts/ 를 부르는 '연결용' 파일이라
    # 복사본에서는 동작하지 않는다. 저장소의 --copy 설치와 같이 실제 스크립트를 넣는다.
    (dst / "scripts").mkdir()
    missing = []
    for f in RUNTIME_SCRIPTS:
        src = repo / "scripts" / f
        if src.is_file():
            shutil.copy2(src, dst / "scripts" / f)
        else:
            missing.append(f)
    if missing:
        out("주의: 저장소에 없는 스크립트 " + ", ".join(missing) + " — 저장소 구조가 바뀌었을 수 있습니다.")
    shutil.copy2(repo / "LICENSE", dst / "LICENSE")
    (dst / "SOURCE.txt").write_text(
        "출처: https://github.com/epoko77-ai/im-not-ai (MIT)\n원본 경로: codex/skills/humanize-korean\n"
        "받은 버전: {}\n설치일: {}\n".format(rev, datetime.date.today()), encoding="utf-8")
    return dst


def install_en(repo, skills_dir, rev):
    dst = skills_dir / "humanizer"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    shutil.copy2(repo / "SKILL.md", dst / "SKILL.md")
    shutil.copy2(repo / "LICENSE", dst / "LICENSE")
    (dst / "SOURCE.txt").write_text(
        "출처: https://github.com/blader/humanizer (MIT)\n받은 버전: {}\n설치일: {}\n".format(
            rev, datetime.date.today()), encoding="utf-8")
    return dst


def build_portable(ko_repo):
    """웹 앱 업로드용 묶음 세 가지를 dist/ 에 만든다. 스킬 이름 = 폴더 이름 = legal-polish.
      legal-polish.zip       ZIP 안 최상위가 legal-polish/ 폴더  → Claude.ai, ChatGPT
      legal-polish-flat.zip  ZIP 안 최상위에 SKILL.md            → Microsoft 365 Copilot Cowork
      legal-polish/          압축하지 않은 폴더                  → Gemini 앱(폴더 업로드)
    """
    src = ROOT / "portable" / "legal-polish"
    dist = ROOT / "dist"
    folder = dist / "legal-polish"
    if folder.exists():
        shutil.rmtree(folder)
    shutil.copytree(src, folder)
    with_rules = False
    if ko_repo is not None:
        refs = resolve_dir(ko_repo, "codex/skills/humanize-korean/references", "skills/humanize-korean/references")
        if (refs / "quick-rules.md").is_file():
            (folder / "references").mkdir(exist_ok=True)
            shutil.copy2(refs / "quick-rules.md", folder / "references" / "quick-rules-ko.md")
            shutil.copy2(ko_repo / "LICENSE", folder / "references" / "LICENSE-im-not-ai.txt")
            with_rules = True
    files = sorted(f for f in folder.rglob("*") if f.is_file())
    zpath = dist / "legal-polish.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, "legal-polish/" + f.relative_to(folder).as_posix())
    with zipfile.ZipFile(dist / "legal-polish-flat.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.relative_to(folder).as_posix())
    return zpath, with_rules


def main():
    ap = argparse.ArgumentParser(description="im-not-ai·humanizer 스킬 설치(설치 스크립트 실행 없음)")
    ap.add_argument("--target", choices=sorted(TARGETS), default="agents",
                    help="agents=.agents/skills (Antigravity·Codex·Gemini CLI), claude=.claude/skills")
    ap.add_argument("--only", choices=["ko", "en"], help="한쪽만 설치")
    ap.add_argument("--source-ko", help="im-not-ai 를 미리 받아 둔 폴더(ZIP 압축 푼 곳)")
    ap.add_argument("--source-en", help="humanizer 를 미리 받아 둔 폴더")
    ap.add_argument("--portable", action="store_true", help="dist/legal-polish.zip 도 만들기")
    a = ap.parse_args()

    skills_dir = ROOT / TARGETS[a.target]
    skills_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="polish-skills-"))
    ko_repo = None
    try:
        for lang in ("ko", "en"):
            if a.only and a.only != lang:
                continue
            given = a.source_ko if lang == "ko" else a.source_en
            if given:
                repo, rev = Path(given).resolve(), "로컬 폴더(" + Path(given).name + ")"
            else:
                url, name = REPOS[lang]
                repo = tmp / name
                out("받는 중: " + url)
                rev = clone(url, repo)
            if lang == "ko":
                ko_repo = repo
                dst = install_ko(repo, skills_dir, rev)
            else:
                dst = install_en(repo, skills_dir, rev)
            out("설치: {}  ({})".format(dst.relative_to(ROOT).as_posix(), rev))
        if a.portable:
            z, with_rules = build_portable(ko_repo)
            note = " (im-not-ai quick-rules 포함)" if with_rules else " (한국어 규칙 파일 없이)"
            out("만듦: dist/legal-polish.zip · dist/legal-polish-flat.zip · dist/legal-polish/" + note)
        if a.target == "claude":
            for own in ("polish-ko", "polish-en"):
                src = ROOT / ".agents" / "skills" / own
                if src.is_dir():
                    copy_tree(src, skills_dir / own)
                    out("복사: " + (skills_dir / own).relative_to(ROOT).as_posix())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    out("")
    out("다음 단계")
    if a.target == "agents":
        out("  Antigravity: 이 폴더를 열고 에이전트 창에서 /skills reload → /polish-ko 또는 /polish-en")
    else:
        out("  Claude Code: 이 폴더에서 claude 실행 → /polish-ko 또는 /polish-en (스킬 목록은 /skills)")
    out("  점검 도구: python tools/polish_check.py 원문.md 윤문본.md --terms terms.txt")


if __name__ == "__main__":
    main()
