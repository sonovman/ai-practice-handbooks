#!/usr/bin/env python3
"""19편 도구 시험 (네트워크·모델 없이). 실행: python tools/test_think_tools.py"""
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import build_upload  # noqa: E402
import evidence_check as ec  # noqa: E402
import meeting_pack as mp  # noqa: E402

SRC = ("총 4,812건의 배송 중 4,437건이 사람의 원격 개입 없이 완료되어 자율 완료율은 92.2%였다.\n"
       "평균 배송 시간은 23.4분으로, 이륜차 배송의 평균 18.9분보다 길었다. 2025년 3월부터 8월까지.")


def levels(res):
    return [(i["level"], i["item"]) for i in res["items"]]


class Evidence(unittest.TestCase):
    def test_exact_quote_and_numbers_pass(self):
        out = "## [원문]\n- 결과: “자율 완료율은 92.2%였다.” 기간은 2025년.\n"
        r = ec.check(SRC, out)
        self.assertEqual(r["status"], "OK")

    def test_quote_with_line_break_in_source(self):
        src = "자율 완료율은\n92.2%였다."
        r = ec.check(src, "“자율 완료율은 92.2%였다.”")
        self.assertEqual(r["summary"]["인용 확인"], 1)

    def test_fabricated_quote_fails(self):
        r = ec.check(SRC, "“보행자의 81.6%가 로봇에 만족했다.”")
        self.assertIn(("FAIL", "인용(원문에 없음)"), levels(r))

    def test_altered_number_in_quote_fails(self):
        r = ec.check(SRC, "“사람의 원격 개입 없이 완료되어 자율 완료율은 95.2%였다.”")
        self.assertIn(("FAIL", "인용 속 수치가 원문과 다름"), levels(r))

    def test_small_wording_change_warns(self):
        r = ec.check(SRC, "“총 4,812건의 배송 중 4,437건이 사람의 개입 없이 완료되어 자율 완료율은 92.2%였다.”")
        self.assertIn(("WARN", "인용(부분 일치)"), levels(r))

    def test_unsupported_number_fails_but_derived_warns(self):
        r = ec.check(SRC, "운영 비용은 35% 절감되었다.")
        self.assertIn(("FAIL", "수치(원문에 없음)"), levels(r))
        r2 = ec.check(SRC, "계산: 375 ÷ 4,812 ≈ 7.8%")
        self.assertNotIn("FAIL", [lv for lv, _ in levels(r2)])

    def test_list_numbers_ignored(self):
        r = ec.check(SRC, "1. 첫째\n2. 둘째\n3. 셋째")
        self.assertEqual(r["status"], "OK")

    def test_fact_section_without_quote_warns(self):
        r = ec.check(SRC, "## [원문] 결과\n- 로봇은 이륜차보다 빨랐다: 평균 배송 시간 18.9분.\n")
        self.assertIn(("WARN", "[원문] 문장에 인용 없음"), levels(r))

    def test_cli_exit(self):
        d = Path(tempfile.mkdtemp())
        try:
            (d / "s.txt").write_text(SRC, encoding="utf-8")
            (d / "o.md").write_text("“보행자의 81.6%가 만족했다.”", encoding="utf-8")
            self.assertEqual(ec.main([str(d / "s.txt"), str(d / "o.md"), "--report", str(d / "r.md")]), 2)
            self.assertTrue((d / "r.md").exists())
        finally:
            shutil.rmtree(d)


class Meeting(unittest.TestCase):
    def test_new_and_collect(self):
        d = Path(tempfile.mkdtemp())
        try:
            (d / "agenda.md").write_text("신제품 출시 여부", encoding="utf-8")
            (d / "roles.md").write_text("## CFO\n돈\n\n## 경쟁사 법무팀(가상)\n회피\n", encoding="utf-8")
            m = d / "m"
            mp.main(["new", str(d / "agenda.md"), "--roles", str(d / "roles.md"), "--out", str(m)])
            files = sorted(p.name for p in m.glob("0*.md"))
            self.assertIn("01-CFO.md", files)
            self.assertIn("02-경쟁사-법무팀-가상.md", files)
            self.assertIn("독립적으로", (m / "01-CFO.md").read_text(encoding="utf-8"))
            with self.assertRaises(SystemExit):  # 의견서 부족
                mp.main(["collect", str(m)])
            (m / "opinions" / "CFO.md").write_text("보류", encoding="utf-8")
            (m / "opinions" / "경쟁사-법무팀-가상.md").write_text("반대", encoding="utf-8")
            mp.main(["collect", str(m)])
            chair = (m / "99-chair.md").read_text(encoding="utf-8")
            self.assertIn("다수결로 정하지 않는다", chair)
            self.assertIn("### CFO", chair)
            self.assertNotIn("## 반론(레드팀)", chair)
            (m / "opinions" / "_red-team.md").write_text("공통 가정 반박", encoding="utf-8")
            mp.main(["collect", str(m)])
            self.assertIn("## 반론(레드팀)", (m / "99-chair.md").read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(d)

    def test_roles_need_two(self):
        with self.assertRaises(SystemExit):
            mp.parse_roles("## 혼자\n설명")


class Upload(unittest.TestCase):
    def test_build_layouts(self):
        d = Path(tempfile.mkdtemp())
        try:
            made = build_upload.build(build_upload.ROOT, d)
            self.assertEqual(set(made), set(build_upload.SKILLS))
            z = zipfile.ZipFile(d / "ai-meeting.zip").namelist()
            self.assertIn("ai-meeting/SKILL.md", z)
            self.assertIn("ai-meeting/references/rubric.md", z)
            flat = zipfile.ZipFile(d / "slow-think-flat.zip").namelist()
            self.assertIn("SKILL.md", flat)
            self.assertTrue((d / "paper-brief" / "SKILL.md").is_file())
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main(verbosity=1)
