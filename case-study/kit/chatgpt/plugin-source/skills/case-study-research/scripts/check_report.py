#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_report.py — 판례 심층 해설(마크다운)이 정해진 형식과 기본 원칙을 지켰는지 점검

하는 일
  1. 헤더 7개(사건명 ~ 후속 소송 이력 확인 상태)가 있고 비어 있지 않은지
  2. 11개 항목(## 1. ~ ## 11.)이 순서대로 있는지
  3. 6번(법원의 판단 이유)이 가장 긴 항목인지
  4. 8번에 심급 표(법원·사건번호·판결일·출처 칸)가 있는지, '미확인' 표시가 있는지
  5. 11번에 심화 학습 질문이 3개 이상인지
  6. 원문 출처 칸에 링크(URL)가 있는지, 조사 기준일이 날짜 형식인지
  7. 판결문 확인 상태가 '전체 열람'이 아닌데 본문이 "원문에 기초한 확정적 분석"처럼 말하지 않는지
  8. 출처 등급 표시([공식 원문] [원문 사본] [2차 자료] [미확인])가 쓰였는지

하지 않는 일
  - 판결 내용이 맞는지, 인용문이 원문에 있는지는 확인하지 않습니다. 그것은 사람이 원문으로 합니다.

사용법
  python check_report.py 해설.md
필요한 것: Python 3.8 이상 (추가 설치 없음)
"""
import re
import sys

HEADERS = ["사건명", "법원 및 사건번호", "판결 선고일", "원문 출처 및 링크", "조사 기준일",
           "판결문 확인 상태", "후속 소송 이력 확인 상태"]
SECTIONS = ["사건을 한눈에 이해하기", "사건의 배경 및 주요 사실관계", "당사자들의 주장", "핵심 법적 쟁점",
            "적용 법률 및 법리", "법원의 판단 이유", "판결의 결론과 법적 효과",
            "항소·상고·환송 및 후속 소송 이력", "판결의 의의 및 비판적 분석",
            "교재 인용 내용과 실제 판결문 비교", "핵심 정리와 심화 학습 질문"]
GRADES = ["[공식 원문]", "[원문 사본]", "[2차 자료]", "[미확인]"]
OVERCLAIM = ["공식 원문에 기초한 확정적", "원문 전체를 검토한 결과 확정", "확정적으로 분석"]


def header_value(text, name):
    m = re.search(r"\*\*" + re.escape(name) + r":\*\*[ \t]*(.*)", text)
    return None if m is None else m.group(1).strip()


def split_sections(text):
    pos = []
    for i, title in enumerate(SECTIONS, 1):
        m = re.search(r"^##\s*" + str(i) + r"\.\s*" + re.escape(title), text, re.M)
        pos.append(m.start() if m else None)
    bodies = {}
    found = [(i, p) for i, p in enumerate(pos, 1) if p is not None]
    for k, (i, p) in enumerate(found):
        end = found[k + 1][1] if k + 1 < len(found) else len(text)
        bodies[i] = text[p:end]
    return pos, bodies


def check(text):
    rows = []
    add = lambda ok, item, detail: rows.append(("통과" if ok is True else ("주의" if ok is None else "실패"), item, detail))

    missing = [h for h in HEADERS if not header_value(text, h)]
    add(not missing, "헤더 7개", "빠지거나 빈 칸: " + ", ".join(missing) if missing else "모두 있음")

    src = header_value(text, "원문 출처 및 링크") or ""
    add(bool(re.search(r"https?://", src)), "원문 링크", "URL 있음" if re.search(r"https?://", src) else "원문 출처 칸에 URL이 없습니다")

    day = header_value(text, "조사 기준일") or ""
    add(bool(re.search(r"\d{4}-\d{2}-\d{2}|\d{4}\.\s*\d{1,2}\.\s*\d{1,2}", day)), "조사 기준일", day or "없음")

    pos, bodies = split_sections(text)
    absent = [str(i) for i, p in enumerate(pos, 1) if p is None]
    order_ok = [p for p in pos if p is not None] == sorted(p for p in pos if p is not None)
    add(not absent and order_ok, "11개 항목", ("빠짐: " + ", ".join(absent)) if absent else ("순서 어긋남" if not order_ok else "모두 순서대로 있음"))

    if 6 in bodies and len(bodies) > 1:
        lens = {i: len(re.sub(r"\s", "", b)) for i, b in bodies.items()}
        longest = max(lens, key=lens.get)
        add(longest == 6, "판단 이유 분량", "6번 {}자 / 가장 긴 항목 {}번 {}자".format(lens[6], longest, lens[longest]))

    s8 = bodies.get(8, "")
    has_table = bool(re.search(r"^\|.*법원.*사건번호.*판결일.*출처.*\|", s8, re.M))
    add(has_table, "8번 심급 표", "법원·사건번호·판결일·출처 칸이 있는 표" if has_table else "표가 없거나 필수 칸이 빠졌습니다")
    add(("미확인" in s8) or ("확인 불가" in s8) or None, "8번 미확인 표시", "있음" if ("미확인" in s8 or "확인 불가" in s8) else "미확인 사항을 적는 줄이 없습니다(모두 확인했다면 그렇게 적으세요)")

    s11 = bodies.get(11, "")
    tail = s11.split("심화 학습 질문")[-1] if "심화 학습 질문" in s11 else ""
    qn = len(re.findall(r"^\s*(?:\d+[.)]|[-*])\s+\S", tail, re.M))
    add(qn >= 3, "심화 질문", "{}개".format(qn))

    status = header_value(text, "판결문 확인 상태") or ""
    if "전체 열람" not in status:
        bad = [w for w in OVERCLAIM if w in text]
        add(not bad, "과장 표현", "확인 상태가 '{}'인데 '{}' 표현이 있습니다".format(status[:12], bad[0]) if bad else "없음")

    used = [g for g in GRADES if g in text]
    add(bool(used) or None, "출처 등급 표시", ", ".join(used) if used else "출처 등급 표시가 없습니다")
    return rows


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    text = open(argv[0], encoding="utf-8-sig").read()
    rows = check(text)
    print("판례 심층 해설 형식 점검 — {}\n".format(argv[0]))
    for s, item, detail in rows:
        print("[{}] {:<12} {}".format(s, item, detail))
    fails = sum(1 for r in rows if r[0] == "실패")
    print("\n실패 {}건 · 주의 {}건".format(fails, sum(1 for r in rows if r[0] == "주의")))
    print("형식 점검일 뿐입니다. 판결 내용과 인용문은 원문으로 확인하세요.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
