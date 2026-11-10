#!/usr/bin/env python3
"""청구항 → 한정 원장(Limitation Ledger) 초안 (핸드북 30). 표준 라이브러리만.

청구항 텍스트를 '분해 후보'로 나누고, 각 후보에 유형·주의 표시를 붙입니다.
도구는 '후보'만 냅니다. 최종 분해(원자적 한정 명제 확정)는 사람이 3대 시험으로 합니다.

  python tools/claim_parse.py sample/claim_en.txt            # 표(Markdown) 출력
  python tools/claim_parse.py sample/claim_ko.txt --json out.json
"""
import argparse
import json
import re
import sys

HANGUL = re.compile(r"[가-힣]")

# ── 영문 신호어 ─────────────────────────────────────────────
EN_TRANSITIONS = [
    "consisting essentially of", "consisting of", "comprising", "including",
    "characterized in that", "which comprises", "having",
]
EN_FLAGS = [
    ("mpf", r"\b(means|step)\s+for\b"),
    ("mpf_candidate", r"\b(module|unit|mechanism|element|device)\s+(for|configured to)\b"),
    ("negative", r"\b(without|free of|absence of|devoid of|not|no)\b"),
    ("markush", r"selected from the group consisting of"),
    ("alternative", r"\b(or|either|at least one of|one of)\b"),
    ("relation", r"\b(between|after|before|when|while|upon|in response to|until|adjacent|above|below)\b"),
    ("numeric", r"\d+(\.\d+)?\s*(to|-|~)\s*\d+|\b\d+(\.\d+)?\s*(%|mm|cm|rpm|degrees?|°|ms|hz|v)\b|\b(about|approximately|substantially)\b"),
    ("configured", r"\b(configured to|adapted to|operable to|capable of|programmed to)\b"),
    ("whereby", r"\bwhereby\b"),
]
# ── 국문 신호어 ─────────────────────────────────────────────
KO_FLAGS = [
    ("mpf", r"(위한|하는)\s*수단"),
    ("negative", r"(없이|없는|없음|않는|않고|배제|제외하고|비포함)"),
    ("markush", r"(으로|로)\s*이루어진\s*군(으로|에서)"),
    ("alternative", r"(또는|혹은|중\s*어느\s*하나|중\s*적어도\s*하나|중\s*하나)"),
    ("relation", r"(사이에|사이의|후에|이후|전에|이전|때|경우|동안|응답하여|인접)"),
    ("numeric", r"\d+(\.\d+)?\s*(~|-|내지)\s*\d+|\d+(\.\d+)?\s*(%|mm|cm|rpm|도|°)"),
    ("configured", r"(하도록\s*구성된|하도록\s*형성된|할\s*수\s*있는|가능한)"),
    ("whereby", r"(이에\s*의해|그\s*결과|함으로써)"),
]

NOTES = {
    "mpf": "기능식(means-plus-function) 후보. 미국은 §112(f): 명세서의 대응 구조·행위·물질(SAM)과 그 균등물로 한정 — LHC에 SAM 위치를 적을 것. 한국은 명문 규정이 없어 명세서를 참작해 해석.",
    "mpf_candidate": "'means' 없이도 구조가 불분명한 기능 용어(module·unit 등)는 §112(f)로 해석될 수 있음(Williamson). 명세서의 구조 개시를 확인.",
    "negative": "부정한정. 대상물에서 '없음'을 입증해야 함 — 관련 작동 영역에서의 부재를 사실·설명으로.",
    "markush": "마쿠시 군. 대안 각각이 별도 종(species) — 하나라도 선행기술에 있으면 신규성 위험.",
    "alternative": "대안 구조(or). 'or'는 독립 부품이 아니라 이 한정 안의 관계. 포괄적(A, B 또는 둘 다)인지 배타적(둘 중 하나만)인지 명세서·출원경과로 확정.",
    "relation": "관계·순서·조건 한정. 물리적 부품으로 만들지 말고 명제 안의 조건으로 보존.",
    "numeric": "수치범위. 경계값·측정 조건·'약(about)'의 해석을 명세서로 확인.",
    "configured": "기능적 능력 표현. 'configured to'는 '그렇게 설계·프로그램됨'으로 좁게 해석될 수 있고, 'capable of'와 다름 — 한정으로 취급.",
    "whereby": "결과 표현. 단순 결과면 비제한일 수 있으나 특허성에 중요한 조건이면 한정(Hoffer). 삭제하지 말고 행에 남길 것.",
    "antecedent": "선행사(antecedent) 확인 필요 — 'the/said X'·'상기 X'가 앞에서 도입되지 않았음.",
    "method_step": "방법 단계. 순서는 문언·논리상 요구될 때만 한정(Altiris). 실제 수행·행위 주체를 매핑.",
}

