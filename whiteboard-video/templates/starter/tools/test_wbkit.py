#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wbkit.py 시험 — python tools/test_wbkit.py  (API를 부르지 않습니다)"""
import base64
import json
import os
import shutil
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock

import wbkit as W

SCRIPT = "## scene-01 첫 장면\n첫 문장입니다.\n두 번째 문장은 조금 더 깁니다.\n\n## scene-02 둘째\n<!-- 그림: 나무 -->\n마지막 문장.\n"


def make_wav(path, sec, rate=24000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * sec))


class Base(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        (self.d / "script.md").write_text(SCRIPT, encoding="utf-8")
        (self.d / "audio").mkdir()
        make_wav(self.d / "audio" / "scene-01.wav", 6.0)
        make_wav(self.d / "audio" / "scene-02.wav", 3.0)

    def tearDown(self):
        shutil.rmtree(self.d)


class Script(Base):
    def test_read(self):
        s = W.read_script(self.d / "script.md")
        self.assertEqual([x["id"] for x in s], ["scene-01", "scene-02"])
        self.assertEqual(s[1]["lines"], ["마지막 문장."])          # 주석 줄은 읽지 않음

    def test_bad_script(self):
        (self.d / "bad.md").write_text("제목 없이 문장만\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            W.read_script(self.d / "bad.md")


class TTS(Base):
    def test_model_routing(self):
        url, body = W.request_body("gemini-3.8-flash-tts", "안녕", "Kore", "차분하게")
        self.assertTrue(url.endswith("/interactions"))
        self.assertEqual(body["generation_config"]["speech_config"], [{"voice": "Kore"}])
        self.assertEqual(body["input"][0]["content"][0]["annotations"][0]["style"], "차분하게")
        url2, body2 = W.request_body("gemini-2.5-flash-preview-tts", "안녕", "Kore")
        self.assertIn(":generateContent", url2)
        self.assertEqual(body2["generationConfig"]["responseModalities"], ["AUDIO"])

    def test_find_and_save_pcm(self):
        pcm = b"\x01\x00" * 24000
        resp = {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "audio/L16;rate=24000", "data": base64.b64encode(pcm).decode()}}]}}]}
        data, mime = W.find_audio(resp)
        W.save_audio(base64.b64decode(data), self.d / "a.wav")
        self.assertAlmostEqual(W.wav_seconds(self.d / "a.wav"), 1.0, places=2)

    def test_find_and_save_wav(self):
        make_wav(self.d / "src.wav", 2.0)
        raw = (self.d / "src.wav").read_bytes()
        resp = {"output_audio": {"mime_type": "audio/wav", "data": base64.b64encode(raw).decode()}}
        data, _ = W.find_audio(resp)
        W.save_audio(base64.b64decode(data), self.d / "b.wav")
        self.assertEqual((self.d / "b.wav").read_bytes(), raw)    # RIFF는 그대로

    def test_tts_with_fake_api(self):
        pcm = base64.b64encode(b"\x00\x00" * 48000).decode()
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "AIza" + "x" * 35}, clear=False), \
             mock.patch.object(W, "call_api", return_value={"output_audio": {"data": pcm, "mime_type": "audio/l16"}}):
            W.tts(self.d / "script.md", self.d / "out")
        self.assertAlmostEqual(W.wav_seconds(self.d / "out" / "scene-02.wav"), 2.0, places=2)


