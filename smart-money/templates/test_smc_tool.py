#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""smc_tool.py 시험 — python test_smc_tool.py"""
import os
import tempfile
import unittest
from pathlib import Path

import smc_tool as T

HERE = Path(__file__).resolve().parent
DAILY = T.load(HERE / "sample" / "daily.csv")
HOURLY = T.load(HERE / "sample" / "hourly.csv")


def bar(o, h, l, c, v=100):
    return {"date": "", "open": o, "high": h, "low": l, "close": c, "volume": v}


class Load(unittest.TestCase):
    def test_korean_headers_and_commas(self):
        rows = ["날짜,시가,고가,저가,종가,거래량"] + ['2026-01-{:02d},"1,000",1010,990,1005,10'.format(i) for i in range(1, 32)]
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("\n".join(rows))
        try:
            bars = T.load(f.name)
            self.assertEqual(len(bars), 31)
            self.assertEqual(bars[0]["open"], 1000)
        finally:
            os.unlink(f.name)

    def test_too_few_bars(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("date,open,high,low,close\n" + "\n".join("d,1,2,0,1" for _ in range(10)))
        try:
            with self.assertRaises(ValueError):
                T.load(f.name)
        finally:
            os.unlink(f.name)


class Structure(unittest.TestCase):
    def test_daily_uptrend(self):
        hs, ls = T.swings(DAILY)
        self.assertEqual(T.trend_of(DAILY, hs, ls)[0], "상승")

    def test_no_lookahead(self):
        hs, ls = T.swings(DAILY, 3)
        for i, kind, lvl in T.structure_breaks(DAILY, hs, ls, 3):
            src = [j for j in hs + ls if DAILY[j]["close"] == lvl and j + 3 <= i]
            self.assertTrue(src, "돌파 시점에 아직 확정되지 않은 스윙을 썼습니다: {}".format(DAILY[i]["date"]))

    def test_hourly_mss_up_last(self):
        hs, ls = T.swings(HOURLY)
        ev = T.structure_breaks(HOURLY, hs, ls)
        self.assertEqual(ev[-1][1], "상향 MSS")

    def test_fvg_and_fill(self):
        bars = [bar(100, 101, 99, 100)] * 3 + [bar(100, 102, 99, 101), bar(101, 110, 101, 109), bar(109, 112, 105, 111),
                                              bar(111, 111, 103, 104), bar(104, 105, 100, 101)]
        g = [x for x in T.fvgs(bars) if x["dir"] == "상승"]
        self.assertEqual((g[0]["lo"], g[0]["hi"]), (102, 105))
        self.assertEqual(g[0]["state"], "모두 메움")

    def test_order_block_trinity(self):
        _, info = T.facts(DAILY)
        valid = [o for o in info["obs"] if o["disp"] and o["fvg"] and o["dir"] == "매수"]
        self.assertTrue(valid)
        self.assertGreater(valid[-1]["prox"], valid[-1]["dist"])

    def test_sweep_needs_close_back(self):
        bars = [bar(100, 101, 99, 100 + (i % 7)) for i in range(20)]
        hs, ls = T.swings(bars)
        lv = bars[ls[-1]]["close"]
        bars.append(bar(lv + 2, lv + 3, lv - 5, lv + 1))      # 꼬리만 이탈, 종가 복귀
        bars.append(bar(lv, lv + 1, lv - 6, lv - 3))          # 종가도 이탈 → 스윕 아님
        kinds = [(i, k) for i, k, _ in T.sweeps(bars, hs, ls)]
        self.assertIn((20, "하단 스윕"), kinds)
        self.assertNotIn((21, "하단 스윕"), kinds)

    def test_facts_text(self):
        text, _ = T.facts(DAILY, "가상종목A", "일봉")
        for h in ("## 3. 구조 돌파", "## 4. 오더 블록", "## 8. 되돌림 위치", "33~66% 구간 안"):
            self.assertIn(h, text)


class Size(unittest.TestCase):
    def test_long(self):
        r = T.size(10_000_000, 1, 12080, 11860, 12940, fee_pct=0.2)
        self.assertEqual(r["qty"], 373)
        self.assertLessEqual(r["loss"], 100_000)
        self.assertAlmostEqual(r["rr"], 3.02, places=2)

    def test_short_side(self):
        self.assertTrue(T.size(1000, 1, 100, 105)["side"].startswith("숏"))


class Stats(unittest.TestCase):
    def test_r_multiple_long_short(self):
        self.assertEqual(T.r_multiple({"진입": "100", "손절": "90", "청산": "120"}), 2)
        self.assertEqual(T.r_multiple({"진입": "100", "손절": "110", "청산": "80"}), 2)
        self.assertEqual(T.r_multiple({"진입": "100", "손절": "110", "청산": "110"}), -1)

    def test_sample_journal(self):
        _, s = T.stats(HERE / "sample" / "journal-sample.csv")
        self.assertEqual(s["n"], 10)
        self.assertAlmostEqual(s["hit"], 0.6)
        self.assertAlmostEqual(s["exp"], 0.7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
