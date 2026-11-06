#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_verdict.py — 협의체 결론(마크다운)이 정해진 형식과 합의 규칙을 지켰는지 점검

하는 일
  1. 머리 3칸(정리한 질문·판단 기준·진행 방식)이 있는지
  2. 7개 항목(## 1. ~ ## 7.)이 순서대로 있는지
  3. 1번 표에 위원 5명(레드팀·원점 질문자·기회 탐색자·외부인·실행가)이 모두 있는지
  4. 2번 상호 검토가 익명 표기(응답 A~E)를 쓰는지
  5. 3번에 위원마다 '변경' 또는 '유지'와 이유가 있는지
  6. 4번 합의 수준·신뢰도가 정해진 값인지, 치명적 반대가 '있음'인데 '강한/전원 합의'로 판정하지 않았는지
  7. 6번 첫 번째 할 일이 하나인지
하지 않는 일
  - 결론이 옳은지는 판단하지 않습니다.

사용법:  python check_verdict.py 결론.md
필요한 것: Python 3.8 이상 (추가 설치 없음)
"""
import re
import sys

ROLES = ["레드팀", "원점 질문자", "기회 탐색자", "외부인", "실행가"]
SECTIONS = ["독립 의견", "익명 상호 검토", "반박과 수정", "합의 판정", "권고", "첫 번째 할 일", "확인 필요 사항"]
LEVELS = ["전원 합의", "강한 합의", "조건부 합의", "합의 불가"]
MODES = ["병렬 서브에이전트", "단일 대화 순차", "교차 플랫폼"]


def field(text, name):
    m = re.search(r"\*\*" + re.escape(name) + r":\*\*[ \t]*(.*)", text)
    return m.group(1).strip() if m else ""


def bullet(text, name):
    m = re.search(r"^\s*[-*]\s*" + re.escape(name) + r"\s*[:：]\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else ""


def sections(text):
    pos = []
    for i, t in enumerate(SECTIONS, 1):
        m = re.search(r"^##\s*" + str(i) + r"\.\s*" + re.escape(t), text, re.M)
        pos.append(m.start() if m else None)
    found = [(i, p) for i, p in enumerate(pos, 1) if p is not None]
    body = {}
    for k, (i, p) in enumerate(found):
        body[i] = text[p:found[k + 1][1] if k + 1 < len(found) else len(text)]
    return pos, body


def check(text):
    out = []
    add = lambda ok, item, d: out.append(("통과" if ok else "실패", item, d))

    miss = [h for h in ("정리한 질문", "판단 기준", "진행 방식") if not field(text, h)]
    add(not miss, "머리 3칸", "빠짐: " + ", ".join(miss) if miss else "모두 있음")
    mode = field(text, "진행 방식")
    add(any(m in mode for m in MODES), "진행 방식", mode or "없음")

    pos, body = sections(text)
    absent = [str(i) for i, p in enumerate(pos, 1) if p is None]
    ordered = [p for p in pos if p is not None] == sorted(p for p in pos if p is not None)
    add(not absent and ordered, "7개 항목", "빠짐: " + ", ".join(absent) if absent else ("순서 어긋남" if not ordered else "모두 순서대로"))

    s1 = body.get(1, "")
    lack = [r for r in ROLES if not re.search(r"^\|\s*" + re.escape(r) + r"\s*\|", s1, re.M)]
    add(not lack, "위원 5명", "1번 표에 없음: " + ", ".join(lack) if lack else "모두 있음")

    s2 = body.get(2, "")
    anon = re.findall(r"응답\s*([A-E])", s2)
    named = [r for r in ROLES if r in s2]
    add(bool(anon) and not named, "익명 검토", "응답 {} 표기{}".format("·".join(sorted(set(anon))) or "없음", ", 위원 이름 노출: " + ", ".join(named) if named else ""))

    s3 = body.get(3, "")
    rows = [l for l in s3.splitlines() if l.startswith("|") and not re.match(r"^\|\s*(위원|-)", l)]
    bad = []
    for l in rows:
        cells = [c.strip() for c in l.strip("|").split("|")]
        if len(cells) < 3 or not re.search(r"변경|유지", cells[1]) or len(cells[2]) < 4:
            bad.append(cells[0] if cells else "?")
    add(len(rows) >= 5 and not bad, "반박과 수정", "{}행{}".format(len(rows), ", 이유·입장 부족: " + ", ".join(bad) if bad else ""))

    s4 = body.get(4, "")
    level = bullet(s4, "합의 수준")
    conf = bullet(s4, "신뢰도")
    block = bullet(s4, "치명적 반대")
    lv = next((x for x in LEVELS if x in level), "")
    add(bool(lv), "합의 수준", level or "없음")
    add(conf[:1] in ("상", "중", "하") and bool(conf), "신뢰도", conf or "없음")
    contradiction = block.startswith("있음") and lv in ("전원 합의", "강한 합의")
    add(bool(block) and not contradiction, "치명적 반대 규칙", "치명적 반대가 있는데 '{}'로 판정".format(lv) if contradiction else (block or "표시 없음"))

    s6 = body.get(6, "")
    items = [l for l in s6.splitlines()[1:] if l.strip() and not l.strip().startswith("(")]
    many = len([l for l in items if re.match(r"\s*([-*]|\d+[.)])\s+", l)]) > 1
    add(bool(items) and not many, "첫 번째 할 일", "하나" if items and not many else ("여러 개" if many else "없음"))
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    rows = check(open(argv[0], encoding="utf-8-sig").read())
    print("협의체 결론 형식 점검 — {}\n".format(argv[0]))
    for s, item, d in rows:
        print("[{}] {:<10} {}".format(s, item, d))
    fails = sum(1 for r in rows if r[0] == "실패")
    print("\n실패 {}건 — 형식 점검일 뿐, 결론의 옳고 그름은 사람이 판단합니다.".format(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