TYPE_ORDER = ["mpf", "negative", "markush", "alternative", "relation", "numeric", "configured", "whereby"]


def detect_lang(text):
    return "ko" if HANGUL.search(text) else "en"


def normalize(text):
    text = text.replace("\r\n", "\n").strip()
    text = re.sub(r"^\s*\d+\s*[.)]\s*", "", text)      # 앞 번호 "1." 제거
    text = re.sub(r"^\s*【?청구항\s*\d+】?\s*", "", text)
    return text


def flags_for(segment, lang):
    table = KO_FLAGS if lang == "ko" else EN_FLAGS
    low = segment if lang == "ko" else segment.lower()
    found = []
    for name, pat in table:
        if re.search(pat, low):
            found.append(name)
    if "markush" in found and "alternative" in found:
        found.remove("alternative")
    if "mpf" in found and "mpf_candidate" in found:
        found.remove("mpf_candidate")
    return found


def main_type(flags, is_method):
    for t in TYPE_ORDER:
        if t in flags:
            return {"mpf": "mpf", "markush": "alternative"}.get(t, t)
    return "step" if is_method else "structure"


def split_en(text):
    low = text.lower()
    pos, word = None, None
    for t in EN_TRANSITIONS:
        m = re.search(r"\b" + re.escape(t) + r"\b", low)
        if m and (pos is None or m.start() < pos):
            pos, word = m.start(), t
    if pos is None:
        return "", "", text
    pre = text[:pos].strip().rstrip(",")
    body = text[pos + len(word):].lstrip(" :,\n")
    return pre, word, body


def split_ko(text):
    t = text.strip().rstrip(".")
    first = t.find(";") if ";" in t else len(t)
    m = re.search(r"(에\s*있어서|으로서|로서)\s*,", t)
    if m and m.start() > first:
        m = None
    if m:
        pre = t[:m.end()].rstrip(",").strip()
        body = t[m.end():].strip()
        tail = re.search(r"(을|를)?\s*(포함하는|포함하고|구비하는)\s*(것을\s*특징으로\s*하는)?\s*([^;,\n]*)$", body)
        word = "에 있어서/로서"
        if tail:
            body = body[:tail.start()].strip()
            word = (tail.group(2) + (" " + tail.group(3) if tail.group(3) else "")).strip()
        return pre, word, body
    tail = re.search(r"(을|를)?\s*(포함하는|구비하는|포함하여\s*이루어진)\s*([^;,\n]+)$", t)
    if tail:                                    # "A; B; 를 포함하는 착즙기" — 전제부가 끝에
        return tail.group(3).strip(), tail.group(2), t[:tail.start()].strip()
    return "", "", t


def split_body(body, lang, is_method):
    parts = [p.strip() for p in re.split(r";", body) if p.strip()]
    if len(parts) <= 1:
        if lang == "en" and is_method:
            parts = [p.strip() for p in re.split(r",\s*(?=[a-z]+ing\b)", body) if p.strip()]
        elif lang == "ko":
            parts = [p.strip() for p in re.split(r",\s*\n", body) if p.strip()]
    clean = []
    for p in parts:
        p = re.sub(r"^(and|or)\s+", "", p.strip(), flags=re.I)
        p = re.sub(r"^(및|그리고)\s*", "", p).strip()
        p = re.sub(r"[;,.]?\s*(and)?$", "", p).strip()
        p = re.sub(r"\s*(및|그리고)$", "", p).strip()
        if p:
            clean.append(p)
    return clean


def split_sub(clause, lang):
    """wherein / 여기서 절을 하위 한정으로."""
    if lang == "en":
        pieces = re.split(r",?\s*(?:and\s+)?wherein\s+", clause, flags=re.I)
    else:
        pieces = re.split(r",?\s*(?:여기서|이때)\s*,?\s*", clause)
    pieces = [p.strip(" ,") for p in pieces if p.strip(" ,")]
    return pieces


