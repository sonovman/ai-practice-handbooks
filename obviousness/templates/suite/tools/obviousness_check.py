#!/usr/bin/env python3
"""진보성(비자명성) 판단 재료 점검기 (핸드북 33). 표준 라이브러리만.

판단(개시 여부·기술상식 성립·결합 동기)은 사람·AI가 obviousness.json에 '근거 위치와 함께' 적고,
이 도구는 그 판단을 공개된 규칙으로 집계·점검합니다. 결론(진보성 있음/없음)은 내리지 않습니다.

  python tools/obviousness_check.py sample/obviousness.json
  python tools/obviousness_check.py sample/obviousness.json --out work/reports/obviousness.md
  python tools/obviousness_check.py sample/obviousness.json --chart C1 --chart-out work/02_chart.json

하는 일
  1. 선행문헌 분류  A 신규성 부정 후보 / B 주인용발명(최근접) 후보 / C 보조 문헌 / X 기준일 이후
  2. 상위 B와 청구항의 차이점 목록
  3. 차이점별 '기준일 당시 기술상식·주지관용기술' 조사 기록과 증거 강도 점검
  4. 결합 논리(빠진 한정·동기·성공 기대·저해 사유·유사 분야) 점검
  5. 2차적 고려사항(객관적 지표)·효과 점검
  6. 고른 결합을 30편 진보성 Claim Chart(invalidity_103)로 변환

점수(B 순위) = 100 × 관련성 × (1 − 수정부담/총가중치)            (28편 rank_closest와 같은 틀)
  관련성: 분야·과제 둘 다 1.0 / 하나 0.8 / 없음 0.5     개시도: ● 1 · ◐ 0.5 · ○ 0
  수정부담 = Σ 가중치 × (1−개시도) × 난이도
  난이도: 차이점이 증거 충분한 기술상식이면 0.25 / 다른 문헌이 ●로 메우면 0.5 / 아니면 1.0
          그 문헌이 그 방향을 꺼린다(teaches_away, 단순 선호·장단점 비교 제외)면 1.0
종료 코드: 오류 없으면 0, 있으면 1
"""
import argparse
import json
import re
import sys
from datetime import date

GRADE = {"●": 1.0, "◐": 0.5, "○": 0.0}
STRONG = {"textbook", "handbook", "standard", "review", "dictionary"}   # 교과서·핸드북·표준·총설·사전
COULD = re.compile(r"(할\s*수\s*있었|결합할\s*수\s*있|could\s+have|could\s+combine|가능했|가능하다)", re.I)
WHY = re.compile(r"(이유|때문|동기|목적으로|위해|하려|because|in order to|so as to|to\s+\w+\s+the|요구|필요)", re.I)
OTT = re.compile(r"(2143\s*\(E\)|obvious\s*to\s*try|시도할\s*만|시도의\s*자명)", re.I)
CROSS = re.compile(r"(?<![A-Za-z0-9])(C\d+)(?![0-9])")
TA_WEAK = {"preference", "tradeoff"}          # 단순 선호·장단점 비교 — 저해 아님(Gurley·Fulton)
TA_STRONG = {"discourage", "inoperable", "principle"}
TYPE_NOTE = {
    "selection": "선택발명 — 구성(선택)의 곤란성을 먼저 보고, 효과의 현저성은 그 판단을 보완한다(대법원 2021. 4. 8. 2019후10609).",
    "crystal": "결정형 발명 — 다형체 스크리닝이 통상적이라는 사정만으로 곤란성을 부정하지 않고 교시·동기·스크리닝 범위·예측 못한 효과를 종합(2022. 3. 31. 2018후10923). 같은 기준에서 진보성 부정 사례(2024. 3. 28. 2021후10343).",
    "numeric": "수치한정 발명 — 공지 구성의 수치만 한정했고 현저한 효과가 명세서에 없으면 반복 실험으로 고를 수 있는 단순 수치한정으로 본다(2010후2698 제2항 판단 중). 임계적 의의를 확인.",
    "medical_use": "의약용도 발명 — 선행발명의 치료 효과가 임상시험으로 확인될 것까지 요구되지 않으며, 기준일 기술수준에서 쉽게 예측되면 진보성이 부정될 수 있다(2019. 1. 31. 2016후502). 미국은 합리적 성공 기대를 엄격히 다툼(ImmunoGen 2025).",
}
SELF = re.compile(r"(대상\s*특허|본건\s*특허|본\s*발명|이\s*특허|the\s+patent|subject\s+patent|'\d{3}\s*patent|청구항\s*\d)", re.I)


