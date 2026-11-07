#!/usr/bin/env python3
"""윤문 도구 시험 (네트워크·실제 모델 없이). 실행: python tools/test_polish_tools.py"""
import http.server
import json
import shutil
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import ollama_polish  # noqa: E402
import polish_check  # noqa: E402
import setup_skills  # noqa: E402

KO = ('## 검토\n\n출원발명은 "적어도 2개의 센서"를 포함하는 구성이다. 다만, 선행문헌 2에 개시될 가능성이 있다.\n\n'
      '출원인은 2026년 12월 31일까지 의견서를 제출하여야 한다.')
EN = ("A device comprising at least two sensors, wherein the controller may adjust the gain. "
      "It is not suitable for use above 85 °C.")


def lv(res, item):
    return next(i["level"] for i in res["items"] if i["item"] == item)


class PolishCheck(unittest.TestCase):
    def test_identical_passes(self):
        r = polish_check.check(KO, KO, ["출원발명"])
        self.assertEqual(r["status"], "OK")
        self.assertEqual(r["language"], "ko")

    def test_quote_change_fails(self):
        r = polish_check.check(KO, KO.replace("적어도 2개의", "2개의"))
        self.assertEqual(lv(r, "인용문"), "FAIL")
        self.assertEqual(lv(r, "한정·조건 표현"), "FAIL")

    def test_date_change_fails(self):
        r = polish_check.check(KO, KO.replace("31일", "30일"))
        self.assertEqual(lv(r, "수치·날짜·단위"), "FAIL")

    def test_proviso_and_hedge(self):
        after = KO.replace("다만, ", "").replace("개시될 가능성이 있다", "개시되어 있다")
        r = polish_check.check(KO, after)
        self.assertEqual(lv(r, "한정·조건 표현"), "FAIL")
        self.assertEqual(lv(r, "완곡(가능·추측) 표현"), "WARN")

    def test_obligation_softened(self):
        r = polish_check.check(KO, KO.replace("제출하여야 한다", "제출한다"))
        self.assertEqual(lv(r, "당위·의무 표현"), "WARN")

    def test_heading_lost(self):
        r = polish_check.check(KO, KO.replace("## 검토\n\n", ""))
        self.assertEqual(lv(r, "제목"), "FAIL")

    def test_terms(self):
        r = polish_check.check(KO, KO.replace("출원발명", "이 발명"), ["출원발명"])
        self.assertEqual(lv(r, "정의 용어"), "FAIL")

    def test_english_limiters_and_negation(self):
        bad = EN.replace("comprising at least", "with").replace("may adjust", "adjusts").replace("not ", "")
        r = polish_check.check(EN, bad)
        self.assertEqual(r["language"], "en")
        self.assertEqual(lv(r, "한정·조건 표현"), "FAIL")
        self.assertEqual(lv(r, "부정 표현"), "WARN")
        self.assertEqual(r["status"], "FAIL")

    def test_change_rate_thresholds(self):
        self.assertLess(polish_check.change_rate("가나다라마바사", "가나다라마바사"), 0.01)
        r = polish_check.check("가나다라마바사아자차카타파하" * 3, "전혀 다른 문장입니다" * 3)
        self.assertEqual(lv(r, "변경률"), "FAIL")

    def test_cli_exit_codes(self):
        d = Path(tempfile.mkdtemp())
        try:
            (d / "a.md").write_text(KO, encoding="utf-8")
            (d / "b.md").write_text(KO.replace("31일", "30일"), encoding="utf-8")
            self.assertEqual(polish_check.main([str(d / "a.md"), str(d / "a.md")]), 0)
            self.assertEqual(polish_check.main([str(d / "a.md"), str(d / "b.md"), "--report", str(d / "r.md")]), 2)
            self.assertIn("실패", (d / "r.md").read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(d)


class FakeOllama(http.server.BaseHTTPRequestHandler):
    seen = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeOllama.seen.append(body)
        text = body["messages"][1]["content"].split("원문:\n", 1)[1]
        polished = text.replace("에 있어서, ", "에서 ")
        reply = {"message": {"content": "<think>생각</think>" + ollama_polish.START + "\n" + polished + "\n" + ollama_polish.END}}
        data = json.dumps(reply).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


class OllamaPolish(unittest.TestCase):
    def test_refuses_remote_host(self):
        with self.assertRaises(SystemExit):
            ollama_polish.check_local("https://example.com:11434")
        ollama_polish.check_local("http://127.0.0.1:11434")
        ollama_polish.check_local("http://localhost:11434")

    def test_split_keeps_headings_and_code(self):
        text = "# 제목\n\n문단 하나.\n\n```\ncode\n\nmore\n```\n\n문단 둘."
        kinds = [k for k, _ in ollama_polish.split_blocks(text, 1000)]
        self.assertEqual(kinds, ["keep", "edit", "keep", "edit"])

    def test_extract(self):
        s, e = ollama_polish.START, ollama_polish.END
        self.assertEqual(ollama_polish.extract("<think>x</think>" + s + "\n결과\n" + e, "원문"), "결과")
        self.assertEqual(ollama_polish.extract("엉뚱한 답", "원문"), "원문")

    def test_end_to_end_with_fake_server(self):
        srv = http.server.HTTPServer(("127.0.0.1", 0), FakeOllama)
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        d = Path(tempfile.mkdtemp())
        try:
            src = d / "doc.md"
            src.write_text("# 제목\n\n본 검토에 있어서, 출원발명은 신규성이 있을 수 있다.\n", encoding="utf-8")
            code = ollama_polish.main([str(src), "--host", "http://127.0.0.1:{}".format(srv.server_port),
                                       "--legal", "--model", "test"])
            outp = (d / "doc.polished.md").read_text(encoding="utf-8")
            self.assertIn("본 검토에서 출원발명은", outp)
            self.assertTrue(outp.startswith("# 제목"))
            self.assertTrue((d / "doc.polished.report.md").exists())
            self.assertIn(code, (0, 1))
            sent = FakeOllama.seen[-1]
            self.assertFalse(sent["stream"])
            self.assertIn("특허·법률", sent["messages"][0]["content"])
        finally:
            srv.shutdown()
            shutil.rmtree(d)


class SetupSkills(unittest.TestCase):
    def make_repos(self, d, symlink_as_text=False):
        ko = d / "im-not-ai"
        (ko / "codex/skills/humanize-korean/agents").mkdir(parents=True)
        (ko / "codex/skills/humanize-korean/SKILL.md").write_text("---\nname: humanize-korean\n---\n", encoding="utf-8")
        (ko / "codex/skills/humanize-korean/agents/openai.yaml").write_text("x", encoding="utf-8")
        (ko / "skills/humanize-korean/references").mkdir(parents=True)
        (ko / "skills/humanize-korean/references/quick-rules.md").write_text("# 규칙", encoding="utf-8")
        if symlink_as_text:  # Windows에서 심볼릭 링크가 텍스트 파일로 풀린 상황
            (ko / "codex/skills/humanize-korean/references").write_text("../../../skills/humanize-korean/references")
        (ko / "scripts").mkdir()
        for f in setup_skills.RUNTIME_SCRIPTS:
            (ko / "scripts" / f).write_text("# " + f, encoding="utf-8")
        (ko / "LICENSE").write_text("MIT", encoding="utf-8")
        en = d / "humanizer"
        en.mkdir()
        (en / "SKILL.md").write_text("---\nname: humanizer\n---\n", encoding="utf-8")
        (en / "LICENSE").write_text("MIT", encoding="utf-8")
        return ko, en

    def test_install_copies_real_scripts_and_refs(self):
        d = Path(tempfile.mkdtemp())
        try:
            ko, en = self.make_repos(d, symlink_as_text=True)
            skills = d / "proj" / ".agents" / "skills"
            dst = setup_skills.install_ko(ko, skills, "test")
            self.assertTrue((dst / "references" / "quick-rules.md").is_file())
            self.assertEqual((dst / "scripts" / "verify_gates.py").read_text(encoding="utf-8"), "# verify_gates.py")
            self.assertTrue((dst / "LICENSE").is_file())
            e = setup_skills.install_en(en, skills, "test")
            self.assertTrue((e / "SKILL.md").is_file())
        finally:
            shutil.rmtree(d)

    def test_portable_zip_layout(self):
        d = Path(tempfile.mkdtemp())
        old_root = setup_skills.ROOT
        try:
            ko, _ = self.make_repos(d)
            root = d / "proj"
            (root / "portable" / "legal-polish").mkdir(parents=True)
            (root / "portable" / "legal-polish" / "SKILL.md").write_text("---\nname: legal-polish\n---\n", encoding="utf-8")
            setup_skills.ROOT = root
            z, with_rules = setup_skills.build_portable(ko)
            names = zipfile.ZipFile(z).namelist()
            self.assertIn("legal-polish/SKILL.md", names)  # Claude.ai: 폴더가 ZIP 최상위
            self.assertIn("legal-polish/references/quick-rules-ko.md", names)
            flat = zipfile.ZipFile(root / "dist" / "legal-polish-flat.zip").namelist()
            self.assertIn("SKILL.md", flat)  # Copilot Cowork: SKILL.md가 최상위
            self.assertTrue((root / "dist" / "legal-polish" / "SKILL.md").is_file())  # Gemini: 폴더
            self.assertTrue(with_rules)
        finally:
            setup_skills.ROOT = old_root
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main(verbosity=1)
