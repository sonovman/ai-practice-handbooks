#!/usr/bin/env python3
"""해석 결과 → 30편 한정 원장·Claim Chart에 반영하고 영향 보고 (핸드북 31). 표준 라이브러리만.

30편 차트 JSON(limitations·rows)에 해석 기록(terms[].ledger_id·construction)을 넣어
- limitations[].construction 칸을 채우고(3열 차트가 됨),
- 해석이 '조건'을 더한 행(requires)에서 대응 사실에 그 조건의 근거가 보이지 않으면 '재검토'로 표시하고,
- 같은 해석을 유효성 열에도 적용했는지(대칭성) 표시합니다.

  python tools/apply_to_ledger.py ../../claim-chart/.../chart_good.json sample/construction_good.json \
      --out work/chart_construed.json --report work/impact.md
"""
import argparse
import copy
import json
import re
import sys


def toks(s):
    return set(t for t in re.findall(r"[A-Za-z가-힣0-9.]+", (s or "").lower()) if len(t) > 1)


def apply(chart, cons):
    out = copy.deepcopy(chart)
    lims = {l["id"]: l for l in out.get("limitations", [])}
    rows = {r["id"]: r for r in out.get("rows", [])}
    impact = []
    done = {}
    for t in cons.get("terms", []):
        lid = t.get("ledger_id")
        if not lid or lid not in lims:
            impact.append({"term": t.get("term"), "id": lid, "status": "원장에 없음", "note": "ledger_id를 30편 원장 ID와 맞추세요."})
            continue
        lim = lims[lid]
        before = done.get(lid, lim.get("construction", ""))
        new = t.get("construction", "")
        lim["construction"] = (done[lid] + " / " + new) if lid in done else new
        done[lid] = lim["construction"]
        if t.get("mpf", {}).get("applies") and t.get("mpf", {}).get("structure"):
            lim["sam"] = "%s (%s)" % (t["mpf"]["structure"], t["mpf"].get("structure_cite", ""))
            lim["type"] = "mpf"
        row = rows.get(lid)
        status, note = "반영", ""
        req = t.get("requires") or []          # 해석이 더한 확인 조건(예: "높이 0.3mm 이상")
        if row:
            facts = " ".join([f.get("text", "") + " " + f.get("pin", "") for f in row.get("facts", [])] + [row.get("explanation", "")])
            missing = [q for q in req if not (toks(q.get("evidence_hint", q.get("text", ""))) & toks(facts))]
            if missing:
                status = "재검토"
                note = "해석이 요구하는 조건의 근거가 대응 사실에 없음: " + "; ".join(q.get("text", "") for q in missing)
                row["needs_review"] = True
                row.setdefault("review_notes", []).append(note)
            if t.get("used_for", {}).get("validity") is None and req:
                note += (" / " if note else "") + "유효성 열에도 같은 해석을 적용해 다시 보세요(대칭성)."
        else:
            status, note = "행 없음", "30편 차트에 대응 행이 없습니다."
        impact.append({"term": t.get("term"), "id": lid, "status": status, "before": before, "after": new, "note": note})
    return out, impact


def impact_md(impact, meta):
    out = ["# 해석 반영 영향 보고 — %s" % meta.get("patent", "?"), "",
           "| 원장 ID | 용어 | 상태 | 해석 | 확인할 점 |", "|---|---|---|---|---|"]
    for i in impact:
        out.append("| [%s] | %s | %s | %s | %s |" % (i.get("id"), i.get("term"), i.get("status"),
                                                 (i.get("after") or "").replace("|", "/"), (i.get("note") or "").replace("|", "/")))
    n = sum(1 for i in impact if i["status"] == "재검토")
    out += ["", "재검토 %d건 — 30편 `chart_lint.py`를 다시 돌리고, 표시된 행의 사실을 보강하거나 결론(충족/불충족)을 바꾸세요." % n]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="해석 결과를 30편 원장·차트에 반영")
    ap.add_argument("chart_json")
    ap.add_argument("construction_json")
    ap.add_argument("--out")
    ap.add_argument("--report")
    a = ap.parse_args(argv)
    with open(a.chart_json, encoding="utf-8") as f:
        chart = json.load(f)
    with open(a.construction_json, encoding="utf-8") as f:
        cons = json.load(f)
    out, impact = apply(chart, cons)
    md = impact_md(impact, cons.get("meta", {}))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(md)
    sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
