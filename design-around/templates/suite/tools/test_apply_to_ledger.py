#!/usr/bin/env python3
"""apply_to_ledger.py 시험 (핸드북 31). 실행: python tools/test_apply_to_ledger.py"""
import json
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import apply_to_ledger as al  # noqa: E402

SAMPLE = os.path.join(HERE, "..", "sample")


def load(n):
    with open(os.path.join(SAMPLE, n), encoding="utf-8") as f:
        return json.load(f)


def run():
    return al.apply(load("chart_from_30.json"), load("construction_good.json"))


def t_fills_construction():
    out, _ = run()
    lim = {l["id"]: l for l in out["limitations"]}
    assert "0.3mm" in lim["1d"]["construction"] and "투영" in lim["1d"]["construction"]
    assert "배타" not in lim["1f"]["construction"] and "하나만" in lim["1f"]["construction"]


def t_flags_review_for_missing_fact():
    out, imp = run()
    st = {(i["id"], i["term"]): i["status"] for i in imp}
    assert st[("1d", "ribs")] == "재검토"
    assert st[("1f", "configured to select either a juice mode or a smoothie mode")] == "반영"
    row = [r for r in out["rows"] if r["id"] == "1d"][0]
    assert row.get("needs_review") is True


def t_mpf_sets_sam():
    out, _ = run()
    lim = {l["id"]: l for l in out["limitations"]}
    assert "M1" in lim["1e"]["sam"] and lim["1e"]["type"] == "mpf"


def t_unknown_id_reported():
    c = load("construction_good.json")
    c["terms"].append({"term": "x", "ledger_id": "9z", "construction": "y"})
    _, imp = al.apply(load("chart_from_30.json"), c)
    assert imp[-1]["status"] == "원장에 없음"


def t_input_not_mutated():
    ch = load("chart_from_30.json")
    al.apply(ch, load("construction_good.json"))
    assert not any(r.get("needs_review") for r in ch["rows"])


def t_report_markdown():
    _, imp = run()
    md = al.impact_md(imp, {"patent": "p"})
    assert "재검토 1건" in md and "| [1d] |" in md


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
if __name__ == "__main__":
    for t in TESTS:
        t()
        print("ok  ", t.__name__)
    print("apply_to_ledger: %d개 시험 통과" % len(TESTS))
