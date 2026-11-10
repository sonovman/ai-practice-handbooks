#!/usr/bin/env python3
"""보고서 점검기 (핸드북 34). 경영진 보고서(마크다운)를 자료·집계·승인 기준선과 대조한다.

  python tools/report_lint.py work/reports/report.md --intake work/01_intake.json \
      --stats work/02_stats.json --baseline work/03_analysis.md

오류(error)는 고치고 다시, 경고(warn)는 사람이 확인. 이 도구는 형식·일관성 점검이지 내용의 옳음을 보장하지 않는다.
점검 코드
  R01 'Corpus' 용어          R02 번호 옆 출원인·영문명(또는 미확인) 표기 누락
  R03 자료에 없는 문헌번호    R04 출원번호를 공개·등록번호처럼 사용
  R05 정밀분석 후보 5건 초과  R06 Action Items 5개 초과
  R07 핵심 동향에 근거강도 없음  R08 문헌 수가 집계와 다름
  R09 공개 지연 구간의 '감소' 서술  R10 승인 기준선 태그 누락·불일치
  R11 당사 청구항 대조 없는 침해·FTO 단정  R12 요약 문장 수(5~7)
"""
import argparse
import json
import re
from pathlib import Path

from pi_common import compact, utf8_console

NUM_PATTERNS = [
    r"\bKR\s?(?:10|20)-\d{4}-\d{7}\s?[AUBY]?\d?",
    r"\bKR\s?(?:10|20)-\d{7}\s?[BY]\d?",
    r"\bUS\s?\d{4}/?\d{7}\s?A\d",
    r"\bUS\s?\d{1,2},?\d{3},?\d{3}\s?B\d",
    r"\bJP\s?\d{4}-\d{6}\s?A",
    r"\bJP\s?\d{7}\s?[BU]\d?",
    r"\bCN\s?\d{9}\s?[ABU]",
    r"\bCN\s?\d{12}\.?\d?",
    r"\bEP\s?\d\s?\d{3}\s?\d{3}\s?[AB]\d",
]
NUM_RE = re.compile("|".join("(?:%s)" % p for p in NUM_PATTERNS))
LEGAL_RE = re.compile(r"침해한다|침해함|침해에 해당|비침해|침해하지 않는다|FTO\s*(?:확보|문제\s*없)|자유실시\s*가능")
LEGAL_OK = re.compile(r"당사 청구항 대조|확정 아님|미확정|판단하지 않|단정하지 않|결론 아님")
DECLINE_RE = re.compile(r"감소|줄었|줄어|둔화|급감|하락|꺾")
LAG_OK = re.compile(r"공개 지연|미완결|미공개|18개월|공개되지 않")


def core(num):
    c = compact(num)
    return re.sub(r"[A-Z]\d?$", "", c[2:]) if c[:2].isalpha() else re.sub(r"[A-Z]\d?$", "", c)


def build_lookup(intake):
    look = {}
    for r in intake["records"]:
        for f in ("pub_no", "reg_no", "app_no"):
            if r.get(f):
                k = core(r[f])
                if k and (k not in look or f != "app_no"):
                    look[k] = (r, f)
    return look


def sections(lines):
    """(제목, 수준, 시작줄, 끝줄) 목록."""
    heads = [(i, len(m.group(1)), m.group(2).strip()) for i, l in enumerate(lines)
             for m in [re.match(r"^(#{1,6})\s+(.*)", l)] if m]
    out = []
    for n, (i, lv, title) in enumerate(heads):
        end = len(lines)
        for j, lv2, _ in heads[n + 1:]:
            if lv2 <= lv:
                end = j
                break
        out.append((title, lv, i, end))
    return out


