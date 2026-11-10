#!/usr/bin/env python3
"""역할 배치(HEAD·BUILDER·REVIEWER) 독립성 점검과 추천.

원칙
  - REVIEWER는 BUILDER와 다른 회사여야 한다(자기 답안 자기 채점 방지) → 같으면 BLOCK
  - HEAD와 REVIEWER가 같은 회사면 '독립성 낮음'(Director도 REDUCED_INDEPENDENCE로 표시)
  - 한 CLI의 구독 한도가 끝났을 때 넘어갈 순서(failover)를 미리 정해 둔다

사용
  python role_matrix.py --head claude --builder agy --reviewer codex
  python role_matrix.py --available claude,codex          # 가능한 배치를 추천
"""
import argparse
import itertools
import json
import sys

VENDOR = {"claude": "Anthropic", "codex": "OpenAI", "agy": "Google", "antigravity": "Google"}
# 역할별 선호 순서(숙련도 기준이 아니라 '서로 다른 회사로 나누기 쉬운 순서')
PREFERENCE = {
    "head": ["claude", "codex", "agy"],
    "builder": ["agy", "codex", "claude"],
    "reviewer": ["codex", "claude", "agy"],
}


def vendor(cli):
    v = VENDOR.get((cli or "").lower())
    if not v:
        raise ValueError(f"알 수 없는 CLI: {cli!r} (claude / codex / agy)")
    return v


def assess(head, builder, reviewer):
    h, b, r = vendor(head), vendor(builder), vendor(reviewer)
    issues = []
    if b == r:
        issues.append(("BLOCK", "BUILDER와 REVIEWER가 같은 회사입니다 — 자기 답안을 자기가 채점하게 됩니다."))
    if h == r:
        issues.append(("WARN", "HEAD와 REVIEWER가 같은 회사입니다 — 독립성 낮음(REDUCED_INDEPENDENCE)."))
    if h == b:
        issues.append(("INFO", "HEAD와 BUILDER가 같은 회사입니다 — 허용되지만 계획 오류를 같이 놓칠 수 있습니다."))
    level = "BLOCK" if any(l == "BLOCK" for l, _ in issues) else ("WARN" if issues and any(l == "WARN" for l, _ in issues) else "OK")
    return {"roles": {"head": head, "builder": builder, "reviewer": reviewer},
            "vendors": {"head": h, "builder": b, "reviewer": r},
            "level": level, "issues": [m for _, m in issues]}


def _score(combo):
    head, builder, reviewer = combo
    a = assess(head, builder, reviewer)
    penalty = {"OK": 0, "WARN": 10, "BLOCK": 100}[a["level"]]
    pref = (PREFERENCE["head"].index(head) + PREFERENCE["builder"].index(builder)
            + PREFERENCE["reviewer"].index(reviewer))
    return penalty + pref


def recommend(available):
    avail = [c.strip().lower() for c in available if c.strip()]
    avail = ["agy" if c == "antigravity" else c for c in avail]
    for c in avail:
        vendor(c)
    if len(set(avail)) < 2:
        raise ValueError("서로 다른 CLI가 최소 2개 필요합니다.")
    combos = [c for c in itertools.product(avail, repeat=3)]
    best = min(combos, key=_score)
    result = assess(*best)
    # 한도 소진 시 넘어갈 순서: 같은 역할에서 다른 회사 우선
    result["failover"] = {
        role: [c for c in PREFERENCE[role] if c in avail and c != result["roles"][role]]
        for role in ("head", "builder", "reviewer")
    }
    # REVIEWER 대체 후보에서 BUILDER와 같은 회사는 뺀다(자기 채점 방지). 남는 게 없으면 사람이 검수.
    b_vendor = result["vendors"]["builder"]
    result["failover"]["reviewer"] = [c for c in result["failover"]["reviewer"] if vendor(c) != b_vendor]
    if not result["failover"]["reviewer"]:
        result["failover"]["reviewer"] = ["사람 검수(대체 REVIEWER 없음)"]
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description="역할 배치 독립성 점검")
    ap.add_argument("--head"); ap.add_argument("--builder"); ap.add_argument("--reviewer")
    ap.add_argument("--available", help="쉼표로 구분한 사용 가능 CLI 목록")
    a = ap.parse_args(argv)
    try:
        if a.available:
            out = recommend(a.available.split(","))
        elif a.head and a.builder and a.reviewer:
            out = assess(a.head, a.builder, a.reviewer)
        else:
            ap.error("--head/--builder/--reviewer 세 개를 모두 주거나 --available 을 주세요.")
    except ValueError as e:
        print(f"[오류] {e}")
        return 1
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 2 if out["level"] == "BLOCK" else 0


if __name__ == "__main__":
    sys.exit(main())
