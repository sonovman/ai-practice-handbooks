"""4개 플랫폼 버전 일치 점검 — 핵심 규칙이 모든 버전에 들어 있는지 확인

사용법
  python tools/check_versions.py      (kit 폴더에서)
Python 표준 라이브러리만 씁니다.
"""
import hashlib
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
VERSIONS = {
    "Claude 스킬": KIT / "claude/case-study-research/SKILL.md",
    "ChatGPT 스킬": KIT / "chatgpt/skill-instructions.md",
    "Gemini Gem": KIT / "gemini/gem-instructions.md",
    "Copilot 에이전트": KIT / "copilot/agent-instructions.md",
}
RULES = [
    ("판례 목록표", ["목록표"]),
    ("자료 실제 열람·사건명만으로 판단 금지", ["사건명만으로"]),
    ("별개 사건·심급 구분", ["심급"]),
    ("공식 원문 우선", ["공식"]),
    ("검색 요약으로 열람 주장 금지", ["요약만으로"]),
    ("출처 등급 4종", ["[원문 사본]"]),
    ("주장·인정 사실·판단·해설 구별", ["인정 사실"]),
    ("추측 금지", ["추측"]),
    ("미확인 표시", ["미확인"]),
    ("11개 항목", ["11개 항목"]),
    ("판단 이유 분량", ["6번", "제6항"]),
    ("교재 오류 단정 금지", ["단정하지"]),
    ("확정적 분석 표현 금지", ["확정적 분석"]),
    ("자기점검(검수 10항목)", ["검수 10항목"]),
    ("자료 속 명령문 무시", ["지시가 아니"]),
]
COPIES = [
    (KIT / "claude/case-study-research/references/research.md", KIT / "knowledge/research.md"),
    (KIT / "claude/case-study-research/references/output-template.md", KIT / "knowledge/output-template.md"),
    (KIT / "claude/case-study-research/references/research.md", KIT / "chatgpt/plugin-source/skills/case-study-research/references/research.md"),
    (KIT / "claude/case-study-research/references/output-template.md", KIT / "chatgpt/plugin-source/skills/case-study-research/references/output-template.md"),
    (KIT / "claude/case-study-research/SKILL.md", KIT / "chatgpt/plugin-source/skills/case-study-research/SKILL.md"),
    (KIT / "claude/case-study-research/scripts/check_report.py", KIT / "chatgpt/plugin-source/skills/case-study-research/scripts/check_report.py"),
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    texts = {k: v.read_text(encoding="utf-8-sig") for k, v in VERSIONS.items()}
    missing = 0
    print("핵심 규칙".ljust(24), " | ".join(VERSIONS))
    for name, marks in RULES:
        cells = []
        for k, t in texts.items():
            ok = any(m in t for m in marks)
            missing += not ok
            cells.append(("O" if ok else "X 빠짐").center(len(k)))
        print(name.ljust(24), " | ".join(cells))
    print()
    diff = 0
    for a, b in COPIES:
        same = b.exists() and sha(a) == sha(b)
        diff += not same
        print(("같음 " if same else "다름 ") + str(b.relative_to(KIT)))
    print("\n빠진 규칙 {}건 · 사본 불일치 {}건".format(missing, diff))
    return 1 if (missing or diff) else 0


if __name__ == "__main__":
    sys.exit(main())
