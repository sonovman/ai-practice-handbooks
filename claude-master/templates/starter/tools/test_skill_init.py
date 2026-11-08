#!/usr/bin/env python3
"""skill_init.py 시험. 표준 라이브러리만 사용.  python tools/test_skill_init.py"""
import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import skill_init as S


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_creates_skill_files(self):
        with redirect_stdout(io.StringIO()):
            rc = S.main(["my-skill", "--out", self.out, "--desc", "엑셀에서 개인정보 칼럼 제거"])
        self.assertEqual(rc, 0)
        base = Path(self.out) / "my-skill"
        self.assertTrue((base / "SKILL.md").exists())
        self.assertTrue((base / "references" / "notes.md").exists())
        md = (base / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: my-skill", md)
        self.assertIn("엑셀에서 개인정보 칼럼 제거", md)

    def test_with_tool(self):
        with redirect_stdout(io.StringIO()):
            S.main(["t-skill", "--out", self.out, "--with-tool"])
        self.assertTrue((Path(self.out) / "t-skill" / "tools" / "run.py").exists())

    def test_bad_name_rejected(self):
        with self.assertRaises(SystemExit):
            S.main(["Bad_Name", "--out", self.out])
        with self.assertRaises(SystemExit):
            S.main(["has space", "--out", self.out])

    def test_long_desc_warns(self):
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            S.main(["ok-name", "--out", self.out, "--desc", "가" * (S.DESC_MAX + 5)])
        self.assertIn("주의", err.getvalue())

    def test_no_overwrite_without_force(self):
        with redirect_stdout(io.StringIO()):
            S.main(["dup", "--out", self.out])
        with self.assertRaises(SystemExit):
            S.main(["dup", "--out", self.out])
        # --force 면 통과
        with redirect_stdout(io.StringIO()):
            rc = S.main(["dup", "--out", self.out, "--force"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
