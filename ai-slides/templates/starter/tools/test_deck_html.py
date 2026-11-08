#!/usr/bin/env python3
"""deck_html.py 시험. 표준 라이브러리만 사용.  python tools/test_deck_html.py"""
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import deck_html as D

SRC = """# [Slide 1] 표지
- Layout: Type D
- Subtitle: 부제입니다
- Highlight: 70% 단축
# [Slide 2] 배경
- Layout: Type F
- Left: 처리 지연 4.2일
- Right: AI 도입
"""


class T(unittest.TestCase):
    def test_parse(self):
        s = D.parse(SRC)
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0][0], "표지")
        self.assertEqual(s[0][1], "Type D")

    def test_build_has_sections_and_selfcontained(self):
        doc = D.build(D.parse(SRC), "테스트")
        self.assertEqual(doc.count("<section class='slide'>"), 2)
        self.assertIn("<style>", doc)
        # 외부 리소스 없음
        self.assertNotIn("http://", doc)
        self.assertNotIn("https://", doc)
        self.assertNotIn("<script", doc)

    def test_cols_layout(self):
        doc = D.build(D.parse(SRC))
        self.assertIn("class='cols'", doc)  # Left/Right → 2열

    def test_escaping(self):
        s = "# [Slide 1] <b>x</b>\n- 내용 <tag>\n"
        doc = D.build(D.parse(s))
        self.assertIn("&lt;b&gt;", doc)

    def test_out_file(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "s.md"; src.write_text(SRC, encoding="utf-8")
            out = Path(d) / "deck.html"
            with redirect_stdout(io.StringIO()):
                rc = D.main([str(src), "--out", str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())
            self.assertIn("<section", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
