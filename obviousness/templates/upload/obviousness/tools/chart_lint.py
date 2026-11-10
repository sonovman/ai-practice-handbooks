#!/usr/bin/env python3
"""Claim Chart 품질 점검기 (핸드북 30). 표준 라이브러리만.

한정 원장 + 대응 행(JSON)을 받아, 법원·상대방이 흔히 문제 삼는 결함을 찾습니다.
결과는 오류(E, 고쳐야 함)와 경고(W, 사람이 판단)로 나눕니다. 법적 결론을 내리지 않습니다.

  python tools/chart_lint.py sample/chart_good.json
  python tools/chart_lint.py sample/chart_bad.json --strict   # 경고도 실패로
종료 코드: 오류 없으면 0, 있으면 1 (--strict면 경고도 1)
"""
import argparse
import json
import re
import sys
from datetime import date

PIN = re.compile(r"(p\.?\s*\d|pp\.|page|쪽|면|¶|para|단락|문단|fig|도\s*\d|도면|부호|col\.?\s*\d|line|행|라인|표\s*\d|table|"
                 r"함수|function|\(\)|\.c\b|\.py\b|\.cpp\b|\.java\b|\.js\b|lines?\s*\d|청구항\s*\d|\[\d{4}\]|section|§|절)", re.I)
RANGE = re.compile(r"(?:p{1,2}\.?|page|쪽)?\s*(\d+)\s*[-~–]\s*(\d+)\s*(?:쪽|면|pages?)?", re.I)
VAGUE = re.compile(r"(전체|전반|참조$|entire|passim|generally|throughout|이하\s*참조|매뉴얼\s*참조|see\s+generally)", re.I)
PLACEHOLDER = re.compile(r"(information and belief|정보와\s*믿음|정보\s*및\s*믿음|추후\s*(보완|보충|입증|제출)|to be supplemented|"
                         r"reserve[s]? the right|권리를\s*유보|\be\.g\.|including but not limited to|이에\s*한정되지\s*않|등을\s*포함하나|"
                         r"전문가\s*(의견|보고서)로\s*(입증|보완)|discovery\s*후\s*보완)", re.I)
BECAUSE = re.compile(r"(because|since|왜냐하면|때문|이므로|므로|따라서)", re.I)
DOE_BOILER = re.compile(r"(to the extent.*not literally|문언\s*침해가\s*아니(라면|더라도).*균등)", re.I)
SEE_CLAIM = re.compile(r"^\s*(see\s+claim\s*\d+|청구항\s*\d+\s*(참조|과\s*같음|와\s*같음))\s*\.?\s*$", re.I)
CONNECTOR_ONLY = re.compile(r"^\s*(or|and|either|when|between|before|after|또는|및|그리고|혹은)\s*$", re.I)
RECV = re.compile(r"(receiv|수신|read\b|읽|download|inbound|server)", re.I)
SEND = re.compile(r"(send|transmit|송신|write\b|쓰기|upload|outbound|client|dosend)", re.I)
NEG_WORD = re.compile(r"(없|부재|absent|absence|does not|no\s+\w+\s+(is|are)|not\s+(include|have|present))", re.I)
NATIVE = re.compile(r"(`[^`]+`|\"[^\"]+\"|“[^”]+”|'[^']+'|[A-Z]{1,5}-?\d{1,5}|[A-Za-z_]+\(\)|\b[A-Z][a-z]+[A-Z]\w*)")

STOP = set("a an the of to in on at for and or with by is are be said 상기 및 또는 의 을 를 이 가 은 는 에 로 으로 하는 된".split())


def tokens(s):
    return [t for t in re.findall(r"[A-Za-z가-힣0-9]+", (s or "").lower()) if t not in STOP and len(t) > 1]


def parse_date(s):
    try:
        y, m, d = [int(x) for x in str(s)[:10].split("-")]
        return date(y, m, d)
    except Exception:
        return None


