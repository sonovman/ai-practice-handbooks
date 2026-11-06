#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cite_check.py — 리서치 메모 속 인용을 '확인 목록'과 대조하는 점검기

하는 일
  1. 메모(.md/.txt)에서 판결·결정, 사건번호, 심판번호, 법령 조문, 특허문헌 번호를 뽑습니다.
  2. 사람이 원문으로 확인해 적은 확인 목록(citation-log.csv)과 하나씩 대조합니다.
  3. 날짜가 미래이거나 사건번호 연도보다 앞서는 등 형식상 이상한 인용을 표시합니다.
  4. 인용과 같은 줄에 따옴표로 묶은 문장이 있으면, 확인 목록의 '원문발췌'에 그대로 있는지 봅니다.
  5. 결과를 표(마크다운)로 내고, 문제가 하나라도 있으면 종료코드 1을 돌려줍니다.

하지 않는 일
  - 인터넷에서 판례가 실제로 있는지 찾지 않습니다. 존재·내용·효력 확인은 사람이
    대법원 종합법률정보, 국가법령정보센터, KIPRIS 등 원문에서 직접 합니다.
  - 이 점검을 통과했다는 것은 "확인 목록에 있는 것만 썼다"는 뜻이지, 그 내용이 옳다는 뜻이 아닙니다.

사용법
  python cite_check.py 메모.md citation-log.csv
  python cite_check.py 메모.md citation-log.csv --out 점검결과.md

