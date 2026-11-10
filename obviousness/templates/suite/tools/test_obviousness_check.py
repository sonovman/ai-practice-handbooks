#!/usr/bin/env python3
"""obviousness_check.py 시험 (표준 라이브러리 unittest).  python tools/test_obviousness_check.py"""
import copy
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import obviousness_check as oc  # noqa: E402
import chart_lint as cl  # noqa: E402

SAMPLE = os.path.join(HERE, "..", "sample", "obviousness.json")


def base():
    with open(SAMPLE, encoding="utf-8") as f:
        return json.load(f)


def codes(st, kind="errors"):
    return [c for _, c, _ in st[kind]]


def ref(doc, rid):
    return next(r for r in doc["references"] if r["id"] == rid)


def cgk(doc, kid):
    return next(k for k in doc["cgk"] if k["id"] == kid)


class T(unittest.TestCase):
    def test_01_sample_no_errors(self):
        st = oc.analyze(base())
        self.assertEqual(st["errors"], [])

    def test_02_classification(self):
        cls = {x["id"]: x["cls"] for x in oc.analyze(base())["res"]}
        self.assertEqual(cls, {"D3": "B", "D2": "C", "D1": "-", "D4": "X"})

    def test_03_examiner_ref_not_closest(self):
        # 심사관이 인용한 D1보다 D3가 더 적은 수정으로 청구항에 이른다
        res = oc.analyze(base())["res"]
        self.assertEqual(res[0]["id"], "D3")
        d1 = next(x for x in res if x["id"] == "D1")
        self.assertLess(d1["score"], res[0]["score"])

    def test_04_full_disclosure_is_A(self):
        d = base()
        for k in ref(d, "D3")["map"]:
            ref(d, "D3")["map"][k] = {"grade": "●", "pin": "¶[0001]", "text": "\"x\""}
        cls = {x["id"]: x["cls"] for x in oc.analyze(d)["res"]}
        self.assertEqual(cls["D3"], "A")

    def test_05_difference_without_cgk_research(self):
        d = base()
        d["cgk"] = [k for k in d["cgk"] if k["id"] != "K1"]
        d["combinations"] = d["combinations"][:0]
        st = oc.analyze(d)
        self.assertIn("O04", codes(st))

    def test_06_cgk_evidence_after_priority(self):
        d = base()
        cgk(d, "K1")["evidence"][0]["date"] = "2021-05-01"
        st = oc.analyze(d)
        self.assertIn("O05", codes(st))

    def test_07_cgk_without_evidence(self):
        d = base()
        cgk(d, "K1")["evidence"] = []
        st = oc.analyze(d)
        self.assertIn("O05", codes(st))
        self.assertIn("O09", codes(st))   # 불성립한 기술상식으로는 결합 불가

    def test_08_single_patent_is_weak(self):
        st = oc.analyze(base())
        self.assertIn(("K3", "O06"), [(i, c) for i, c, _ in st["warnings"]])
        self.assertEqual(st["kstr"]["K3"], "weak")
        self.assertEqual(st["kstr"]["K1"], "strong")

    def test_09_three_applicants_is_strong(self):
        d = base()
        k3 = cgk(d, "K3")
        k3["evidence"] += [
            {"source": "KR-가상-007", "type": "patent", "applicant": "가상 정", "date": "2016-01-01", "pin": "¶[0005]"},
            {"source": "US-가상-008", "type": "patent", "applicant": "Virtual Kitchen", "date": "2015-01-01", "pin": "col.2:3-9"}]
        self.assertEqual(oc.analyze(d)["kstr"]["K3"], "strong")

    def test_10_missing_limitation_in_combination(self):
        d = base()
        d["combinations"][0]["steps"] = [s for s in d["combinations"][0]["steps"] if s["limitation"] != "1f"]
        st = oc.analyze(d)
        self.assertIn("O10", codes(st))

    def test_11_secondary_ref_must_disclose(self):
        d = base()
        d["combinations"][0]["steps"][0]["from"] = "D1"   # D1은 1c.2를 개시하지 않음
        self.assertIn("O09", codes(oc.analyze(d)))

    def test_12_motivation_required(self):
        d = base()
        d["combinations"][0]["steps"][0]["motivation_source"] = ""
        self.assertIn("O11", codes(oc.analyze(d)))

    def test_13_hindsight_from_patent_itself(self):
        d = base()
        d["combinations"][0]["steps"][0]["motivation_source"] = "대상 특허 ¶[0016]"
        self.assertIn("O11", codes(oc.analyze(d)))

    def test_14_expectation_required_us(self):
        d = base()
        d["combinations"][0]["steps"][1]["expectation"] = ""
        self.assertIn("O12", codes(oc.analyze(d)))
        d["meta"]["forum"] = "kr"
        self.assertNotIn("O12", codes(oc.analyze(d)))

    def test_15_teaching_away_warns(self):
        st = oc.analyze(base())
        self.assertIn("O13", [c for i, c, _ in st["warnings"] if i.startswith("C2")])

    def test_16_post_priority_ref_in_combination(self):
        d = base()
        d["combinations"][0]["steps"][2]["from"] = "D4"
        self.assertIn("O03", codes(oc.analyze(d)))

    def test_17_non_analogous(self):
        d = base()
        ref(d, "D2")["same_field"] = False
        for c in d["combinations"]:
            c.pop("analogous", None)
        self.assertIn("O14", codes(oc.analyze(d)))
        for c in d["combinations"]:
            c["analogous"] = {"D2": "착즙률(압착 효율)이라는 같은 과제를 다룸"}
        self.assertNotIn("O14", codes(oc.analyze(d)))

    def test_18_secondary_must_be_reviewed(self):
        d = base()
        d["secondary"] = {}
        self.assertIn("O17", codes(oc.analyze(d)))

    def test_19_aapa_in_ipr(self):
        d = base()
        d["meta"]["proceeding"] = "ipr"
        d["references"].append({"id": "AAPA", "pub": "대상 특허 배경기술", "date": "2020-12-01", "kind": "aapa",
                                "same_field": True, "same_problem": True,
                                "map": {l["id"]: {"grade": "●", "pin": "¶[0002]", "text": "\"x\""} for l in d["limitations"]}})
        d["combinations"][0]["steps"][2]["from"] = "AAPA"
        self.assertIn("O08", codes(oc.analyze(d)))

    def test_20_missing_pin(self):
        d = base()
        ref(d, "D3")["map"]["1d"]["pin"] = ""
        self.assertIn("O02", codes(oc.analyze(d)))

    def test_21_chart_passes_lint(self):
        ch = oc.to_chart(base(), "C1")
        e, w = cl.lint(ch)
        self.assertEqual(e, [])
        self.assertEqual(ch["meta"]["chart_type"], "invalidity_103")
        self.assertEqual([r["id"] for r in ch["rows"]], [l["id"] for l in base()["limitations"]])

    def test_22_posita_required(self):
        d = base()
        d["posita"] = {}
        self.assertIn("O01", codes(oc.analyze(d)))


    def test_23_analogous_vs_other_reference(self):
        d = base()
        ref(d, "D2")["same_field"] = False
        for c in d["combinations"]:
            c["analogous"] = {"D2": "D3와 같은 압착 구조를 다룸"}
        st = oc.analyze(d)
        self.assertIn("O21", codes(st, "warnings"))

    def test_24_obvious_to_try_needs_three_axes(self):
        d = base()
        st0 = d["combinations"][0]["steps"][1]
        st0["rationale"] = "MPEP 2143(E) obvious to try"
        self.assertIn("O22", codes(oc.analyze(d)))
        st0["ott"] = {"finite": "감속비 1:20~1:40 세 가지 표준 기어", "guidance": "D2가 45rpm을 권장",
                      "predictable": "회전수는 감속비로 계산된다"}
        self.assertNotIn("O22", codes(oc.analyze(d)))

    def test_25_could_without_would(self):
        d = base()
        d["combinations"][0]["steps"][0]["motivation"] = "D2의 테이퍼 간극을 D3에 결합할 수 있었다"
        self.assertIn("O23", codes(oc.analyze(d), "warnings"))

    def test_26_cross_combination_rationale(self):
        d = base()
        d["combinations"][1]["steps"][0]["motivation_source"] = "C1 참조"
        self.assertIn("O25", codes(oc.analyze(d)))

    def test_27_mere_preference_is_not_teaching_away(self):
        d = base()
        ref(d, "D1")["map"]["1g"]["ta_kind"] = "preference"
        st = oc.analyze(d)
        self.assertNotIn("O13", [c for i, c, _ in st["warnings"] if i.startswith("C2")])
        self.assertTrue(any("Gurley" in m for _, _, m in st["info"]))

    def test_28_known_feature_weakens_nexus(self):
        d = base()
        d["secondary"]["items"][1]["feature_known_in"] = ["D3"]
        st = oc.analyze(d)
        self.assertTrue(any("Yita" in m for _, _, m in st["warnings"]))

    def test_29_invention_type_note(self):
        d = base()
        d["meta"]["invention_type"] = "selection"
        self.assertTrue(any("2019후10609" in m for _, _, m in oc.analyze(d)["info"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
