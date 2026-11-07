#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chart_check.py — LLM이 만든 클레임 차트와 판정 결과를 점검하는 도구 (핸드북 15편)

명령
  verify  LLM 출력(```json 블록)의 클레임 차트를 대상 문서 원문과 대조
          ① 모든 구성요소가 있는지 ② 인용문이 원문에 실제로 있는지(지어낸 근거 차단)
          ③ 식별번호가 맞는지 ④ 결론이 '모든 구성요소 원칙'과 맞는지
  score   자기 지도 텍스트 쌍(pairs.jsonl)에 대한 판정을 정답 레이블과 비교
          정확도·정밀도·재현율·F1, 점수가 있으면 AUC, 쌍 종류별 성적

사용 예
  python chart_check.py verify sample/chart-A.md --target sample/product-A.txt --elements 6
  python chart_check.py score sample/pairs.jsonl sample/predictions.csv

필요한 것: Python 3.8 이상 (추가 설치 없음)
"""
import argparse
import csv
import difflib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pairkit  # noqa: E402

STATUSES = ("개시", "부분 개시", "불명", "미개시")


def out(s=""):
    print(s)


def norm(s):
    return re.sub(r"\s+", "", re.sub(r"[\"'“”‘’「」『』]", "", s or ""))


def find_json(text):
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if not m:
        m = re.search(r"(\{\s*\"purpose\".*\})", text, re.S)
    if not m:
        raise ValueError("```json 블록을 찾지 못했습니다.")
    return json.loads(m.group(1))


def quote_found(quote, paras, para_id=None):
    """인용문이 (지정 문단 또는 전체) 원문에 있는지. 띄어쓰기·따옴표 차이는 무시, 그 밖에는 95% 이상 일치."""
    q = norm(quote)
    if len(q) < 6:
        return False, None, 0.0
    pool = [p for p in paras if p["id"] == para_id] or paras
    best, best_id = 0.0, None
    for p in pool:
        t = norm(p["text"])
        if q in t:
            return True, p["id"], 1.0
        sm = difflib.SequenceMatcher(None, q, t, autojunk=False)
        blk = sm.find_longest_match(0, len(q), 0, len(t))
        start = max(0, blk.b - blk.a)
        r = difflib.SequenceMatcher(None, q, t[start:start + len(q)], autojunk=False).ratio()
        if r > best:
            best, best_id = r, p["id"]
    return best >= 0.95, best_id, best


def expected_verdict(statuses):
    if statuses and all(s == "개시" for s in statuses):
        return "모든 구성요소 개시"
    if any(s == "미개시" for s in statuses):
        return "일부 미개시"
    return "추가 검토 필요"


def verify(chart, target_doc, n_elements=None):
    rows = []
    add = lambda level, item, detail: rows.append((level, item, detail))
    els = chart.get("elements", [])
    ids = [e.get("id") for e in els]
    if n_elements:
        miss = ["E{}".format(i) for i in range(1, n_elements + 1) if "E{}".format(i) not in ids]
        add("실패" if miss else "통과", "구성요소", "빠짐: " + ", ".join(miss) if miss else "{}개 모두".format(n_elements))
    paras = target_doc["paras"]
    valid_ids = {p["id"] for p in paras}
    statuses = []
    for e in els:
        st = e.get("status", "")
        statuses.append(st)
        if st not in STATUSES:
            add("실패", e.get("id", "?"), "판단 값 '{}' — {} 중 하나여야 합니다.".format(st, "/".join(STATUSES)))
            continue
        ev = e.get("evidence", []) or []
        if st in ("개시", "부분 개시") and not ev:
            add("실패", e["id"], "'{}'인데 인용 근거가 없습니다.".format(st))
        for q in ev:
            pid = str(q.get("para", "")).zfill(4) if q.get("para") else None
            if pid and pid not in valid_ids:
                add("실패", e["id"], "식별번호 [{}]가 대상 문서에 없습니다.".format(pid))
            ok, where, r = quote_found(q.get("quote", ""), paras, pid)
            if not ok and pid:                      # 표시한 문단에 없으면 전체에서 다시 찾는다
                ok2, where2, r2 = quote_found(q.get("quote", ""), paras, None)
                if ok2:
                    ok, where, r = ok2, where2, r2
            if ok and pid and where != pid:
                add("주의", e["id"], "인용문은 [{}]에 있습니다(표시는 [{}]).".format(where, pid))
            elif ok:
                add("통과", e["id"], "{} · 인용 확인 [{}]".format(st, where))
            else:
                add("실패", e["id"], "인용문을 원문에서 찾지 못했습니다(최고 일치 {:.0%}) — 지어냈거나 중간을 생략·바꿔 쓴 인용: “{}”".format(r, q.get("quote", "")[:40]))
        if e.get("equivalent_check"):
            add("주의", e["id"], "균등 검토 필요 — 사람이 판단")
    exp = expected_verdict(statuses)
    got = chart.get("verdict", "")
    add("통과" if exp in got else "실패", "결론", "'{}'{}".format(got, "" if exp in got else " → 모든 구성요소 원칙상 '{}'".format(exp)))
    return rows, exp


# ---------------------------------------------------------------- score
def auc(labels, scores):
    pos = [s for l, s in zip(labels, scores) if l == 1]
    neg = [s for l, s in zip(labels, scores) if l == 0]
    if not pos or not neg:
        return None
    win = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return win / (len(pos) * len(neg))


def score(pairs_path, pred_path):
    gold = [json.loads(l) for l in open(pairs_path, encoding="utf-8") if l.strip()]
    with open(pred_path, encoding="utf-8-sig", newline="") as f:
        preds = list(csv.DictReader(f))
    if len(preds) != len(gold):
        raise ValueError("판정 {}줄 / 쌍 {}줄 — 줄 수가 같아야 합니다(같은 순서).".format(len(preds), len(gold)))
    y = [g["label"] for g in gold]
    p = [int(float(r["pred"])) for r in preds]
    s = [float(r["score"]) for r in preds] if preds and preds[0].get("score") not in (None, "") else None
    tp = sum(1 for a, b in zip(y, p) if a == 1 and b == 1)
    fp = sum(1 for a, b in zip(y, p) if a == 0 and b == 1)
    fn = sum(1 for a, b in zip(y, p) if a == 1 and b == 0)
    tn = sum(1 for a, b in zip(y, p) if a == 0 and b == 0)
    acc = (tp + tn) / len(y)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    L = ["# 판정 점검 — {} × {}".format(pairs_path, pred_path), "",
         "- 쌍 {}개 · 정확도 {:.0%} · 정밀도 {:.0%} · 재현율 {:.0%} · F1 {:.2f}".format(len(y), acc, prec, rec, f1),
         "- 혼동표: 1을 1로 {} · 0을 1로 {} · 1을 0으로 {} · 0을 0으로 {}".format(tp, fp, fn, tn)]
    if s:
        a = auc(y, s)
        if a is not None:
            L.append("- AUC {:.2f} (점수로 1과 0을 가르는 힘, 0.5 = 동전 던지기)".format(a))
    by = defaultdict(list)
    for g, b in zip(gold, p):
        by[g.get("kind", "?")].append(g["label"] == b)
    L += ["", "| 쌍 종류 | 개수 | 맞힌 비율 |", "|---|---|---|"]
    for k, v in by.items():
        L.append("| {} | {} | {:.0%} |".format(k, len(v), sum(v) / len(v)))
    hard = by.get("어려운 다른 문헌", [])
    if hard and all(hard) and acc == 1.0:
        L += ["", "⚠ 모두 맞혔다면 평가 세트가 너무 쉬울 수 있습니다. 같은 분류코드(CPC)·같은 출원인의 문헌으로 어려운 쌍을 늘리세요."]
    if len(y) < 100:
        L.append("⚠ 쌍이 {}개입니다. 모델·프롬프트를 비교하려면 수백 쌍 이상이 필요합니다.".format(len(y)))
    return "\n".join(L) + "\n", {"acc": acc, "prec": prec, "rec": rec, "f1": f1}


def main(argv=None):
    ap = argparse.ArgumentParser(description="클레임 차트·판정 점검")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify")
    v.add_argument("chart", help="LLM 출력 파일(마크다운 안의 ```json 블록)")
    v.add_argument("--target", required=True, help="대상 문서(인용문을 대조할 원문)")
    v.add_argument("--elements", type=int, help="구성요소 개수(빠짐 확인)")
    s = sub.add_parser("score")
    s.add_argument("pairs")
    s.add_argument("predictions", help="CSV: pred(0/1)[,score(0~1)] — pairs.jsonl과 같은 순서")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        if a.cmd == "verify":
            chart = find_json(Path(a.chart).read_text(encoding="utf-8-sig"))
            rows, exp = verify(chart, pairkit.load_doc(a.target), a.elements)
            out("클레임 차트 점검 — {}\n".format(a.chart))
            for level, item, detail in rows:
                out("[{}] {:<6} {}".format(level, item, detail))
            fails = sum(1 for r in rows if r[0] == "실패")
            out("\n실패 {}건 — 형식·근거 점검일 뿐, 개시 판단의 옳고 그름은 변리사가 확인합니다.".format(fails))
            return 1 if fails else 0
        text, _ = score(a.pairs, a.predictions)
        out(text)
    except (ValueError, OSError, json.JSONDecodeError) as e:
        out("오류: " + str(e))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
