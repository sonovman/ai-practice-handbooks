#!/usr/bin/env python3
"""build_upload 시험. 실행: python tools/test_build_upload.py"""
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_upload  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "triad-dev-review"


class BuildUploadTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def test_real_skill_validates(self):
        self.assertEqual(build_upload.validate(SKILL), "triad-dev-review")

    def test_three_forms(self):
        z, flat, folder = build_upload.build(SKILL, self.out)
        with zipfile.ZipFile(z) as f:
            self.assertIn("triad-dev-review/SKILL.md", f.namelist())
        with zipfile.ZipFile(flat) as f:
            names = f.namelist()
            self.assertIn("SKILL.md", names)
            self.assertIn("references/review-checklist.md", names)
            self.assertTrue(all(n.count("/") <= 2 for n in names), "M365는 깊이 3 이하")
        self.assertTrue((folder / "SKILL.md").is_file())

    def test_bad_skill_rejected(self):
        bad = self.out / "Bad_Name"
        bad.mkdir()
        (bad / "SKILL.md").write_text("---\nname: Bad_Name\ndescription: x\n---\nbody\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_upload.validate(bad)
        long = self.out / "long-desc"
        long.mkdir()
        (long / "SKILL.md").write_text("---\nname: long-desc\ndescription: " + "가" * 201 + "\n---\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_upload.validate(long)


if __name__ == "__main__":
    unittest.main(verbosity=2)
