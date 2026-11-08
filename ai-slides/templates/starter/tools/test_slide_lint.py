#!/usr/bin/env python3
"""slide_lint.py 시험. 표준 라이브러리만 사용.  python tools/test_slide_lint.py"""
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import slide_lint as L

GOOD = """# [Slide 1] 표지
- Layout: Type D
- Highlight: 민원 70% 단축
# [Slide 2] 배경
- Layout: Type F
- Left: 처리 지연 4.2일
- Right: AI 자동 작성 도입
# [Slide 3] 전략
- Layout: Type C
- Card 1: 챗봇 85% 달성
"""


class T(unittest.TestCase):
    def test_split_counts(self):
        self.assertEqual(len(L.split_slides(GOOD)), 3)

    def test_layout_detect(self):
        s = L.split_slides(GOOD)
        self.assertEqual(L.layout_of(s[0]), "TypeD")
        self.assertEqual(L.layout_of(s[1]), "TypeF")

    def test_slide_count_gate(self):
        r = L.scan(GOOD, slides_expected=3)
        g = [x for x in r["gates"] if "분량" in x["name"]][0]
        self.assertTrue(g["ok"])
        r2 = L.scan(GOOD, slides_expected=5)
        g2 = [x for x in r2["gates"] if "분량" in x["name"]][0]
        self.assertFalse(g2["ok"])
        self.assertEqual(r2["status"], "FAIL")

    def test_require_keywords(self):
        r = L.scan(GOOD, require=["표지", "없는키워드"])
        g = [x for x in r["gates"] if "요구사항" in x["name"]][0]
        self.assertFalse(g["ok"])
        self.assertIn("없는키워드", g["detail"])

    def test_cliche_fail(self):
        bad = "# [Slide 1] 제목\n- 이것은 혁신이 아니라 진화입니다\n"
        r = L.scan(bad)
        g = [x for x in r["gates"] if "문체" in x["name"]][0]
        self.assertFalse(g["ok"])
        self.assertEqual(r["status"], "FAIL")

    def test_number_consistency(self):
        with tempfile.TemporaryDirectory() as d:
            body = Path(d) / "body.md"
            body.write_text("민원 70% 단축, 4.2일 소요", encoding="utf-8")
            # 슬라이드에 본문에 없는 9999 등장 → FAIL
            slides = "# [Slide 1] x\n- 70% 단축\n- 4.2일\n- 비용 9999억 절감\n"
            r = L.scan(slides, body=str(body))
            g = [x for x in r["gates"] if "사실관계" in x["name"]][0]
            self.assertFalse(g["ok"])
            self.assertIn("9999", g["detail"])

    def test_diversity_warning(self):
        same = "".join("# [Slide {}] s\n- Layout: Type A\n- 내용\n".format(i) for i in range(1, 5))
        r = L.scan(same)
        self.assertTrue(any("쏠림" in t for t in r["tastes"]))

    def test_pass_clean(self):
        r = L.scan(GOOD, slides_expected=3, require=["표지", "전략"])
        self.assertIn(r["status"], ("PASS", "WARN"))
        self.assertTrue(all(g["ok"] for g in r["gates"]))

    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "s.md"; f.write_text(GOOD, encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                rc = L.main([str(f), "--slides", "3"])
            self.assertIn(rc, (0, 1))
            with redirect_stdout(io.StringIO()):
                rc2 = L.main([str(f), "--slides", "9"])
            self.assertEqual(rc2, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
