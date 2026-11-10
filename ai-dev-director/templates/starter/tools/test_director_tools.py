#!/usr/bin/env python3
"""키트 도구 시험 (표준 라이브러리 unittest). 실행: python tools/test_director_tools.py"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apply_gate  # noqa: E402
import director_preflight as pf  # noqa: E402
import role_matrix  # noqa: E402

SAMPLE_CONFIG = """head:
  provider: claude
autonomy:
  enabled: true
  head_proxy: true   # 사람 대신 결정
  auto_apply: on_pass
verification:
  test_command: "python -m pytest tests/"
solomon:
  allowed_roots:
    - "D:/work"
  denied:
    - "D:/work/ai-dev-director"
"""


class PreflightTests(unittest.TestCase):
    def test_runtime_blocks_when_fewer_than_two_clis(self):
        which = lambda n: "/usr/bin/" + n if n in ("git", "claude") else None
        codes = {f["code"]: f["level"] for f in pf.check_runtime(which=which, version=(3, 11))}
        self.assertEqual(codes["CLI_TOO_FEW"], "BLOCK")

    def test_runtime_warns_on_two_clis_and_blocks_old_python(self):
        which = lambda n: "/x/" + n if n in ("git", "claude", "codex") else None
        codes = {f["code"]: f["level"] for f in pf.check_runtime(which=which, version=(3, 8))}
        self.assertEqual(codes["PYTHON_OLD"], "BLOCK")
        self.assertEqual(codes["CLI_TWO_ONLY"], "WARN")

    def test_env_flags_keys_director_does_not_strip(self):
        found = pf.check_env({"ANTHROPIC_API_KEY": "x", "CODEX_API_KEY": "y", "CLAUDE_CODE_USE_BEDROCK": "1"})
        levels = {(f["code"], f["level"]) for f in found}
        self.assertIn(("KEY_STRIPPED", "INFO"), levels)
        warned = " ".join(f["message"] for f in found if f["level"] == "WARN")
        self.assertIn("CODEX_API_KEY", warned)
        self.assertIn("CLAUDE_CODE_USE_BEDROCK", warned)

    def test_yaml_reader_ignores_comments(self):
        self.assertEqual(pf._yaml_value(SAMPLE_CONFIG, "autonomy.head_proxy"), "true")
        self.assertEqual(pf._yaml_value(SAMPLE_CONFIG, "autonomy.auto_apply"), "on_pass")
        self.assertEqual(pf._yaml_list(SAMPLE_CONFIG, "solomon.allowed_roots"), ["D:/work"])

    def test_config_warns_on_risky_defaults(self):
        d = tempfile.mkdtemp()
        try:
            Path(d, "config.yaml").write_text(SAMPLE_CONFIG, encoding="utf-8")
            Path(d, "companion.json").write_text('{"port": 8081, "allowed_projects": []}', encoding="utf-8")
            codes = {f["code"] for f in pf.check_config(d)}
            self.assertIn("AUTO_APPLY_ON", codes)
            self.assertIn("HEAD_PROXY_ON", codes)
            self.assertIn("SOLOMON_ROOTS", codes)
        finally:
            shutil.rmtree(d)

    def test_project_flags_auto_exec_files(self):
        d = tempfile.mkdtemp()
        try:
            Path(d, ".claude").mkdir()
            Path(d, ".claude", "settings.json").write_text("{}", encoding="utf-8")
            Path(d, ".env").write_text("TOKEN=x", encoding="utf-8")
            codes = [f["code"] for f in pf.check_project(d)]
            self.assertIn("AUTO_EXEC_FILE", codes)
            self.assertIn("DOTENV", codes)
        finally:
            shutil.rmtree(d)

    def test_main_exit_code(self):
        d = tempfile.mkdtemp()
        try:
            self.assertEqual(pf.main(["--director", d, "--json"]), 1)  # config.yaml 없음 → BLOCK
        finally:
            shutil.rmtree(d)


class ApplyGateTests(unittest.TestCase):
    def test_classify(self):
        res = apply_gate.classify([
            "src/calc.py", "tests/test_calc.py", ".claude/settings.json", ".claude/hooks/x.sh",
            ".mcp.json", "tests/conftest.py", "package.json", "../outside.py", ".git/config", "",
        ])
        self.assertEqual(sorted(res["ok"]), ["src/calc.py", "tests/test_calc.py"])
        reviewed = {r["path"] for r in res["review"]}
        self.assertTrue({".claude/settings.json", ".claude/hooks/x.sh", ".mcp.json",
                         "tests/conftest.py", "package.json"} <= reviewed)
        blocked = {r["path"] for r in res["block"]}
        self.assertEqual(blocked, {"../outside.py", ".git/config"})
        self.assertEqual(apply_gate.decide(res), "BLOCK")

    def test_decide_pass_and_review(self):
        self.assertEqual(apply_gate.decide(apply_gate.classify(["src/a.py"])), "PASS")
        self.assertEqual(apply_gate.decide(apply_gate.classify(["src\\a.py", "AGENTS.md"])), "HUMAN_REVIEW")

    @unittest.skipUnless(shutil.which("git"), "git 필요")
    def test_worktree_mode_with_real_git(self):
        d = tempfile.mkdtemp()
        try:
            run = lambda *a: subprocess.run(a, cwd=d, check=True, capture_output=True)
            run("git", "init", "-q")
            run("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "base")
            Path(d, "src").mkdir()
            Path(d, "src", "calc.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
            self.assertEqual(apply_gate.main(["--worktree", d]), 0)
            Path(d, ".mcp.json").write_text("{}", encoding="utf-8")
            self.assertEqual(apply_gate.main(["--worktree", d]), 2)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_unreadable_input_fails_closed(self):
        self.assertEqual(apply_gate.main(["--worktree", os.path.join(tempfile.gettempdir(), "no-such-dir-xyz")]), 1)


class RoleMatrixTests(unittest.TestCase):
    def test_default_layout_is_ok(self):
        self.assertEqual(role_matrix.assess("claude", "agy", "codex")["level"], "OK")

    def test_same_vendor_builder_reviewer_blocks(self):
        self.assertEqual(role_matrix.assess("claude", "codex", "codex")["level"], "BLOCK")

    def test_head_reviewer_same_vendor_warns(self):
        a = role_matrix.assess("claude", "codex", "claude")
        self.assertEqual(a["level"], "WARN")

    def test_recommend_with_two_clis_avoids_self_review(self):
        r = role_matrix.recommend(["claude", "codex"])
        self.assertNotEqual(r["vendors"]["builder"], r["vendors"]["reviewer"])
        self.assertNotEqual(r["vendors"]["head"], r["vendors"]["reviewer"])
        self.assertEqual(r["level"], "OK")
        # 대체 REVIEWER가 BUILDER와 같은 회사가 되지 않아야 한다
        self.assertEqual(r["failover"]["reviewer"], ["사람 검수(대체 REVIEWER 없음)"])

    def test_recommend_three(self):
        r = role_matrix.recommend(["claude", "codex", "antigravity"])
        self.assertEqual(r["level"], "OK")
        self.assertEqual(r["roles"], {"head": "claude", "builder": "agy", "reviewer": "codex"})
        self.assertIn("codex", r["failover"]["builder"])

    def test_unknown_cli(self):
        with self.assertRaises(ValueError):
            role_matrix.assess("gpt", "agy", "codex")


if __name__ == "__main__":
    unittest.main(verbosity=2)
