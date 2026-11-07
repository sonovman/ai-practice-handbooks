#!/usr/bin/env python3
"""역공학 근거 로그 (핸드북 21). 표준 라이브러리만 사용.

REA의 Evidence v2(통과/실패/미확인 구분)를 흉내 낸 작은 기록 도구입니다.
AI가 "이렇게 동작한다"고 말할 때마다, 그 근거(디컴파일 위치·주소·상수)를 한 줄씩 적어 두고
재구현한 코드가 원본과 맞는지(통과/실패) 표시합니다. 추측과 근거를 섞지 않기 위한 장치입니다.

  python tools/evidence_log.py add  --claim "200+10%는 220" --kind pseudocode --loc "calc.dll +0x1a2f" --status unknown
  python tools/evidence_log.py add  --claim "pan 상수 1.5625" --kind constant --loc "0x420068" --status pass --note "3205 케이스 일치"
  python tools/evidence_log.py list
  python tools/evidence_log.py report --out work/evidence.md

파일은 work/evidence.jsonl 에 한 줄 JSON으로 쌓입니다.
kind 예시: pseudocode(의사코드) · assembly(어셈블리) · constant(상수) · xref(호출관계) · string(문자열) · network(요청) · unknown
status: pass(원본과 일치 확인) · fail(불일치) · unknown(미확인·추측)
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "work" / "evidence.jsonl"
STATUSES = {"pass", "fail", "unknown"}


def add(a):
    if a.status not in STATUSES:
        sys.exit("status는 pass/fail/unknown 중 하나")
    path = Path(a.file)
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
           "claim": a.claim, "kind": a.kind, "loc": a.loc, "status": a.status, "note": a.note or ""}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    sys.stdout.write("기록: [{}] {} ({} @ {})\n".format(rec["status"], rec["claim"], rec["kind"], rec["loc"]))
    return 0


def load(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def summarize(recs):
    c = {"pass": 0, "fail": 0, "unknown": 0}
    for r in recs:
        c[r.get("status", "unknown")] = c.get(r.get("status", "unknown"), 0) + 1
    return c


def cmd_list(a):
    recs = load(a.file)
    if not recs:
        sys.stdout.write("기록 없음\n")
        return 0
    for i, r in enumerate(recs, 1):
        sys.stdout.write("{:>2}. [{}] {} — {} @ {} {}\n".format(
            i, r["status"], r["claim"], r["kind"], r["loc"], ("· " + r["note"]) if r.get("note") else ""))
    c = summarize(recs)
    sys.stdout.write("\n통과 {pass} · 실패 {fail} · 미확인 {unknown}\n".format(**c))
    return 0 if c["fail"] == 0 and c["unknown"] == 0 else 1


def cmd_report(a):
    recs = load(a.file)
    c = summarize(recs)
    lines = ["# 역공학 근거 로그", "",
             "- 통과 {pass} · 실패 {fail} · 미확인 {unknown}".format(**c), "",
             "| # | 상태 | 주장 | 근거 종류 | 위치 | 메모 |", "|---|---|---|---|---|---|"]
    lab = {"pass": "통과", "fail": "실패", "unknown": "미확인"}
    for i, r in enumerate(recs, 1):
        lines.append("| {} | {} | {} | {} | {} | {} |".format(
            i, lab.get(r["status"], r["status"]), r["claim"], r["kind"], r["loc"], r.get("note", "").replace("|", "/")))
    lines += ["", "> 미확인(unknown)은 아직 근거로 확인되지 않은 추측입니다. 재구현·보고 전에 통과/실패로 바꾸거나 '추정'으로 표시하세요.",
              "> 실패(fail)가 남아 있으면 재구현 결과를 신뢰하지 마세요."]
    text = "\n".join(lines) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        sys.stdout.write("저장: {}\n".format(a.out))
    else:
        sys.stdout.write(text)
    return 0 if c["fail"] == 0 and c["unknown"] == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="역공학 근거 로그")
    ap.add_argument("--file", default=str(DEFAULT))
    sub = ap.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("add")
    pa.add_argument("--claim", required=True)
    pa.add_argument("--kind", default="unknown")
    pa.add_argument("--loc", default="")
    pa.add_argument("--status", default="unknown")
    pa.add_argument("--note", default="")
    sub.add_parser("list")
    pr = sub.add_parser("report")
    pr.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "add":
        return add(a)
    if a.cmd == "list":
        return cmd_list(a)
    return cmd_report(a)


if __name__ == "__main__":
    sys.exit(main())
