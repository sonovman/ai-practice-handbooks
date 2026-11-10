#!/usr/bin/env python3
"""patent-intelligence 도구 시험 (핸드북 34).  python tools/test_pi_tools.py"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pi_common as C  # noqa: E402
import pi_gate as G  # noqa: E402
import pi_intake as I  # noqa: E402
import pi_stats as S  # noqa: E402
import report_lint as L  # noqa: E402
import render_report as RR  # noqa: E402
import export_for_copilot as EX  # noqa: E402

PROJECT = {"data_date": "2026-11-01", "trend_base_date": "2024-11-01", "lag_months": 18}


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        subprocess.run([sys.executable, str(HERE / "make_sample.py"), str(cls.tmp)], check=True, capture_output=True)
        cls.res = I.run(cls.tmp / "this_round.xlsx", PROJECT, cls.tmp / "prev_round.csv", cls.tmp / "pdf")
        cls.by = {r["id"]: r for r in cls.res["records"]}
        cls.st = S.stats(cls.res, cls.tmp / "clusters.csv", cls.tmp / "scores.csv")


class CommonTests(unittest.TestCase):
    def test_dates(self):
        self.assertEqual(C.parse_date("2025.03.04"), "2025-03-04")
        self.assertEqual(C.parse_date("20250304"), "2025-03-04")
        self.assertEqual(C.parse_date("45000"), "2023-03-15")
        self.assertIsNone(C.parse_date("미상"))

    def test_doc_type_rules(self):
        self.assertEqual(C.doc_type("KR", "", "20-2025-0001234", "", ""), "utility")
        self.assertEqual(C.doc_type("CN", "", "202520990042.1", "", ""), "utility")
        self.assertEqual(C.doc_type("CN", "", "202410990041.5", "CN 1 A", ""), "invention")
        self.assertEqual(C.doc_type("JP", "", "", "", "JP 3200001 U"), "utility")
        self.assertEqual(C.doc_type("US", "", "", "", "US D1,000,001 S"), "design")

    def test_country_from_number(self):
        self.assertEqual(C.norm_country("", "", "CN 129900041 A"), "CN")
        self.assertEqual(C.norm_country("대한민국"), "KR")

    def test_xlsx_roundtrip_and_header_detection(self):
        tmp = Path(tempfile.mkdtemp()) / "t.xlsx"
        C.write_xlsx(tmp, [["제목 줄"], [], ["국가코드", "출원번호", "공개번호", "출원인"], ["KR", "10-2025-0000001", "KR 10-2026-0000001 A", "갑"]])
        al = C.load_aliases(HERE.parent / "config" / "column_aliases.csv")
        header, fields, unknown, rows = C.read_table(tmp, al)
        self.assertEqual(fields, ["country", "app_no", "pub_no", "applicant"])
        self.assertEqual(rows[0]["applicant"], "갑")


class IntakeTests(Base):
    def test_counts(self):
        s = self.res["summary"]
        self.assertEqual(s["rows_read"], 21)
        self.assertEqual(s["documents"], 20)          # 중복 1행 합침
        self.assertEqual(s["new_observed"], 7)        # 직전 회차 비교
        self.assertEqual(s["trend_scope"], 16)
        self.assertEqual(s["lag_zone_docs"], 1)

    def test_duplicate_merged_keeps_numbers(self):
        self.assertEqual(self.by["D006"]["rows"], [10, 25])
        self.assertTrue(self.by["D006"]["pub_no"].startswith("KR 10-2025"))

    def test_no_number_is_error(self):
        codes = [(i["code"], i.get("id")) for i in self.res["issues"]]
        self.assertIn(("I01", "D020"), codes)
        self.assertFalse(self.by["D020"]["evidence_ok"])

    def test_applicant_alias_group_and_english(self):
        self.assertEqual(self.by["D004"]["applicant_canon"], "가나전자 주식회사")   # 영문 원문도 같은 회사로
        self.assertEqual(self.by["D012"]["group"], "가나그룹")                    # 계열사 묶음
        self.assertEqual(self.by["D011"]["applicant_display"], "다라테크 주식회사 (영문명 미확인)")
        self.assertIn("비공식 번역", self.by["D009"]["applicant_display"])

    def test_family_and_signal(self):
        self.assertEqual(self.by["D003"]["family_key"], self.by["D004"]["family_key"])
        self.assertEqual(self.res["summary"]["families"], 16)
        self.assertEqual(self.res["summary"]["tech_signals"], 15)

    def test_cn_dual_candidate_only(self):
        p = self.res["cn_dual_candidates"]
        self.assertEqual(len(p), 1)
        self.assertEqual((p[0]["invention"], p[0]["utility"]), ("D009", "D010"))
        self.assertEqual(p[0]["status"], "CN Dual-filing Candidate")
        self.assertEqual(self.by["D009"]["signal_key"], self.by["D010"]["signal_key"])

    def test_missing_pdfs(self):
        miss = sorted(i["id"] for i in self.res["issues"] if i["code"] == "I03")
        self.assertEqual(miss, ["D002", "D011"])

    def test_new_flag_fallback_without_previous(self):
        r = I.run(self.tmp / "this_round.xlsx", PROJECT)
        self.assertEqual(r["summary"]["new_basis"], "신규 표시 열")
        self.assertEqual(r["summary"]["new_observed"], 8)  # D006: 표시 열은 신규, 직전 목록엔 이미 있음 → 두 기준이 다를 수 있음


class StatsTests(Base):
    def test_lag_year(self):
        self.assertEqual(self.st["lag_start_year"], 2025)
        self.assertTrue(self.st["trend"][2025]["incomplete"])
        self.assertFalse(self.st["trend"][2024]["incomplete"])

    def test_group_counts(self):
        g = {x["group"]: x for x in self.st["groups"]}
        self.assertEqual(g["가나그룹"]["signals"], 6)
        self.assertEqual(self.st["multi_country_signals_by_group"], {"가나그룹": 1})

    def test_grade_candidates(self):
        c = self.st["clusters"]
        self.assertEqual(c["건조·분쇄"]["grade_candidate"], "T1 후보")
        self.assertEqual(c["건조·분쇄"]["independent_groups"], 4)
        self.assertEqual(c["미생물 발효"]["grade_candidate"], "T2 후보")
        self.assertIn("근거 최소", c["냄새 저감"]["note"])

    def test_scores_scaling_cap_and_exception(self):
        sc = {x["id"]: x for x in self.st["scores"]}
        self.assertEqual(sc["D007"]["full"], 80)
        self.assertAlmostEqual(sc["D007"]["scaled"], 81.2)
        self.assertTrue(sc["D017"]["recommend"])
        self.assertEqual(sc["D017"]["basis"], "Strategic Exception")
        self.assertFalse(sc["D020"]["recommend"])         # 번호 없음
        self.assertLessEqual(sum(1 for x in sc.values() if x["recommend"]), 5)

    def test_cap_over_five_warns(self):
        p = self.tmp / "many.csv"
        lines = ["id,relevance,proximity,design_around,persistence,expansion,info_value,strategic_exception,reason"]
        for i in range(1, 8):
            lines.append("D%03d,25,20,20,15,10,10,," % i)
        p.write_text("\n".join(lines), encoding="utf-8")
        st = S.stats(self.res, None, p)
        self.assertEqual(sum(1 for x in st["scores"] if x["recommend"]), 5)
        self.assertTrue(any(i["code"] == "S05" for i in st["issues"]))

    def test_score_range_error(self):
        p = self.tmp / "bad.csv"
        p.write_text("id,relevance,proximity,design_around,persistence,expansion,info_value\nD001,30,0,0,0,0,0\nD999,1,1,1,1,1,1\n", encoding="utf-8")
        codes = {i["code"] for i in S.stats(self.res, None, p)["issues"]}
        self.assertTrue({"S03", "S04"} <= codes)

    def test_svg_written(self):
        out = self.tmp / "c.svg"
        S.svg_trend(self.st, out)
        self.assertIn("미완결", out.read_text(encoding="utf-8"))


class GateTests(unittest.TestCase):
    def setUp(self):
        self.p = Path(tempfile.mkdtemp()) / "state.json"
        self.st = G.init(self.p, "R1")

    def test_interpret(self):
        self.assertEqual(G.interpret("승인"), "approve")
        self.assertEqual(G.interpret("계속"), "implicit_approve")
        self.assertEqual(G.interpret("계속", accept_continue=False), "unclear")
        self.assertEqual(G.interpret("3번 빼고 다시"), "revise")
        self.assertEqual(G.interpret("추가자료 보낼게요"), "add_data")
        self.assertEqual(G.interpret(""), "wait")
        self.assertEqual(G.interpret("음…"), "unclear")

    def test_cannot_skip_gate(self):
        G.submit(self.st, "ANALYSIS", "a.md")
        with self.assertRaises(SystemExit):
            G.submit(self.st, "REPORT", "r.md")

    def test_silence_does_not_approve(self):
        G.submit(self.st, "ANALYSIS", "a.md")
        st, kind, _ = G.reply(self.st, "")
        self.assertEqual(kind, "wait")
        self.assertNotIn("ANALYSIS", st["approved"])

    def test_revise_then_continue_sets_baseline(self):
        G.submit(self.st, "ANALYSIS", "a.md")
        G.reply(self.st, "결론 2 수정해 줘")
        G.submit(self.st, "ANALYSIS", "a.md")
        st, kind, _ = G.reply(self.st, "계속")
        self.assertEqual(st["baseline"]["version"], 2)
        self.assertIn("묵시", st["baseline"]["how"])
        G.submit(st, "REPORT", "r.md")  # 이제 허용

    def test_candidates_need_report_approval(self):
        G.submit(self.st, "ANALYSIS", "a.md")
        G.reply(self.st, "승인")
        G.submit(self.st, "REPORT", "r.md")
        with self.assertRaises(SystemExit):
            G.submit(self.st, "CANDIDATES", "c.md")


class LintTests(Base):
    def setUp(self):
        self.base = "[B01] 근거 [B02] 근거"

    def lint(self, text, baseline=True):
        return {i["code"] for i in L.lint(text, self.res, self.st, self.base if baseline else None)}

    def test_good_line(self):
        t = "- US 12,990,031 B2 ALPHA HOME INC. — 동시 건조 [B01]\n"
        self.assertEqual(self.lint(t), set())

    def test_missing_english_and_unknown_number(self):
        t = "- US 2025/0900011 A1 가나전자 — x\n- CN 129999999 A 누구\n"
        codes = self.lint(t)
        self.assertIn("R02", codes)
        self.assertIn("R03", codes)

    def test_application_number_used(self):
        self.assertIn("R04", self.lint("- KR 10-2024-0099021 가나전자 주식회사 (GANA ELECTRONICS CO. LTD.)\n"))

    def test_corpus_legal_counts_lag_baseline(self):
        t = ("Corpus 기준 공개특허 모집단 99건\n- 당사 제품이 침해한다\n- 2025년 출원이 감소했다\n- 결론 [B07]\n")
        codes = self.lint(t)
        self.assertTrue({"R01", "R08", "R11", "R09", "R10"} <= codes)

    def test_candidate_and_action_caps(self):
        rows = "\n".join("| %d | KR 10-2025-0990021 A | 가나전자 주식회사 (GANA ELECTRONICS CO. LTD.) |" % i for i in range(6))
        t = "## 정밀분석 후보\n| 순위 | 문헌 | 출원인 |\n|---|---|---|\n%s\n## CEO Action Items\n%s\n" % (rows, "\n".join("%d. 일" % i for i in range(1, 7)))
        codes = self.lint(t)
        self.assertTrue({"R05", "R06"} <= codes)

    def test_trend_needs_strength(self):
        t = "## 3. 핵심 기술동향\n### 3.1 무엇\n본문\n### 3.2 다른 것\n근거강도 중\n"
        issues = L.lint(t, self.res, self.st, None)
        self.assertEqual(sum(1 for i in issues if i["code"] == "R07"), 1)

    def test_sample_reports(self):
        rep = HERE.parent / "sample" / "work" / "reports"
        if not rep.exists():
            self.skipTest("sample 없음")
        intake = json.loads((HERE.parent / "sample" / "work" / "01_intake.json").read_text(encoding="utf-8"))
        stats = json.loads((HERE.parent / "sample" / "work" / "02_stats.json").read_text(encoding="utf-8"))
        base = (HERE.parent / "sample" / "work" / "03_analysis.md").read_text(encoding="utf-8")
        good = L.lint((rep / "report.md").read_text(encoding="utf-8"), intake, stats, base)
        bad = L.lint((rep / "report_bad.md").read_text(encoding="utf-8"), intake, stats, base)
        self.assertEqual([i for i in good if i["level"] == "error"], [])
        self.assertGreaterEqual(sum(1 for i in bad if i["level"] == "error"), 8)


class CopilotExportTests(unittest.TestCase):
    def test_export_formats_copilot_can_read(self):
        work = HERE.parent / "sample" / "work"
        if not (work / "02_stats.md").exists():
            self.skipTest("sample 없음")
        out = Path(tempfile.mkdtemp())
        made = EX.export(work, out)
        self.assertIn("02_stats.html", made)
        self.assertIn("scores.xlsx", made)
        self.assertIn("state.txt", made)
        allowed = {".html", ".xlsx", ".txt"}
        self.assertTrue(all(Path(m).suffix in allowed for m in made))
        self.assertIn("<svg", (out / "02_stats.html").read_text(encoding="utf-8"))


class RenderTests(unittest.TestCase):
    def test_render(self):
        h = RR.render("# 제목\n\n문단 **굵게**\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n- 하나\n- 둘\n\n![차트](c.svg)\n")
        for s in ("<h1>제목</h1>", "<strong>굵게</strong>", "<td>1</td>", "<li>둘</li>", '<img alt="차트" src="c.svg">'):
            self.assertIn(s, h)


if __name__ == "__main__":
    C.utf8_console()
    unittest.main(verbosity=2)
