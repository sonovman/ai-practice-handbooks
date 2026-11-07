#!/usr/bin/env python3
"""전문 용어 번역 점검기 (핸드북 20). 표준 라이브러리만 사용.

영어 원문을 한국어로 요약할 때(또는 그 반대) 전문 용어가 일반 사전 뜻으로 잘못 옮겨지는 경우를 잡습니다.
예) prosecution history estoppel → '기소 이력 금반언'(오역) / '출원경과 금반언'(권장)
    hazard ratio → '위험률'(다른 개념) / '위험비'(권장)

  python tools/term_check.py 요약.md --glossary glossary/patent-legal.csv --source 원문.txt
  python tools/term_check.py 요약.md --glossary glossary/*.csv

용어집 CSV 열: source,target,avoid,note
  source  원문 쪽 용어(대소문자 무시)      target  요약에 써야 할 용어(| 로 여러 개 허용)
  avoid   쓰면 안 되는 번역(| 로 구분)      note    설명
판정  FAIL 피해야 할 번역 사용 · WARN 원문에 있는 용어가 요약에 권장 번역 없이 빠짐 · OK
종료 코드 0 / 1 / 2
"""
import argparse
import csv
import glob
import json
import re
import sys
from pathlib import Path


def load(paths):
    rows = []
    for pat in paths:
        for p in sorted(glob.glob(pat)) or [pat]:
            with open(p, encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    if not r.get("source") or r["source"].startswith("#"):
                        continue
                    rows.append({
                        "source": r["source"].strip(),
                        "target": [t.strip() for t in (r.get("target") or "").split("|") if t.strip()],
                        "avoid": [t.strip() for t in (r.get("avoid") or "").split("|") if t.strip()],
                        "note": (r.get("note") or "").strip(),
                        "file": Path(p).name,
                    })
    return rows


def contains(text, term):
    if re.search(r"[A-Za-z]", term):
        return re.search(r"(?<![A-Za-z-])" + re.escape(term) + r"(?![A-Za-z-])", text, re.I) is not None
    return term in text


def check(summary, rows, source=None):
    items = []
    for r in rows:
        failed = False
        for bad in r["avoid"]:
            if contains(summary, bad):
                failed = True
                items.append({"level": "FAIL", "term": r["source"], "found": bad,
                              "use": " / ".join(r["target"]), "note": r["note"]})
        if not failed and source is not None and contains(source, r["source"]):
            ok = any(contains(summary, t) for t in r["target"]) or contains(summary, r["source"])
            if not ok:
                items.append({"level": "WARN", "term": r["source"], "found": "(권장 번역 없음)",
                              "use": " / ".join(r["target"]),
                              "note": "원문의 이 개념이 요약에서 빠졌거나 다른 말로 옮겨졌는지 확인"})
    status = "FAIL" if any(i["level"] == "FAIL" for i in items) else "WARN" if items else "OK"
    return {"status": status, "items": items, "terms": len(rows)}


def to_markdown(res, path):
    mark = {"OK": "통과", "WARN": "경고", "FAIL": "실패"}
    lines = ["# 전문 용어 점검 보고서", "", "- 요약: `{}`".format(path),
             "- 판정: **{}** · 용어집 {}개 항목".format(mark[res["status"]], res["terms"]), ""]
    if res["items"]:
        lines += ["| 판정 | 원문 용어 | 요약에서 발견 | 권장 | 메모 |", "|---|---|---|---|---|"]
        for i in res["items"]:
            lines.append("| {} | {} | {} | {} | {} |".format(mark[i["level"]], i["term"], i["found"], i["use"], i["note"]))
    lines += ["", "> 용어집에 있는 말만 봅니다. 조직의 용어집을 계속 늘려 가세요."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="전문 용어 번역 점검")
    ap.add_argument("summary")
    ap.add_argument("--glossary", nargs="+", required=True, help="용어집 CSV(와일드카드 가능)")
    ap.add_argument("--source", help="원문 파일(있으면 빠진 용어도 점검)")
    ap.add_argument("--report")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = load(a.glossary)
    summary = Path(a.summary).read_text(encoding="utf-8-sig")
    source = Path(a.source).read_text(encoding="utf-8-sig") if a.source else None
    res = check(summary, rows, source)
    if a.json:
        sys.stdout.write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    else:
        md = to_markdown(res, a.summary)
        sys.stdout.write(md)
        if a.report:
            Path(a.report).write_text(md, encoding="utf-8")
    return {"OK": 0, "WARN": 1, "FAIL": 2}[res["status"]]


if __name__ == "__main__":
    sys.exit(main())
