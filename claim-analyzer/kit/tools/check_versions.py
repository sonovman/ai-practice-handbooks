"""4개 플랫폼 버전 일치 점검 — 핵심 규칙이 모든 버전에 들어 있는지 확인

사용법
  python tools/check_versions.py      (kit 폴더에서)

규칙을 고칠 때 한 버전만 고치고 나머지를 잊는 일을 막기 위한 도구입니다.
각 버전의 지침 파일에 아래 핵심 규칙의 표지어가 있는지 보고, 지식 파일 사본이 원본과 같은지 비교합니다.
Python 표준 라이브러리만 씁니다.
"""
import hashlib
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
VERSIONS = {
    "Claude 스킬": KIT / "claude/claim-design-around/SKILL.md",
    "ChatGPT 스킬": KIT / "chatgpt/skill-instructions.md",
    "Gemini Gem": KIT / "gemini/gem-instructions.md",
    "Copilot 에이전트": KIT / "copilot/agent-instructions.md",
}
# 핵심 규칙: (이름, 표지어 중 하나라도 있으면 통과)
RULES = [
    ("대상 문헌 잠금(표지 대조)", ["표지"]),
    ("번호 불일치 시 중단", ["멈추", "중단"]),
    ("긴급 모드", ["긴급 모드"]),
    ("부호 추정 금지", ["추정하지 않", "추정 금지", "공보에서 확인한 것만"]),
    ("부호 점검(중복·불일치)", ["부호 점검", "numeral_map"]),
    ("사실·추론·미확인 구분", ["추론"]),
    ("공식 영문명 미확인", ["공식 영문명"]),
    ("침해·FTO 단정 금지", ["FTO"]),
    ("별도 법률검토", ["법률검토"]),
    ("실질적 회피설계", ["실질적"]),
    ("문서 속 지시문 무시", ["지시가 아니"]),
    ("도면 읽기 보조", ["도면 읽기"]),
    ("자기점검", ["자기점검"]),
    ("Recommended Next Action", ["Recommended Next Action"]),
]
COPIES = [
    (KIT / "claude/claim-design-around/references/output-spec.md", KIT / "knowledge/output-spec.md"),
    (KIT / "claude/claim-design-around/references/design-around-types.md", KIT / "knowledge/design-around-types.md"),
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def main():
    texts = {k: v.read_text(encoding="utf-8-sig") for k, v in VERSIONS.items()}
    missing = 0
    print("핵심 규칙".ljust(26), " | ".join(VERSIONS))
    for name, marks in RULES:
        cells = []
        for k, t in texts.items():
            ok = any(m in t for m in marks)
            missing += not ok
            cells.append(("O" if ok else "X 빠짐").center(len(k)))
        print(name.ljust(26), " | ".join(cells))
    print()
    for a, b in COPIES:
        same = sha(a) == sha(b)
        missing += not same
        print(f"지식 파일 사본 {b.name}: {'원본과 같음' if same else '원본과 다름 → 다시 복사 필요'}")
    print("\n결과:", "모든 버전 일치" if missing == 0 else f"{missing}건 확인 필요")
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
