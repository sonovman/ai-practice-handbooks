#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
smc_tool.py — 스마트 머니 차트 분석(핸드북 14편)의 '사실 추출·계산·검증' 도구

AI가 차트 그림에서 숫자를 어림하는 대신, 가격 데이터(CSV)에서 판단 근거가 되는 사실을
정해진 규칙으로 뽑아 줍니다. 해석과 시나리오 작성은 스킬(AI)이, 숫자는 이 도구가 맡습니다.

세 가지 명령
  facts  OHLCV CSV → 종가 기준 스윙·추세·구조 돌파(BOS/MSS)·FVG·오더 블록 후보·
         유동성 스윕·거래량(노력 대 결과)·되돌림 비율을 마크다운으로 출력
  size   자본금·허용 손실·진입가·손절가로 수량과 손익비 계산(수수료·슬리피지 포함)
  stats  매매 기록(CSV)으로 적중률·평균 R·기대값 계산 — '정확도'를 숫자로 확인

사용 예
  python smc_tool.py facts sample/daily.csv --name "가상종목A" --tf 일봉
  python smc_tool.py size --capital 10000000 --risk 1 --entry 10450 --stop 10080 --target 11600
  python smc_tool.py stats journal.csv

CSV 머리글: date,open,high,low,close,volume (또는 날짜,시가,고가,저가,종가,거래량)
필요한 것: Python 3.8 이상 (추가 설치 없음)
이 도구의 출력은 기계적 규칙에 따른 관찰이며, 투자 권유나 수익 보장이 아닙니다.
"""
import argparse
import csv
import math
import sys
from pathlib import Path

ALIASES = {
    "date": ("date", "datetime", "time", "날짜", "일자", "시간"),
    "open": ("open", "시가"),
    "high": ("high", "고가"),
    "low": ("low", "저가"),
    "close": ("close", "종가", "현재가"),
    "volume": ("volume", "vol", "거래량"),
}


def out(s=""):
    print(s)


# ---------------------------------------------------------------- 읽기
def num(x):
    x = (x or "").strip().replace(",", "")
    return float(x) if x not in ("", "-", "?") else None


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    head = [h.strip().lower() for h in rows[0]]
    idx = {}
    for key, names in ALIASES.items():
        for i, h in enumerate(head):
            if h in names:
                idx[key] = i
                break
    miss = [k for k in ("open", "high", "low", "close") if k not in idx]
    if miss:
        raise ValueError("CSV에 필요한 열이 없습니다: " + ", ".join(miss))
    bars = []
    for r in rows[1:]:
        if not r or not any(c.strip() for c in r):
            continue
        b = {k: num(r[i]) if k != "date" else r[i].strip() for k, i in idx.items()}
        if None in (b["open"], b["high"], b["low"], b["close"]):
            continue
        b.setdefault("volume", None)
        b.setdefault("date", str(len(bars) + 1))
        bars.append(b)
    if len(bars) < 30:
        raise ValueError("캔들이 {}개입니다. 구조를 보려면 30개 이상이 필요합니다.".format(len(bars)))
    return bars


# ---------------------------------------------------------------- 기본 계산
def atr(bars, n=14):
    trs = []
    for i, b in enumerate(bars):
        pc = bars[i - 1]["close"] if i else b["close"]
        trs.append(max(b["high"] - b["low"], abs(b["high"] - pc), abs(b["low"] - pc)))
    res = []
    for i in range(len(trs)):
        w = trs[max(0, i - n + 1):i + 1]
        res.append(sum(w) / len(w))
    return res


def vol_ratio(bars, n=20):
    """거래량 ÷ 직전 n봉 평균. 거래량이 없으면 None."""
    if any(b["volume"] is None for b in bars):
        return [None] * len(bars)
    res = []
    for i, b in enumerate(bars):
        w = [x["volume"] for x in bars[max(0, i - n):i]] or [b["volume"]]
        avg = sum(w) / len(w)
        res.append(b["volume"] / avg if avg else None)
    return res


def swings(bars, k=3):
    """종가 기준 스윙. 좌우 k봉보다 종가가 높으면(낮으면) 스윙 고점(저점). 마지막 k봉은 아직 확정 불가."""
    hs, ls = [], []
    c = [b["close"] for b in bars]
    for i in range(k, len(c) - k):
        w = c[i - k:i + k + 1]
        if c[i] == max(w) and w.count(c[i]) == 1:
            hs.append(i)
        if c[i] == min(w) and w.count(c[i]) == 1:
            ls.append(i)
    return hs, ls


def trend_of(bars, hs, ls):
    c = [b["close"] for b in bars]
    if len(hs) < 2 or len(ls) < 2:
        return "판단 불가", "스윙이 부족합니다"
    h1, h2 = c[hs[-2]], c[hs[-1]]
    l1, l2 = c[ls[-2]], c[ls[-1]]
    hh, hl = h2 > h1, l2 > l1
    if hh and hl:
        return "상승", "고점 {:,.0f}→{:,.0f}(HH), 저점 {:,.0f}→{:,.0f}(HL)".format(h1, h2, l1, l2)
    if not hh and not hl:
        return "하락", "고점 {:,.0f}→{:,.0f}(LH), 저점 {:,.0f}→{:,.0f}(LL)".format(h1, h2, l1, l2)
    return "중립·전환 중", "고점 {} / 저점 {} — 방향이 엇갈림".format("HH" if hh else "LH", "HL" if hl else "LL")


def structure_breaks(bars, hs, ls, k=3):
    """종가가 직전 확정 스윙을 넘는 순간. 직전 흐름과 같은 방향이면 BOS, 반대면 MSS."""
    c = [b["close"] for b in bars]
    events, bias = [], None
    last_h = last_l = None
    hset, lset = set(hs), set(ls)
    for i in range(len(bars)):
        # i봉 시점에 확정된 스윙만 사용(미래 데이터 차단): 스윙 j는 j+k봉에서 확정
        j = i - k
        if j in hset:
            last_h = j
        if j in lset:
            last_l = j
        if last_h is not None and c[i] > c[last_h] and (i == 0 or c[i - 1] <= c[last_h]):
            kind = "BOS" if bias == "up" else "MSS"
            events.append((i, "상향 " + kind, c[last_h]))
            bias, last_h = "up", None
        elif last_l is not None and c[i] < c[last_l] and (i == 0 or c[i - 1] >= c[last_l]):
            kind = "BOS" if bias == "down" else "MSS"
            events.append((i, "하향 " + kind, c[last_l]))
            bias, last_l = "down", None
    return events


def is_disp(b, a, up=True):
    rng = b["high"] - b["low"]
    body = (b["close"] - b["open"]) if up else (b["open"] - b["close"])
    return rng > 0 and body / rng >= 0.65 and rng >= 1.3 * a


def fvgs(bars):
    """3봉 불균형: 상승 FVG = 3번째 봉 저가 > 1번째 봉 고가. 이후 가격이 메웠는지 추적."""
    res = []
    for i in range(1, len(bars) - 1):
        a, c3 = bars[i - 1], bars[i + 1]
        if c3["low"] > a["high"]:
            lo, hi, d = a["high"], c3["low"], "상승"
        elif c3["high"] < a["low"]:
            lo, hi, d = c3["high"], a["low"], "하락"
        else:
            continue
        state = "미체결"
        for b in bars[i + 2:]:
            if d == "상승" and b["low"] <= lo or d == "하락" and b["high"] >= hi:
                state = "모두 메움"
                break
            if d == "상승" and b["low"] < hi or d == "하락" and b["high"] > lo:
                state = "일부 메움"
        res.append({"i": i, "dir": d, "lo": lo, "hi": hi, "state": state})
    return res


def order_blocks(bars, a, events, gaps):
    """구조 돌파를 만든 변위 직전의 마지막 반대색 캔들. 변위·FVG·BOS/MSS 세 조건을 각각 표시."""
    res = []
    for (ei, kind, lvl) in events:
        up = kind.startswith("상향")
        # 돌파봉에서 거슬러 올라가며 변위봉 찾기(최대 5봉)
        disp = None
        for j in range(ei, max(0, ei - 5) - 1, -1):
            if is_disp(bars[j], a[j], up):
                disp = j
                break
        start = disp if disp is not None else ei
        ob = None
        for j in range(start - 1, max(0, start - 8) - 1, -1):
            b = bars[j]
            if (b["close"] < b["open"]) if up else (b["close"] > b["open"]):
                ob = j
                break
        if ob is None:
            continue
        has_fvg = any(g["dir"] == ("상승" if up else "하락") and ob <= g["i"] <= ei + 1 for g in gaps)
        b = bars[ob]
        prox, dist = (b["high"], b["low"]) if up else (b["low"], b["high"])
        mitig = "미방문"
        for x in bars[ei + 1:]:
            if up and x["low"] <= prox or (not up) and x["high"] >= prox:
                mitig = "재방문"
            if up and x["close"] < dist or (not up) and x["close"] > dist:
                mitig = "무효(종가 이탈)"
                break
        res.append({"i": ob, "dir": "매수" if up else "매도", "prox": prox, "dist": dist,
                    "disp": disp is not None, "fvg": has_fvg, "bos": True, "state": mitig, "event": ei})
    return res


def sweeps(bars, hs, ls, k=3):
    """꼬리로만 직전 스윙을 넘고 종가는 안쪽에서 마감한 봉(유동성 스윕)."""
    c = [b["close"] for b in bars]
    res = []
    for i in range(len(bars)):
        prev_l = [j for j in ls if j + k < i]
        prev_h = [j for j in hs if j + k < i]
        if prev_l:
            lv = c[prev_l[-1]]
            if bars[i]["low"] < lv < c[i]:
                res.append((i, "하단 스윕", lv))
        if prev_h:
            hv = c[prev_h[-1]]
            if bars[i]["high"] > hv > c[i]:
                res.append((i, "상단 스윕", hv))
    return res


# ---------------------------------------------------------------- facts
def facts(bars, name="종목", tf="", k=3):
    a = atr(bars)
    vr = vol_ratio(bars)
    hs, ls = swings(bars, k)
    c = [b["close"] for b in bars]
    tr, why = trend_of(bars, hs, ls)
    ev = structure_breaks(bars, hs, ls, k)
    gaps = fvgs(bars)
    obs = order_blocks(bars, a, ev, gaps)
    sw = sweeps(bars, hs, ls, k)
    last = bars[-1]
    d = lambda i: bars[i]["date"]
    L = []
    L.append("# 차트 사실 요약 — {} {}".format(name, tf).rstrip())
    L.append("")
    L.append("기계적 규칙으로 뽑은 관찰입니다. 해석·시나리오는 스킬이 이 표를 근거로 작성합니다.")
    L.append("")
    L.append("## 1. 데이터")
    L.append("- 캔들 {}개 · {} ~ {} · 거래량 {}".format(len(bars), d(0), d(-1),
             "있음" if vr[-1] is not None else "없음(거래량 판단 생략)"))
    L.append("- 마지막 봉({}): 시가 {:,.0f} · 고가 {:,.0f} · 저가 {:,.0f} · **종가 {:,.0f}**".format(
        last["date"], last["open"], last["high"], last["low"], last["close"]))
    L.append("- ATR(14) {:,.0f} — 봉 하나의 평균 변동 폭. 손절 폭이 이보다 작으면 잡음에 걸리기 쉽습니다.".format(a[-1]))
    L.append("")
    L.append("## 2. 종가 기준 스윙과 추세 (좌우 {}봉 비교)".format(k))
    L.append("- 추세: **{}** — {}".format(tr, why))
    L.append("- 최근 스윙 고점: " + (", ".join("{} {:,.0f}".format(d(i), c[i]) for i in hs[-3:]) or "없음"))
    L.append("- 최근 스윙 저점: " + (", ".join("{} {:,.0f}".format(d(i), c[i]) for i in ls[-3:]) or "없음"))
    L.append("- 마지막 {}봉은 아직 스윙으로 확정할 수 없습니다.".format(k))
    L.append("")
    L.append("## 3. 구조 돌파 (종가 기준)")
    if ev:
        for i, kind, lvl in ev[-4:]:
            v = " · 거래량 {:.1f}배".format(vr[i]) if vr[i] else ""
            L.append("- {} **{}** — 스윙 {:,.0f}을 종가 {:,.0f}로 넘음{}".format(d(i), kind, lvl, c[i], v))
    else:
        L.append("- 없음")
    L.append("")
    L.append("## 4. 오더 블록 후보 (돌파를 만든 변위 직전의 마지막 반대색 캔들)")
    if obs:
        L.append("| 날짜 | 방향 | 근위선 | 원위선 | 변위 | FVG | 구조 돌파 | 세 조건 | 현재 |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for o in obs[-3:]:
            ok = o["disp"] and o["fvg"] and o["bos"]
            L.append("| {} | {} | {:,.0f} | {:,.0f} | {} | {} | {} | {} | {} |".format(
                d(o["i"]), o["dir"], o["prox"], o["dist"], "✓" if o["disp"] else "✗", "✓" if o["fvg"] else "✗",
                "✓", "**충족**" if ok else "미충족", o["state"]))
    else:
        L.append("- 없음")
    L.append("")
    L.append("## 5. 불균형 존 FVG (방향별 최근 2개, 모두 메운 것 제외)")
    live = sorted([g for g in gaps if g["state"] != "모두 메움" and g["dir"] == "상승"][-2:] +
                  [g for g in gaps if g["state"] != "모두 메움" and g["dir"] == "하락"][-2:], key=lambda g: g["i"])
    if live:
        for g in live:
            L.append("- {} {} FVG {:,.0f} ~ {:,.0f} — {}".format(d(g["i"]), g["dir"], g["lo"], g["hi"], g["state"]))
    else:
        L.append("- 없음")
    L.append("")
    L.append("## 6. 유동성 스윕 (꼬리로만 이탈, 종가는 복귀)")
    if sw:
        for i, kind, lvl in sw[-3:]:
            v = " · 거래량 {:.1f}배".format(vr[i]) if vr[i] else ""
            L.append("- {} {} — 기준 {:,.0f}, 꼬리 {:,.0f}, 종가 {:,.0f}{}".format(
                d(i), kind, lvl, bars[i]["low"] if "하단" in kind else bars[i]["high"], c[i], v))
    else:
        L.append("- 없음")
    L.append("")
    L.append("## 7. 거래량 — 노력 대 결과")
    if vr[-1] is None:
        L.append("- 거래량 없음")
    else:
        L.append("- 마지막 봉 거래량: 직전 20봉 평균의 {:.1f}배".format(vr[-1]))
        if ev:
            bi = ev[-1][0]
            imp = [x["volume"] for x in bars[max(0, bi - 3):bi + 1]]
            pull = [x["volume"] for x in bars[bi + 1:]]
            if pull:
                r = (sum(pull) / len(pull)) / (sum(imp) / len(imp))
                tag = "수축 → 노 서플라이 가능성" if r < 0.7 else ("비슷함" if r < 1.1 else "증가 → 되돌림에 매물 출회 주의")
                L.append("- 마지막 돌파 이후 평균 거래량 ÷ 돌파 구간 평균 = {:.2f} ({})".format(r, tag))
        if len(hs) >= 2 and c[hs[-1]] > c[hs[-2]]:
            v1 = bars[hs[-2]]["volume"]
            v2 = bars[hs[-1]]["volume"]
            if v2 < v1:
                L.append("- 다이버전스 주의: 종가 고점은 높아졌는데 그 봉 거래량은 줄었습니다({:,.0f} → {:,.0f}).".format(v1, v2))
    L.append("")
    L.append("## 8. 되돌림 위치")
    if ev and ev[-1][1].startswith("상향"):
        bi = ev[-1][0]
        lo_i = min(range(max(0, bi - 15), bi + 1), key=lambda i: bars[i]["low"])
        hi_i = max(range(bi, len(bars)), key=lambda i: bars[i]["high"])
        lo, hi = bars[lo_i]["low"], bars[hi_i]["high"]
        if hi > lo:
            rr = (hi - c[-1]) / (hi - lo)
            zone = "33~66% 구간 안" if 0.33 <= rr <= 0.66 else ("얕음(33% 미만)" if rr < 0.33 else "깊음(66% 초과)")
            L.append("- 마지막 상승 파동 {:,.0f}({}) → {:,.0f}({}) 기준 현재 되돌림 {:.0%} — {}".format(
                lo, d(lo_i), hi, d(hi_i), rr, zone))
    elif ev:
        bi = ev[-1][0]
        hi_i = max(range(max(0, bi - 15), bi + 1), key=lambda i: bars[i]["high"])
        lo_i = min(range(bi, len(bars)), key=lambda i: bars[i]["low"])
        hi, lo = bars[hi_i]["high"], bars[lo_i]["low"]
        if hi > lo:
            rr = (c[-1] - lo) / (hi - lo)
            L.append("- 마지막 하락 파동 기준 현재 반등 {:.0%}".format(rr))
    else:
        L.append("- 기준 파동 없음")
    L.append("")
    L.append("## 9. 다음 유동성 풀 (위아래 가장 가까운 확정 스윙)")
    up = sorted(c[i] for i in hs if c[i] > c[-1])
    dn = sorted((c[i] for i in ls if c[i] < c[-1]), reverse=True)
    L.append("- 위: " + (", ".join("{:,.0f}".format(x) for x in up[:2]) or "확정 스윙 없음(신고가 영역)"))
    L.append("- 아래: " + (", ".join("{:,.0f}".format(x) for x in dn[:2]) or "확정 스윙 없음"))
    return "\n".join(L) + "\n", {"trend": tr, "events": ev, "obs": obs, "fvgs": gaps, "sweeps": sw,
                                  "swings": (hs, ls), "atr": a[-1]}


# ---------------------------------------------------------------- size
def size(capital, risk_pct, entry, stop, target=None, fee_pct=0.0, slip=0.0, lot=1):
    if entry == stop:
        raise ValueError("진입가와 손절가가 같습니다.")
    side = "롱(매수)" if entry > stop else "숏(매도)"
    per = abs(entry - stop) + slip * 2 + (entry + stop) * fee_pct / 100
    budget = capital * risk_pct / 100
    qty = int(budget / per // lot * lot)
    res = {"side": side, "per": per, "budget": budget, "qty": qty, "loss": qty * per,
           "notional": qty * entry, "rr": None}
    if target is not None:
        gain = abs(target - entry) - slip * 2 - (entry + target) * fee_pct / 100
        res["rr"] = gain / per if per else None
        res["gain"] = qty * gain
    return res


# ---------------------------------------------------------------- stats
def verdict(row):
    return (row.get("판정") or row.get("결정") or "?").strip()


def r_multiple(row):
    e, s, x = num(row.get("진입")), num(row.get("손절")), num(row.get("청산"))
    if None in (e, s, x) or e == s:
        return None
    return (x - e) / (e - s)          # 롱·숏 모두 이 식 하나로 부호가 맞음


def stats(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    trades = [(r, r_multiple(r)) for r in rows]
    done = [(r, m) for r, m in trades if m is not None]
    holds = [r for r in rows if verdict(r).startswith("관망")]
    L = ["# 매매 기록 검증 — {}".format(path), ""]
    L.append("- 기록 {}건 · 청산까지 끝난 거래 {}건 · 관망 {}건".format(len(rows), len(done), len(holds)))
    if not done:
        L.append("- 청산된 거래가 없어 계산할 수 없습니다.")
        return "\n".join(L) + "\n", {}
    rs = [m for _, m in done]
    wins = [m for m in rs if m > 0]
    hit = len(wins) / len(rs)
    exp = sum(rs) / len(rs)
    L.append("- 적중률 {:.0%} ({}승 {}패)".format(hit, len(wins), len(rs) - len(wins)))
    L.append("- 평균 R {:+.2f} · 이긴 거래 평균 {:+.2f}R · 진 거래 평균 {:+.2f}R".format(
        exp, sum(wins) / len(wins) if wins else 0,
        sum(m for m in rs if m <= 0) / max(1, len(rs) - len(wins))))
    L.append("- 기대값(거래 1건당) {:+.2f}R — 0보다 커야 규칙이 돈을 법니다.".format(exp))
    peak = run = mdd = 0.0
    for m in rs:
        run += m
        peak = max(peak, run)
        mdd = min(mdd, run - peak)
    L.append("- 누적 {:+.1f}R · 최대 낙폭 {:.1f}R".format(run, mdd))
    by = {}
    for r, m in done:
        by.setdefault(verdict(r), []).append(m)
    L.append("")
    L.append("| 판정 | 건수 | 적중률 | 평균 R |")
    L.append("|---|---|---|---|")
    for kname, ms in sorted(by.items()):
        L.append("| {} | {} | {:.0%} | {:+.2f} |".format(kname, len(ms), sum(1 for m in ms if m > 0) / len(ms), sum(ms) / len(ms)))
    L.append("")
    if len(rs) < 30:
        L.append("⚠ 표본이 {}건입니다. 30건 미만의 적중률은 우연과 구분하기 어렵습니다.".format(len(rs)))
    se = math.sqrt(hit * (1 - hit) / len(rs))
    L.append("적중률의 대략적인 95% 범위: {:.0%} ~ {:.0%}".format(max(0, hit - 1.96 * se), min(1, hit + 1.96 * se)))
    return "\n".join(L) + "\n", {"hit": hit, "exp": exp, "n": len(rs), "mdd": mdd}


# ---------------------------------------------------------------- 실행
def main(argv=None):
    ap = argparse.ArgumentParser(description="스마트 머니 차트 분석 도구")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("facts")
    f.add_argument("csv")
    f.add_argument("--name", default="종목")
    f.add_argument("--tf", default="")
    f.add_argument("--k", type=int, default=3, help="스윙 판단에 쓰는 좌우 봉 수(기본 3)")
    f.add_argument("--out")
    s = sub.add_parser("size")
    s.add_argument("--capital", type=float, required=True)
    s.add_argument("--risk", type=float, default=1.0, help="1회 허용 손실 %% (기본 1)")
    s.add_argument("--entry", type=float, required=True)
    s.add_argument("--stop", type=float, required=True)
    s.add_argument("--target", type=float)
    s.add_argument("--fee", type=float, default=0.0, help="편도 수수료+세금 %% (예: 0.2)")
    s.add_argument("--slip", type=float, default=0.0, help="체결 미끄러짐(가격 단위)")
    s.add_argument("--lot", type=int, default=1)
    t = sub.add_parser("stats")
    t.add_argument("csv")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        if a.cmd == "facts":
            text, _ = facts(load(a.csv), a.name, a.tf, a.k)
            if a.out:
                Path(a.out).write_text(text, encoding="utf-8")
                out("저장: " + a.out)
            else:
                out(text)
        elif a.cmd == "size":
            r = size(a.capital, a.risk, a.entry, a.stop, a.target, a.fee, a.slip, a.lot)
            out("방향 {} · 1회 허용 손실 {:,.0f}".format(r["side"], r["budget"]))
            out("1주(계약)당 위험 {:,.2f} (손절 폭 + 수수료·미끄러짐)".format(r["per"]))
            out("수량 {:,}  · 투입 금액 {:,.0f} · 손절 시 손실 약 {:,.0f}".format(r["qty"], r["notional"], r["loss"]))
            if r["rr"] is not None:
                out("목표 도달 시 이익 약 {:,.0f} · 손익비 1 : {:.2f}{}".format(
                    r["gain"], r["rr"], "" if r["rr"] >= 2 else "  ← 1:2 미만"))
            if r["notional"] > a.capital:
                out("주의: 투입 금액이 자본금보다 큽니다(레버리지). 손절 폭을 넓히거나 수량을 줄이세요.")
            out("갭(장 시작 시 급등락)으로 손절가보다 불리하게 체결될 수 있습니다.")
        else:
            text, _ = stats(a.csv)
            out(text)
    except (ValueError, OSError) as e:
        out("오류: " + str(e))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
