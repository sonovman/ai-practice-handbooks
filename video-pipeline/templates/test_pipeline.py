#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pipeline.py 시험 — python test_pipeline.py"""
import datetime as dt
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import pipeline as P

HERE = Path(__file__).resolve().parent
SCRIPT = (HERE / "example" / "script.txt").read_text(encoding="utf-8")


class Script(unittest.TestCase):
    def test_clean_example_passes(self):
        rows, secs = P.check_script(SCRIPT, 36)
        self.assertEqual([r for r in rows if r[0] != "정보"], [])
        self.assertTrue(30 < secs < 42)

    def test_labels_brackets_filler(self):
        bad = "장면 1: 이 영상에서는 통장 쪼개기를 알아봅니다 (밝게).\n수익률은 3%입니다."
        rules = {r[1] for r in P.check_script(bad)[0]}
        self.assertTrue({"장면 라벨", "괄호", "군더더기 오프닝", "기호 읽기"} <= rules)

    def test_english_word_limit(self):
        rows, _ = P.check_script("This sentence clearly has far more than twelve words in it for the narration test.")
        self.assertIn("긴 문장", {r[1] for r in rows})


class Plan(unittest.TestCase):
    def test_round_up_not_nearest(self):
        r = P.plan(37, clip=5)
        self.assertEqual(r["n_min"], 9)          # 37 ÷ 4.5 = 8.2 → 올림 9
        self.assertTrue(all(s["dur"] <= 4.5 + 1e-9 for s in r["scenes"]))

    def test_classic_36_seconds(self):
        self.assertEqual(P.plan(36, clip=5)["n_min"], 8)

    def test_veo_lite_rejects_5s(self):
        with self.assertRaises(ValueError):
            P.plan(36, tool="veo31-lite", clip=5)

    def test_veo_lite_picks_shortest_clip(self):
        r = P.plan(36, SCRIPT, tool="veo31-lite")
        self.assertEqual(r["base"], 6)
        self.assertTrue(all(s["clip"] in (4, 6, 8) and s["fits"] for s in r["scenes"]))
        self.assertAlmostEqual(r["scenes"][-1]["end"], 36, places=6)

    def test_sentence_boundaries(self):
        r = P.plan(36, SCRIPT, tool="omni-flash-free")
        texts = [s["text"] for s in r["scenes"]]
        self.assertEqual(len(texts), 8)
        self.assertTrue(texts[0].startswith("월급이"))

    def test_long_sentence_split(self):
        r = P.plan(20, "아주 긴 한 문장만 있는 대본입니다.", clip=5)
        self.assertGreaterEqual(len(r["scenes"]), 4)
        self.assertIn("다음 컷", r["scenes"][1]["text"])

    def test_asset_input_has_plan(self):
        r = P.plan(36, SCRIPT, tool="veo31-lite")
        txt = P.asset_input(r, SCRIPT, "warm cinematic")
        self.assertIn("/asset-generator", txt)
        self.assertIn("다시 계산하지 말고", txt)
        self.assertEqual(txt.count("\n| "), len(r["scenes"]) + 1)


class Pack(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_pack_template(self):
        rows, made = P.pack(HERE / "knowledge", HERE / "skills", self.tmp, dt.date(2026, 11, 7))
        self.assertEqual(len(made), 2)
        self.assertFalse([r for r in rows if r[0] == "실패"])
        self.assertTrue([r for r in rows if "붙여 넣지 않았" in r[2]])
        names = zipfile.ZipFile(self.tmp / "story-engine.zip").namelist()
        self.assertIn("story-engine/SKILL.md", names)
        self.assertIn("story-engine/references/01-competitor.md", names)
        self.assertNotIn("story-engine/references/06-tool-terms.md", names)
        a = zipfile.ZipFile(self.tmp / "asset-generator.zip").namelist()
        self.assertIn("asset-generator/references/clip-lengths.md", a)
        self.assertIn("asset-generator/references/06-tool-terms.md", a)

    def test_refresh_warning(self):
        rows, _ = P.pack(HERE / "knowledge", HERE / "skills", self.tmp, dt.date(2027, 3, 15))
        stale = [r[2][:2] for r in rows if r[1] == "갱신 시기" and r[0] == "주의"]
        self.assertEqual(sorted(stale), ["01", "02", "03", "06"])

    def test_strict_fails_on_empty(self):
        rows, _ = P.pack(HERE / "knowledge", HERE / "skills", self.tmp, dt.date(2026, 11, 7), strict=True)
        self.assertTrue([r for r in rows if r[0] == "실패"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