def lint(chart):
    errs, warns = [], []
    E = lambda rid, code, msg: errs.append((rid, code, msg))
    W = lambda rid, code, msg: warns.append((rid, code, msg))
    meta = chart.get("meta", {})
    ctype = meta.get("chart_type", "infringement")
    stage = meta.get("stage", "final")            # pic(초기) | final(디스커버리 후·최종)
    prio = parse_date(meta.get("priority_date"))
    target = (meta.get("target") or {})
    lims = {l["id"]: l for l in chart.get("limitations", [])}
    rows = {r["id"]: r for r in chart.get("rows", [])}

    # E01 전구성요소
    for lid, l in lims.items():
        if CONNECTOR_ONLY.match(l.get("text", "")):
            E(lid, "E12", "접속사·관계어만으로 된 '가짜 요소' — 관련 구성의 조건·대안 명제로 결합하세요.")
        if lid not in rows:
            if l.get("type") == "preamble":
                W(lid, "W01", "전제부 행이 없습니다 — 한정으로 해석될 경우를 대비해 조건부 대응을 두세요.")
            else:
                E(lid, "E01", "대응 행 없음 — 모든 한정은 각각 대응돼야 합니다(전구성요소 원칙).")
    for rid in rows:
        if rid not in lims:
            W(rid, "W02", "원장에 없는 행 — 한정 ID를 맞추세요.")

    refs_102 = set()
    any_doe = False
    for rid, r in rows.items():
        l = lims.get(rid, {})
        theory = r.get("theory", "literal")
        facts = r.get("facts") or []
        expl = r.get("explanation", "") or ""
        assertion = r.get("assertion", "") or ""
        alltext = " ".join([assertion, expl] + [f.get("text", "") for f in facts])

        # E13 종속항 단순 참조
        if SEE_CLAIM.match(expl) or SEE_CLAIM.match(assertion):
            E(rid, "E13", "'청구항 N 참조'만으로는 결론적 기재 — 원용 범위를 명시하고 추가 한정은 따로 주장·사실·설명.")
            continue
        # E02 3박자
        if not assertion.strip():
            E(rid, "E02", "주장(Assertion) 없음.")
        if not facts:
            E(rid, "E02", "사실(Facts) 없음 — 결론만 있는 행은 증거로 취급되지 않습니다.")
        if not expl.strip():
            E(rid, "E02", "설명(Explanation) 없음 — 사실이 왜 한정을 충족하는지 연결하세요.")
        elif not BECAUSE.search(expl):
            W(rid, "W03", "설명에 '왜냐하면/because' 연결이 보이지 않습니다.")
        # E03 핀포인트·덤핑
        for f in facts:
            pin = f.get("pin", "") or ""
            if not pin.strip() or not PIN.search(pin):
                E(rid, "E03", "핀포인트 없음: '%s' — 쪽·단락·도면 부호·파일/함수/행을 특정하세요." % (f.get("source", "?")))
            if VAGUE.search(pin):
                E(rid, "E03", "모호한 인용('%s') — 덤핑으로 봅니다." % pin)
            for mm in RANGE.finditer(pin):
                a, b = mm.group(1), mm.group(2)
                after, before = pin[mm.end():mm.end() + 4], pin[max(0, mm.start() - 7):mm.start()]
                if re.search(r"(행|line)", after, re.I) or re.search(r"(lines?|행)\s*$", before, re.I) \
                        or re.search(r"\d\s*:\s*$", before):
                    if int(b) - int(a) > 80:
                        E(rid, "E03", "코드 인용 범위가 넓음(%s~%s행) — 한정을 충족하는 함수·행만 고르세요." % (a, b))
                    continue
                if int(b) - int(a) > 10:
                    E(rid, "E03", "인용 범위가 넓음(%s~%s, %d쪽) — 필요한 쪽·행만 고르세요." % (a, b, int(b) - int(a)))
            # E14 프랑켄차트
            prod = f.get("product")
            if prod and target.get("name") and prod != target.get("name") and not target.get("representative_basis"):
                E(rid, "E14", "다른 제품(%s)의 증거 혼합 — 대표성 근거 없이 짜깁기하면 안 됩니다." % prod)
            # E10 날짜
            fd = parse_date(f.get("date"))
            if prio and fd:
                if ctype.startswith("invalidity") and fd >= prio:
                    E(rid, "E10", "선행기술 날짜(%s)가 우선일(%s) 이후 — 선행기술이 아닙니다." % (fd, prio))
                if ctype in ("infringement", "domestic_industry") and fd < prio:
                    W(rid, "W10", "침해 증거 날짜(%s)가 우선일(%s)보다 앞섬 — '이후면 침해, 이전이면 선행기술': 자기 특허를 무효로 만들 위험." % (fd, prio))
            if f.get("executed") is False and (l.get("type") == "step" or chart.get("meta", {}).get("method")):
                E(rid, "E17", "실행되지 않는 코드는 방법 단계의 수행 증거가 아닙니다.")
            if ctype == "invalidity_102" and f.get("ref"):
                refs_102.add(f["ref"])
        # E04 청구항 흉내
        ft = " ".join(f.get("text", "") for f in facts)
        lt = set(tokens(l.get("text", "")))
        if ft and lt:
            ftk = tokens(ft)
            overlap = sum(1 for t in ftk if t in lt) / max(1, len(ftk))
            if overlap >= 0.5 and not NATIVE.search(ft):
                E(rid, "E04", "사실이 청구항 문언을 되풀이함(겹침 %.0f%%) — 대상물의 고유 명칭(부품번호·함수명·메뉴명)으로 쓰세요." % (overlap * 100))
        # E05 자리표시자
        if PLACEHOLDER.search(alltext):
            (W if stage == "pic" else E)(rid, "E05", "유보·자리표시자 표현 — 최종 차트에서는 확정 증거로 바꾸세요." +
                                         (" (초기 단계라 경고로만 표시)" if stage == "pic" else ""))
        # E06 균등론
        if theory == "doe":
            any_doe = True
            fwr = r.get("fwr") or {}
            miss = [k for k in ("function", "way", "result", "why_insubstantial") if not (fwr.get(k) or "").strip()]
            if miss:
                E(rid, "E06", "균등론 주장에 %s 없음 — 기능·방식·결과와 차이가 사소한 이유를 한정별로." % ", ".join(miss))
            if not (fwr.get("linking") or "").strip():
                W(rid, "W06", "균등론 연결 증거(전문가 진술 단락·상호교환성 자료) 표시 없음.")
            if (r.get("prosecution_check") or "").strip() == "":
                W(rid, "W07", "출원경과 금반언·공중헌납·한정 형해화 점검 기록 없음.")
        if DOE_BOILER.search(alltext) and theory != "doe":
            E(rid, "E06", "상투적 균등론 문구 — 구체적 F/W/R 없이 쓰면 효력이 없습니다.")
        # E07 기능식
        if l.get("type") == "mpf":
            if not (l.get("sam") or "").strip():
                E(rid, "E07", "기능식 한정인데 원장에 명세서 대응 구조(SAM) 없음.")
            if not (r.get("sam_match") or "").strip():
                E(rid, "E07", "기능만 비교함 — 대상물의 대응 구조가 SAM과 같거나 균등한지 설명(sam_match)하세요.")
        # E11 방향성
        if RECV.search(l.get("text", "")) and SEND.search(ft) and not RECV.search(ft):
            W(rid, "W11", "방향성 의심 — 한정은 수신/읽기인데 증거는 송신/쓰기 쪽입니다.")
        # E15 부정한정
        if l.get("type") == "negative" and not NEG_WORD.search(alltext):
            W(rid, "W15", "부정한정인데 '없음(부재)'을 입증하는 문장이 보이지 않습니다.")

    # E08 진보성
    if ctype == "invalidity_103":
        for k in ("motivation", "expectation"):
            if not (chart.get("combination", {}).get(k) or "").strip():
                E("-", "E08", "진보성(비자명성) 차트에 %s 없음 — 결합 동기와 합리적 성공 기대를 따로 쓰세요." %
                  {"motivation": "결합 동기", "expectation": "성공에 대한 합리적 기대"}[k])
    # E09 신규성 단일 문헌
    if ctype == "invalidity_102" and len(refs_102) > 1:
        E("-", "E09", "신규성 차트에 문헌이 여럿(%s) — 신규성은 단일 문헌, 결합은 진보성 차트로." % ", ".join(sorted(refs_102)))
    # W16 대칭성
    if any_doe and not chart.get("symmetry"):
        W("-", "W16", "균등론으로 범위를 넓혔다면, 같은 넓이로 선행기술에 포섭되지 않는지(대칭성) 기록하세요.")
    # 대표 제품
    if target.get("representative") and not (target.get("representative_basis") or "").strip():
        E("-", "E14", "대표 제품 차트인데 대표성 근거(공통 구조·코드·작동) 없음.")
    return errs, warns


