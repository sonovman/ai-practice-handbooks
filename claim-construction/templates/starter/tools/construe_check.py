#!/usr/bin/env python3
"""청구범위 해석 기록 점검기 (핸드북 31). 표준 라이브러리만.

용어별 해석 기록(JSON)을 받아, 해석 단계에서 흔히 생기는 방법론 오류를 찾습니다.
오류(E, 고쳐야 함)와 경고(W, 사람이 판단)로 나눕니다. 어느 해석이 '옳은지'는 판단하지 않습니다.

  python tools/construe_check.py sample/construction_good.json
  python tools/construe_check.py sample/construction_bad.json --strict
종료 코드: 오류 없으면 0, 있으면 1 (--strict면 경고도 1)
"""
import argparse
import json
import re
import sys
from datetime import date

INTRINSIC = {"claim", "spec", "drawing", "prosecution", "ipr"}
EXTRINSIC = {"dictionary", "expert", "treatise", "article", "inventor"}
DEGREE = re.compile(r"\b(substantially|about|approximately|generally|near|adjacent|relatively|sufficient|small|large|thin|thick|"
                    r"rigid|flexible|unobtrusive|significant|minimal)\b|(실질적|대략|약\s|근처|인접|비교적|충분|얇|두꺼|작은|큰|강성|유연)", re.I)
NONCE = re.compile(r"\b(means|module|mechanism|element|unit|device|component)\s+(for|to|configured)\b|(위한\s*수단|하는\s*수단)", re.I)

STANDARD = {
    "district": "phillips", "itc": "phillips", "ptab": "phillips", "appeal": "phillips",
    "ex_parte": "bri", "reexam": "bri", "reissue": "bri",
    "kr_court": "kr", "kr_trial": "kr", "kr_kipo": "kr",
}


def parse_date(s):
    try:
        y, m, d = [int(x) for x in str(s)[:10].split("-")]
        return date(y, m, d)
    except Exception:
        return None


def words(s):
    return set(re.findall(r"[A-Za-z가-힣0-9]+", (s or "").lower()))


