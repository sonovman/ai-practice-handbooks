#!/usr/bin/env python3
"""21편 도구 시험 (네트워크·REA·디컴파일러 없이). 실행: python tools/test_rea_tools.py"""
import json, shutil, sys, tempfile, unittest, zipfile
from pathlib import Path
TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import scope_check as sc
import evidence_log as el
import build_upload as bu


class Scope(unittest.TestCase):
    def test_own_binary_green(self):
        a={"own":"예","purpose":"교육","tpm":"아니오","server":"아니오","redistribute":"아니오",
           "resell_code":"아니오","lawful_copy":"예","scope_limited":"예","info_easy":"아니오"}
        st,reds,amb,_=sc.evaluate(a); self.assertEqual(st,"GREEN"); self.assertFalse(reds)

    def test_tpm_red(self):
        st,reds,_,_=sc.evaluate({"own":"예","tpm":"예"}); self.assertEqual(st,"RED")
        self.assertTrue(any("보호조치" in r for r in reds))

    def test_clone_red(self):
        st,reds,_,_=sc.evaluate({"own":"아니오","redistribute":"예"})
        self.assertEqual(st,"RED"); self.assertTrue(any("실질적으로 유사" in r for r in reds))

    def test_server_red(self):
        st,reds,_,_=sc.evaluate({"server":"예"}); self.assertEqual(st,"RED")

    def test_interop_without_subsidiarity_amber(self):
        a={"own":"아니오","oss_license":"아니오","authorized":"아니오","lawful_copy":"예",
           "purpose":"호환성","info_easy":"예","scope_limited":"아니오",
           "tpm":"아니오","server":"아니오","redistribute":"아니오","resell_code":"아니오"}
        st,reds,amb,_=sc.evaluate(a); self.assertEqual(st,"AMBER")
        self.assertTrue(any("보충성" in x for x in amb))

    def test_no_authority_amber(self):
        a={"own":"아니오","oss_license":"아니오","authorized":"아니오","lawful_copy":"아니오",
           "purpose":"교육","tpm":"아니오","server":"아니오","redistribute":"아니오","resell_code":"아니오"}
        st,_,amb,_=sc.evaluate(a); self.assertEqual(st,"AMBER")

    def test_cli_exit_codes(self):
        d=Path(tempfile.mkdtemp())
        try:
            (d/"g.json").write_text(json.dumps({"own":"예","purpose":"교육","tpm":"아니오","server":"아니오",
                "redistribute":"아니오","resell_code":"아니오","lawful_copy":"예","scope_limited":"예","info_easy":"아니오"}),encoding="utf-8")
            (d/"r.json").write_text(json.dumps({"tpm":"예"}),encoding="utf-8")
            self.assertEqual(sc.main(["--answers",str(d/"g.json")]),0)
            self.assertEqual(sc.main(["--answers",str(d/"r.json")]),2)
        finally: shutil.rmtree(d)


class Evidence(unittest.TestCase):
    def test_add_list_report(self):
        d=Path(tempfile.mkdtemp())
        try:
            f=str(d/"e.jsonl")
            el.add(type("A",(),{"file":f,"claim":"c1","kind":"constant","loc":"0x1","status":"pass","note":""}))
            el.add(type("A",(),{"file":f,"claim":"c2","kind":"xref","loc":"?","status":"unknown","note":""}))
            recs=el.load(f); self.assertEqual(len(recs),2)
            c=el.summarize(recs); self.assertEqual(c["pass"],1); self.assertEqual(c["unknown"],1)
            self.assertEqual(el.cmd_report(type("A",(),{"file":f,"out":str(d/"r.md")})),1)  # unknown 남음 → 1
            self.assertIn("미확인", (d/"r.md").read_text(encoding="utf-8"))
        finally: shutil.rmtree(d)

    def test_bad_status_rejected(self):
        d=Path(tempfile.mkdtemp())
        try:
            with self.assertRaises(SystemExit):
                el.add(type("A",(),{"file":str(d/"e.jsonl"),"claim":"c","kind":"x","loc":"","status":"maybe","note":""}))
        finally: shutil.rmtree(d)


class Upload(unittest.TestCase):
    def test_layouts(self):
        d=Path(tempfile.mkdtemp())
        try:
            bu.build(ROOT, d)
            z=zipfile.ZipFile(d/"reverse-engineer.zip").namelist()
            self.assertIn("reverse-engineer/SKILL.md", z)
            self.assertIn("reverse-engineer/references/targets.md", z)
            self.assertIn("SKILL.md", zipfile.ZipFile(d/"reverse-engineer-flat.zip").namelist())
        finally: shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main(verbosity=1)
