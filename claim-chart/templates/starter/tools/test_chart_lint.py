#!/usr/bin/env python3
"""chart_lint.py · render_chart.py 시험 (핸드북 30). 실행: python tools/test_chart_lint.py"""
import copy
import json
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chart_lint as cl  # noqa: E402
import render_chart as rc  # noqa: E402

SAMPLE = os.path.join(HERE, "..", "sample")


def load(name):
    with open(os.path.join(SAMPLE, name), encoding="utf-8") as f:
        return json.load(f)


def codes(chart):
    e, w = cl.lint(chart)
    return [c for _, c, _ in e], [c for _, c, _ in w]


def t_good_passes():
    e, w = codes(load("chart_good.json"))
    assert e == [] and w == [], (e, w)


def t_103_passes():
    e, w = codes(load("chart_103.json"))
    assert e == [] and w == [], (e, w)


def t_bad_catches_all():
    e, w = codes(load("chart_bad.json"))
    for c in ("E01", "E03", "E04", "E05", "E06", "E07", "E12", "E13", "E14"):
        assert c in e, (c, e)
    for c in ("W10", "W06", "W07", "W15", "W16"):
        assert c in w, (c, w)


def t_pic_stage_softens_placeholder():
    c = load("chart_bad.json")
    c["meta"]["stage"] = "pic"
    e, w = codes(c)
    assert "E05" not in e and "E05" in w


def t_code_lines_not_pages():
    c = load("chart_good.json")
    assert any("41~58행" in f.get("pin", "") or "41~58" in f.get("pin", "") for r in c["rows"] for f in r["facts"])
    e, _ = codes(c)
    assert "E03" not in e


def t_102_single_reference():
    c = load("chart_103.json")
    c["meta"]["chart_type"] = "invalidity_102"
    e, _ = codes(c)
    assert "E09" in e


def t_103_needs_motivation():
    c = load("chart_103.json")
    c.pop("combination")
    e, _ = codes(c)
    assert e.count("E08") == 2


def t_invalidity_date():
    c = load("chart_103.json")
    c["rows"][1]["facts"][0]["date"] = "2022-01-01"
    e, _ = codes(c)
    assert "E10" in e


def t_dead_code_method():
    c = load("chart_good.json")
    c["meta"]["method"] = True
    [r for r in c["rows"] if r["id"] == "1f"][0]["facts"][1]["executed"] = False
    e, _ = codes(c)
    assert "E17" in e


def t_directionality():
    c = {"meta": {}, "limitations": [{"id": "1a", "text": "a receiver that receives a message", "type": "structure"}],
         "rows": [{"id": "1a", "assertion": "충족", "explanation": "왜냐하면 …",
                   "facts": [{"source": "src", "pin": "net/msg.c, 함수 DoSend() 10~20행", "text": "DoSend()가 메시지를 보낸다"}]}]}
    _, w = codes(c)
    assert "W11" in w


def t_representative_basis():
    c = load("chart_good.json")
    c["meta"]["target"]["representative"] = True
    e, _ = codes(c)
    assert "E14" in e


def t_render_three_column_and_ledger():
    c = load("chart_good.json")
    md = rc.chart_md(c)
    assert "해석·명세서 대응 구조" in md and "[SAM 대비]" in md
    led = rc.ledger_md(c)
    assert led.count("\n| [") == len(c["limitations"])


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
if __name__ == "__main__":
    for t in TESTS:
        t()
        print("ok  ", t.__name__)
    print("chart_lint·render_chart: %d개 시험 통과" % len(TESTS))
