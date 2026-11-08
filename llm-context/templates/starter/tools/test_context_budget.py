#!/usr/bin/env python3
"""context_budget.py 시험. 표준 라이브러리만 사용.  python tools/test_context_budget.py"""
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import context_budget as C


class T(unittest.TestCase):
    def test_est_tokens_cjk_heavier(self):
        kor = C.est_tokens("가" * 160)   # 160 CJK / 1.6 = 100
        eng = C.est_tokens("a" * 160)    # 160 / 4 = 40
        self.assertEqual(kor, 100)
        self.assertEqual(eng, 40)
        self.assertGreater(kor, eng)

    def test_analyze_pct_and_status(self):
        r = C.analyze([("a", 40000), ("b", 10000)], 100000)
        self.assertEqual(r["total"], 50000)
        self.assertEqual(r["status"], "OK")   # exactly 50% → OK
        r2 = C.analyze([("a", 60000)], 100000)
        self.assertEqual(r2["status"], "WARN")
        r3 = C.analyze([("a", 85000)], 100000)
        self.assertEqual(r3["status"], "HIGH")

    def test_text_tokens_item(self):
        with redirect_stdout(io.StringIO()):
            rc = C.main(["--window", "100000", "--text-tokens", "system=1200"])
        self.assertIn(rc, (0, 1, 2))

    def test_file_counted(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "CLAUDE.md"; f.write_text("가" * 1600, encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                rc = C.main([str(f), "--window", "200000"])
            self.assertEqual(rc, 0)   # 1000 tokens / 200000 → OK

    def test_high_exit_code(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "big.md"; f.write_text("가" * 16000, encoding="utf-8")  # 10000 tokens
            with redirect_stdout(io.StringIO()):
                rc = C.main([str(f), "--window", "11000"])  # 10000/11000 = 91% → HIGH
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