def check(doc):
    errs, warns = [], []
    E = lambda t, c, m: errs.append((t, c, m))
    W = lambda t, c, m: warns.append((t, c, m))
    meta = doc.get("meta", {})
    forum = meta.get("forum", "district")
    std = (meta.get("standard") or "").lower()
    want = STANDARD.get(forum)
    filed = parse_date(meta.get("petition_date"))
    if forum == "ptab" and filed and filed < date(2018, 11, 13):
        want = "bri"
    if want and std and std != want:
        E("-", "C01", "절차와 해석 기준이 맞지 않음: %s → %s 기준이어야 함 (입력: %s)." % (forum, want, std))
    if not std:
        W("-", "C01", "해석 기준(standard)을 적지 않았습니다 — 절차별로 Phillips / BRI / 한국 기준을 밝히세요.")

    dependents = doc.get("dependent_limitations", [])     # 종속항이 추가하는 한정 문구들
    seen = {}
    for t in doc.get("terms", []):
        tid = t.get("term", "?")
        cons = t.get("construction", "") or ""
        ev = t.get("evidence", []) or []
        kinds = {e.get("type") for e in ev}
        intrinsic_ev = [e for e in ev if e.get("type") in INTRINSIC]
        extrinsic_ev = [e for e in ev if e.get("type") in EXTRINSIC]

        # 일관성
        key = tid.lower()
        if key in seen and seen[key] != cons and not t.get("claim_specific_reason"):
            W(tid, "C09", "같은 용어를 다르게 해석함 — 특허 전체에서 같은 의미가 추정됩니다(다르게 볼 근거를 claim_specific_reason에).")
        seen.setdefault(key, cons)

        # 실질적 다툼을 '통상의 의미'로 덮음
        if t.get("disputed") and re.fullmatch(r"\s*(plain and ordinary meaning|plain meaning|통상의\s*의미|문언\s*그대로)\s*\.?\s*", cons, re.I):
            E(tid, "C11", "당사자가 범위를 다투는데 '통상의 의미'로만 정함 — 다툼이 승패를 가르면 경계를 직접 정해야 합니다.")
        if not cons.strip():
            E(tid, "C11", "해석 결론 없음.")
        # 증거 위계
        if not intrinsic_ev:
            E(tid, "C02", "내재적 증거(청구항·명세서·출원경과) 근거 없음 — 해석은 청구항 문언에서 출발합니다.")
        for e in ev:
            if not (e.get("cite") or "").strip():
                E(tid, "C02", "근거 위치 없음(%s) — 단락·도면·서류·쪽을 적으세요." % e.get("type"))
        if extrinsic_ev and any(e.get("contradicts_intrinsic") for e in extrinsic_ev):
            E(tid, "C02", "내재적 기록과 충돌하는 외재적 증거를 결론에 사용 — 사전·전문가 증언은 내재적 기록을 뒤집지 못합니다.")
        if t.get("basis") == "extrinsic" and intrinsic_ev:
            W(tid, "C02", "내재적 증거가 있는데 외재적 증거를 주된 근거로 둠 — 보조 근거로 낮추세요.")
        # 실시예 한정 수입
        if t.get("imports_embodiment") and not (t.get("lexicography") or t.get("disclaimer")):
            E(tid, "C03", "실시예의 구성을 청구항에 끌어들임 — 명세서의 명시적 정의나 명백한 권리 포기가 없으면 허용되지 않습니다.")
        lx = t.get("lexicography")
        if lx and not (lx.get("quote") and lx.get("cite")):
            E(tid, "C04", "자기 정의(lexicography) 주장에 정의 문장·위치가 없음 — 통상 의미를 바꾸려는 명확한 정의가 필요합니다.")
        dc = t.get("disclaimer")
        if dc:
            if not (dc.get("quote") and dc.get("cite")):
                E(tid, "C05", "권리 포기 주장에 해당 진술·위치가 없음.")
            if dc.get("clarity") not in ("clear", "명백"):
                E(tid, "C05", "권리 포기는 '명백하고 확실'해야 함 — 모호한 진술로는 범위를 줄이지 않습니다.")
            if dc.get("source") == "ipr":
                W(tid, "C05", "IPR 등 특허청 절차에서 특허권자 진술도 권리 포기가 될 수 있음 — 침해 쪽에도 같은 범위를 적용하세요.")
            if dc.get("is_estoppel_only"):
                W(tid, "C05", "출원경과 '금반언'(균등 제한)과 '권리 포기'(문언 범위 축소)는 다름 — 어느 효과인지 구분하세요.")
        # 기능식
        text = t.get("claim_text", "") or tid
        mpf = t.get("mpf")
        if NONCE.search(text) and mpf is None:
            W(tid, "C06", "기능식(§112(f)) 후보 표현 — 해당 여부(mpf.applies)를 판단해 기록하세요.")
        if mpf and mpf.get("applies"):
            if forum.startswith("kr"):
                W(tid, "C06", "한국: 기능적 표현은 원칙적으로 그 기능을 가진 모든 구성으로 보되 용어의 기술적 의의는 발명의 설명을 참작해 객관적·합리적으로 해석(대법원 2009. 7. 23. 2007후4977) — 미국 §112(f)식 '명세서 구조와 균등물로 자동 축소' 규칙은 없습니다.")
            else:
                if not (mpf.get("function") or "").strip():
                    E(tid, "C06", "기능식인데 청구된 기능을 특정하지 않음(1단계).")
                if not (mpf.get("structure") or "").strip() or not (mpf.get("structure_cite") or "").strip():
                    E(tid, "C06", "기능식인데 명세서의 대응 구조와 위치가 없음(2단계) — 없으면 불명확성(§112(b)) 위험.")
                if mpf.get("software") and not (mpf.get("algorithm") or "").strip():
                    E(tid, "C06", "컴퓨터 구현 기능식: 범용 프로세서가 아니라 명세서의 알고리즘이 구조입니다.")
        # 정도 표현
        if DEGREE.search(text) and not (t.get("objective_standard") or "").strip():
            W(tid, "C07", "정도·상대 표현 — 명세서가 주는 객관적 기준(예·수치·기능)을 objective_standard에 적으세요(합리적 확실성).")
        # 청구항 차별화
        for dl in dependents:
            dw = words(dl.get("text"))
            if dw and len(dw & words(cons)) >= max(2, int(len(dw) * 0.6)) and (re.match(r"\d+", t.get("ledger_id", "")) or [None])[0] == str(dl.get("parent", "")):
                W(tid, "C08", "해석이 종속항 %s의 추가 한정과 겹침 — 독립항에 그 한정이 없다고 추정됩니다(청구항 차별화)." % dl.get("id"))
        # 인위적 불명확성
        if t.get("indefinite") and t.get("added_words"):
            cw = words(text)
            added = [w for w in t["added_words"] if w.lower() not in cw]
            if added:
                E(tid, "C12", "청구항에 없는 말(%s)을 해석으로 넣고 그 말 때문에 불명확하다고 판단 — 인위적 불명확성." % ", ".join(added))
        if t.get("stipulated") and t.get("definite_because_stipulated"):
            W(tid, "C13", "의미에 합의했다고 명확성이 자동 충족되지는 않음 — 합리적 확실성은 따로 판단.")
        # 대칭성
        use = t.get("used_for") or {}
        if use.get("infringement") and use.get("validity") and use["infringement"] != use["validity"]:
            E(tid, "C10", "침해와 유효성에 다른 해석을 씀 — 청구항은 양쪽에 같은 의미여야 합니다.")
        # 제법한정
        pbp = t.get("product_by_process")
        if pbp:
            if forum.startswith("kr"):
                if pbp.get("infringement_limited_to_process") and not pbp.get("clearly_unreasonable_reason"):
                    E(tid, "C14", "한국: 제법한정물건은 특허요건·침해 모두 물건 자체로 해석이 원칙 — 제조방법으로 한정하려면 '명백히 불합리한 사정'을 적으세요(2015. 2. 12. 2013후1726).")
            else:
                if pbp.get("infringement_limited_to_process") is False:
                    E(tid, "C14", "미국: 침해 판단에서는 제법 한정이 한정으로 작동(Abbott v. Sandoz, en banc 2009).")
                if pbp.get("validity_limited_to_process"):
                    E(tid, "C14", "미국: 유효성은 물건 자체로 판단 — 제조방법이 달라도 같은 물건이 공지면 신규성 문제.")
        # 전제부
        if t.get("preamble_limiting") and not (t.get("preamble_reason") or "").strip():
            W(tid, "C16", "전제부를 한정으로 보는 근거(선행사 제공·출원경과 의존·Jepson 등)를 적으세요.")
        # 항소심 실권
        if meta.get("stage") == "appeal" and t.get("new_on_appeal"):
            if t.get("forfeiture_exception"):
                W(tid, "C15", "실권 예외 주장: %s — 기록상 방어 기회가 없었는지 확인." % t["forfeiture_exception"])
            else:
                E(tid, "C15", "원심 기록에 없던 새 해석 — 실권(forfeiture) 대상. 예외(기습적 직권 해석 등)면 사유를 적으세요.")
    return errs, warns


def report(doc, errs, warns):
    m = doc.get("meta", {})
    out = ["# 해석 점검 결과 — %s / %s" % (m.get("patent", "?"), m.get("forum", "?")),
           "", "- 기준: %s · 단계: %s" % (m.get("standard", "?"), m.get("stage", "trial")),
           "- 오류 %d건 · 경고 %d건" % (len(errs), len(warns)), ""]
    if errs:
        out += ["## 오류 (고쳐야 함)"] + ["- [%s] %s %s" % e for e in errs] + [""]
    if warns:
        out += ["## 경고 (사람이 판단)"] + ["- [%s] %s %s" % w for w in warns] + [""]
    if not errs and not warns:
        out.append("통과 — 방법론 결함을 찾지 못했습니다. (해석의 옳고 그름은 별도 판단)")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="청구범위 해석 기록 점검")
    ap.add_argument("construction_json")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    with open(a.construction_json, encoding="utf-8") as f:
        doc = json.load(f)
    errs, warns = check(doc)
    rep = report(doc, errs, warns)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(rep)
    sys.stdout.write(rep)
    return 1 if errs or (a.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
