#!/usr/bin/env python3
"""token_cost.py 시험. 표준 라이브러리만 사용.  python tools/test_token_cost.py"""
import io
import unittest
from contextlib import redirect_stdout

import token_cost as T


class Test(unittest.TestCase):
    def test_per_tok(self):
        self.assertAlmostEqual(T.per_tok(3), 3e-6)

    def test_output_more_expensive(self):
        # 같은 토큰 수라도 출력(단가 15)이 입력(3)보다 5배
        rows, total = T.compute(1000, 1000, 0, 0, 3, 15, 3.75, 0.3)
        d = {k: c for k, _, c in rows}
        self.assertAlmostEqual(d["출력(+사고)"], d["입력(비캐시)"] * 5)

    def test_cache_read_cheaper(self):
        rows, total = T.compute(1000, 0, 0, 1000, 3, 15, 3.75, 0.3)
        d = {k: c for k, _, c in rows}
        self.assertAlmostEqual(d["캐시 읽기"], d["입력(비캐시)"] * 0.1)

    def test_total_sums(self):
        rows, total = T.compute(1000, 1000, 100, 100, 3, 15, 3.75, 0.3)
        self.assertAlmostEqual(total, sum(c for _, _, c in rows))

    def test_defaults_applied(self):
        # out-price·cache 미지정 → 비율 적용
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = T.main(["--in", "1000", "--out", "1000", "--cache-read", "1000", "--in-price", "3"])
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("합계", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
