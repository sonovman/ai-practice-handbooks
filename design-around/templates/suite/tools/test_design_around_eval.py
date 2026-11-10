#!/usr/bin/env python3
"""design_around_eval.py 시험 (핸드북 32). 실행: python tools/test_design_around_eval.py"""
import copy
import json
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design_around_eval as da  # noqa: E402

SAMPLE = os.path.join(HERE, "..", "sample")


def load(n):
    with open(os.path.join(SAMPLE, n), encoding="utf-8") as f:
        return json.load(f)


def run(doc=None, chart=None):
    res, errs = da.evaluate(doc or load("design_input.json"), chart)
    return {r["id"]: r for r in res}, errs


def t_overall_levels():
    r, errs = run()
    assert errs == []
    want = {"O1": "HIGH", "O2": "HIGH", "O3": "LOW", "O4": "HIGH", "O5": "HIGH", "O6": "LOW"}
    for k, v in want.items():
        assert r[k]["result"]["us"]["overall"] == v, (k, r[k]["result"]["us"]["overall"])
        assert r[k]["result"]["kr"]["overall"] == v, (k, "kr")


def t_untouched_independent_claim_is_high():
    r, _ = run()
    assert r["O1"]["result"]["us"]["claims"][1][0] == "LOW"
    assert r["O1"]["result"]["us"]["claims"][7][0] == "HIGH"


def t_mpf_disclosed_structure_is_literal_us():
    r, _ = run()
    lv, why = r["O4"]["result"]["us"]["claims"][1]
    assert lv == "HIGH" and "헌납" in why[0]


def t_kr_functional_literal_override():
    r, _ = run()
    lv, why = r["O4"]["result"]["kr"]["claims"][1]
    assert lv == "HIGH" and "문언 충족" in why[0]


def t_function_moved_elsewhere_high():
    r, _ = run()
    lv, why = r["O5"]["result"]["us"]["claims"][1]
    assert lv == "HIGH" and "어딘가" in why[0]


def t_way_without_evidence_is_med():
    d = load("design_input.json")
    ch = d["options"][4]["changes"][0]          # O5
    ch.update({"function_moved_to": "", "way_differs": True, "way_evidence": ""})
    r, _ = run(d)
    assert r["O5"]["result"]["us"]["claims"][1][0] == "MED"
    assert any(n.startswith("W08") for n in r["O5"]["notes"])


def t_known_interchangeable_beats_way():
    d = load("design_input.json")
    ch = d["options"][4]["changes"][0]
    ch.update({"function_moved_to": "", "way_differs": True, "way_evidence": "시험", "known_interchangeable": True})
    r, _ = run(d)
    assert r["O5"]["result"]["us"]["claims"][1][0] == "HIGH"


def t_festo_rebuttal_med():
    d = load("design_input.json")
    d["options"][0]["changes"][0]["rebuttal_risk"] = "보정 당시 예측 불가 주장 가능"
    r, _ = run(d)
    assert r["O1"]["result"]["us"]["claims"][1][0] == "MED"


def t_surrender_without_record_errors():
    d = load("design_input.json")
    d["options"][4]["changes"][0]["in_surrendered_territory"] = True   # 1c.2 has no amendment
    _, errs = run(d)
    assert any(e[0] == "E05" for e in errs)


def t_kr_free_art_whole_product_beats_literal():
    d = load("design_input.json")
    ch = d["options"][3]["changes"][0]           # O4 1e
    ch["kr"]["free_art_whole_product"] = True
    r, _ = run(d)
    assert r["O4"]["result"]["kr"]["claims"][1][0] == "LOW"
    assert r["O4"]["result"]["us"]["claims"][1][0] == "HIGH"


def t_construction_mismatch_with_31():
    d = load("design_input.json")
    d["claims"][0]["limitations"][3]["construction"] = "둘 다 수행해도 됨"
    _, errs = run(d, load("chart_construed_31.json"))
    assert any(e[0] == "E10" for e in errs)


def t_review_flag_from_31():
    r, _ = run(None, load("chart_construed_31.json"))
    assert any(n.startswith("W12") for n in r["O1"]["notes"])


def t_report_renders():
    d = load("design_input.json")
    res, errs = da.evaluate(d)
    md = da.report(d, res, errs)
    assert "| O3 두 모드 자동 동시 운용(모드 버튼 제거) | **LOW** | **LOW** |" in md


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
if __name__ == "__main__":
    for t in TESTS:
        t()
        print("ok  ", t.__name__)
    print("design_around_eval: %d개 시험 통과" % len(TESTS))