def pdate(s):
    try:
        y, m, d = [int(x) for x in str(s)[:10].split("-")]
        return date(y, m, d)
    except Exception:
        return None


def weight(l):
    return float(l.get("weight", 3 if l.get("core") else 1))


def cgk_strength(k, prio):
    """기술상식 항목 하나의 증거 강도: strong / weak / none, 그리고 문제 목록."""
    ev = k.get("evidence") or []
    probs = []
    valid = []
    for e in ev:
        d = pdate(e.get("date"))
        if d is None:
            probs.append(("E", "O05", "증거 날짜 없음: %s — 기준일 전 자료인지 확인할 수 없습니다." % e.get("source", "?")))
        elif prio and d >= prio:
            probs.append(("E", "O05", "증거 날짜(%s)가 기준일(%s) 이후: %s — 기준일 당시 기술상식의 증거가 아닙니다." % (d, prio, e.get("source", "?"))))
        else:
            valid.append(e)
        if not (e.get("pin") or "").strip():
            probs.append(("E", "O05", "증거 위치(쪽·단락) 없음: %s" % e.get("source", "?")))
    if k.get("status") != "established":
        return "none", probs
    if not valid:
        if k.get("evident_to_public"):
            probs.append(("W", "O05", "증거 없이 '누구나 아는 사실'로 처리 — 일반인에게도 자명한 경우에만 허용됩니다. 다투면 증거가 필요합니다."))
            return "weak", probs
        probs.append(("E", "O05", "기술상식이라 했으나 기준일 전 증거가 없음 — 주장만으로는 기술상식이 되지 않습니다."))
        return "none", probs
    kinds = {e.get("type", "") for e in valid}
    applicants = {(e.get("applicant") or e.get("source", "")).strip() for e in valid if e.get("type") == "patent"}
    if kinds & STRONG or len({e.get("source") for e in valid if e.get("type") != "patent"}) >= 2 or len(applicants) >= 3:
        return "strong", probs
    probs.append(("W", "O06", "증거가 특허 문헌 %d건(출원인 %d곳)뿐 — 한두 건의 명세서만으로는 주지관용기술로 보기 어렵습니다. "
                  "교과서·핸드북·표준 또는 서로 다른 출원인의 여러 문헌을 더하세요." % (len(valid), len(applicants))))
    return "weak", probs