필요한 것: Python 3.8 이상 (추가 설치 없음)
"""
import argparse
import csv
import datetime as dt
import re
import sys
import unicodedata

# ── 1. 인용을 찾는 규칙 ──────────────────────────────────────────
COURT = r"(대법원(?:\s*전원합의체)?|특허법원|헌법재판소|[가-힣]{2,6}(?:고등|지방|가정|행정|회생)법원(?:\s*[가-힣]{2,4}지원)?)"
DATE = r"(\d{4})\s*\.\s*(\d{1,2})\s*\.\s*(\d{1,2})\s*\.?"
CASENO = r"(\d{2,4})([가-힣]{1,3})(\d{1,7})"

RE_DECISION = re.compile(COURT + r"\s*" + DATE + r"\s*(?:선고|자)\s*" + CASENO + r"\s*(판결|결정|심결)")
RE_CASENO = re.compile(r"(?<![\d-])" + CASENO + r"(?!\d)")
RE_LAW = re.compile(
    r"((?:구\s*)?(?:특허법|실용신안법|디자인보호법|상표법|민법|민사소송법|형법|발명진흥법|"
    r"부정경쟁방지 및 영업비밀보호에 관한 법률|부정경쟁방지법))\s*"
    r"(?:\([^)]*\)\s*)?"
    r"제\s*(\d+)\s*조(?:의\s*(\d+))?(?:\s*제\s*(\d+)\s*항)?(?:\s*제\s*(\d+)\s*호)?"
)
RE_KRPAT = re.compile(r"(?:특허|등록특허|공개특허|실용신안|출원)?\s*(?:공보\s*)?(?:제\s*)?(10|20|30|40)-(\d{4})-(\d{7})|(?:특허\s*)?제\s*(10|20)-(\d{7})\s*호")
RE_FOREIGN = re.compile(r"\b(US|EP|JP|WO|CN)\s?(\d{4}/\d{6}|\d{4}-\d{6}|\d{1,2},\d{3},\d{3}|\d{7,11})\s?([A-Z]\d?)?\b")

# 사건부호 → 그 부호를 쓰는 기관 (자주 쓰는 것만)
CODE_OWNER = {
    "후": "대법원",      # 특허·실용신안·디자인·상표 사건 상고
    "허": "특허법원",    # 심결취소소송
    "당": "특허심판원",  # 당사자계 심판 (무효·권리범위확인 등)
    "원": "특허심판원",  # 결정계 심판 (거절결정불복 등)
}
TRIBUNAL_CODES = {"당", "원", "정", "취"}
# 사건번호처럼 생겼지만 사건번호가 아닌 것 (금액·단위 등)
NOT_CASE_CODES = {"년", "월", "일", "원정", "개", "명", "건", "호", "항", "조", "쪽", "면", "번", "차", "회", "위", "층", "km", "만", "억", "천"}


def norm(s):
    """비교용 정규화: 유니코드 통일, 공백·문장부호 제거"""
    s = unicodedata.normalize("NFC", s or "")
    s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    return re.sub(r"[\s\.\,\·\"'「」『』《》<>()\[\]]", "", s)


def full_year(y):
    y = int(y)
    if y >= 1000:
        return y
    return 1900 + y if y >= 47 else 2000 + y


def key_case(year, code, serial):
    return "{}{}{}".format(full_year(year), code, int(serial))


def key_law(name, jo, ui, hang, ho):
    name = re.sub(r"\s+", "", name)  # '구 특허법'은 '구특허법'으로 남겨 현행법과 구분
    k = "{}제{}조".format(name, jo)
    if ui:
        k += "의{}".format(ui)
    if hang:
        k += "제{}항".format(hang)
    if ho:
        k += "제{}호".format(ho)
    return k


def key_from_text(text):
    """확인 목록의 '인용' 칸 하나에서 비교 키를 만든다"""
    m = RE_DECISION.search(text)
    if m:
        return key_case(m.group(5), m.group(6), m.group(7))
    m = RE_LAW.search(text)
    if m:
        return key_law(*m.groups())
    m = RE_KRPAT.search(text)
    if m:
        if m.group(1):
            return "{}-{}-{}".format(m.group(1), m.group(2), m.group(3))
        return "{}-{}".format(m.group(4), m.group(5))
    m = RE_FOREIGN.search(text)
    if m:
        return (m.group(1) + re.sub(r"[^\d]", "", m.group(2))).upper()
    m = RE_CASENO.search(text)
    if m and m.group(2) not in NOT_CASE_CODES:
        return key_case(m.group(1), m.group(2), m.group(3))
    return norm(text)


# ── 2. 메모에서 인용 뽑기 ────────────────────────────────────────
QUOTE = re.compile(r"[\"“]([^\"“”]{8,}?)[\"”]")


def extract(memo_text, today):
    found = []  # dict: line, kind, text, key, issues(list)
    for ln, line in enumerate(memo_text.splitlines(), 1):
        spans = []
        quotes = QUOTE.findall(line)

        def add(kind, m, key, issues=None):
            spans.append((m.start(), m.end()))
            found.append({"line": ln, "kind": kind, "text": m.group(0).strip(),
                          "key": key, "issues": issues or [], "quotes": quotes})

        for m in RE_DECISION.finditer(line):
            court = re.sub(r"\s+", "", m.group(1))
            y, mo, d = int(m.group(2)), int(m.group(3)), int(m.group(4))
            cy, code = full_year(m.group(5)), m.group(6)
            issues = []
            try:
                date = dt.date(y, mo, d)
                if date > today:
                    issues.append("선고일이 미래")
                if y < cy:
                    issues.append("선고연도({})가 사건번호 연도({})보다 앞섬".format(y, cy))
            except ValueError:
                issues.append("없는 날짜")
            owner = CODE_OWNER.get(code)
            base_court = "대법원" if court.startswith("대법원") else court
            if owner and owner != base_court and not (owner == "특허심판원" and m.group(8) == "심결"):
                issues.append("사건부호 '{}'는 보통 {} 사건".format(code, owner))
            add("판결·결정", m, key_case(m.group(5), code, m.group(7)), issues)

        for m in RE_LAW.finditer(line):
            add("법령", m, key_law(*m.groups()))

        for m in RE_KRPAT.finditer(line):
            if any(s <= m.start() < e for s, e in spans):
                continue
            issues = []
            if m.group(1):
                key = "{}-{}-{}".format(m.group(1), m.group(2), m.group(3))
                if int(m.group(2)) > today.year:
                    issues.append("문헌번호의 연도가 미래")
            else:
                key = "{}-{}".format(m.group(4), m.group(5))
            add("특허문헌", m, key, issues)

        for m in RE_FOREIGN.finditer(line):
            add("특허문헌", m, (m.group(1) + re.sub(r"[^\d]", "", m.group(2))).upper())

        for m in RE_CASENO.finditer(line):
            if any(s <= m.start() < e for s, e in spans):
                continue
            code = m.group(2)
            if code in NOT_CASE_CODES or len(m.group(1)) == 3:
                continue
            issues = []
            if full_year(m.group(1)) > today.year:
                issues.append("사건번호 연도가 미래")
            kind = "심판번호" if code in TRIBUNAL_CODES else "사건번호"
            add(kind, m, key_case(m.group(1), code, m.group(3)), issues)
    return found


# ── 3. 확인 목록 읽기 ────────────────────────────────────────────
def load_verified(path):
    rows = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            cite = (r.get("인용") or "").strip()
            if not cite:
                continue
            k = key_from_text(cite)
            rows[k] = r
    return rows


# ── 4. 대조와 보고 ───────────────────────────────────────────────
def check(found, verified):
    results = []
    for c in found:
        row = verified.get(c["key"])
        problems = list(c["issues"])
        if row is None:
            verdict = "미검증(목록에 없음)"
        else:
            st = (row.get("상태") or "").strip()
            if st == "확인됨":
                verdict = "확인됨"
            elif st == "폐기":
                verdict = "폐기된 인용이 다시 나옴"
            else:
                verdict = "미검증({})".format(st or "상태 빈칸")
            # 인용문 대조
            src = norm(row.get("원문발췌", ""))
            for q in c["quotes"]:
                if len(norm(q)) < 8:
                    continue
                if not src:
                    problems.append("인용문을 대조할 원문발췌가 목록에 없음")
                elif norm(q) not in src:
                    problems.append("인용문이 원문발췌와 다름: “{}”".format(q[:40] + ("…" if len(q) > 40 else "")))
        ok = verdict == "확인됨" and not problems
        results.append(dict(c, verdict=verdict, problems=problems, ok=ok))
    return results


def report(results, memo, csvpath, today):
    bad = [r for r in results if not r["ok"]]
    out = []
    out.append("# 인용 점검 결과\n")
    out.append("- 메모: `{}`  \n- 인용 목록: `{}`  \n- 점검일: {}".format(memo, csvpath, today.isoformat()))
    out.append("- 인용 {}건 중 **통과 {}건 · 문제 {}건**\n".format(len(results), len(results) - len(bad), len(bad)))
    out.append("| 줄 | 종류 | 인용 | 판정 | 문제 |")
    out.append("|---:|---|---|---|---|")
    for r in results:
        mark = "통과" if r["ok"] else "**확인 필요**"
        out.append("| {} | {} | {} | {} · {} | {} |".format(
            r["line"], r["kind"], r["text"].replace("|", "/"), mark, r["verdict"],
            "<br>".join(r["problems"]) or "—"))
    out.append("")
    if bad:
        out.append("## 다음 할 일\n")
        out.append("1. '확인 필요' 인용은 원문(종합법률정보·국가법령정보센터·KIPRIS 등)에서 직접 찾습니다.")
        out.append("2. 찾으면 citation-log.csv에 원문발췌·확인처·확인일과 함께 `확인됨`으로, 못 찾으면 `폐기`로 적습니다.")
        out.append("3. 폐기한 인용은 메모에서 지우고, 그 자리를 '미결 쟁점'으로 남깁니다. AI에게 대체 판례를 새로 묻지 않습니다.")
    else:
        out.append("모든 인용이 인용 목록의 확인됨 항목과 일치합니다. 제출 전에 인용문을 원문과 한 번 더 눈으로 대조하세요.")
    out.append("\n> 이 점검은 '인용 목록에서 확인됨인 것만 썼는지'를 봅니다. 판례의 존재·내용·현재 효력은 사람이 원문에서 확인합니다.")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="리서치 메모의 인용을 확인 목록과 대조합니다.")
    ap.add_argument("memo", help="점검할 메모 파일 (.md, .txt)")
    ap.add_argument("verified", help="인용 목록 CSV (citation-log.csv)")
    ap.add_argument("--out", help="결과를 저장할 마크다운 파일")
    ap.add_argument("--today", help="기준일 YYYY-MM-DD (기본: 오늘)")
    a = ap.parse_args(argv)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()

    with open(a.memo, encoding="utf-8-sig") as f:
        memo_text = f.read()
    results = check(extract(memo_text, today), load_verified(a.verified))
    text = report(results, a.memo, a.verified, today)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(text)
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
