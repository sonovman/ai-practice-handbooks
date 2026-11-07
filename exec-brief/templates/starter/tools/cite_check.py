#!/usr/bin/env python3
"""판례 인용 대조기 (핸드북 20). 표준 라이브러리만 사용.

AI가 쓴 판례 요약·보고서에서 사건번호·판례 인용을 뽑아
① 사용자가 준 원문(판결문·자료)에 실제로 있는지 대조하고
② 원문에 없는 인용은 '공식 데이터베이스에서 확인 전 사용 금지'로 표시하며
③ 모든 인용에 대해 확인할 곳(관할별 공식·공개 DB)을 목록으로 붙입니다.
AI가 지어낸 사건번호가 서면에 들어가는 사고를 막기 위한 도구입니다. 판례의 '내용'이 맞는지는 판단하지 않습니다.

  python tools/cite_check.py 요약.md --source 판결문.txt
  python tools/cite_check.py 요약.md --source 판결문.txt 참고자료.md --report cite.md
  python tools/cite_check.py 요약.md                    # 원문 없이: 인용 목록과 확인할 곳만

판정  FAIL 원문에 없는 인용 · WARN 원문에 있지만 공식 DB 확인 전 · OK 인용 없음
종료 코드 0 / 1 / 2
"""
import argparse
import json
import re
import sys
from pathlib import Path

# 한국 사건부호(긴 것부터). 예: 2020다12345, 2019후1234, 2021허5678, 2018헌바123
KR_CODES = ["가합", "가단", "가소", "구합", "구단", "카합", "카단", "카기", "재다", "헌가", "헌바", "헌마", "헌라", "헌나",
            "고합", "고단", "다카", "다", "도", "두", "후", "허", "나", "누", "마", "그", "므", "르", "브", "스", "추",
            "노", "초", "모", "드", "라", "인"]
KR_RE = re.compile(r"(?<![0-9A-Za-z가-힣])((?:19|20)?\d{2})\s?(" + "|".join(KR_CODES) + r")\s?(\d{2,6})(?![0-9])")
US_RE = re.compile(r"\b(\d{1,4})\s+(U\.\s?S\.|S\.\s?Ct\.|L\.\s?Ed\.(?:\s?2d)?|F\.\s?Supp\.(?:\s?[23]d)?|F\.(?:\s?[234]d|\s?4th)?|"
                   r"F\.\s?App'x|U\.S\.P\.Q\.(?:\s?2d)?|USPQ(?:2d)?|WL)\s+(\d{1,7})\b")
UK_RE = re.compile(r"\[(\d{4})\]\s+(UKSC|UKHL|UKPC|EWCA\s+(?:Civ|Crim)|EWHC|SGHC|SGCA|HCA|FCA|FCAFC|NZSC)\s+(\d{1,5})"
                   r"(?:\s*\((?:Pat|Ch|Admin|Comm|IPEC|QB|KB)\))?")
EU_RE = re.compile(r"\b([CT])\s?-\s?(\d{1,4})\s?/\s?(\d{2})\b")
ECLI_RE = re.compile(r"\bECLI:[A-Z]{2}:[A-Z0-9]{1,7}:\d{4}:[A-Za-z0-9.]{1,25}")
JP_RE = re.compile(r"(昭和|平成|令和)(\d{1,2}|元)年\(([^)\s]{1,4})\)第(\d{1,6})号")

WHERE = {
    "KR": "대법원 누리집 판례 검색(scourt.go.kr) · 국가법령정보센터(law.go.kr) · 법제처 Open API(8편)",
    "US": "CourtListener(courtlistener.com) · 법원 공식 사이트 · Westlaw/Lexis",
    "UK": "Find Case Law(caselaw.nationalarchives.gov.uk) · BAILII(bailii.org)",
    "EU": "CURIA(curia.europa.eu) · EUR-Lex(eur-lex.europa.eu)",
    "JP": "裁判所 裁判例検索(courts.go.jp)",
}


