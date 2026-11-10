#!/usr/bin/env python3
"""construe_check.py 시험 (핸드북 31). 실행: python tools/test_construe_check.py"""
import copy
import json
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import construe_check as cc  # noqa: E402

SAMPLE = os.path.join(HERE, "..", "sample")


def load(n):
    with open(os.path.join(SAMPLE, n), encoding="utf-8") as f:
        return json.load(f)


def codes(d):
    e, w = cc.check(d)
    return [c for _, c, _ in e], [c for _, c, _ in w]


def t_good_passes():
    assert codes(load("construction_good.json")) == ([], [])


def t_bad_catches():
    e, w = codes(load("construction_bad.json"))
    for c in ("C01", "C02", "C03", "C05", "C06", "C10", "C11", "C12", "C14", "C15"):
        assert c in e, (c, e)
    for c in ("C07", "C08", "C09", "C13"):
        assert c in w, (c, w)


def t_kr_only_warnings():
    e, w = codes(load("construction_kr.json"))
    assert e == [] and "C06" in w and "C05" in w, (e, w)


def t_ptab_before_2018_is_bri():
    d = load("construction_good.json")
    d["meta"].update({"forum": "ptab", "standard": "bri", "petition_date": "2018-01-10"})
    e, _ = codes(d)
    assert "C01" not in e
    d["meta"]["petition_date"] = "2019-01-10"
    e, _ = codes(d)
    assert "C01" in e


def t_ex_parte_bri():
    d = load("construction_good.json")
    d["meta"].update({"forum": "ex_parte", "standard": "phillips"})
    e, _ = codes(d)
    assert "C01" in e


def t_lexicography_needs_quote():
    d = load("construction_good.json")
    [t for t in d["terms"] if t["term"] == "ribs"][0]["lexicography"] = {"quote": "", "cite": ""}
    e, _ = codes(d)
    assert "C04" in e


def t_software_mpf_needs_algorithm():
    d = load("construction_good.json")
    m = [t for t in d["terms"] if t["ledger_id"] == "1e"][0]["mpf"]
    m["software"] = True
    e, _ = codes(d)
    assert "C06" in e
    m["algorithm"] = "도5 흐름도 S1~S4"
    e, _ = codes(d)
    assert "C06" not in e


def t_kr_pbp_needs_reason():
    d = load("construction_kr.json")
    p = d["terms"][1]["product_by_process"]
    p["infringement_limited_to_process"] = True
    e, _ = codes(d)
    assert "C14" in e
    p["clearly_unreasonable_reason"] = "명세서 전체에 비해 권리범위가 지나치게 넓어짐"
    e, _ = codes(d)
    assert "C14" not in e


def t_forfeiture_exception():
    d = load("construction_bad.json")
    [t for t in d["terms"] if t["term"] == "controller"][0]["forfeiture_exception"] = "심판원이 통지 없이 새 해석 채택"
    e, w = codes(d)
    assert "C15" not in e and "C15" in w


def t_missing_standard_warns():
    d = load("construction_good.json")
    d["meta"].pop("standard")
    _, w = codes(d)
    assert "C01" in w


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
if __name__ == "__main__":
    for t in TESTS:
        t()
        print("ok  ", t.__name__)
    print("construe_check: %d개 시험 통과" % len(TESTS))
