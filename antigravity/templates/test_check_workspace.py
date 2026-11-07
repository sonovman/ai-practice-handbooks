#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_workspace.py 시험 — python test_check_workspace.py"""
import json
import tempfile
import unittest
from pathlib import Path

import check_workspace as C

HERE = Path(__file__).resolve().parent


def levels(rows, area=None):
    return [r for r in rows if area is None or r[1] == area]


class Starter(unittest.TestCase):
    def test_starter_rules_and_skills_pass(self):
        rows = C.check(HERE / "starter", permissions=HERE / "starter" / "permissions.example.json")
        self.assertFalse([r for r in rows if r[0] == "실패"])
        self.assertEqual(len([r for r in rows if r[1] == "스킬" and r[0] == "통과"]), 2)

    def test_example_mcp_placeholder_caught(self):
        rows = C.check(HERE / "starter", mcp=HERE / "starter" / "mcp_config.example.json")
        mcp = levels(rows, "MCP")
        self.assertTrue(any(r[0] == "실패" and "예시 경로" in r[2] for r in mcp))
        self.assertFalse(any(r[0] == "통과" for r in mcp))

    def test_real_path_passes(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mcp.json"
            p.write_text(json.dumps({"mcpServers": {"cal": {"command": "node", "args": ["/home/me/mcp/index.js"]}}}), encoding="utf-8")
            rows = C.check(HERE / "starter", mcp=p)
            self.assertTrue(any(r[0] == "통과" and r[1] == "MCP" for r in rows))


class Bad(unittest.TestCase):
    def setUp(self):
        self.rows = C.check(HERE / "fixtures" / "bad", permissions=HERE / "fixtures" / "bad" / "permissions.json")
        self.text = "\n".join(r[2] for r in self.rows)

    def test_rules(self):
        for k in ("globs가 없습니다", "frontmatter가 필요", "trigger 'sometimes'"):
            self.assertIn(k, self.text)

    def test_skills(self):
        self.assertIn("소문자·숫자·하이픈", self.text)
        self.assertIn("description이 없습니다", self.text)

    def test_mcp(self):
        self.assertIn("httpUrl은 지원되지 않습니다", self.text)
        self.assertIn("상대 경로", self.text)
        self.assertIn("비밀값이 그대로", self.text)

    def test_permissions(self):
        self.assertIn("allow에 command(*)", self.text)
        self.assertIn("always-proceed", self.text)

    def test_bad_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "m.json"
            p.write_text('{ "mcpServers": { // 주석\n } }', encoding="utf-8")
            rows = C.check(HERE / "starter", mcp=p)
            self.assertTrue(any("JSON 문법 오류" in r[2] for r in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
