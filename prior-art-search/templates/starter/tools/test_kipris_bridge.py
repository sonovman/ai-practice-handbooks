#!/usr/bin/env python3
"""kipris_bridge.py 오프라인 시험 — 10편 fixtures/search_sample.xml을 가짜 응답으로 쓴다(서버 접속 없음)."""
import io, sys, tempfile, unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# 10편 kipris_client.py를 tools/ 에 복사하지 않았으면 이 시험은 건너뛴다(오류 대신 skip).
try:
    import kipris_client as kc  # 10편
    import kipris_bridge as kb  # 애드온(내부에서 kipris_client 사용)
    HAVE_DEPS = True
except Exception:
    HAVE_DEPS = False

PLAN = HERE.parent / "sample" / "plan.json"
FX = HERE / "fixtures" / "search_sample.xml"  # 10편 fixtures 폴더를 tools/ 아래로 복사


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@unittest.skipUnless(HAVE_DEPS and FX.exists(), "10편 kipris_client.py와 fixtures/search_sample.xml을 tools/ 에 복사하세요")
class T(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.usage = kc.Usage(self.tmp / "u.json")
        self.urls = []

    def opener(self, url, timeout=0):
        self.urls.append(url)
        return FakeResp(FX.read_bytes())

    def run_main(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            kb.main([str(PLAN), "--out", str(self.tmp / "imports")] + list(args), opener=self.opener, usage=self.usage)
        return buf.getvalue()

    def test_segments_and_or(self):
        segs, j = kb.split_segments("TL=[(a+b)*(c)]+AB=[(a+b)*(c)]")
        self.assertEqual(j, "+")
        self.assertEqual(segs[1], ("AB", "(a+b)*(c)"))
        segs, j = kb.split_segments("TL=[x]*IPC=[A47J19/02]")
        self.assertEqual(j, "*")

    def test_near_converted(self):
        calls, notes = kb.to_calls([{"id": "Q3", "expr": "CL=[(리브+돌기)^10(스크루)]"}])
        self.assertEqual(calls[0]["params"]["claimScope"], "(리브+돌기)*(스크루)")
        self.assertTrue(notes)

    def test_plan_only_makes_no_call(self):
        out = self.run_main()
        self.assertIn("계획만", out)
        self.assertEqual(self.urls, [])

    def test_run_writes_csv_and_counts(self):
        self.run_main("--run", "--per-second", "40")
        self.assertTrue((self.tmp / "imports" / "kipris_all.csv").exists())
        # 28편 개선 반영: ta(명칭+요약)는 TL=[..]+AB=[..] 로 생성돼 필드마다 따로 호출된다.
        # Q1(ta)=2, Q2(ta)=2, Q3(claims)=1 → 총 5건.
        self.assertEqual(self.usage.count, 5)
        self.assertTrue(all("ServiceKey=" in u for u in self.urls))

    def test_probe_one_call(self):
        out = self.run_main("--probe", "--run", "--per-second", "40")
        self.assertEqual(len(self.urls), 1)
        self.assertIn("XML 앞부분", out)

    def test_max_calls_guard(self):
        with self.assertRaises(SystemExit):
            self.run_main("--pages", "20", "--max-calls", "10")

    def test_cutoff_check(self):
        self.assertEqual(kb.cutoff_check({"openDate": "20150101"}, "20200315"), "이전")
        self.assertTrue(kb.cutoff_check({"openDate": "20210101"}, "20200315").startswith("이후"))


if __name__ == "__main__":
    import os
    os.environ.setdefault("KIPRIS_KEY", "TESTKEY")
    unittest.main(verbosity=1)