def analyze(doc, min_coverage=None, top=2):
    E, W, I = [], [], []
    add = {"E": E, "W": W, "I": I}
    meta = doc.get("meta", {})
    prio = pdate(meta.get("priority_date"))
    proc = meta.get("proceeding", "exam")
    forum = meta.get("forum", "us+kr")
    mc = float(min_coverage if min_coverage is not None else meta.get("min_coverage", 0.6))
    lims = doc.get("limitations", [])
    lid = [l["id"] for l in lims]
    L = {l["id"]: l for l in lims}
    w = {k: weight(L[k]) for k in lid}
    wsum = sum(w.values()) or 1.0
    refs = doc.get("references", [])
    R = {r["id"]: r for r in refs}
    K = {k["id"]: k for k in doc.get("cgk", [])}

    # 0. 기준
    if not prio:
        E.append(("-", "O01", "meta.priority_date(기준일: 우선일·출원일) 없음 — 모든 선행기술·기술상식은 이 날짜 기준입니다."))
    posita = doc.get("posita") or {}
    if not (posita.get("definition") or "").strip():
        E.append(("-", "O01", "통상의 기술자 수준(posita.definition) 없음 — 기술수준을 먼저 정해야 차이의 용이성을 판단할 수 있습니다."))
    elif not posita.get("basis"):
        W.append(("-", "O01", "통상의 기술자 수준의 근거(posita.basis) 없음 — 선행문헌의 기술수준·교육·실무 경력 근거를 적으세요."))
    for k in lid:
        if L[k].get("needs_review"):
            W.append((k, "O18", "31편 해석 반영 뒤 '재검토' 표시가 남은 한정 — 해석을 확정한 뒤 개시 여부를 다시 보세요."))

    # 1. 대비표 검증
    for r in refs:
        mp = r.get("map") or {}
        for k in lid:
            e = mp.get(k)
            if e is None:
                E.append((r["id"], "O02", "%s 대비 누락 — 모든 한정을 ●/◐/○로 대비하세요." % k))
                continue
            if e.get("grade") not in GRADE:
                E.append((r["id"], "O02", "%s grade는 ●/◐/○ 중 하나" % k))
            elif GRADE[e["grade"]] > 0 and not (e.get("pin") or "").strip():
                E.append((r["id"], "O02", "%s를 %s로 적었는데 근거 위치(pin) 없음 — 사후적 고찰을 막으려면 위치가 필요합니다." % (k, e["grade"])))
        for k in mp:
            if k not in L:
                W.append((r["id"], "O02", "원장에 없는 한정 ID '%s'" % k))

    def g(r, k):
        return GRADE.get(((r.get("map") or {}).get(k) or {}).get("grade"), 0.0)

    def late(r):
        d = pdate(r.get("date"))
        return bool(prio and d and d >= prio)

    # 기술상식 강도
    kstr = {}
    for kid, k in K.items():
        s, probs = cgk_strength(k, prio)
        kstr[kid] = s
        for lvl, code, msg in probs:
            add[lvl].append((kid, code, msg))
        for x in k.get("limitations", []):
            if x not in L:
                W.append((kid, "O04", "원장에 없는 한정 ID '%s'" % x))
    cgk_for = {}
    for kid, k in K.items():
        for x in k.get("limitations", []):
            cgk_for.setdefault(x, []).append(kid)

    full_by = {k: [r["id"] for r in refs if g(r, k) == 1.0 and not late(r)] for k in lid}

    # 2. 분류
    res = []
    for r in refs:
        cov = sum(w[k] * g(r, k) for k in lid) / wsum
        effort, gaps = 0.0, []
        for k in lid:
            if g(r, k) >= 1.0:
                continue
            e = (r.get("map") or {}).get(k) or {}
            strong_k = [x for x in cgk_for.get(k, []) if kstr.get(x) == "strong"]
            others = [p for p in full_by[k] if p != r["id"]]
            diff = 0.25 if strong_k else (0.5 if others else 1.0)
            if e.get("teaches_away") and e.get("ta_kind") not in TA_WEAK:
                diff = 1.0
            effort += w[k] * (1 - g(r, k)) * diff
            gaps.append({"lim": k, "grade": e.get("grade", "○"), "diff": diff, "refs": others,
                         "cgk": cgk_for.get(k, []), "teaches_away": e.get("teaches_away", "")})
        rel = {2: 1.0, 1: 0.8, 0: 0.5}[int(bool(r.get("same_field"))) + int(bool(r.get("same_problem")))]
        score = round(100 * rel * (1 - effort / wsum), 1)
        if late(r):
            cls = "X"
        elif all(g(r, k) == 1.0 for k in lid):
            cls = "A"
        elif (r.get("same_field") or r.get("same_problem")) and cov >= mc:
            cls = "B"
        else:
            cls = "-"
        res.append({"id": r["id"], "pub": r.get("pub", ""), "date": r.get("date", ""), "cls": cls,
                    "coverage": round(cov, 3), "relevance": rel, "effort": round(effort, 2), "score": score, "gaps": gaps})
    order = {"A": 0, "B": 1, "-": 2, "C": 2, "X": 3}
    res.sort(key=lambda x: (order[x["cls"]], -x["score"], -x["coverage"]))
    bases = [x for x in res if x["cls"] in "AB"][:top]
    sec = set()
    for b in bases:
        for gp in b["gaps"]:
            sec.update(gp["refs"])
    for x in res:
        if x["cls"] == "-" and x["id"] in sec:
            x["cls"] = "C"
    if not [x for x in res if x["cls"] == "A"]:
        I.append(("-", "I", "A(신규성 부정 후보) 없음 — 한 문헌이 모든 한정을 개시하지 않으므로 진보성으로 다툽니다."))
    if not [x for x in res if x["cls"] == "B"] and not [x for x in res if x["cls"] == "A"]:
        W.append(("-", "O15", "B(주인용발명 후보)가 없음 — 같은 분야·같은 과제의 문헌을 더 찾거나 대비를 다시 보세요."))

    # 3. 차이점 × 기술상식 조사 (상위 B마다)
    diffs = []
    for b in [x for x in res if x["cls"] == "B"][:top]:
        for gp in b["gaps"]:
            ks = gp["cgk"]
            diffs.append({"base": b["id"], "lim": gp["lim"], "grade": gp["grade"], "refs": gp["refs"],
                          "cgk": [(kid, K[kid].get("status", "?"), kstr.get(kid, "none")) for kid in ks],
                          "teaches_away": gp["teaches_away"]})
            if not ks:
                E.append((gp["lim"], "O04", "주인용 후보 %s와의 차이점인데 기준일 당시 기술상식·주지관용기술 조사 기록이 없음 — "
                          "차이점마다 조사하고, 찾지 못했으면 status: not_found로 남기세요." % b["id"]))

    # 4. 결합 점검
    combos = []
    for c in doc.get("combinations", []):
        cid = c.get("id", "?")
        base = c.get("base")
        cE, cW = [], []
        if base not in R:
            cE.append((cid, "O09", "주인용 문헌 '%s'가 references에 없음" % base))
            combos.append({"id": cid, "base": base, "errors": cE, "warnings": cW, "sources": []})
            E.extend(cE)
            continue
        br = R[base]
        if late(br):
            cE.append((cid, "O03", "주인용 %s는 기준일 이후 공개 — 선행기술이 아닙니다." % base))
        if proc == "ipr" and br.get("kind") == "aapa":
            cE.append((cid, "O08", "IPR에서 출원인 자인 선행기술(AAPA)은 근거(basis)의 일부가 될 수 없습니다 — 기술상식의 증거로만."))
        bcls = next((x["cls"] for x in res if x["id"] == base), "-")
        if bcls not in "AB":
            cW.append((cid, "O15", "주인용 %s는 B 후보가 아님(분류 %s) — 가장 적은 수정으로 이르는 출발점인지 다시 보세요." % (base, bcls)))
        steps = c.get("steps", [])
        filled = {k for k in lid if g(br, k) == 1.0}
        sources = {base}
        for s in steps:
            k, src = s.get("limitation"), s.get("from")
            tag = "%s·%s" % (cid, k)
            if k not in L:
                cE.append((tag, "O09", "원장에 없는 한정 ID"))
                continue
            sources.add(src)
            if src in R:
                rr = R[src]
                if g(rr, k) < 1.0:
                    cE.append((tag, "O09", "%s는 %s를 ●로 개시하지 않음 — 보조 문헌은 빠진 한정을 온전히 메워야 합니다." % (src, k)))
                if late(rr):
                    cE.append((tag, "O03", "%s는 기준일 이후 공개 — 결합에 쓸 수 없습니다." % src))
                if proc == "ipr" and rr.get("kind") == "aapa":
                    cE.append((tag, "O08", "IPR에서 AAPA를 결합 문헌(근거)으로 쓸 수 없습니다."))
                ana = (c.get("analogous") or {}).get(src) or rr.get("pertinent_problem") or ""
                if not (rr.get("same_field") or ana):
                    cE.append((tag, "O14", "%s가 유사 분야 문헌인지 근거 없음 — 같은 분야이거나, 발명자가 풀던 과제와 합리적으로 관련돼야 합니다(In re Bigio·In re Clay)." % src))
                elif not rr.get("same_field") and re.search(r"(?<![A-Za-z0-9])(D\d+|%s)(?![0-9])" % re.escape(base), ana) and not re.search(r"(대상\s*특허|본건|청구항|발명자|과제)", ana):
                    cW.append((tag, "O21", "%s의 유사성 근거가 다른 선행문헌과의 비교뿐 — 대상 특허의 과제와 직접 비교해야 합니다(Sanofi-Aventis v. Mylan 2023)." % src))
                if ((rr.get("map") or {}).get(k) or {}).get("teaches_away"):
                    cW.append((tag, "O13", "%s 자체가 이 방향을 꺼림: %s" % (src, rr["map"][k]["teaches_away"])))
                if L[k].get("type") == "mpf" and not ((rr.get("map") or {}).get(k) or {}).get("sam_match"):
                    cW.append((tag, "O20", "기능식 한정 — 명세서 대응 구조(SAM)와 같거나 균등한 구조인지(sam_match) 적으세요."))
            elif src in K:
                kk = K[src]
                if k not in kk.get("limitations", []):
                    cE.append((tag, "O09", "기술상식 %s는 %s에 대한 조사 항목이 아님" % (src, k)))
                if kstr.get(src) == "none":
                    cE.append((tag, "O09", "기술상식 %s가 성립하지 않음(status %s 또는 증거 없음) — 빠진 한정을 메울 수 없습니다." % (src, kk.get("status"))))
                elif kstr.get(src) == "weak":
                    cW.append((tag, "O06", "기술상식 %s의 증거가 약함 — 다투면 무너질 수 있습니다." % src))
                if L[k].get("core") or w[k] >= 3:
                    cW.append((tag, "O07", "핵심 한정을 문헌이 아닌 기술상식으로 메움 — 미국 판례는 이 경우 증거에 기댄 구체적 설명을 요구합니다"
                               "(Arendi 2016·K/S HIMPP 2014). 한국도 주지관용은 증명 대상입니다(2012후436)."))
                if proc == "ipr" and any(e.get("type") == "aapa" for e in kk.get("evidence", [])):
                    cW.append((tag, "O08", "AAPA를 기술상식의 증거로 씀 — IPR에서는 근거(basis)가 아니라 보조 증거로만 쓰였는지 확인하세요."))
            else:
                cE.append((tag, "O09", "출처 '%s'가 references에도 cgk에도 없음" % src))
            ms = s.get("motivation_source") or ""
            if CROSS.search(ms) and CROSS.search(ms).group(1) != cid:
                cE.append((tag, "O25", "다른 결합(%s)의 논증을 원용 — 결합마다 따로 설명해야 하고, 심판부가 대신 메워 주지 않습니다(In re Magnum Oil Tools 2016)." % CROSS.search(ms).group(1)))
            mt = s.get("motivation") or ""
            if mt and COULD.search(mt) and not WHY.search(mt):
                cW.append((tag, "O23", "'결합할 수 있었다(could)'만 있고 '그렇게 했을 이유(would)'가 보이지 않음(PersonalWeb 2017)."))
            if OTT.search(s.get("rationale", "")):
                ott = s.get("ott") or {}
                miss = [k for k, v in (("finite", "유한한 해결책"), ("guidance", "방향 지침"), ("predictable", "결과 예측 가능")) if not (ott.get(k) or "").strip()]
                if miss:
                    cE.append((tag, "O22", "시도의 자명성(obvious to try) 주장에 %s 근거 없음 — 무방향 탐색은 자명하지 않습니다(KSR·In re O'Farrell·In re Kubin)." %
                               "·".join(dict((("finite", "유한한 해결책"), ("guidance", "방향 지침"), ("predictable", "결과 예측 가능")))[k] for k in miss)))
            if not (s.get("motivation") or "").strip() or not (s.get("motivation_source") or "").strip():
                cE.append((tag, "O11", "결합 동기 또는 그 근거 위치 없음 — '알려진 요소들이니 합칠 수 있다'만으로는 부족합니다(KSR·Virtek 2024)."))
            elif SELF.search(s.get("motivation_source", "")):
                cE.append((tag, "O11", "동기의 근거가 대상 특허 자신 — 발명을 알고 난 뒤의 시각(사후적 고찰)입니다. 선행기술·기술상식에서 찾으세요."))
            if "us" in forum and not (s.get("expectation") or "").strip():
                cE.append((tag, "O12", "성공에 대한 합리적 기대 없음 — 결합하면 될 것이라고 기대할 근거를 적으세요."))
            be = (br.get("map") or {}).get(k) or {}
            if be.get("teaches_away"):
                kind = be.get("ta_kind", "")
                if kind in TA_WEAK:
                    I.append((tag, "I", "주인용 %s의 기재는 단순 선호·장단점 비교(%s) — 그 자체로 저해는 아닙니다(In re Gurley·In re Fulton). 다만 결합 동기 판단에 함께 무게를 둡니다." % (base, kind)))
                else:
                    extra = " 변경하면 주인용의 작동 원리·기술적 의미가 사라짐 — 결합 동기가 부정될 수 있습니다(In re Gordon, 대법원 2010후2698)." if kind in ("principle", "inoperable") else ""
                    cW.append((tag, "O13", "주인용 %s가 이 변경을 꺼림: %s —%s 반박하지 못하면 결합 동기가 무너집니다(한국 2014후2184)." % (base, be["teaches_away"], extra)))
            filled.add(k)
        miss = [k for k in lid if k not in filled]
        if miss:
            cE.append((cid, "O10", "결합해도 빠지는 한정: %s — 청구항 전체에 이르지 못합니다." % ", ".join(miss)))
        if len(sources) >= 4:
            cW.append((cid, "O16", "근거 %d개(문헌·기술상식)를 엮음 — 많을수록 '청구항을 지도 삼아 짜 맞춘' 사후적 고찰로 보일 수 있습니다." % len(sources)))
        combos.append({"id": cid, "base": base, "errors": cE, "warnings": cW, "sources": sorted(sources), "missing": miss})
        E.extend(cE)
        W.extend(cW)

    # 5. 2차적 고려사항·효과
    sc = doc.get("secondary") or {}
    if not sc.get("reviewed"):
        E.append(("-", "O17", "2차적 고려사항(상업적 성공·오랜 필요·타인의 실패·예상 밖 효과·모방 등)을 검토했다는 기록 없음 — "
                  "결론을 내리기 전에 함께 검토해야 합니다(In re Cyclobenzaprine 2012)."))
    for i, it in enumerate(sc.get("items", []), 1):
        tag = "2차#%d" % i
        if not (it.get("source") or "").strip():
            E.append((tag, "O17", "근거 자료 위치 없음(%s)" % it.get("type", "?")))
        if not (it.get("nexus") or "").strip():
            W.append((tag, "O17", "청구항과의 관련성(nexus) 설명 없음 — 성공·호평이 청구된 특징 때문인지 보여야 합니다(Fox Factory 2019)."))
        if it.get("feature_known_in"):
            W.append((tag, "O17", "성공·호평을 이끈 특징이 이미 선행기술(%s)에 있음 — 관련성(nexus)이 약해집니다(Yita v. MacNeil 2023)." % ", ".join(it["feature_known_in"])))
        if it.get("coextensive") and (it.get("nexus") or "").strip():
            I.append((tag, "I", "제품이 청구항과 사실상 같으면(coextensive) 관련성이 추정될 수 있습니다(Fox Factory 2019·WBIP 2016). 상대방은 브랜드·마케팅 등 다른 원인으로 반박할 수 있습니다."))
        if it.get("type") == "commercial_success" and "kr" in forum:
            I.append((tag, "I", "한국: 상업적 성공은 참고 자료일 뿐, 그것만으로 진보성이 인정되지 않습니다(2002후2846·2005후3284)."))
    itype = meta.get("invention_type")
    if itype in TYPE_NOTE:
        I.append(("-", "I", TYPE_NOTE[itype]))
    eff = doc.get("effects") or {}
    if "kr" in forum:
        if eff.get("remarkable") in (None, "", "unknown"):
            W.append(("-", "O19", "효과 판단 미정 — 한국은 구성의 곤란성을 중심으로 보되 목적의 특이성·효과의 현저성을 참작합니다. "
                      "명세서에 기재된 효과와 그 근거를 적으세요."))
        elif not (eff.get("evidence") or "").strip():
            W.append(("-", "O19", "효과 주장에 근거 위치 없음"))
    return {"meta": meta, "posita": posita, "res": res, "diffs": diffs, "combos": combos, "kstr": kstr,
            "errors": E, "warnings": W, "info": I}


