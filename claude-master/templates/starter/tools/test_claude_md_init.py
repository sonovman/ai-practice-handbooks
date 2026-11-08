#!/usr/bin/env python3
"""claude_md_init.py 시험. 표준 라이브러리만 사용.  python tools/test_claude_md_init.py"""
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import claude_md_init as M


def make_tree(root):
    root = Path(root)
    (root / "src").mkdir()
    (root / "docs").mkdir()
    (root / "work").mkdir()            # SKIP_DIRS
    (root / "__pycache__").mkdir()     # SKIP_DIRS
    (root / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
    (root / "docs" / "guide.md").write_text("# g\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[x]\n", encoding="utf-8")
    (root / "README.md").write_text("# r\n", encoding="utf-8")


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_tree(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_walk_skips_dirs(self):
        dirs, files = M.walk(self.root, 2)
        self.assertIn("src", dirs)
        self.assertIn("docs", dirs)
        self.assertNotIn("work", dirs)
        self.assertNotIn("__pycache__", dirs)
        self.assertIn("src/app.py", files)

    def test_detect_kind_python(self):
        kinds = M.detect_kind(self.root)
        self.assertIn("파이썬", kinds)

    def test_claude_md_has_sections_and_folders(self):
        dirs, files = M.walk(self.root, 2)
        md = M.build_claude_md(self.root, "테스트", dirs, files, M.detect_kind(self.root))
        for h in ["# 테스트", "## 1.", "## 2.", "## 3.", "## 4.", "## 5."]:
            self.assertIn(h, md)
        self.assertIn("`src/`", md)
        self.assertIn("INDEX.md", md)

    def test_index_lists_top_dirs(self):
        dirs, files = M.walk(self.root, 2)
        idx = M.build_index(self.root, "테스트", dirs, files)
        self.assertIn("`src/`", idx)
        self.assertIn("`docs/`", idx)

    def test_write_creates_files_and_no_overwrite(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            M.main([str(self.root), "--write"])
        self.assertTrue((self.root / "CLAUDE.md").exists())
        self.assertTrue((self.root / "INDEX.md").exists())
        # 다시 --write(무 force) → 덮어쓰지 않음
        (self.root / "CLAUDE.md").write_text("KEEP\n", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            M.main([str(self.root), "--write"])
        self.assertEqual((self.root / "CLAUDE.md").read_text(encoding="utf-8"), "KEEP\n")
        # --force → 덮어씀
        with redirect_stdout(io.StringIO()):
            M.main([str(self.root), "--write", "--force"])
        self.assertNotEqual((self.root / "CLAUDE.md").read_text(encoding="utf-8"), "KEEP\n")

    def test_preview_does_not_write(self):
        with redirect_stdout(io.StringIO()):
            M.main([str(self.root)])
        self.assertFalse((self.root / "CLAUDE.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
