"""prompt_lint.py 시험 — python test_prompt_lint.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import prompt_lint as p

HERE = Path(__file__).parent


def rules(text):
    return [(lv, r) for lv, r, _ in p.check(text)]


class T(unittest.TestCase):
    def test_before_example_flags(self):
        r = rules((HERE / "examples/before.md").read_text(encoding="utf-8"))
        for want in ["태그 짝", "꺾쇠 빈칸", "변수 속 선택지", "선택지 규칙", "따옴표 의미", "강조 남용", "강한 어조", "출력 형식"]:
            self.assertIn(want, [x[1] for x in r], want)

    def test_after_example_clean(self):
        r = rules((HERE / "examples/after.md").read_text(encoding="utf-8"))
        self.assertFalse([x for x in r if x[0] in ("실패", "주의")], r)

    def test_unclosed_and_misordered_tags(self):
        self.assertIn(("실패", "태그 짝"), rules("# 출력 형식\n<a><b></a></b>"))

    def test_code_block_ignored(self):
        text = "# 역할\n예시:\n```\n<이름> 님께 \"급건\" **A** **B** **C** **D** **E**\n```\n# 출력 형식\n- 한 줄"
        self.assertFalse([x for x in rules(text) if x[0] != "정보"])

    def test_long_data_outside_tag(self):
        text = "# 자료\n" + "가" * 200 + "\n# 출력 형식\n- 요약"
        self.assertIn(("주의", "자료 경계"), rules(text))
        text2 = "# 자료\n<자료>\n" + "가" * 200 + "\n</자료>\n# 출력 형식\n- 요약"
        self.assertNotIn(("주의", "자료 경계"), rules(text2))

    def test_fill(self):
        done, missing = p.fill("{a}와 {b}", {"a": "1"})
        self.assertEqual(missing, ["b"])
        done, missing = p.fill("{a}와 {b}", {"a": "1", "b": "2"})
        self.assertEqual((done, missing), ("1와 2", []))

    def test_fill_skips_code(self):
        done, missing = p.fill("{a}\n```\n{json_key}\n```", {"a": "x"})
        self.assertEqual(missing, [])
        self.assertIn("{json_key}", done)


if __name__ == "__main__":
    unittest.main(verbosity=2)
