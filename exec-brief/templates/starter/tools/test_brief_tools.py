#!/usr/bin/env python3
"""20편 도구 시험 (네트워크·모델 없이). 실행: python tools/test_brief_tools.py"""
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import build_upload  # noqa: E402
import cite_check as cc  # noqa: E402
import evidence_check as ec  # noqa: E402
import term_check as tc  # noqa: E402

JUDG = "사건 2026나99999 특허권침해금지\n제1심판결 서울중앙지방법원 2025. 3. 14. 선고 2024가합99998 판결\n판결선고 2026. 9. 25."


class Cite(unittest.TestCase):
    def test_extract_formats(self):
        text = ("대법원 2020다12345, 2019후 1234, 헌재 2018헌바123, 2026년12월 기한, "
                "535 U.S. 722, 123 F.4th 45, 98 F. Supp. 3d 101, [2025] UKSC 12, [2024] EWHC 1383 (Pat), "
                "C-123/20, ECLI:EU:C:2021:123, 令和3年(受)第456号")
        keys = [k for _, k, _ in cc.extract(text)]
        for want in ["2020다12345", "2019후1234", "2018헌바123", "535 U.S. 722", "123 F.4th 45",
                     "98 F. Supp. 3d 101", "C-123/20", "ECLI:EU:C:2021:123"]:
            self.assertIn(want, keys)
        self.assertTrue(any("UKSC" in k for k in keys))
        self.assertTrue(any("令和3年" in k for k in keys))
        self.assertFalse(any(k.startswith("2026년") for k in keys))  # 날짜는 사건번호 아님

    def test_in_source_warns_outside_fails(self):
        r = cc.check("2026나99999 판결과 대법원 2019다999999 판결", [JUDG])
        lv = {i["citation"]: i["level"] for i in r["items"]}
        self.assertEqual(lv["2026나99999"], "WARN")
        self.assertEqual(lv["2019다999999"], "FAIL")
        self.assertEqual(r["status"], "FAIL")

    def test_no_source_lists_where(self):
        r = cc.check("535 U.S. 722", None)
        self.assertEqual(r["items"][0]["level"], "WARN")
        self.assertIn("CourtListener", r["items"][0]["where"])

    def test_no_citation_ok(self):
        self.assertEqual(cc.check("판례 인용 없음", [JUDG])["status"], "OK")


class Term(unittest.TestCase):
    def rows(self):
        return tc.load([str(ROOT / "glossary" / "*.csv")])

    def test_mistranslation_fails(self):
        r = tc.check("기소 이력 금반언에 따라 등가 원칙", self.rows())
        found = [i["found"] for i in r["items"] if i["level"] == "FAIL"]
        self.assertIn("기소 이력 금반언", found)
        self.assertIn("등가 원칙", found)

    def test_missing_concept_warns(self):
        r = tc.check("요약입니다.", self.rows(), source="The hazard ratio was 0.71.")
        self.assertTrue(any(i["term"] == "hazard ratio" and i["level"] == "WARN" for i in r["items"]))

    def test_non_obviousness_not_counted_as_obviousness(self):
        r = tc.check("비자명성 판단 없음", self.rows(), source="no view on non-obviousness")
        self.assertFalse(any(i["term"] == "obviousness" for i in r["items"]))

    def test_good_passes(self):
        r = tc.check("위험비는 0.71이었다.", self.rows(), source="The hazard ratio was 0.71.")
        self.assertFalse(any(i["term"] == "hazard ratio" for i in r["items"]))


class Evidence(unittest.TestCase):
    def test_date_change_caught(self):
        r = ec.check(JUDG, "선고 2026. 9. 15.")
        self.assertEqual(r["status"], "FAIL")

    def test_quote_ok(self):
        r = ec.check(JUDG, "“판결선고 2026. 9. 25.”")
        self.assertEqual(r["summary"]["인용 확인"], 1)


class Upload(unittest.TestCase):
    def test_layouts(self):
        d = Path(tempfile.mkdtemp())
        try:
            build_upload.build(ROOT, d)
            z = zipfile.ZipFile(d / "case-brief.zip").namelist()
            self.assertIn("case-brief/SKILL.md", z)
            self.assertIn("case-brief/references/jurisdictions.md", z)
            self.assertIn("case-brief/references/glossary/patent-legal.csv", z)
            self.assertIn("SKILL.md", zipfile.ZipFile(d / "exec-brief-flat.zip").namelist())
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main(verbosity=1)
