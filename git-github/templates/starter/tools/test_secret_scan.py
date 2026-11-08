#!/usr/bin/env python3
"""22편 도구 시험. 실행: python tools/test_secret_scan.py"""
import shutil, sys, tempfile, unittest
from pathlib import Path
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import secret_scan as ss


def mk(files):
    d = Path(tempfile.mkdtemp())
    for name, content in files.items():
        p = d / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return d


class Scan(unittest.TestCase):
    def kinds(self, res):
        return [i["kind"] for i in res["items"]]

    def test_hardcoded_key_fails(self):
        d = mk({"app.py": 'OPENAI_API_KEY = "sk-proj-FAKEdemo1234567890ABCDEF"\n'})
        try:
            r = ss.scan(d); self.assertEqual(r["status"], "FAIL")
            self.assertTrue(any("OpenAI" in k for k in self.kinds(r)))
        finally: shutil.rmtree(d)

    def test_env_file_tracked_fails(self):
        d = mk({".env": "X=1\n"})
        try:
            r = ss.scan(d)
            self.assertTrue(any("민감 파일(추적 대상)" in k for k in self.kinds(r)))
            self.assertEqual(r["status"], "FAIL")
        finally: shutil.rmtree(d)

    def test_env_ignored_is_warn_not_fail(self):
        d = mk({".env": "OPENAI_API_KEY=sk-proj-FAKEdemo1234567890ABCDEF\n", ".gitignore": ".env\n"})
        try:
            r = ss.scan(d)
            self.assertEqual(r["status"], "WARN")  # 제외됐으니 실패 아님
            self.assertTrue(all(i["level"] != "FAIL" for i in r["items"]))
        finally: shutil.rmtree(d)

    def test_env_example_not_flagged(self):
        d = mk({".env.example": "OPENAI_API_KEY=\n"})
        try:
            self.assertEqual(ss.scan(d)["status"], "OK")
        finally: shutil.rmtree(d)

    def test_clean_ok(self):
        d = mk({"main.py": "print('hello')\n", "README.md": "# hi\n"})
        try:
            self.assertEqual(ss.scan(d)["status"], "OK")
        finally: shutil.rmtree(d)

    def test_aws_and_pem_and_db(self):
        d = mk({"a.txt": "AKIAABCDEFGHIJKLMNOP\n",
                "b.txt": "-----BEGIN RSA PRIVATE KEY-----\nabc\n",
                "c.txt": "mongodb+srv://u:p@cluster.net/db\n"})
        try:
            r = ss.scan(d); ks = " ".join(self.kinds(r))
            self.assertIn("AWS", ks); self.assertIn("개인키", ks); self.assertIn("DB 접속", ks)
        finally: shutil.rmtree(d)

    def test_json_password(self):
        d = mk({"config.json": '{ "password": "hunter2hunter2" }\n'})
        try:
            self.assertTrue(any("비밀번호" in k for k in self.kinds(ss.scan(d))))
        finally: shutil.rmtree(d)

    def test_pem_suffix_file(self):
        d = mk({"server.pem": "x\n"})
        try:
            self.assertTrue(any("민감 파일" in k for k in self.kinds(ss.scan(d))))
        finally: shutil.rmtree(d)

    def test_skip_git_dir(self):
        d = mk({".git/config": 'password = "secret123"\n', "ok.py": "x=1\n"})
        try:
            self.assertEqual(ss.scan(d)["status"], "OK")  # .git 내부는 건너뜀
        finally: shutil.rmtree(d)

    def test_redact(self):
        self.assertEqual(ss.redact("sk-proj-ABCDEFGHIJ"), "sk-pro…IJ")

    def test_cli_exit(self):
        d = mk({"app.py": 'k="sk-proj-FAKEdemo1234567890ABCDEF"\n'})
        try:
            self.assertEqual(ss.main([str(d), "--report", str(d/"r.md")]), 2)
            self.assertEqual(ss.main(["--suggest-gitignore"]), 0)
        finally: shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main(verbosity=1)
