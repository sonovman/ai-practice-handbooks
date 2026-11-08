#!/usr/bin/env python3
"""claude_md_lint.py 시험. 표준 라이브러리만 사용.  python tools/test_claude_md_lint.py"""
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import claude_md_lint as L

SLIM = """# 프로젝트 핵심 지침
1. 모든 수정은 테스트를 먼저 작성(TDD)한다.
2. 비밀 키는 파일에 직접 쓰지 않는다.
3. 스키마 변경 시 migrations/ 이력 파일을 만든다.
4. 테스트 코드는 수정하지 말고 이행 코드를 고친다.
"""

VAGUE = """# 지침
1. 항상 깨끗한 코드를 작성하고 신중히 처리한다.
2. 주석을 잘 달고 가독성 좋게 짠다.
"""


class T(unittest.TestCase):
    def test_slim_passes(self):
        r = L.analyze(SLIM, 200, 10)
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["n_rules"], 4)

    def test_vague_warns(self):
        r = L.analyze(VAGUE, 200, 10)
        self.assertEqual(r["status"], "WARN")
        self.assertTrue(r["vague"])

    def test_obvious_detected(self):
        r = L.analyze(VAGUE, 200, 10)
        self.assertTrue(any("주석" in o[1] for o in r["obvious"]))

    def test_over_lines_fails(self):
        big = "# h\n" + "\n".join("설명 줄 {}".format(i) for i in range(250))
        r = L.analyze(big, 200, 10)
        self.assertTrue(r["over_lines"])
        self.assertEqual(r["status"], "FAIL")

    def test_over_rules_fails(self):
        many = "# h\n" + "\n".join("{}. 규칙".format(i) for i in range(1, 15))
        r = L.analyze(many, 200, 10)
        self.assertTrue(r["over_rules"])
        self.assertEqual(r["status"], "FAIL")

    def test_rule_count_bullets_and_numbers(self):
        txt = "- 불릿 규칙\n1. 번호 규칙\n* 별 규칙\n일반 문장\n"
        r = L.analyze(txt, 200, 10)
        self.assertEqual(r["n_rules"], 3)

    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "C.md"; f.write_text(SLIM, encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(L.main([str(f)]), 0)
            f.write_text(VAGUE, encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(L.main([str(f)]), 1)
            f.write_text("# h\n" + "\n".join(str(i) for i in range(250)), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(L.main([str(f)]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
