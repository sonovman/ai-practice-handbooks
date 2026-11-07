#!/usr/bin/env python3
"""요약·보고서의 '원문 근거' 대조기 (핸드북 19·20). 표준 라이브러리만 사용.

AI가 쓴 요약에 붙은 인용(“…”)이 원문에 실제로 있는지, 요약 속 수치가 원문에 있는지 확인합니다.
"원문 구절을 병기하라"는 지시만으로는 인용 자체를 지어내는 경우를 막지 못하기 때문입니다.

  python tools/evidence_check.py 원문.txt 요약.md
  python tools/evidence_check.py 논문.pdf 요약.md --report report.md      # PDF는 pdftotext 필요
  python tools/evidence_check.py 원문.md 요약.md --json

판정
  FAIL  원문에서 찾을 수 없는 인용 / 원문에 없는 수치(계산·추정 표시 없음)
  WARN  일부만 일치하는 인용(글자 바뀜 의심) / 계산·추정 표시가 붙은 수치 / [원문] 구획에 인용 없는 문장
  OK    그대로 확인됨
종료 코드  0 통과 · 1 경고 · 2 실패
"""
import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

QUOTE_RE = re.compile(r"“([^”\n]{6,})”|\"([^\"\n]{6,})\"|「([^」\n]{6,})」|『([^』\n]{6,})』")
NUM_RE = re.compile(r"(?<![\w.])[-−]?\d[\d,]*(?:\.\d+)?\s?(?:%|%p|퍼센트|배|명|건|개|곳|대|회|년|개월|주|일|시간|분|초|원|달러|km|m|cm|mm|kg|g|ms|s|℃|°C|점)?")
DERIVED_MARK = re.compile(r"계산|추정|환산|약\s|≈|~|어림|derived|approx", re.I)
YEAR_LIKE = re.compile(r"^(19|20)\d\d(년)?$")
FACT_HEAD = re.compile(r"^\s*#{1,6}\s*.*(\[원문\]|원문 사실|Facts?)", re.I)
OTHER_HEAD = re.compile(r"^\s*#{1,6}\s")


def read_source(path):
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        if shutil.which("pdftotext") is None:
            sys.exit("PDF를 읽으려면 pdftotext(poppler)가 필요합니다. 또는 원문을 .txt로 저장해 넣으세요.")
        r = subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True, text=True, check=True)
        return r.stdout
    return p.read_text(encoding="utf-8-sig")


def squash(s):
    """공백·줄바꿈·하이픈 줄넘김·따옴표 차이를 무시하고 비교."""
    s = s.replace("-\n", "").replace("­", "")
    s = re.sub(r"[\s​]+", "", s)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return s.lower()


def norm_num(tok):
    t = tok.replace("−", "-").replace(",", "").replace(" ", "")
    return t


def bare(tok):
    m = re.match(r"-?\d+(?:\.\d+)?", norm_num(tok))
    return m.group(0) if m else tok


def best_match_ratio(quote_sq, source_sq):
    """인용이 원문 어딘가와 얼마나 겹치는지(가장 긴 공통 구간 / 인용 길이)."""
    if not quote_sq:
        return 0.0
    if quote_sq in source_sq:
        return 1.0
    sm = difflib.SequenceMatcher(None, source_sq, quote_sq, autojunk=False)
    blocks = sm.get_matching_blocks()
    # 인용 길이 범위 안에서 겹친 글자 수 합으로 근사
    best = 0
    for b in blocks:
        if b.size == 0:
            continue
        start = b.a - b.b
        window = source_sq[max(0, start): max(0, start) + len(quote_sq)]
        r = difflib.SequenceMatcher(None, window, quote_sq, autojunk=False).ratio()
        best = max(best, r)
        if best > 0.97:
            break
    return best


def strip_quotes(text):
    return QUOTE_RE.sub(" ", text)