def lint(text, intake, stats=None, baseline_text=None):
    lines = text.splitlines()
    issues = []
    look = build_lookup(intake)

    def add(code, level, ln, msg):
        issues.append({"code": code, "level": level, "line": ln, "msg": msg})

    for i, l in enumerate(lines, start=1):
        if re.search(r"corpus", l, re.I):
            add("R01", "error", i, "'Corpus' 대신 '공개특허 모집단·분석대상 문헌' 등으로")
        for m in NUM_RE.finditer(l):
            num = m.group(0).strip()
            hit = look.get(core(num))
            if not hit:
                add("R03", "error", i, "자료(01_intake)에 없는 번호: %s — 오타이거나 지어낸 번호" % num)
                continue
            rec, field = hit
            if field == "app_no":
                add("R04", "error", i, "%s는 출원번호 — 공개·등록번호로 바꿔 쓸 것(%s)" % (num, rec.get("pub_no") or rec.get("reg_no") or "번호 없음"))
                continue
            name_ok = rec["applicant_canon"] in l
            st = rec["en_status"]
            if st in ("official", "official_original", "unofficial", "data_provided"):
                en_ok = (rec["applicant_en"] in l) or rec["applicant_en"] == rec["applicant_canon"]
                if st == "unofficial":
                    en_ok = en_ok and "비공식" in l
            else:
                en_ok = "영문명 미확인" in l
            if not (name_ok and en_ok):
                add("R02", "error", i, "%s 옆에 '%s' 표기가 필요" % (num, rec["applicant_display"]))
        if LEGAL_RE.search(l) and not LEGAL_OK.search(l):
            add("R11", "error", i, "당사 청구항 대조 없이 침해·비침해·FTO를 단정하는 표현")

    secs = sections(lines)

    def count_items(a, b, need_number=False):
        n = 0
        for l in lines[a + 1:b]:
            s = l.strip()
            is_row = s.startswith("|") and not re.match(r"^\|[\s\-:|]+\|$", s)
            is_item = re.match(r"^(\d+\.|[-*])\s+", s)
            if is_row or is_item:
                if need_number and not NUM_RE.search(s):
                    continue
                n += 1
        return n

    for title, lv, a, b in secs:
        if "정밀분석 후보" in title:
            n = count_items(a, b, need_number=True)
            if n > 5:
                add("R05", "error", a + 1, "정밀분석 후보 %d건 — 최대 5건" % n)
        if re.search(r"Action|즉시 결정|실행 과제", title, re.I):
            n = count_items(a, b)
            if n > 5:
                add("R06", "error", a + 1, "Action Items %d개 — 최대 5개" % n)
        if "핵심 기술동향" in title:
            subs = [x for x in secs if x[1] == lv + 1 and a < x[2] < b]
            for st_, _, sa, sb in subs:
                if "근거강도" not in "\n".join(lines[sa:sb]):
                    add("R07", "error", sa + 1, "'%s'에 근거강도(강/중/약)와 근거 수가 없음" % st_)

    if stats:
        s = stats["summary"]
        checks = [(r"분석대상[^0-9\n|]{0,14}(\d+)\s*건", s["trend_scope"], "기술동향 분석대상"),
                  (r"신규 관측[^0-9\n|]{0,14}(\d+)\s*건", s["new_observed"], "이번 회차 신규 관측"),
                  (r"공개특허 모집단[^0-9\n|]{0,14}(\d+)\s*건", s["documents"], "공개특허 모집단")]
        for pat, want, label in checks:
            for i, l in enumerate(lines, start=1):
                for m in re.finditer(pat, l):
                    if int(m.group(1)) != want:
                        add("R08", "error", i, "%s %s건 ≠ 집계 %d건" % (label, m.group(1), want))
        ly = stats.get("lag_start_year")
        if ly:
            for i, l in enumerate(lines, start=1):
                yrs = [int(y) for y in re.findall(r"(20\d{2})년?", l)]
                if DECLINE_RE.search(l) and any(y >= ly for y in yrs) and not LAG_OK.search(l):
                    add("R09", "warn", i, "%d년 이후는 공개 미완결 — '감소'로 읽기 전에 공개 지연을 밝힐 것" % ly)

    tags_known = set(re.findall(r"\[(B\d{2})\]", baseline_text or ""))
    for i, l in enumerate(lines, start=1):
        for t in re.findall(r"\[(B\d{2})\]", l):
            if baseline_text is not None and t not in tags_known:
                add("R10", "error", i, "[%s]는 승인된 분석 기준선에 없음 — 신규 분석사항으로 분리해 재승인" % t)
    for title, lv, a, b in secs:
        if re.search(r"Executive Summary|핵심 요약", title, re.I):
            body = " ".join(l for l in lines[a + 1:b] if l.strip() and not l.startswith("#"))
            sents = [x for x in re.split(r"(?<=\.)\s+", body) if len(x.strip()) > 8]
            if not 5 <= len(sents) <= 7:
                add("R12", "warn", a + 1, "요약 문장 %d개 — 5~7문장 권장" % len(sents))
            if baseline_text is not None:
                for x in sents:
                    if not re.search(r"\[B\d{2}\]", x) and "신규 분석사항" not in x:
                        add("R10", "warn", a + 1, "요약 문장에 기준선 태그가 없음: %s…" % x.strip()[:30])
    return issues


def to_markdown(issues, path):
    e = sum(1 for i in issues if i["level"] == "error")
    w = sum(1 for i in issues if i["level"] == "warn")
    L = ["# 보고서 점검 결과", "", "- 대상: `%s` · 오류 %d · 경고 %d" % (path, e, w), ""]
    for i in issues:
        L.append("- [%s %s] %d행: %s" % (i["level"], i["code"], i["line"], i["msg"]))
    if not issues:
        L.append("- 형식·일관성 점검 통과(내용의 옳음은 사람이 검토)")
    return "\n".join(L) + "\n"


def main():
    utf8_console()
    ap = argparse.ArgumentParser(description="경영진 보고서 점검")
    ap.add_argument("report")
    ap.add_argument("--intake", default="work/01_intake.json")
    ap.add_argument("--stats")
    ap.add_argument("--baseline")
    ap.add_argument("--out")
    a = ap.parse_args()
    text = Path(a.report).read_text(encoding="utf-8")
    intake = json.loads(Path(a.intake).read_text(encoding="utf-8"))
    stats = json.loads(Path(a.stats).read_text(encoding="utf-8")) if a.stats else None
    base = Path(a.baseline).read_text(encoding="utf-8") if a.baseline else None
    issues = lint(text, intake, stats, base)
    md = to_markdown(issues, a.report)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
    print(md)
    raise SystemExit(1 if any(i["level"] == "error" for i in issues) else 0)


if __name__ == "__main__":
    main()
