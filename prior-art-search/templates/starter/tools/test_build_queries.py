#!/usr/bin/env python3
"""build_queries.py 시험. 표준 라이브러리만 사용.  python tools/test_build_queries.py"""
import json
import unittest

import build_queries as B

PLAN = {
    "title": "t", "cutoff_date": "20200315",
    "features": [
        {"id": "F1", "ko": ["스크루"], "en": ["screw", "auger"]},
        {"id": "F2", "core": True, "ko": ["리브"], "en": ["rib"]},
        {"id": "F3", "ko": ["착즙"], "en": ["juicer", "juice extractor"]},
    ],
    "classes": {"cpc": ["A47J19/025"]},
    "queries": [
        {"id": "Q1", "features": ["F1", "F3"], "field": "ta"},
        {"id": "Q3", "features": ["F2", "F1"], "field": "claims", "near": 10, "use_class": True},
    ],
}


class T(unittest.TestCase):
    def test_kipris_ta_includes_title_and_abstract(self):
        out, _ = B.build_all(PLAN)
        q1 = out["KIPRIS"][0]["expr"]
        self.assertIn("스크루", q1)          # 한국어 키워드
        self.assertIn("*", q1)                # AND = *
        self.assertIn("TL=[", q1)             # ta → TL
        self.assertIn("AB=[", q1)             # 개선: ta는 요약(AB)까지 포함
        self.assertIn("]+AB=[", q1)           # TL=[...]+AB=[...]

    def test_google_english_and_near(self):
        out, _ = B.build_all(PLAN)
        g1 = out["GooglePatents"][0]["expr"]
        self.assertIn("screw", g1)            # 영어 키워드
        self.assertIn(" AND ", g1)
        g3 = out["GooglePatents"][1]["expr"]
        self.assertIn("NEAR/10", g3)          # 근접

    def test_google_multiword_phrase_quoted(self):
        out, _ = B.build_all(PLAN)
        g1 = out["GooglePatents"][0]["expr"]
        self.assertIn('"juice extractor"', g1)  # 개선: 여러 단어 표현은 따옴표

    def test_google_url_has_before_cutoff(self):
        out, _ = B.build_all(PLAN)
        url = out["GooglePatents"][0]["url"]
        self.assertIn("before=publication:20200315", url)

    def test_espacenet_and_patentscope_fields(self):
        out, _ = B.build_all(PLAN)
        self.assertIn("ta=", out["Espacenet"][0]["expr"])
        self.assertIn("EN_CL:", out["PATENTSCOPE"][1]["expr"])  # claims → EN_CL

    def test_kr_no_cutoff_variant(self):
        out, _ = B.build_all(PLAN)
        self.assertIn("_KR_no_cutoff", out)
        self.assertEqual(len(out["_KR_no_cutoff"]), len(PLAN["queries"]))

    def test_sheet_mentions_terms_and_safety(self):
        out, cutoff = B.build_all(PLAN)
        sheet = B.to_sheet(PLAN, out, cutoff)
        self.assertIn("자동 수집", sheet)     # 약관 주의
        self.assertIn("확대된 선출원", sheet)


if __name__ == "__main__":
    unittest.main(verbosity=2)
