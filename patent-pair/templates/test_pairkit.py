#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pairkit.py · chart_check.py 시험 — python test_pairkit.py"""
import json
import tempfile
import unittest
from pathlib import Path

import chart_check as C
import pairkit as P

HERE = Path(__file__).resolve().parent
S = HERE / "sample"


class Extract(unittest.TestCase):
    def test_kr_publication(self):
        d = P.load_doc(S / "KR1020250013094.txt")
        self.assertEqual(len(d["claims"]), 14)
        self.assertEqual([c["no"] for c in d["claims"] if c["independent"]], [1, 5, 12, 13])
        self.assertGreater(len(d["paras"]), 100)
        self.assertNotIn(" -7- ", " ".join(p["text"] for p in d["paras"]))

    def test_us_style_claims(self):
        t = "What is claimed is:\n1. A method comprising: receiving data; and storing the data.\n2. The method of claim 1, wherein the data is text.\n[0001] Data is received.\n"
        d = P.extract(t)
        self.assertEqual([(c["no"], c["independent"]) for c in d["claims"]], [(1, True), (2, False)])

    def test_plain_doc_gets_paragraphs(self):
        d = P.load_doc(S / "product-B.txt")
        self.assertEqual(d["paras"][0]["id"], "0001")

    def test_korean_line_join(self):
        self.assertEqual(P.joiner("의", "해", True), "의해")
        self.assertEqual(P.joiner("의", "해", False), "의 해")
        self.assertEqual(P.joiner("추출하고,", "상기", True), "추출하고, 상기")


class Elements(unittest.TestCase):
    def test_claim1_split(self):
        d = P.load_doc(S / "KR1020250013094.txt")
        el = P.elements(d["claims"][0]["text"])
        self.assertTrue(el["preamble"].endswith("방법으로서"))
        self.assertEqual(len(el["elements"]), 6)
        self.assertFalse(el["elements"][2]["text"].startswith("및"))
        self.assertNotIn("특징으로", el["elements"][-1]["text"])


class Bundle(unittest.TestCase):
    def test_short_target_whole(self):
        text, el, scores = P.bundle(P.load_doc(S / "KR1020250013094.txt"), 1, P.load_doc(S / "product-A.txt"))
        self.assertIn("전문을 넣습니다", text)
        self.assertIn("[0004]", text)
        self.assertEqual(len(scores), 6)
        self.assertNotIn("과제를 달성하기", text.split("## 용어 해석")[1].split("## 대상")[0])

    def test_long_target_candidates(self):
        long_doc = {"name": "long", "paras": [{"id": "{:04d}".format(i), "text": "무관한 문장 " * 40 + str(i)} for i in range(1, 60)]}
        text, _, _ = P.bundle(P.load_doc(S / "KR1020250013094.txt"), 1, long_doc, top=2)
        self.assertIn("### E1 후보", text)


class Pairs(unittest.TestCase):
    def test_labels_and_kinds(self):
        docs = [P.load_doc(f) for f in sorted((S / "corpus").glob("*.txt"))]
        rows, trip = P.pairs(docs)
        self.assertEqual(sum(r["label"] for r in rows), len(docs))
        for r in rows:
            if r["label"] == 1:
                self.assertEqual(r["src_claim"], r["src_desc"])
            else:
                self.assertNotEqual(r["src_claim"], r["src_desc"])
        self.assertEqual(len(trip), len(docs))
        for i in range(0, len(rows), 3):                      # 같은 청구항의 무작위 쌍과 어려운 쌍은 다른 문헌
            self.assertNotEqual(rows[i + 1]["src_desc"], rows[i + 2]["src_desc"])


class Verify(unittest.TestCase):
    def test_good_charts_pass(self):
        for c in "AB":
            chart = C.find_json((S / "chart-{}.md".format(c)).read_text(encoding="utf-8"))
            rows, _ = C.verify(chart, P.load_doc(S / "product-{}.txt".format(c)), 6)
            self.assertFalse([r for r in rows if r[0] == "실패"], c)

    def test_draft_caught(self):
        chart = C.find_json((S / "chart-A-draft.md").read_text(encoding="utf-8"))
        rows, exp = C.verify(chart, P.load_doc(S / "product-A.txt"), 6)
        fails = [r for r in rows if r[0] == "실패"]
        self.assertEqual(exp, "추가 검토 필요")
        self.assertTrue(any("E6" in r[2] for r in fails))
        self.assertTrue(any(r[1] == "E2" for r in fails))
        self.assertTrue(any(r[1] == "결론" for r in fails))
        self.assertTrue(any(r[0] == "주의" and r[1] == "E4" for r in rows))

    def test_verdict_rule(self):
        self.assertEqual(C.expected_verdict(["개시", "개시"]), "모든 구성요소 개시")
        self.assertEqual(C.expected_verdict(["개시", "미개시", "불명"]), "일부 미개시")
        self.assertEqual(C.expected_verdict(["개시", "부분 개시"]), "추가 검토 필요")


class Score(unittest.TestCase):
    def test_sample(self):
        _, m = C.score(S / "pairs.jsonl", S / "predictions.csv")
        self.assertEqual(m["acc"], 1.0)

    def test_auc(self):
        self.assertEqual(C.auc([1, 0, 1, 0], [0.9, 0.1, 0.8, 0.2]), 1.0)
        self.assertEqual(C.auc([1, 0], [0.5, 0.5]), 0.5)

    def test_length_mismatch(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("pred\n1\n")
        with self.assertRaises(ValueError):
            C.score(S / "pairs.jsonl", f.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
