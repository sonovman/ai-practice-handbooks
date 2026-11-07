#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pairkit.py — '청구항 × 발명의 설명' 텍스트 쌍 전처리 도구 (핸드북 15편)

특허출원 10-2024-0075102(공개 10-2025-0013094)의 아이디어 — 청구항과 발명의 설명을
짝지은 '텍스트 쌍'을 판단 단위로 삼는 방식 — 을 범용 LLM(Claude·ChatGPT·Gemini·Copilot)과
함께 쓰기 위한 전처리를 자동으로 합니다. 판단(개시 여부)은 LLM과 사람이, 자르고 찾고
묶는 일은 이 도구가 맡습니다.

명령
  extract   특허문헌 텍스트 → 청구항(독립항 표시)·식별번호 문단을 JSON으로
  elements  청구항 하나를 구성요소로 나눈 초안(분설안)
  bundle    관심 특허의 청구항 구성요소 × 대상 문서 설명 → 구성요소별 근거 후보(상위 k개)와
            LLM에 붙여 넣을 요청문(클레임 차트 작성용)
  pairs     여러 문헌으로 자기 지도 학습·평가용 텍스트 쌍 생성
            (같은 문헌 = 1, 다른 문헌 = 0, 가장 비슷한 다른 문헌 = 어려운 0)