class SRT(Base):
    def test_build(self):
        t = W.build_srt(self.d / "script.md", self.d / "audio", self.d / "n.srt", self.d / "s.json")
        self.assertEqual([x["sceneDurationMs"] for x in t], [6500, 3500])
        self.assertEqual(t[1]["start"], 6.5)
        cues = W.parse_srt(self.d / "n.srt")
        self.assertEqual(len(cues), 3)
        self.assertAlmostEqual(cues[1][1], 6.0, places=2)         # 장면 1의 마지막 자막은 음성 끝에서 끝남
        self.assertAlmostEqual(cues[2][0], 6.5, places=2)

    def test_sync(self):
        W.build_srt(self.d / "script.md", self.d / "audio", self.d / "n.srt", self.d / "s.json")
        ann = {"canvas": {"width": 100, "height": 100}, "sceneDurationMs": 1, "elements": [
            {"id": "a", "sequence": 1, "reveal": {"startMs": 0, "durationMs": 1}, "subtitle": ""},
            {"id": "b", "sequence": 2, "reveal": {"startMs": 0, "durationMs": 1}, "subtitle": ""}]}
        (self.d / "scene-01-x.annotation.json").write_text(json.dumps(ann), encoding="utf-8")
        W.sync(self.d / "s.json", self.d / "n.srt", self.d)
        got = json.loads((self.d / "scene-01-x.annotation.json").read_text(encoding="utf-8"))
        self.assertEqual(got["sceneDurationMs"], 6500)
        self.assertEqual(got["elements"][0]["reveal"]["startMs"], 200)
        self.assertEqual(got["elements"][1]["subtitle"], "두 번째 문장은 조금 더 깁니다.")
        self.assertGreater(got["elements"][1]["reveal"]["startMs"], got["elements"][0]["reveal"]["startMs"])


class Key(Base):
    def test_keycheck_finds_leak_and_gitignore(self):
        fake = "AIza" + "B" * 35
        (self.d / "app.py").write_text('KEY = "{}"\n'.format(fake), encoding="utf-8")
        (self.d / ".env").write_text("GEMINI_API_KEY={}\n".format(fake), encoding="utf-8")
        with mock.patch.dict(os.environ, {}, clear=True):
            rows = W.keycheck(self.d)
        text = "\n".join(r[1] for r in rows)
        self.assertIn("app.py", text)
        self.assertIn(".gitignore에 없습니다", text)
        self.assertNotIn(fake, text)                               # 키 값은 화면에 나오지 않음
        self.assertIn("AIza…BB", text)

    def test_keycheck_clean(self):
        (self.d / ".gitignore").write_text(".env\n", encoding="utf-8")
        (self.d / ".env").write_text("GEMINI_API_KEY=AIza" + "c" * 35 + "\n", encoding="utf-8")
        if os.name == "posix":
            os.chmod(self.d / ".env", 0o600)
        with mock.patch.dict(os.environ, {}, clear=True):
            rows = W.keycheck(self.d)
        self.assertFalse([r for r in rows if r[0] == "실패"])

    def test_env_precedence(self):
        (self.d / ".env").write_text("GEMINI_API_KEY=from-file\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "from-env"}, clear=True):
            self.assertEqual(W.find_key(self.d)[0], "from-env")
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(W.find_key(self.d), ("from-file", "프로젝트 .env의 GEMINI_API_KEY"))


class HF(Base):
    def test_composition(self):
        W.build_srt(self.d / "script.md", self.d / "audio", self.d / "n.srt", self.d / "s.json")
        p = W.hyperframes(self.d / "s.json", self.d / "n.srt", self.d / "hf")
        html = p.read_text(encoding="utf-8")
        self.assertIn('id="scene-01-video"', html)
        self.assertIn('id="scene-02-voice"', html)
        self.assertIn('data-duration="10.000"', html)
        self.assertIn("data-no-timeline", html)
        self.assertEqual(html.count('class="cap clip"'), 3)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg 필요")
class Assemble(Base):
    def test_assemble(self):
        import subprocess
        W.build_srt(self.d / "script.md", self.d / "audio", self.d / "n.srt", self.d / "s.json")
        for sid, sec in (("scene-01", 4.0), ("scene-02", 5.0)):         # 1은 음성보다 짧고, 2는 길다
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0xF5EBD7:s=320x180:d={}".format(sec),
                            "-pix_fmt", "yuv420p", str(self.d / (sid + "-whiteboard.mp4"))], check=True)
        sec = W.assemble(self.d / "s.json", self.d, self.d / "audio", self.d / "final.mp4", srt=self.d / "n.srt",
                         width=640, height=360)
        self.assertAlmostEqual(sec, 10.0, delta=0.2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
