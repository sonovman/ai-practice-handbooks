#!/usr/bin/env python3
"""mini_triad 시험 — 실제 CLI 대신 가짜 BUILDER/REVIEWER 스크립트로 전 과정을 돌린다.
실행: python tools/test_mini_triad.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mini_triad  # noqa: E402

FAKE_BUILDER = textwrap.dedent('''
    import os, sys
    from pathlib import Path
    sys.stdin.read()
    mode = os.environ.get("FAKE_MODE", "good")
    Path("src").mkdir(exist_ok=True); Path("tests").mkdir(exist_ok=True)
    Path("src/calc.py").write_text("def add(a, b):\\n    return a + b\\n", encoding="utf-8")
    body = "a + b == 3" if mode != "badtest" else "False"
    Path("tests/test_calc.py").write_text(
        "import sys, unittest\\nsys.path.insert(0, 'src')\\nfrom calc import add\\n"
        "class T(unittest.TestCase):\\n    def test_add(self):\\n        a, b = 1, 2\\n"
        "        self.assertTrue(" + body + ")\\n        self.assertEqual(add(1, 2), 3)\\n", encoding="utf-8")
    if mode == "plant":
        Path(".mcp.json").write_text("{}", encoding="utf-8")
    if mode == "outside":
        Path("README.md").write_text("changed", encoding="utf-8")
''')

FAKE_REVIEWER = textwrap.dedent('''
    import os, sys
    text = sys.stdin.read()
    mode = os.environ.get("FAKE_MODE", "good")
    if ".mini_triad" in os.getcwd():
        print('{"verdict": "FAIL", "reasons": ["reviewer ran inside worktree"]}'); sys.exit(0)
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CODEX_API_KEY"):
        print('{"verdict": "FAIL", "reasons": ["api key leaked"]}'); sys.exit(0)
    if mode == "garbage":
        print("Looks fine to me!"); sys.exit(0)
    if "def add" not in text:
        print('{"verdict": "FAIL", "reasons": ["diff missing"]}'); sys.exit(0)
    print("검토 완료")
    print('{"verdict": "PASS", "reasons": []}')
''')


@unittest.skipUnless(shutil.which("git"), "git 필요")
class MiniTriadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.proj = self.tmp / "proj"
        self.proj.mkdir()
        g = lambda *a: subprocess.run(["git", *a], cwd=self.proj, check=True, capture_output=True)
        g("init", "-q")
        (self.proj / "README.md").write_text("demo\n", encoding="utf-8")
        g("add", "-A")
        g("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "base")
        (self.tmp / "b.py").write_text(FAKE_BUILDER, encoding="utf-8")
        (self.tmp / "r.py").write_text(FAKE_REVIEWER, encoding="utf-8")
        self.builder = [sys.executable, str(self.tmp / "b.py")]
        self.reviewer = [sys.executable, str(self.tmp / "r.py")]
        self.order = {"goal": "src/calc.py에 add(a, b)와 테스트", "allowed_paths": ["src/*", "tests/*", ".mcp.json"],
                      "max_files": 5}
        self.test_cmd = f'"{sys.executable}" -m unittest discover -s tests'
        self.old = dict(os.environ)

    def tearDown(self):
        os.environ.clear(); os.environ.update(self.old)
        subprocess.run(["git", "worktree", "prune"], cwd=self.proj, capture_output=True)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def go(self, mode, order=None):
        os.environ["FAKE_MODE"] = mode
        return mini_triad.run(self.proj, order or self.order, self.builder, self.reviewer, self.test_cmd,
                              timeout=60, log=lambda *_: None)

    def test_pass_and_original_untouched(self):
        os.environ["ANTHROPIC_API_KEY"] = "should-be-stripped"
        rep = self.go("good")
        self.assertEqual(rep["verdict"], "PASS", rep["steps"])
        self.assertFalse((self.proj / "src").exists(), "원본은 그대로여야 함")
        branches = subprocess.run(["git", "branch"], cwd=self.proj, capture_output=True, text=True).stdout
        self.assertIn(rep["branch"], branches)
        self.assertTrue(Path(rep["report_file"]).is_file())

    def test_garbage_review_fails_closed(self):
        self.assertEqual(self.go("garbage")["verdict"], "FAIL")

    def test_failing_test_fails(self):
        rep = self.go("badtest")
        self.assertEqual(rep["verdict"], "FAIL")
        self.assertEqual(rep["steps"][-1]["step"], "테스트")

    def test_planted_agent_config_stops_for_human(self):
        rep = self.go("plant")
        self.assertEqual(rep["verdict"], "HUMAN_REVIEW")

    def test_out_of_scope_write_fails(self):
        rep = self.go("outside")
        self.assertEqual(rep["verdict"], "FAIL")
        self.assertEqual(rep["steps"][-1]["step"], "스코프 가드")

    def test_split_cmd_strips_quotes(self):
        self.assertEqual(mini_triad.split_cmd('"/opt/py thon/python" -m pytest -q'),
                         ["/opt/py thon/python", "-m", "pytest", "-q"])

    def test_parse_verdict(self):
        self.assertEqual(mini_triad.parse_verdict('ok\n{"verdict":"PASS","reasons":[]}')[0], "PASS")
        self.assertEqual(mini_triad.parse_verdict('{"verdict":"maybe"}')[0], "FAIL")
        self.assertEqual(mini_triad.parse_verdict("")[0], "FAIL")
        self.assertEqual(mini_triad.parse_verdict('{"verdict": PASS}')[0], "FAIL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