def check(source, output):
    src_sq = squash(source)
    src_nums = {bare(m.group(0)) for m in NUM_RE.finditer(source)}
    items = []

    quotes = [next(g for g in m.groups() if g) for m in QUOTE_RE.finditer(output)]
    q_ok = q_warn = q_fail = 0
    for q in quotes:
        r = best_match_ratio(squash(q), src_sq)
        if r >= 0.999:
            q_ok += 1
        elif r >= 0.85:
            bad_nums = [m.group(0).strip() for m in NUM_RE.finditer(q) if bare(m.group(0)) not in src_nums]
            if bad_nums:
                q_fail += 1
                items.append({"level": "FAIL", "item": "인용 속 수치가 원문과 다름",
                              "detail": "{} — {}".format(", ".join(bad_nums), q[:80])})
            else:
                q_warn += 1
                items.append({"level": "WARN", "item": "인용(부분 일치)", "detail": "{:.0%} 일치 — 글자가 바뀌었는지 확인: {}".format(r, q[:80])})
        else:
            q_fail += 1
            items.append({"level": "FAIL", "item": "인용(원문에 없음)", "detail": q[:100]})

    n_fail = n_warn = 0
    for line in output.splitlines():
        body = strip_quotes(line)
        for m in NUM_RE.finditer(body):
            tok = m.group(0).strip()
            b = bare(tok)
            if not re.search(r"\d", b) or len(b.replace(".", "").replace("-", "")) < 1:
                continue
            if b in src_nums:
                continue
            if re.fullmatch(r"\d", b) and not re.search(r"[%배명건]", tok):
                continue  # 목록 번호·단계 번호(1, 2, 3 …)는 건너뜀
            if YEAR_LIKE.match(norm_num(tok)) and b in {bare(x) for x in re.findall(r"(?:19|20)\d\d", source)}:
                continue
            if DERIVED_MARK.search(line):
                n_warn += 1
                items.append({"level": "WARN", "item": "수치(계산·추정 표시)", "detail": "{} — 계산식이나 근거를 함께 적었는지 확인: {}".format(tok, line.strip()[:90])})
            else:
                n_fail += 1
                items.append({"level": "FAIL", "item": "수치(원문에 없음)", "detail": "{} — {}".format(tok, line.strip()[:90])})

    # [원문] 구획 안에서 인용 없이 쓴 문장
    in_fact, unq = False, []
    for line in output.splitlines():
        if FACT_HEAD.match(line):
            in_fact = True
            continue
        if OTHER_HEAD.match(line):
            in_fact = False
        if in_fact and re.search(r"[가-힣A-Za-z]{4,}", line) and not QUOTE_RE.search(line) and len(line.strip()) > 25:
            unq.append(line.strip()[:70])
    for u in unq:
        items.append({"level": "WARN", "item": "[원문] 문장에 인용 없음", "detail": u})

    status = "FAIL" if any(i["level"] == "FAIL" for i in items) else "WARN" if items else "OK"
    summary = {"인용": len(quotes), "인용 확인": q_ok, "인용 부분 일치": q_warn, "인용 없음": q_fail,
               "원문에 없는 수치": n_fail, "계산·추정 수치": n_warn}
    return {"status": status, "summary": summary, "items": items}


def to_markdown(res, src, out):
    mark = {"OK": "통과", "WARN": "경고", "FAIL": "실패"}
    s = res["summary"]
    lines = ["# 원문 근거 대조 보고서", "", "- 원문: `{}`".format(src), "- 요약: `{}`".format(out),
             "- 판정: **{}**".format(mark[res["status"]]),
             "- 인용 {}개 중 확인 {} · 부분 일치 {} · 원문에 없음 {}".format(s["인용"], s["인용 확인"], s["인용 부분 일치"], s["인용 없음"]),
             "- 원문에 없는 수치 {} · 계산·추정 표시 수치 {}".format(s["원문에 없는 수치"], s["계산·추정 수치"]), ""]
    if res["items"]:
        lines += ["| 판정 | 항목 | 내용 |", "|---|---|---|"]
        for i in res["items"]:
            lines.append("| {} | {} | {} |".format(mark[i["level"]], i["item"], i["detail"].replace("|", "/")))
    lines += ["", "> 기계 대조는 '원문에 그 글자가 있는가'만 봅니다. 인용이 맞아도 맥락을 거꾸로 읽었는지는 사람이 확인합니다."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="요약의 인용·수치를 원문과 대조")
    ap.add_argument("source", help="원문(.txt .md, .pdf는 pdftotext 필요)")
    ap.add_argument("output", help="AI가 쓴 요약·보고서(.md)")
    ap.add_argument("--report", help="보고서 저장 경로(.md)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = check(read_source(a.source), Path(a.output).read_text(encoding="utf-8-sig"))
    if a.json:
        sys.stdout.write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    else:
        md = to_markdown(res, a.source, a.output)
        sys.stdout.write(md)
        if a.report:
            Path(a.report).write_text(md, encoding="utf-8")
    return {"OK": 0, "WARN": 1, "FAIL": 2}[res["status"]]


if __name__ == "__main__":
    sys.exit(main())
