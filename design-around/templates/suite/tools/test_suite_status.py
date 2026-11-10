#!/usr/bin/env python3
"""suite_status.py 시험 (핸드북 32 통합 오케스트레이터). 실행: python tools/test_suite_status.py"""
import json
import os
import shutil
import sys
import tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import suite_status as ss  # noqa: E402

EXAMPLE = os.path.join(HERE, "..", "cases", "example")


def copy_case():
    d = tempfile.mkdtemp()
    dst = os.path.join(d, "case")
    shutil.copytree(EXAMPLE, dst)
    return dst


def set_case(case, **kw):
    p = os.path.join(case, "case.json")
    c = json.load(open(p, encoding="utf-8"))
    c.update(kw)
    json.dump(c, open(p, "w", encoding="utf-8"), ensure_ascii=False)


def t_dry_status_next_is_s4():
    st = ss.status(copy_case())
    assert st["next"][0] == "S4" and st["next"][1] == "claim-construe"


def t_run_creates_construed_and_reports():
    c = copy_case()
    st = ss.status(c, run=True)
    assert os.path.exists(os.path.join(c, "work", "04_chart_construed.json"))
    for f in ("chart_lint.md", "construction_check.md", "design_around.md", "impact.md"):
        assert os.path.exists(os.path.join(c, "work", "reports", f)), f
    assert st["results"]["chart"][2] == 1          # 재검토 1행(31편 [1d])
    assert st["results"]["design"][1] == ["O3", "O6"]
    assert st["next"][0] == "G3"


def t_review_fixed_moves_to_g5():
    c = copy_case()
    ss.status(c, run=True)
    p = os.path.join(c, "work", "04_chart_construed.json")
    ch = json.load(open(p, encoding="utf-8"))
    for r in ch["rows"]:
        if r.get("needs_review"):
            r["needs_review"] = False
            r["facts"][0]["text"] += "; 돌기 높이 0.6mm(측정표 7행)"
    json.dump(ch, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    st = ss.status(c, run=True)
    assert st["next"][0] == "G5", st["next"]
    set_case(c, human_signoff=True)
    assert ss.status(c, run=True)["next"][0] == "DONE"


def t_missing_ledger_starts_s1():
    c = copy_case()
    os.remove(os.path.join(c, "work", "01_ledger.json"))
    st = ss.status(c)
    assert st["next"][:2] == ("S1", "claim-decompose")


def t_invalidity_order_construe_before_chart():
    c = copy_case()
    set_case(c, purpose="invalidity")
    os.remove(os.path.join(c, "work", "02_chart.json"))
    os.remove(os.path.join(c, "work", "03_construction.json"))
    st = ss.status(c)
    assert st["next"][0] == "S3"


def t_ledger_not_approved_blocks():
    c = copy_case()
    set_case(c, ledger_approved=False, purpose="construction")
    st = ss.status(c, run=True)
    assert st["next"][0] == "G1"


def t_id_mismatch_note():
    c = copy_case()
    p = os.path.join(c, "work", "03_construction.json")
    d = json.load(open(p, encoding="utf-8"))
    d["terms"][0]["ledger_id"] = "9z"
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    st = ss.status(c)
    assert any("ledger_id" in n for n in st["notes"])


def t_markdown():
    md = ss.to_md(ss.status(copy_case()))
    assert "## 다음 할 일" in md and "claim-construe" in md


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
if __name__ == "__main__":
    for t in TESTS:
        t()
        print("ok  ", t.__name__)
    print("suite_status: %d개 시험 통과" % len(TESTS))
