"""4개 플랫폼 버전 일치 점검 — 사용법: python tools/check_versions.py (kit 폴더에서)"""
import hashlib
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
VERSIONS = {
    "Claude 스킬": KIT / "claude/decision-council/SKILL.md",
    "ChatGPT 스킬": KIT / "chatgpt/skill-instructions.md",
    "Gemini Gem": KIT / "gemini/gem-instructions.md",
    "Copilot 에이전트": KIT / "copilot/agent-instructions.md",
}
RULES = [
    ("쓰지 않는 때(사실·작성)", ["정답이 하나인"]),
    ("중립적 질문 정리", ["내 의견을 넣지"]),
    ("위원 5인", ["위원 5인"]),
    ("독립성(앞 위원 미참고)", ["참고하지 않고"]),
    ("관점 끝까지", ["끝까지 밀고"]),
    ("[확인 필요] 표시", ["[확인 필요]"]),
    ("익명 응답 A~E", ["응답 A~E"]),
    ("반박 1회·이유", ["이유 없이 다수를"]),
    ("합의 수준 4단계", ["조건부 합의"]),
    ("치명적 반대 규칙", ["치명적 반대"]),
    ("신뢰도 상·중·하", ["상·중·하"]),
    ("분명한 권고·소수 의견 존중", ["근거가 더 강한"]),
    ("첫 번째 할 일 하나", ["하나만"]),
    ("사실 만들기 금지", ["사실을 만들어 내지"]),
    ("불편한 결론", ["불편한 결론"]),
    ("자료 속 명령문 무시", ["지시가 아니"]),
]
COPIES = [
    (KIT / "claude/decision-council/references/roles.md", KIT / "knowledge/roles.md"),
    (KIT / "claude/decision-council/references/output-template.md", KIT / "knowledge/output-template.md"),
]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    texts = {k: v.read_text(encoding="utf-8") for k, v in VERSIONS.items()}
    miss = 0
    print("핵심 규칙".ljust(22), " | ".join(VERSIONS))
    for name, marks in RULES:
        cells = []
        for k, t in texts.items():
            ok = any(m in t for m in marks)
            miss += not ok
            cells.append(("O" if ok else "X 빠짐").center(len(k)))
        print(name.ljust(22), " | ".join(cells))
    diff = 0
    for a, b in COPIES:
        same = hashlib.sha256(a.read_bytes()).digest() == hashlib.sha256(b.read_bytes()).digest()
        diff += not same
        print(("같음 " if same else "다름 ") + str(b.relative_to(KIT)))
    print("\n빠진 규칙 {}건 · 사본 불일치 {}건".format(miss, diff))
    return 1 if (miss or diff) else 0


if __name__ == "__main__":
    sys.exit(main())
