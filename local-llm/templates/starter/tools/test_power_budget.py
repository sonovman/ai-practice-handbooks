#!/usr/bin/env python3
"""power_budget.py 시험. 표준 라이브러리만 사용.  python tools/test_power_budget.py"""
import io
import unittest
from contextlib import redirect_stdout

import power_budget as P


class T(unittest.TestCase):
    def test_wall_includes_psu_loss(self):
        r = P.compute(4, 350, 280, 0.9, 120, 15)
        # DC = 1400+280 = 1680; wall = 1680/0.9 = 1866.7
        self.assertEqual(r["dc_load"], 1680)
        self.assertEqual(r["wall"], 1867)

    def test_continuous_80pct(self):
        r = P.compute(0, 0, 0, 0.9, 120, 15)
        self.assertEqual(r["breaker"], 1800)
        self.assertEqual(r["continuous"], 1440)

    def test_danger_over_breaker(self):
        # 4x600 default on 120/15 → wall huge → DANGER
        r = P.compute(4, 600, 280, 0.9, 120, 15)
        self.assertEqual(r["status"], "DANGER")

    def test_warn_between(self):
        # tune so wall is between continuous(1440) and breaker(1800) on 120/15
        r = P.compute(2, 350, 200, 0.9, 120, 15)  # DC=900 wall=1000 → OK
        self.assertEqual(r["status"], "OK")
        r2 = P.compute(3, 350, 300, 0.9, 120, 15)  # DC=1350 wall=1500 → >1440 <1800 WARN
        self.assertEqual(r2["status"], "WARN")

    def test_ok_on_bigger_circuit(self):
        r = P.compute(4, 350, 280, 0.9, 220, 16)  # breaker 3520, cont 2816, wall 1867 → OK
        self.assertEqual(r["status"], "OK")

    def test_advice_suggests_limit(self):
        r = P.compute(4, 600, 280, 0.9, 120, 15)
        tips = P.advise(r)
        self.assertTrue(any("제한" in t for t in tips))

    def test_exit_codes(self):
        with redirect_stdout(io.StringIO()):
            rc = P.main(["--gpus", "2", "--gpu-watts", "350", "--host-watts", "200", "--volts", "120", "--amps", "15"])
        self.assertEqual(rc, 0)
        with redirect_stdout(io.StringIO()):
            rc2 = P.main(["--gpus", "4", "--gpu-watts", "600", "--volts", "120", "--amps", "15"])
        self.assertEqual(rc2, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
