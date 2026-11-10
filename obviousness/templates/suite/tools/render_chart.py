#!/usr/bin/env python3
"""차트 JSON → 보기 좋은 Markdown 표 (핸드북 30). 표준 라이브러리만.

  python tools/render_chart.py sample/chart_good.json              # Claim Chart(2열, 필요 시 3열)
  python tools/render_chart.py sample/chart_good.json --ledger     # 한정 원장(9열)
  python tools/render_chart.py sample/chart_good.json --out work/chart.md
"""
import argparse
import json
import sys


def esc(s):
    return (s or "").replace("|", "/").replace("\n", "<br>")


def rhc(r):
    parts = ["**[주장]** " + esc(r.get("assertion"))]
    for f in r.get("facts") or []:
        parts.append("**[사실]** %s, %s%s: %s" % (esc(f.get("source")), esc(f.get("pin")),
                                                (" (" + f["date"] + ")") if f.get("date") else "", esc(f.get("text"))))
    if r.get("sam_match"):
        parts.append("**[SAM 대비]** " + esc(r["sam_match"]))
    fwr = r.get("fwr") or {}
    if r.get("theory") == "doe":
        for k, lab in (("function", "기능"), ("way", "방식"), ("result", "결과"), ("why_insubstantial", "차이가 사소한 이유"),
                       ("linking", "연결 증거")):
            if fwr.get(k):
                parts.append("**[%s]** %s" % (lab, esc(fwr[k])))
    parts.append("**[설명]** " + esc(r.get("explanation")))
    return "<br>".join(parts)


def chart_md(c):
    m = c.get("meta", {})
    t = m.get("target") or {}
    lims = c.get("limitations", [])
    rows = {r["id"]: r for r in c.get("rows", [])}
    three = any(l.get("construction") or l.get("sam") for l in lims)
    out = ["# Claim Chart — %s 청구항 %s" % (m.get("patent", "?"), m.get("claim", "?")), "",
           "| 특허 | 우선일 | 대상 | 버전 | 대상 일자 | 유형 |", "|---|---|---|---|---|---|",
           "| %s | %s | %s | %s | %s | %s |" % (m.get("patent", ""), m.get("priority_date", ""), t.get("name", ""),
                                            t.get("version", ""), t.get("date", ""), m.get("chart_type", "")), ""]
    if three:
        out += ["| 청구한정 (LHC) | 해석·명세서 대응 구조 | 대응 사실과 설명 (RHC) |", "|---|---|---|"]
    else:
        out += ["| 청구한정 (LHC) | 대응 사실과 설명 (RHC) |", "|---|---|"]
    for l in lims:
        r = rows.get(l["id"])
        left = "**[%s]** %s" % (l["id"], esc(l.get("text")))
        right = rhc(r) if r else "**(대응 행 없음)**"
        if three:
            mid = esc(l.get("construction")) + (("<br>SAM: " + esc(l["sam"])) if l.get("sam") else "")
            out.append("| %s | %s | %s |" % (left, mid, right))
        else:
            out.append("| %s | %s |" % (left, right))
    if c.get("combination"):
        cb = c["combination"]
        out += ["", "**결합 동기**: " + esc(cb.get("motivation")), "", "**성공에 대한 합리적 기대**: " + esc(cb.get("expectation"))]
    if c.get("symmetry"):
        out += ["", "**대칭성 점검**: " + esc(c["symmetry"])]
    return "\n".join(out) + "\n"


def ledger_md(c):
    rows = {r["id"]: r for r in c.get("rows", [])}
    out = ["# 한정 원장 — %s 청구항 %s" % (c.get("meta", {}).get("patent", "?"), c.get("meta", {}).get("claim", "?")), "",
           "| ID | 청구 문언 | 원자적 한정 명제 | 유형 | 명세서·도면 근거 | 출원경과 | 문언 | 균등 | 유효성(§102/§103) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for l in c.get("limitations", []):
        r = rows.get(l["id"], {})
        out.append("| [%s] | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            l["id"], esc(l.get("text")), esc(l.get("proposition")), esc(l.get("type")), esc(l.get("intrinsic")),
            esc(l.get("prosecution")), esc(r.get("literal")), esc(r.get("doe")), esc(r.get("validity"))))
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="차트 JSON을 Markdown 표로")
    ap.add_argument("chart_json")
    ap.add_argument("--ledger", action="store_true", help="한정 원장(9열)으로 출력")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    with open(a.chart_json, encoding="utf-8") as f:
        c = json.load(f)
    md = ledger_md(c) if a.ledger else chart_md(c)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(md)
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
