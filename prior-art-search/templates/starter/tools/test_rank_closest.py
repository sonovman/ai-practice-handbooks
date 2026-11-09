#!/usr/bin/env python3
"""rank_closest.py 시험. 표준 라이브러리만 사용.  python tools/test_rank_closest.py"""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import rank_closest as R

PLAN = {
    "title": "t", "cutoff_date": "20200315",
    "features": [{"id": "F1"}, {"id": "F2", "core": True}, {"id": "F3"}],
}
MAP = {
    "documents": [
        {"pub": "US...02", "publication_date": "20150505", "same_field": True, "same_problem": True,
         "features": {"F1": {"grade": "◐", "evidence": "[0012]", "gap_type": "design"},
                      "F2": {"grade": "●", "evidence": "[0020]"}, "F3": {"grade": "●", "evidence": "[0001]"}}},
        {"pub": "KR...01", "publication_date": "20110101", "same_field": True, "same_problem": False,
         "features": {"F1": {"grade": "●", "evidence": "[0015]"}, "F2": {"grade": "○"}, "F3": {"grade": "●", "evidence": "[0002]"}}},
        {"pub": "EP...04", "publication_date": "20210101", "same_field": False, "same_problem": True,
         "features": {"F1": {"grade": "●", "evidence": "[0010]"}, "F2": {"grade": "●", "evidence": "[0018]"}, "F3": {"grade": "◐", "evidence": "[0003]"}}},
    ]
}


def run(plan=PLAN, mp=MAP):
    with tempfile.TemporaryDirectory() as d:
        pp = Path(d) / "p.json"; mpp = Path(d) / "m.json"
        pp.write_text(json.dumps(plan), encoding="utf-8")
        mpp.write_text(json.dumps(mp), encoding="utf-8")
        plan2, mp2, fids = R.load(str(pp), str(mpp))
        return R.rank(plan2, mp2, fids)


class T(unittest.TestCase):
    def test_core_weight_default_3(self):
        _, w, _ = run()
        self.assertEqual(w["F2"], 3.0)
        self.assertEqual(w["F1"], 1.0)

    def test_us_is_top_B(self):
        res, _, _ = run()
        self.assertEqual(res[0]["pub"], "US...02")
        self.assertTrue(res[0]["cls"].startswith("B"))

    def test_late_doc_is_X(self):
        res, _, _ = run()
        ep = [r for r in res if r["pub"] == "EP...04"][0]
        self.assertTrue(ep["cls"].startswith("X"))   # 20210101 ≥ cutoff

    def test_kr_becomes_C_supporting(self):
        # KR...01 이 US...02 의 부족 특징 F1 을 ●로 개시 → C 보조
        res, _, _ = run()
        kr = [r for r in res if r["pub"] == "KR...01"][0]
        self.assertEqual(kr["cls"], "C 보조 문헌")

    def test_all_full_is_A(self):
        mp = copy.deepcopy(MAP)
        mp["documents"][0]["features"]["F1"] = {"grade": "●", "evidence": "[0012]"}
        res, _, _ = run(mp=mp)
        us = [r for r in res if r["pub"] == "US...02"][0]
        self.assertTrue(us["cls"].startswith("A"))

    def test_evidence_missing_blocks(self):
        mp = copy.deepcopy(MAP)
        mp["documents"][0]["features"]["F2"] = {"grade": "●"}  # 근거 없음
        with self.assertRaises(SystemExit):
            run(mp=mp)

    def test_teaching_away_excluded_from_B(self):
        mp = copy.deepcopy(MAP)
        mp["documents"][0]["teaching_away"] = True
        res, _, _ = run(mp=mp)
        us = [r for r in res if r["pub"] == "US...02"][0]
        self.assertFalse(us["cls"].startswith("B"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
