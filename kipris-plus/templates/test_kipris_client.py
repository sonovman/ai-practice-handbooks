"""kipris_client.py 오프라인 시험 — 실제 서버에 접속하지 않고 응답 처리만 확인합니다.
사용법: python test_kipris_client.py
"""
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import kipris_client as k

FX = Path(__file__).parent / "fixtures"


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def opener_for(name, seen):
    def _open(url, timeout=0):
        seen.append(url)
        return FakeResp((FX / name).read_bytes())
    return _open


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.usage = k.Usage(Path(self.tmp.name) / "u.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_single_item_is_list(self):
        seen = []
        c = k.Client("SECRET123", usage=self.usage, opener=opener_for("biblio_sample.xml", seen), per_second=40)
        rows, total = k.parse_items(c.get(k.PATH_BIBLIO, {"applicationNumber": "1020990000001"}))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["inventionTitle"], "자동 급수 화분")
        self.assertIn("ServiceKey=SECRET123", seen[0])
        self.assertIn("patUtiModInfoSearchSevice", seen[0])

    def test_many_items_nested_and_total(self):
        rows, total = k.parse_items((FX / "search_sample.xml").read_bytes())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["ipc.code"], "G01D 5/00")
        self.assertEqual(total, "2")

    def test_gateway_error(self):
        with self.assertRaises(k.ApiError) as e:
            k.parse_items((FX / "error_gateway.xml").read_bytes())
        self.assertIn("30", str(e.exception))

    def test_result_code_error(self):
        xml = b"<response><header><resultCode>99</resultCode><resultMsg>LIMIT</resultMsg></header></response>"
        with self.assertRaises(k.ApiError):
            k.parse_items(xml)

    def test_non_xml(self):
        with self.assertRaises(k.ApiError):
            k.parse_items(b"<html><body>error page")

    def test_mask(self):
        self.assertEqual(k.mask("a?x=1&ServiceKey=ABC&y=2"), "a?x=1&ServiceKey=****&y=2")
        self.assertEqual(k.mask("u?serviceKey=Z%2B1"), "u?serviceKey=****")

    def test_no_key_and_rate_limit(self):
        with self.assertRaises(k.ApiError):
            k.Client("")
        with self.assertRaises(k.ApiError):
            k.Client("x", per_second=50)

    def test_key_not_allowed_as_argument(self):
        with self.assertRaises(k.ApiError):
            k.kv_pairs(["ServiceKey=abc"])

    def test_usage_warning(self):
        u = self.usage
        u.add(799)
        self.assertEqual(u.warn_text(), "")
        u.add(1)
        self.assertIn("80%", u.warn_text())
        u.add(200)
        self.assertIn("넘었을 수", u.warn_text())

    def test_csv(self):
        rows, _ = k.parse_items((FX / "search_sample.xml").read_bytes())
        out = Path(self.tmp.name) / "r.csv"
        cols = k.write_csv(rows, out)
        self.assertIn("registerStatus", cols)
        self.assertTrue(out.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_datagokr_url(self):
        c = k.Client("K", key_param="serviceKey")
        url = c.build_url("https://apis.data.go.kr/1431000/StaownTradePatentInfoService/op", {"pageNo": 1})
        self.assertTrue(url.startswith("https://apis.data.go.kr/1431000/StaownTradePatentInfoService/op?"))
        self.assertIn("serviceKey=K", url)


if __name__ == "__main__":
    unittest.main(verbosity=2)