def out(msg):
    sys.stdout.write(msg + "\n")


def squash(s):
    return re.sub(r"[\s​]+", "", s).replace("’", "'").lower()


def extract(text):
    found = []
    for m in KR_RE.finditer(text):
        found.append(("KR", "{}{}{}".format(m.group(1), m.group(2), m.group(3)), m.group(0)))
    for m in US_RE.finditer(text):
        found.append(("US", m.group(0), m.group(0)))
    for m in UK_RE.finditer(text):
        found.append(("UK", m.group(0), m.group(0)))
    for m in EU_RE.finditer(text):
        found.append(("EU", "{}-{}/{}".format(m.group(1), m.group(2), m.group(3)), m.group(0)))
    for m in ECLI_RE.finditer(text):
        found.append(("EU", m.group(0), m.group(0)))
    for m in JP_RE.finditer(text):
        found.append(("JP", m.group(0), m.group(0)))
    seen, uniq = set(), []
    for j, key, raw in found:
        k = squash(key)
        if k not in seen:
            seen.add(k)
            uniq.append((j, key, raw))
    return uniq


def check(summary, sources):
    cites = extract(summary)
    src_sq = squash("\n".join(sources)) if sources else None
    items = []
    for j, key, raw in cites:
        if src_sq is None:
            level, note = "WARN", "원문을 주지 않아 대조 못 함 — 공식 DB에서 확인"
        elif squash(key) in src_sq or squash(raw) in src_sq:
            level, note = "WARN", "원문에 있음 — 서면에 쓰기 전 공식 DB에서 선고일·내용 확인"
        else:
            level, note = "FAIL", "원문에 없는 인용 — 공식 DB에서 존재·내용 확인 전 사용 금지"
        items.append({"level": level, "jurisdiction": j, "citation": key, "note": note, "where": WHERE[j]})
    status = "OK" if not items else ("FAIL" if any(i["level"] == "FAIL" for i in items) else "WARN")
    return {"status": status, "count": len(items), "items": items}


def to_markdown(res, summary_path, srcs):
    mark = {"OK": "통과", "WARN": "확인 필요", "FAIL": "실패"}
    lines = ["# 판례 인용 대조 보고서", "", "- 요약: `{}`".format(summary_path),
             "- 원문: {}".format(", ".join("`{}`".format(s) for s in srcs) if srcs else "(없음)"),
             "- 판정: **{}** · 인용 {}건".format(mark[res["status"]], res["count"]), ""]
    if res["items"]:
        lines += ["| 판정 | 관할 | 인용 | 메모 | 확인할 곳 |", "|---|---|---|---|---|"]
        for i in res["items"]:
            lines.append("| {} | {} | {} | {} | {} |".format(mark[i["level"]], i["jurisdiction"], i["citation"],
                                                         i["note"], i["where"]))
    lines += ["", "> 이 도구는 사건번호 '형식'을 찾아 원문과 글자를 대조할 뿐, 판례가 실제로 존재하는지·그 내용이 요약과 같은지는 판단하지 않습니다.",
              "> 서면·보고서에 쓰는 모든 판례는 공식 데이터베이스에서 원문을 열어 확인합니다."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="판례 인용 대조")
    ap.add_argument("summary", help="AI가 쓴 요약·보고서(.md .txt)")
    ap.add_argument("--source", nargs="*", default=[], help="판결문·참고자료 원문 파일(여러 개 가능)")
    ap.add_argument("--report", help="보고서 저장(.md)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    summary = Path(a.summary).read_text(encoding="utf-8-sig")
    sources = [Path(s).read_text(encoding="utf-8-sig") for s in a.source]
    res = check(summary, sources if a.source else None)
    if a.json:
        out(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        md = to_markdown(res, a.summary, a.source)
        sys.stdout.write(md)
        if a.report:
            Path(a.report).write_text(md, encoding="utf-8")
    return {"OK": 0, "WARN": 1, "FAIL": 2}[res["status"]]


if __name__ == "__main__":
    sys.exit(main())