def report(doc, st):
    m = st["meta"]
    K = {k["id"]: k for k in doc.get("cgk", [])}
    lid = [l["id"] for l in doc.get("limitations", [])]
    out = ["# 진보성 판단 재료 점검 — %s / 청구항 %s" % (m.get("patent", "?"), m.get("claim", "?")), "",
           "- 기준일(우선일): %s · 관할: %s · 절차: %s" % (m.get("priority_date", "?"), m.get("forum", "us+kr"), m.get("proceeding", "exam")),
           "- 통상의 기술자: %s" % (st["posita"].get("definition") or "(미정)"),
           "- 오류 %d건 · 경고 %d건" % (len(st["errors"]), len(st["warnings"])), "",
           "## 1. 선행문헌 분류 (A 신규성 부정 / B 주인용 후보 / C 보조 / X 기준일 이후)", "",
           "| 순위 | 문헌 | 공개일 | 분류 | 점수 | 가중개시율 | 관련성 | " + " | ".join(lid) + " |",
           "|---|---|---|---|---:|---:|---:|" + "|".join(["---"] * len(lid)) + "|"]
    R = {r["id"]: r for r in doc.get("references", [])}
    for i, x in enumerate(st["res"], 1):
        mp = R[x["id"]].get("map") or {}
        out.append("| %d | %s %s | %s | %s | %s | %.0f%% | %g | %s |" % (
            i, x["id"], x["pub"], x["date"], x["cls"], x["score"] if x["cls"] != "X" else "–", x["coverage"] * 100,
            x["relevance"], " | ".join((mp.get(k) or {}).get("grade", "?") for k in lid)))
    out += ["", "## 2. 주인용 후보와의 차이점 × 기준일 당시 기술상식", "",
            "| 주인용 | 차이점 | 개시도 | 메울 문헌 | 기술상식 조사 | 저해 사유 |", "|---|---|---|---|---|---|"]
    for d in st["diffs"]:
        ks = "; ".join("%s(%s·%s)" % (kid, s, {"strong": "증거 충분", "weak": "증거 약함", "none": "불성립"}[t]) for kid, s, t in d["cgk"]) or "**조사 없음**"
        out.append("| %s | %s | %s | %s | %s | %s |" % (d["base"], d["lim"], d["grade"], ", ".join(d["refs"]) or "—", ks, d["teaches_away"] or "—"))
    if K:
        out += ["", "### 기술상식·주지관용기술 조사 기록", ""]
        for kid, k in K.items():
            out.append("- **%s** [%s → %s] %s" % (kid, ", ".join(k.get("limitations", [])), k.get("status", "?"), k.get("statement", "")))
            for e in k.get("evidence", []):
                out.append("  - %s (%s, %s) %s" % (e.get("source", "?"), e.get("type", "?"), e.get("date", "?"), e.get("pin", "")))
    out += ["", "## 3. 결합 논리", ""]
    for c in st["combos"]:
        state = "논리 완결 — 사람 판단으로" if not c["errors"] else "결함 있음"
        out.append("- **%s** 주인용 %s + %s → %s" % (c["id"], c["base"], ", ".join(s for s in c["sources"] if s != c["base"]) or "—", state))
        for e in c["errors"]:
            out.append("  - 오류 [%s] %s %s" % e)
        for wv in c["warnings"]:
            out.append("  - 경고 [%s] %s %s" % wv)
    rest_e = [e for e in st["errors"] if not any(e in c["errors"] for c in st["combos"])]
    rest_w = [x for x in st["warnings"] if not any(x in c["warnings"] for c in st["combos"])]
    if rest_e or rest_w or st["info"]:
        out += ["", "## 4. 그 밖의 점검"]
        out += ["- 오류 [%s] %s %s" % e for e in rest_e]
        out += ["- 경고 [%s] %s %s" % x for x in rest_w]
        out += ["- 참고 [%s] %s %s" % x for x in st["info"]]
    out += ["", "> 이 표는 입력된 판단을 같은 규칙으로 집계한 것입니다. 진보성 유무의 결론이 아닙니다.",
            "> 사람이 볼 것: 통상의 기술자 수준, 기술상식의 성립, 결합 동기의 설득력, 저해 사유, 2차적 고려사항의 관련성, 효과의 현저성."]
    return "\n".join(out) + "\n"