def report(chart, errs, warns):
    meta = chart.get("meta", {})
    out = ["# 차트 점검 결과 — %s / 청구항 %s / %s" % (meta.get("patent", "?"), meta.get("claim", "?"),
                                                (meta.get("target") or {}).get("name", "?")),
           "", "- 유형: %s · 단계: %s · 우선일: %s" % (meta.get("chart_type", "infringement"), meta.get("stage", "final"),
                                                 meta.get("priority_date", "?")),
           "- 오류 %d건 · 경고 %d건" % (len(errs), len(warns)), ""]
    if errs:
        out += ["## 오류 (고쳐야 함)"] + ["- [%s] %s %s" % e for e in errs] + [""]
    if warns:
        out += ["## 경고 (사람이 판단)"] + ["- [%s] %s %s" % w for w in warns] + [""]
    if not errs and not warns:
        out.append("통과 — 형식 결함을 찾지 못했습니다. (법적 판단은 별도)")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Claim Chart 품질 점검")
    ap.add_argument("chart_json")
    ap.add_argument("--strict", action="store_true", help="경고도 실패로 처리")
    ap.add_argument("--out", help="결과를 Markdown으로 저장")
    a = ap.parse_args(argv)
    with open(a.chart_json, encoding="utf-8") as f:
        chart = json.load(f)
    errs, warns = lint(chart)
    rep = report(chart, errs, warns)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(rep)
    sys.stdout.write(rep)
    return 1 if errs or (a.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