def antecedent_issues(segments, lang):
    issues = {}
    intro = ""
    for sid, seg in segments:
        if lang == "en":
            for m in re.finditer(r"\b(?:said|the)\s+([a-z][a-z\- ]{2,30}?)(?=[\s,;.]|$)", seg.lower()):
                noun = m.group(1).split()[-1]
                before = intro + " " + seg.lower()[:m.start()]
                if noun not in before and noun not in ("same", "other", "first", "second"):
                    issues.setdefault(sid, []).append(noun)
            intro += " " + seg.lower()
        else:
            for m in re.finditer(r"상기\s*([가-힣A-Za-z0-9]+)", seg):
                noun = m.group(1)
                for _ in range(3):
                    noun = re.sub(r"(의|와|과|은|는|이|가|을|를|에|로|으로|에서)$", "", noun)
                if noun and noun not in intro + " " + seg[:m.start()]:
                    issues.setdefault(sid, []).append(noun)
            intro += " " + seg
    return issues


def parse(text, claim_no=1):
    text = normalize(text)
    lang = detect_lang(text)
    pre, transition, body = (split_ko(text) if lang == "ko" else split_en(text))
    is_method = bool(re.search(r"\b(method|process)\b", pre.lower())) or ("방법" in pre)
    rows = []
    if pre:
        rows.append({"id": "%dpre" % claim_no, "text": pre, "type": "preamble", "flags": [],
                     "notes": ["전제부. 원칙적으로 비제한이나 청구항에 '생명과 의미'를 주면 한정 — 행으로 남기고 조건부로 대응."]})
    letters = "abcdefghijklmnopqrstuvwxyz"
    for i, clause in enumerate(split_body(body, lang, is_method)):
        base = "%d%s" % (claim_no, letters[i % 26])
        subs = split_sub(clause, lang)
        items = [(base, subs[0])] + [("%s.%d" % (base, j), s) for j, s in enumerate(subs[1:], 1)]
        for sid, seg in items:
            fl = flags_for(seg, lang)
            if is_method and sid == base:
                fl.append("method_step")
            rows.append({"id": sid, "text": seg, "type": main_type(fl, is_method), "flags": fl,
                         "notes": [NOTES[f] for f in fl if f in NOTES]})
    for sid, nouns in antecedent_issues([(r["id"], r["text"]) for r in rows], lang).items():
        for r in rows:
            if r["id"] == sid:
                r["flags"].append("antecedent")
                r["notes"].append(NOTES["antecedent"] + " (" + ", ".join(sorted(set(nouns))) + ")")
    return {
        "claim": claim_no, "lang": lang, "is_method": is_method,
        "transition": transition,
        "transition_note": ("개방형 — 추가 구성을 허용하지만 본문의 배타적 선택·부정한정을 무력화하지 못함."
                            if transition in ("comprising", "including", "포함하는", "포함하고", "구비하는")
                            or "포함" in (transition or "") else
                            "폐쇄형·반폐쇄형이면 추가 구성 허용 범위를 따로 확인." if transition else
                            "전환구를 찾지 못함 — 직접 확인."),
        "limitations": rows,
        "tests": ["삭제시험: 이 행을 지우면 권리범위가 의미 있게 넓어지는가?",
                  "대응시험: '대상물이 이 행을 충족하는가?'가 단일·유의미한 질문인가?",
                  "전체성시험: 행들을 합치면 발명 전체가 누락·왜곡 없이 재현되는가?"],
    }


def to_markdown(res):
    out = ["# 한정 원장 초안 — 청구항 %d (%s)" % (res["claim"], "국문" if res["lang"] == "ko" else "영문"),
           "", "- 전환구: `%s` — %s" % (res["transition"] or "?", res["transition_note"]),
           "- 방법 청구항: %s" % ("예" if res["is_method"] else "아니오"), "",
           "| ID | 청구 문언 | 유형 | 표시 | 확인할 점 |", "|---|---|---|---|---|"]
    for r in res["limitations"]:
        note = "<br>".join(r["notes"]) if r["notes"] else ""
        out.append("| [%s] | %s | %s | %s | %s |" % (r["id"], r["text"].replace("|", "/"), r["type"],
                                                     ", ".join(r["flags"]), note))
    out += ["", "## 사람이 확정할 것 (3대 시험)"] + ["- " + t for t in res["tests"]]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="청구항을 한정 원장 초안으로 분해")
    ap.add_argument("claim_file")
    ap.add_argument("--claim-no", type=int, default=1)
    ap.add_argument("--json", help="JSON으로 저장할 경로")
    ap.add_argument("--md", help="Markdown으로 저장할 경로")
    a = ap.parse_args(argv)
    with open(a.claim_file, encoding="utf-8") as f:
        res = parse(f.read(), a.claim_no)
    md = to_markdown(res)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(md)
    if not (a.json or a.md):
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
