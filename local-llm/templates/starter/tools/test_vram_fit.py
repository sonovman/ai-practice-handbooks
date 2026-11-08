#!/usr/bin/env python3
"""vram_fit.py 시험. 표준 라이브러리만 사용.  python tools/test_vram_fit.py"""
import io
import unittest
from contextlib import redirect_stdout

import vram_fit as V


class T(unittest.TestCase):
    def test_weight_math(self):
        self.assertAlmostEqual(V.weight_gb(27, 16), 54.0)
        self.assertAlmostEqual(V.weight_gb(27, 8), 27.0)
        self.assertAlmostEqual(V.weight_gb(594, 4), 297.0)

    def test_kv_upper_zero_without_dims(self):
        self.assertEqual(V.kv_upper_gb(0, 0, 1000, 2), 0.0)

    def test_kv_upper_positive(self):
        self.assertGreater(V.kv_upper_gb(48, 5120, 32000, 2), 0)

    def test_fits_ok(self):
        r = V.compute(27, 8, 48, 0, 0)   # 27GB weights on 48GB → OK
        self.assertEqual(r["status"], "OK")

    def test_spillover_weights(self):
        r = V.compute(27, 16, 24, 0, 0)  # 54GB on 24GB → SPILL
        self.assertEqual(r["status"], "SPILL")

    def test_warn_tight(self):
        r = V.compute(27, 8, 32, 0, 0)   # 29.16 on 32 → ~91% WARN
        self.assertEqual(r["status"], "WARN")

    def test_big_model_fits_at_low_bits(self):
        r = V.compute(594, 4, 384, 0, 0)  # 297 + 23.76 = 320.76 on 384 → OK (판정은 가중치 기준)
        self.assertEqual(r["status"], "OK")

    def test_kv_gb_counts_in_verdict(self):
        r = V.compute(594, 4, 384, 80, 0)  # +80 KV → 400.76 > 384 → SPILL
        self.assertEqual(r["status"], "SPILL")

    def test_exit_codes(self):
        with redirect_stdout(io.StringIO()):
            rc = V.main(["--params", "27", "--bits", "8", "--vram", "48"])
        self.assertEqual(rc, 0)
        with redirect_stdout(io.StringIO()):
            rc2 = V.main(["--params", "27", "--bits", "16", "--vram", "24"])
        self.assertEqual(rc2, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