사용 예
  python pairkit.py extract 공보.txt --out A.json
  python pairkit.py elements A.json --claim 1
  python pairkit.py bundle --claims A.json --claim 1 --target 제품설명.txt --top 3 --out 요청문.md
  python pairkit.py pairs corpus/*.json --out pairs.jsonl --triplets triplets.csv

필요한 것: Python 3.8 이상 (추가 설치 없음). 유사도는 글자 3-그램 TF-IDF 코사인으로,
한국어·영어 모두 형태소 분석 없이 동작합니다(임베딩 모델의 내적 대신 쓰는 가벼운 대용).
"""
import argparse
import csv
import glob
import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

PARA = re.compile(r"^\s*[\[【]\s*(\d{4})\s*[\]】]\s*(.*)$")
CLAIM_KR = re.compile(r"^\s*[【\[]?\s*청구항\s*(\d+)\s*[】\]]?\s*$")
CLAIM_EN_HEAD = re.compile(r"^\s*(what is claimed is|claims|we claim|i claim)\s*:?\s*$", re.I)
CLAIM_EN = re.compile(r"^\s*(\d{1,3})\s*\.\s+(\S.*)$")
DEPENDENT = re.compile(r"제\s*\d+\s*항(에|의|\s*내지|\s*또는|\s*중)|청구항\s*\d+\s*(에|의)|(according to|as claimed in|of|in)\s+claim\s+\d+", re.I)
HANGUL_END = re.compile(r"[가-힣]$")
HANGUL_START = re.compile(r"^[가-힣]")
NOISE = re.compile(r"^\s*((공개특허|등록특허)\s.*|-\s*\d+\s*-)\s*$")
INLINE_PAGE = re.compile(r"\s-\s?\d{1,3}\s?-\s")
RESTATE = re.compile(r"과제를\s*달성하기\s*위한|과제\s*해결\s*수단|to achieve the (above )?object", re.I)


def out(s=""):
    print(s)


# ---------------------------------------------------------------- 추출
def dwidth(s):
    return sum(2 if "\uac00" <= ch <= "\ud7a3" or "\u3000" <= ch <= "\u9fff" else 1 for ch in s)


def joiner(buf, s, prev_full):
    """PDF에서 뽑은 한국어는 줄 끝에서 낱말이 잘립니다. 꽉 찬 줄이 한글로 끝나고 다음 줄이 한글로
    시작하면 붙여 쓰고, 아니면 띄웁니다(어림 규칙 — KIPRIS 전문 텍스트·XML이면 필요 없음)."""
    if buf and prev_full and HANGUL_END.search(buf) and HANGUL_START.match(s):
        return buf + s
    return (buf + " " + s).strip()


def extract(text):
    lines = [l.rstrip() for l in text.replace("\r", "").split("\n")]
    lines = [l for l in lines if not NOISE.match(l)]
    widths = sorted(dwidth(l.strip()) for l in lines if l.strip())
    full = widths[int(len(widths) * 0.9)] * 0.9 if widths else 10 ** 9
    claims, paras = {}, {}
    cur_claim, cur_para, mode = None, None, None
    prev_full = False
    for l in lines:
        s = l.strip()
        was_full, prev_full = prev_full, dwidth(s) >= full
        m = CLAIM_KR.match(s)
        if m:
            cur_claim, cur_para, mode = int(m.group(1)), None, "claim"
            claims[cur_claim] = ""
            continue
        m = PARA.match(s)
        if m:
            cur_para, cur_claim, mode = m.group(1), None, "para"
            paras[cur_para] = m.group(2).strip()
            prev_full = dwidth(l.strip()) >= full
            continue
        if CLAIM_EN_HEAD.match(s):
            mode, cur_claim = "en-claims", None
            continue
        if mode == "en-claims":
            m = CLAIM_EN.match(s)
            if m:
                cur_claim = int(m.group(1))
                claims[cur_claim] = m.group(2).strip()
                continue
        if re.match(r"^\s*(발\s*명\s*의\s*설\s*명|요\s*약\s*서|도\s*면)\s*$", s):
            mode, cur_claim, cur_para = None, None, None
            continue
        if not s:
            continue
        if cur_claim is not None and mode in ("claim", "en-claims"):
            claims[cur_claim] = joiner(claims[cur_claim], s, was_full)
        elif cur_para is not None and mode == "para":
            paras[cur_para] = joiner(paras[cur_para], s, was_full)
    norm = lambda x: re.sub(r"\s+", " ", INLINE_PAGE.sub(" ", x)).strip()
    cl = [{"no": n, "text": norm(t), "independent": not DEPENDENT.search(t)} for n, t in sorted(claims.items()) if t.strip()]
    ps = [{"id": k, "text": norm(v)} for k, v in sorted(paras.items()) if v.strip()]
    return {"claims": cl, "paras": ps}


def load_doc(path):
    p = Path(path)
    if p.suffix.lower() == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    d = extract(p.read_text(encoding="utf-8-sig"))
    if not d["paras"]:                       # 식별번호가 없는 일반 문서(제품 설명서 등): 빈 줄 기준 문단
        blocks = [b.strip() for b in re.split(r"\n\s*\n", p.read_text(encoding="utf-8-sig")) if b.strip()]
        d["paras"] = [{"id": "{:04d}".format(i + 1), "text": re.sub(r"\s+", " ", b)} for i, b in enumerate(blocks)]
    d["name"] = p.stem
    return d


# ---------------------------------------------------------------- 분설
def elements(claim_text):
    """청구항을 전제부와 구성요소로 나눈 초안. 사람이·LLM이 다듬는 출발점."""
    t = claim_text.strip()
    pre, body = "", t
    m = re.search(r"(으로서|로서|에 있어서|comprising|which comprises|including)\s*[,:]", t)
    if m:
        pre, body = t[:m.end()].strip(" ,:"), t[m.end():].strip()
    parts = re.split(r"\s*[;；]\s*(?:및\s+|and\s+)?|\s*단계\s*;\s*", body)
    els = []
    for p in parts:
        p = p.strip(" ,.")
        if not p:
            continue
        # '…포함하되, 상기 …' / 'wherein' 뒤의 한정은 따로 떼어 구성요소로
        sub = re.split(r"(?:포함하되|포함하고)\s*,\s*|,\s*wherein\s+", p)
        for s in sub:
            s = s.strip(" ,.")
            if len(s) > 3:
                els.append(s)
    clean = lambda x: re.sub(r"\s*(것을\s*특징으로\s*하는.*|하는\s*단계를?|단계를?|를\s*포함하는.*)$", "", re.sub(r"^(및|and)\s+", "", x)).strip(" ,.")
    els = [clean(x) for x in els if len(clean(x)) > 3]
    if len(els) == 1:                         # 쉼표로만 이어진 청구항
        els = [s.strip() for s in re.split(r",\s*(?=상기|and\s|the\s)", els[0]) if s.strip()]
    return {"preamble": pre, "elements": [{"id": "E{}".format(i + 1), "text": e} for i, e in enumerate(els)]}


# ---------------------------------------------------------------- 유사도 (글자 3-그램 TF-IDF)
def grams(text, n=3):
    t = re.sub(r"[^0-9A-Za-z가-힣]+", " ", text.lower())
    out_ = []
    for w in t.split():
        w = " " + w + " "
        out_ += [w[i:i + n] for i in range(max(1, len(w) - n + 1))]
    return Counter(out_)


class Index:
    def __init__(self, docs):
        self.vecs = [grams(d) for d in docs]
        df = Counter()
        for v in self.vecs:
            df.update(v.keys())
        n = len(docs)
        self.idf = {g: math.log((n + 1) / (c + 1)) + 1 for g, c in df.items()}
        self.w = [self._weight(v) for v in self.vecs]

    def _weight(self, v):
        w = {g: c * self.idf.get(g, 1.0) for g, c in v.items()}
        norm = math.sqrt(sum(x * x for x in w.values())) or 1.0
        return {g: x / norm for g, x in w.items()}

    def query(self, text):
        q = self._weight(grams(text))
        return [sum(q.get(g, 0) * x for g, x in w.items()) for w in self.w]


def segments(paras, size=600):
    """문단을 이어 붙여 약 size자 단위 조각으로(문단 경계 유지, 식별번호 보존)."""
    segs, buf, ids = [], "", []
    for p in paras:
        if buf and len(buf) + len(p["text"]) > size:
            segs.append({"ids": ids, "text": buf})
            buf, ids = "", []
        buf = (buf + " " + p["text"]).strip()
        ids.append(p["id"])
    if buf:
        segs.append({"ids": ids, "text": buf})
    return segs


def rank(element_texts, paras, top=3, size=600):
    segs = segments(paras, size)
    idx = Index([s["text"] for s in segs])
    res = []
    for e in element_texts:
        sc = idx.query(e)
        order = sorted(range(len(segs)), key=lambda i: -sc[i])[:top]
        res.append([(segs[i], sc[i]) for i in order])
    return res


PROMPT = """# 요청 — 클레임 차트 작성 ({purpose})

아래 <청구항 구성요소>의 각 구성요소가 <대상 문서 근거 후보>에 개시되어 있는지 판단해 주세요.

규칙
- 판단은 구성요소마다 `개시` / `부분 개시` / `불명` / `미개시` 중 하나로 합니다.
- 근거는 대상 문서의 문장을 **그대로 인용**하고 식별번호를 붙입니다. 후보에 근거가 없으면 지어내지 말고 `불명` 또는 `미개시`로 둡니다.
- 청구항 용어는 관심 특허의 발명의 설명에 나온 정의대로 해석합니다(<용어 해석 근거> 참고). 대상 문서가 다른 용어를 써도 같은 기술적 의미면 같은 것으로 봅니다.
- 균등 여부(다른 수단이지만 같은 기능·효과)는 판단하지 말고 `균등 검토 필요`로 따로 표시만 합니다.
- 마지막에 아래 JSON을 ```json 블록으로 출력합니다.

```
{{"purpose": "{purpose}", "claim": "{claim_ref}", "elements": [
  {{"id": "E1", "status": "개시|부분 개시|불명|미개시", "evidence": [{{"para": "0001", "quote": "대상 문서 원문 그대로"}}],
   "reason": "한두 문장", "equivalent_check": false}}
 ],
 "verdict": "모든 구성요소 개시 | 일부 미개시 | 추가 검토 필요"}}
```

## 청구항 구성요소 — {claim_ref}
전제부: {preamble}
{elements}

## 용어 해석 근거 — 관심 특허 자신의 발명의 설명 (같은 문헌 쌍)
{self_ev}

## 대상 문서 근거 후보 — {target}
{target_ev}
"""


def bundle(claim_doc, claim_no, target_doc, purpose="FTO(침해 위험)", top=3, size=600, all_under=8000):
    claim = next((c for c in claim_doc["claims"] if c["no"] == claim_no), None)
    if not claim:
        raise ValueError("청구항 {}이 없습니다.".format(claim_no))
    el = elements(claim["text"])
    texts = [e["text"] for e in el["elements"]]
    # 같은 문헌 쌍: 청구항을 그대로 되풀이한 '과제 해결 수단' 문단은 용어 해석에 보탬이 안 되므로 빼고 찾는다
    own = [p for p in claim_doc.get("paras", []) if not RESTATE.search(p["text"])]
    self_r = rank(texts, own, 1, 1) if own else [[] for _ in texts]
    tgt_r = rank(texts, target_doc["paras"], top, 1 if sum(len(p["text"]) for p in target_doc["paras"]) <= all_under else size)
    E = "\n".join("- **{}** {}".format(e["id"], e["text"]) for e in el["elements"])
    S, T = [], []
    total = sum(len(p["text"]) for p in target_doc["paras"])
    whole = total <= all_under
    if whole:   # 짧은 문서는 거르지 않고 통째로 — 걸러 낼 이유(입력 길이 한계)가 없으므로
        T.append("(대상 문서가 {:,}자로 짧아 전문을 넣습니다. 아래 '후보 위치'는 글자 유사도 참고일 뿐입니다.)".format(total))
        for p in target_doc["paras"]:
            T.append("- [{}] {}".format(p["id"], p["text"]))
        T.append("")
    for e, sr, tr in zip(el["elements"], self_r, tgt_r):
        if sr:
            seg, sc = sr[0]
            S.append("- {} ← [{}] {}".format(e["id"], ",".join(seg["ids"]), seg["text"][:400]))
        if whole:
            T.append("- {} 후보 위치: {}".format(e["id"], ", ".join("[{}] {:.2f}".format(",".join(g["ids"]), c) for g, c in tr)))
            continue
        T.append("### {} 후보".format(e["id"]))
        for seg, sc in tr:
            T.append("- [{}] (유사도 {:.2f}) {}".format(",".join(seg["ids"]), sc, seg["text"]))
    ref = "{} 청구항 {}".format(claim_doc.get("name", "관심 특허"), claim_no)
    text = PROMPT.format(purpose=purpose, claim_ref=ref, preamble=el["preamble"] or "(없음)", elements=E,
                         self_ev="\n".join(S) or "(관심 특허 설명 없음)", target=target_doc.get("name", "대상 문서"),
                         target_ev="\n".join(T))
    scores = [max(sc for _, sc in tr) if tr else 0 for tr in tgt_r]
    return text, el, scores


# ---------------------------------------------------------------- 자기 지도 텍스트 쌍
def pairs(docs, neg=1, seed=7, size=600):
    """같은 문헌(1) · 무작위 다른 문헌(0) · 가장 비슷한 다른 문헌(어려운 0) 쌍을 만든다."""
    rnd = random.Random(seed)
    items = []
    for d in docs:
        ind = [c for c in d["claims"] if c["independent"]]
        if not ind or not d["paras"]:
            continue
        body = [p for p in d["paras"] if not RESTATE.search(p["text"])] or d["paras"]
        items.append((d, ind[0], segments(body, size)))
    if len(items) < 2:
        raise ValueError("독립항과 설명이 있는 문헌이 2개 이상 필요합니다.")
    rows, trip = [], []
    for i, (d, c, segs) in enumerate(items):
        idx = Index([s["text"] for s in segs])
        pos = segs[max(range(len(segs)), key=lambda k: idx.query(c["text"])[k])]
        rows.append({"claim": c["text"], "desc": pos["text"], "label": 1, "kind": "같은 문헌",
                     "src_claim": d["name"], "src_desc": d["name"], "paras": pos["ids"]})
        others = [x for j, x in enumerate(items) if j != i]
        allsegs = [(o[0]["name"], s) for o in others for s in o[2]]
        oi = Index([s["text"] for _, s in allsegs])
        sc = oi.query(c["text"])
        k = max(range(len(allsegs)), key=lambda j: sc[j])
        hn, hs = allsegs[k]
        pool = [o for o in others if o[0]["name"] != hn] or others     # 어려운 쌍과 겹치지 않게
        for o in rnd.sample(pool, min(neg, len(pool))):
            s = rnd.choice(o[2])
            rows.append({"claim": c["text"], "desc": s["text"], "label": 0, "kind": "무작위 다른 문헌",
                         "src_claim": d["name"], "src_desc": o[0]["name"], "paras": s["ids"]})
        rows.append({"claim": c["text"], "desc": hs["text"], "label": 0, "kind": "어려운 다른 문헌",
                     "src_claim": d["name"], "src_desc": hn, "paras": hs["ids"], "similarity": round(sc[k], 3)})
        trip.append({"anchor": c["text"], "positive": pos["text"], "negative": hs["text"]})
    return rows, trip


# ---------------------------------------------------------------- 실행
def main(argv=None):
    ap = argparse.ArgumentParser(description="청구항 × 발명의 설명 텍스트 쌍 전처리")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("file")
    e.add_argument("--out")
    l = sub.add_parser("elements")
    l.add_argument("doc")
    l.add_argument("--claim", type=int, default=1)
    b = sub.add_parser("bundle")
    b.add_argument("--claims", required=True, help="관심 특허(텍스트 또는 extract JSON)")
    b.add_argument("--claim", type=int, default=1)
    b.add_argument("--target", required=True, help="대상 문서(특허·제품 설명서·논문)")
    b.add_argument("--purpose", default="FTO(침해 위험)")
    b.add_argument("--top", type=int, default=3)
    b.add_argument("--size", type=int, default=600, help="설명 조각 크기(글자), 기본 600")
    b.add_argument("--all-under", type=int, default=8000, help="대상 문서가 이 글자 수 이하면 전문을 넣음(기본 8000)")
    b.add_argument("--out")
    p = sub.add_parser("pairs")
    p.add_argument("docs", nargs="+")
    p.add_argument("--neg", type=int, default=1)
    p.add_argument("--out", default="pairs.jsonl")
    p.add_argument("--triplets")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        if a.cmd == "extract":
            d = load_doc(a.file)
            js = json.dumps(d, ensure_ascii=False, indent=1)
            if a.out:
                Path(a.out).write_text(js, encoding="utf-8")
                out("저장: {} — 청구항 {}개(독립항 {}) · 문단 {}개".format(
                    a.out, len(d["claims"]), ", ".join(str(c["no"]) for c in d["claims"] if c["independent"]) or "없음", len(d["paras"])))
            else:
                out(js)
        elif a.cmd == "elements":
            d = load_doc(a.doc)
            c = next((x for x in d["claims"] if x["no"] == a.claim), None)
            if not c:
                out("오류: 청구항 {}이 없습니다.".format(a.claim))
                return 2
            el = elements(c["text"])
            out("청구항 {} ({}) — 분설 초안".format(a.claim, "독립항" if c["independent"] else "종속항"))
            out("전제부: " + (el["preamble"] or "(없음)"))
            for x in el["elements"]:
                out("- {} {}".format(x["id"], x["text"]))
            out("\n초안입니다. 한 구성요소에 기능이 둘 이상 섞였으면 나누고, 의미 단위가 잘렸으면 합치세요.")
        elif a.cmd == "bundle":
            text, el, scores = bundle(load_doc(a.claims), a.claim, load_doc(a.target), a.purpose, a.top, a.size, a.all_under)
            if a.out:
                Path(a.out).write_text(text, encoding="utf-8")
                out("저장: " + a.out)
            out("구성요소별 최고 유사도(참고용 — 판단은 LLM·사람이 근거로):")
            for x, s in zip(el["elements"], scores):
                out("  {} {:.2f}".format(x["id"], s))
            out("가장 약한 구성요소: {} ({:.2f}) — 모든 구성요소 원칙상 차트의 승부처".format(
                el["elements"][scores.index(min(scores))]["id"], min(scores)))
            if not a.out:
                out("\n" + text)
        else:
            files = sorted({f for g in a.docs for f in glob.glob(g)})
            rows, trip = pairs([load_doc(f) for f in files], a.neg)
            with open(a.out, "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            c = Counter(r["kind"] for r in rows)
            out("저장: {} — {}".format(a.out, ", ".join("{} {}".format(k, v) for k, v in c.items())))
            if a.triplets:
                with open(a.triplets, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.DictWriter(f, fieldnames=["anchor", "positive", "negative"])
                    w.writeheader()
                    w.writerows(trip)
                out("저장: {} — (청구항, 같은 문헌 설명, 어려운 다른 문헌 설명) {}줄".format(a.triplets, len(trip)))
            out("주의: '어려운 다른 문헌'은 실제로는 관련 문헌(같은 패밀리·인용 문헌)일 수 있습니다. 학습 전에 눈으로 확인하세요.")
    except (ValueError, OSError) as ex:
        out("오류: " + str(ex))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
