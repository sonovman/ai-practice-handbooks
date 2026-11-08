#!/usr/bin/env python3
"""session_sim.py 시험. 표준 라이브러리만 사용.  python tools/test_session_sim.py"""
import io
import unittest
from contextlib import redirect_stdout

import session_sim as S


class Test(unittest.TestCase):
    def test_two_turn_no_cache_math(self):
        # turns=2, t_in=1000, t_out=1000, start=1000, p_in=1, p_out=1, cache off, no clear
        # t1: prefix=1000 → in=(1000+1000)=2000; out=1000; ctx→3000
        # t2: prefix=3000 → in=(3000+1000)=4000; out=1000
        # total tokens-cost = (2000+1000+4000+1000)*1e-6 = 8000e-6
        total = S.simulate(2, 1000, 1000, 1000, 1, 1, 0.1, cache=False, clear_every=0)
        self.assertAlmostEqual(total, 8000e-6)

    def test_cache_cheaper_than_no_cache(self):
        base = dict(turns=20, t_in=1500, t_out=1500, start_ctx=12000, p_in=3, p_out=15, p_cr=0.3)
        no_cache = S.simulate(cache=False, clear_every=0, **base)
        cache = S.simulate(cache=True, clear_every=0, **base)
        self.assertLess(cache, no_cache)

    def test_clear_reduces_cost(self):
        base = dict(turns=40, t_in=1500, t_out=1500, start_ctx=12000, p_in=3, p_out=15, p_cr=0.3)
        no_clear = S.simulate(cache=True, clear_every=0, **base)
        with_clear = S.simulate(cache=True, clear_every=10, **base)
        self.assertLess(with_clear, no_clear)

    def test_growth_quadratic_ish(self):
        # 긴 세션이 두 배 길면 비용은 두 배보다 더 커진다(누적 재전송)
        base = dict(t_in=1000, t_out=1000, start_ctx=0, p_in=1, p_out=1, p_cr=0.1)
        c20 = S.simulate(turns=20, cache=False, clear_every=0, **base)
        c40 = S.simulate(turns=40, cache=False, clear_every=0, **base)
        self.assertGreater(c40, c20 * 2)

    def test_main_runs(self):
        with redirect_stdout(io.StringIO()):
            rc = S.main(["--turns", "10", "--in-price", "3"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
