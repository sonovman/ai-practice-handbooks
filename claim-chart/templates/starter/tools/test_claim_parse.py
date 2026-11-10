#!/usr/bin/env python3
"""claim_parse.py 시험 (핸드북 30). 실행: python tools/test_claim_parse.py"""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import claim_parse as cp  # noqa: E402

SAMPLE = os.path.join(HERE, "..", "sample")


def ids(res):
    return [r["id"] for r in res["limitations"]]


def by_id(res, i):
    return [r for r in res["limitations"] if r["id"] == i][0]


def t_en_split():
    res = cp.parse(open(os.path.join(SAMPLE, "claim_en.txt"), encoding="utf-8").read())
    assert ids(res) == ["1pre", "1a", "1b", "1c", "1c.1", "1c.2", "1d", "1e", "1f", "1g"], ids(res)
    assert res["transition"] == "comprising"


def t_en_types():
    res = cp.parse(open(os.path.join(SAMPLE, "claim_en.txt"), encoding="utf-8").read())
    assert by_id(res, "1e")["type"] == "mpf"
    assert by_id(res, "1f")["type"] == "alternative" and "configured" in by_id(res, "1f")["flags"]
    assert by_id(res, "1g")["type"] == "negative"
    assert by_id(res, "1d")["type"] == "numeric"


def t_ko_split():
    res = cp.parse(open(os.path.join(SAMPLE, "claim_ko.txt"), encoding="utf-8").read())
    assert res["lang"] == "ko"
    assert ids(res) == ["1pre", "1a", "1b", "1c", "1c.1", "1d", "1e", "1f", "1g"], ids(res)
    assert by_id(res, "1pre")["text"] == "착즙기"


def t_ko_types():
    res = cp.parse(open(os.path.join(SAMPLE, "claim_ko.txt"), encoding="utf-8").read())
    assert by_id(res, "1e")["type"] == "mpf"
    assert by_id(res, "1f")["type"] == "alternative"
    assert by_id(res, "1g")["type"] == "negative"


def t_method():
    res = cp.parse("1. A method of extracting juice, comprising: feeding produce into a drum; rotating a screw; and discharging juice.")
    assert res["is_method"] and all(r["type"] in ("step", "preamble") for r in res["limitations"]), res["limitations"]
    assert "method_step" in by_id(res, "1a")["flags"]


def t_antecedent():
    res = cp.parse("1. A device comprising: a frame; and the blade attached to said frame.")
    assert "antecedent" in by_id(res, "1b")["flags"]
    assert "antecedent" not in by_id(res, "1a")["flags"]


def t_markush_and_whereby():
    res = cp.parse("1. A blend comprising: a sweetener selected from the group consisting of sucrose and xylitol; "
                   "and a binder, whereby the tablet dissolves.")
    assert "markush" in by_id(res, "1a")["flags"] and "alternative" not in by_id(res, "1a")["flags"]
    assert "whereby" in by_id(res, "1b")["flags"]


def t_markdown():
    res = cp.parse(open(os.path.join(SAMPLE, "claim_en.txt"), encoding="utf-8").read())
    md = cp.to_markdown(res)
    assert "| [1f] |" in md and "삭제시험" in md


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
if __name__ == "__main__":
    for t in TESTS:
        t()
        print("ok  ", t.__name__)
    print("claim_parse: %d개 시험 통과" % len(TESTS))