def to_chart(doc, cid):
    """고른 결합을 30편 chart_lint가 읽는 invalidity_103 차트로 바꾼다."""
    c = next((x for x in doc.get("combinations", []) if x.get("id") == cid), None)
    if c is None:
        raise SystemExit("결합 '%s'가 없습니다." % cid)
    R = {r["id"]: r for r in doc.get("references", [])}
    K = {k["id"]: k for k in doc.get("cgk", [])}
    m = doc.get("meta", {})
    base = R[c["base"]]
    step = {s["limitation"]: s for s in c.get("steps", [])}
    keep = ("id", "text", "type", "proposition", "intrinsic", "prosecution", "sam", "construction")
    lims = [{k: l[k] for k in keep if k in l} for l in doc.get("limitations", [])]
    names = [c["base"] + " " + base.get("pub", "")] + sorted({s["from"] + (" " + R[s["from"]].get("pub", "") if s["from"] in R else " 기술상식") for s in c.get("steps", [])})
    rows = []
    for l in doc.get("limitations", []):
        k = l["id"]
        prop = l.get("proposition", l.get("text", ""))
        be = (base.get("map") or {}).get(k) or {}
        if be.get("grade") == "●" and k not in step:
            src, e = base, be
            assertion = "주인용 %s(%s)가 개시한다 — %s." % (c["base"], base.get("pub", ""), e.get("pin", ""))
        elif k in step and step[k]["from"] in R:
            src = R[step[k]["from"]]
            e = (src.get("map") or {}).get(k) or {}
            assertion = "주인용 %s에는 없음(차이점) → 보조 문헌 %s(%s)가 개시한다." % (c["base"], src["id"], src.get("pub", ""))
        elif k in step and step[k]["from"] in K:
            kk = K[step[k]["from"]]
            facts = [{"source": ev.get("source", ""), "pin": ev.get("pin", ""), "date": ev.get("date", ""),
                      "text": ev.get("text", ""), "ref": kk["id"]} for ev in kk.get("evidence", [])[:3]]
            rows.append({"id": k, "theory": "literal",
                         "assertion": "주인용 %s에는 없음(차이점) → 기준일 당시 기술상식 %s로 보완한다: %s" % (c["base"], kk["id"], kk.get("statement", "")),
                         "facts": facts,
                         "explanation": "기준일 전 자료들이 '%s'를 통상의 기술자가 널리 아는 기술로 보여 주므로 차이점을 메운다. 왜냐하면 %s이기 때문이다."
                                        % (kk.get("statement", ""), step[k].get("motivation", "").rstrip(".")),
                         "basis": "cgk"})
            continue
        else:
            rows.append({"id": k, "theory": "literal", "assertion": "결합 %s로도 개시되지 않음." % cid, "facts": [],
                         "explanation": "근거 필요"})
            continue
        fact = {"source": "%s %s" % (src["id"], src.get("pub", "")), "pin": e.get("pin", ""), "date": src.get("date", ""),
                "text": e.get("text", ""), "ref": src["id"]}
        why = e.get("why") or "기재된 구조·관계가 한정 명제와 같기"
        row = {"id": k, "theory": "literal", "assertion": assertion, "facts": [fact],
               "explanation": "%s의 %s 기재는 '%s'에 해당하므로 개시한다. 왜냐하면 %s 때문이다." % (src["id"], e.get("pin", ""), prop, why)}
        if e.get("sam_match"):
            row["sam_match"] = e["sam_match"]
        rows.append(row)
    mot = " / ".join("[%s] %s: %s (근거 %s)" % (s["limitation"], s["from"], s.get("motivation", ""), s.get("motivation_source", ""))
                     for s in c.get("steps", []))
    exp = " / ".join("[%s] %s" % (s["limitation"], s.get("expectation", "")) for s in c.get("steps", []))
    chart = {"meta": {"patent": m.get("patent", ""), "claim": m.get("claim", 1), "priority_date": m.get("priority_date", ""),
                      "chart_type": "invalidity_103", "stage": "final",
                      "target": {"name": " + ".join(names), "version": "-", "date": base.get("date", "")},
                      "source": "obviousness_check.py --chart %s" % cid},
             "limitations": lims, "rows": rows,
             "combination": {"motivation": mot, "expectation": exp}}
    if m.get("symmetry"):
        chart["symmetry"] = m["symmetry"]
    return chart


def main(argv=None):
    ap = argparse.ArgumentParser(description="진보성 판단 재료 점검")
    ap.add_argument("json_path")
    ap.add_argument("--min-coverage", type=float)
    ap.add_argument("--top", type=int, default=2, help="차이점·보조 문헌을 볼 상위 B 개수")
    ap.add_argument("--out", help="보고서를 Markdown으로 저장")
    ap.add_argument("--chart", help="이 결합 ID를 30편 invalidity_103 차트로 변환")
    ap.add_argument("--chart-out", help="변환한 차트 저장 경로(기본: 표준 출력)")
    a = ap.parse_args(argv)
    with open(a.json_path, encoding="utf-8") as f:
        doc = json.load(f)
    st = analyze(doc, a.min_coverage, a.top)
    if a.chart:
        ch = to_chart(doc, a.chart)
        s = json.dumps(ch, ensure_ascii=False, indent=2)
        if a.chart_out:
            with open(a.chart_out, "w", encoding="utf-8") as f:
                f.write(s + "\n")
        else:
            sys.stdout.write(s + "\n")
            return 0
    rep = report(doc, st)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(rep)
    sys.stdout.write(rep)
    return 1 if st["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
