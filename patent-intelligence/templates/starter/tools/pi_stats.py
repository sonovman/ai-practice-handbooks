#!/usr/bin/env python3
"""2단계 집계 (핸드북 34). 01_intake.json → 연도·국가·출원인·기술군 집계, 등급 후보, 중요도 점수, 차트(SVG).

  python tools/pi_stats.py work/01_intake.json --clusters work/clusters.csv \
      --scores work/scores.csv --out work/02_stats.json

- 숫자는 전부 여기서 센다(AI가 눈대중으로 세지 않게). 등급·점수의 '판단'은 사람·AI가 정독 후 확정.
- 연도는 최선일(우선일, 없으면 출원일) 기준 — 기술이 만들어진 시점에 가깝다.
- 공개 지연 구간에 걸친 연도는 '미완결'로 표시하고 차트에서 흐리게 그린다.
"""
import argparse
import csv
import datetime as dt
import json
from collections import Counter, defaultdict
from pathlib import Path

from pi_common import utf8_console

COUNTRIES = ["KR", "US", "JP", "CN", "EP", "WO"]
WEIGHTS = {"relevance": 25, "proximity": 20, "design_around": 20, "persistence": 15, "expansion": 10, "info_value": 10}
LABELS = {"relevance": "핵심제품 관련성", "proximity": "청구항·구조 근접성", "design_around": "회피설계 신호",
          "persistence": "경쟁사 지속성", "expansion": "제품·시장 확장성", "info_value": "전략적 정보가치"}
MAX_CANDIDATES = 5


def lag_start_year(data_date, lag_months):
    d = dt.date.fromisoformat(data_date)
    m = d.year * 12 + (d.month - 1) - int(round(lag_months))
    return m // 12


def load_clusters(path, recs):
    cmap = {r["id"]: r.get("cluster") for r in recs if r.get("cluster")}
    if path and Path(path).exists():
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if (row.get("id") or "").strip() and (row.get("cluster") or "").strip():
                    cmap[row["id"].strip()] = row["cluster"].strip()
    return cmap


def stats(intake, clusters_path=None, scores_path=None, threshold=60.0, scope="trend"):
    proj = intake.get("project", {})
    s = intake["summary"]
    recs = [r for r in intake["records"] if r["doc_type"] != "design"]
    if scope == "trend":
        base = [r for r in recs if r["in_trend_scope"]]
    else:
        base = recs
    lag_year = lag_start_year(s["data_date"], s["lag_months"]) if s.get("data_date") else None
    issues = []

    # 연도 × 국가 (전체 모집단 — 기술계보 포함)
    years = sorted({int(r["first_date"][:4]) for r in recs if r.get("first_date")})
    trend = {}
    for y in years:
        row = Counter()
        sig = set()
        for r in recs:
            if r.get("first_date") and int(r["first_date"][:4]) == y:
                row[r["country"]] += 1
                sig.add(r["signal_key"])
        trend[y] = {"by_country": dict(row), "docs": sum(row.values()), "signals": len(sig),
                    "incomplete": bool(lag_year is not None and y >= lag_year)}

    # 출원인 그룹
    groups = defaultdict(lambda: {"docs": 0, "signals": set(), "countries": Counter(), "years": [],
                                  "names": set(), "display": None, "trend_docs": 0})
    for r in recs:
        g = groups[r["group"]]
        g["docs"] += 1
        g["signals"].add(r["signal_key"])
        g["countries"][r["country"]] += 1
        if r.get("first_date"):
            g["years"].append(r["first_date"])
        g["names"].add(r["applicant_canon"])
        g["display"] = g["display"] or r["applicant_display"]
        if r["in_trend_scope"]:
            g["trend_docs"] += 1
    base_date = s.get("trend_base_date")
    group_rows = []
    for name, g in groups.items():
        first = min(g["years"]) if g["years"] else None
        group_rows.append({
            "group": name, "display": g["display"], "members": sorted(g["names"]),
            "docs": g["docs"], "signals": len(g["signals"]), "trend_docs": g["trend_docs"],
            "countries": dict(g["countries"]), "first_date": first,
            "last_date": max(g["years"]) if g["years"] else None,
            "new_entrant": bool(base_date and first and first >= base_date)})
    group_rows.sort(key=lambda x: (-x["signals"], -x["docs"], x["group"]))

    # 패밀리 국가 확장(시장 신호) — 기술신호별 진출 국가 수
    sig_c = defaultdict(set)
    sig_g = {}
    for r in recs:
        sig_c[r["signal_key"]].add(r["country"])
        sig_g[r["signal_key"]] = r["group"]
    coverage = Counter(len(v) for v in sig_c.values())
    multi = Counter(sig_g[k] for k, v in sig_c.items() if len(v) >= 3)
    country_targets = Counter()
    for k, v in sig_c.items():
        for c in v:
            country_targets[c] += 1

    # 기술군과 등급 후보
    cmap = load_clusters(clusters_path, recs)
    clusters = {}
    if cmap:
        tmp = defaultdict(lambda: {"signals": defaultdict(set), "docs": 0, "ids": [], "years": []})
        for r in base:
            c = cmap.get(r["id"])
            if not c:
                continue
            t = tmp[c]
            t["signals"][r["group"]].add(r["signal_key"])
            t["docs"] += 1
            t["ids"].append(r["id"])
            if r.get("first_date"):
                t["years"].append(int(r["first_date"][:4]))
        for c, t in tmp.items():
            per_group = {g: len(v) for g, v in t["signals"].items()}
            total = len(set().union(*t["signals"].values())) if t["signals"] else 0
            indep = len(per_group)
            heavy = sorted([g for g, n in per_group.items() if n >= 2])
            if indep >= 2 and total >= 2:
                cand = "T1 후보"
            elif heavy:
                cand = "T2 후보"
            elif total == 1:
                cand = "T4 또는 T5 (작동원리·신규성으로 판단)"
            else:
                cand = "판단 필요"
            note = []
            if heavy and cand == "T1 후보":
                note.append("T2 신호도 있음: " + ", ".join(heavy))
            if cand == "T1 후보" and total == 2:
                note.append("근거 최소(2건) — 문제해결 방향·구조가 같은지 정독으로 확인")
            clusters[c] = {"docs": t["docs"], "signals": total, "independent_groups": indep,
                           "per_group": per_group, "grade_candidate": cand, "note": "; ".join(note),
                           "ids": t["ids"], "year_span": [min(t["years"]), max(t["years"])] if t["years"] else None}
        missing = [r["id"] for r in base if r["id"] not in cmap]
        if missing:
            issues.append({"code": "S01", "level": "warn",
                           "msg": "기술군이 지정되지 않은 분석대상 %d건: %s" % (len(missing), ", ".join(missing[:12]) + (" …" if len(missing) > 12 else ""))})
    else:
        issues.append({"code": "S02", "level": "info", "msg": "기술군 지정 전 — 1차 선별 뒤 clusters.csv(id,cluster)를 만들면 등급 후보를 계산"})

    # 중요도 점수
    scores = []
    if scores_path and Path(scores_path).exists():
        ids = {r["id"]: r for r in intake["records"]}
        with open(scores_path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                did = (row.get("id") or "").strip()
                if not did:
                    continue
                if did not in ids:
                    issues.append({"code": "S03", "level": "error", "msg": "점수표의 %s가 자료에 없음" % did})
                    continue
                parts, missing_prox, bad = {}, False, []
                for k, w in WEIGHTS.items():
                    v = (row.get(k) or "").strip()
                    if v == "":
                        if k == "proximity":
                            missing_prox = True
                            continue
                        v = "0"
                    try:
                        x = float(v)
                    except ValueError:
                        bad.append(k)
                        continue
                    if not 0 <= x <= w:
                        bad.append("%s(0~%d)" % (k, w))
                    parts[k] = x
                if bad:
                    issues.append({"code": "S04", "level": "error", "msg": "%s 점수 범위·형식 오류: %s" % (did, ", ".join(bad))})
                raw = sum(parts.values())
                full = 80 if missing_prox else 100
                scaled = round(raw / full * 100, 1)
                rec = ids[did]
                scores.append({"id": did, "number": rec.get("reg_no") or rec.get("pub_no") or "번호 없음",
                               "applicant": rec["applicant_display"], "parts": parts, "raw": raw, "full": full,
                               "scaled": scaled, "proximity_pending": missing_prox,
                               "exception": (row.get("strategic_exception") or "").strip().upper() in ("Y", "YES", "1", "O"),
                               "reason": (row.get("reason") or "").strip(), "evidence_ok": rec["evidence_ok"]})
        scores.sort(key=lambda x: -x["scaled"])
        picks = [x for x in scores if x["evidence_ok"] and (x["scaled"] >= threshold or x["exception"])]
        dropped = picks[MAX_CANDIDATES:]
        for i, x in enumerate(scores, start=1):
            x["rank"] = i
            x["recommend"] = x in picks[:MAX_CANDIDATES]
            x["basis"] = ("Strategic Exception" if x["exception"] and x["scaled"] < threshold else
                          ("점수 ≥ %g" % threshold if x["recommend"] else ""))
        if dropped:
            issues.append({"code": "S05", "level": "warn",
                           "msg": "후보 상한 %d건 초과로 제외: %s — 정말 필요한지 사람이 비교" % (MAX_CANDIDATES, ", ".join(x["id"] for x in dropped))})
        if any(x["proximity_pending"] for x in scores):
            issues.append({"code": "S06", "level": "info",
                           "msg": "당사 청구항이 없어 근접성(20점)을 비우고 80점 만점을 100점으로 환산 — 보고서에 '근접성 미확정'으로 표기"})
        for x in scores:
            if not x["evidence_ok"]:
                issues.append({"code": "S07", "level": "warn", "msg": "%s는 공개·등록번호가 없어 후보에서 뺌" % x["id"]})

    return {"scope": scope, "scope_docs": len(base), "lag_start_year": lag_year,
            "trend": trend, "groups": group_rows,
            "family_coverage": dict(sorted(coverage.items())), "multi_country_signals_by_group": dict(multi),
            "country_targets": dict(country_targets),
            "clusters": clusters, "scores": scores, "threshold": threshold, "issues": issues,
            "summary": s, "project": proj}


# ── SVG ────────────────────────────────────────────────
PALETTE = {"KR": "#111111", "US": "#4a4a4a", "JP": "#7a7a7a", "CN": "#a6a6a6", "EP": "#cfcfcf", "WO": "#e6e6e6"}


def svg_trend(st, path):
    years = sorted(st["trend"])
    if not years:
        return
    W, H, L, B, T = 640, 300, 48, 46, 40
    maxv = max(v["docs"] for v in st["trend"].values()) or 1
    bw = (W - L - 20) / len(years)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" font-family="sans-serif" font-size="11">' % (W, H),
           '<defs><pattern id="h" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
           '<rect width="6" height="6" fill="#fff"/><line x1="0" y1="0" x2="0" y2="6" stroke="#999" stroke-width="2"/></pattern></defs>',
           '<rect width="100%" height="100%" fill="#fff"/>',
           '<text x="%d" y="18" font-size="13" font-weight="700">최선일 연도별 문헌 수(국가별)</text>' % L,
           '<text x="%d" y="18" text-anchor="end" fill="#666">빗금 = 공개 지연 구간(최근 %d개월 출원은 아직 덜 공개됨)</text>' % (W - 20, int(st["summary"]["lag_months"]))]
    for i in range(0, 5):
        y = H - B - (H - B - T) * i / 4
        out.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="#e5e5e5"/>' % (L, W - 20, y, y))
        out.append('<text x="%d" y="%.1f" text-anchor="end" fill="#666">%d</text>' % (L - 6, y + 4, round(maxv * i / 4)))
    for i, yv in enumerate(years):
        d = st["trend"][yv]
        x = L + i * bw + bw * 0.15
        y0 = H - B
        for c in COUNTRIES:
            n = d["by_country"].get(c, 0)
            if not n:
                continue
            h = (H - B - T) * n / maxv
            fill = "url(#h)" if d["incomplete"] else PALETTE[c]
            out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#fff"/>' % (x, y0 - h, bw * 0.7, h, fill))
            y0 -= h
        out.append('<text x="%.1f" y="%d" text-anchor="middle">%d</text>' % (x + bw * 0.35, H - B + 16, yv))
        out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-weight="700">%d</text>' % (x + bw * 0.35, y0 - 4, d["docs"]))
        if d["incomplete"]:
            out.append('<text x="%.1f" y="%d" text-anchor="middle" fill="#666">미완결</text>' % (x + bw * 0.35, H - B + 30))
    lx = L
    for c in COUNTRIES:
        if any(st["trend"][y]["by_country"].get(c) for y in years):
            out.append('<rect x="%d" y="%d" width="10" height="10" fill="%s"/><text x="%d" y="%d">%s</text>' % (lx, H - 12, PALETTE[c], lx + 14, H - 3, c))
            lx += 48
    out.append("</svg>")
    Path(path).write_text("\n".join(out), encoding="utf-8")


def svg_groups(st, path, top=8):
    rows = st["groups"][:top]
    if not rows:
        return
    W, rowh, L = 640, 26, 230
    H = 40 + rowh * len(rows) + 20
    maxv = max(r["signals"] for r in rows) or 1
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" font-family="sans-serif" font-size="11">' % (W, H),
           '<rect width="100%" height="100%" fill="#fff"/>',
           '<text x="10" y="18" font-size="13" font-weight="700">출원인 그룹별 기술신호 수(검은 막대)와 문헌 수(회색)</text>']
    for i, r in enumerate(rows):
        y = 34 + i * rowh
        name = r["group"] + (" · 신규진입" if r["new_entrant"] else "")
        out.append('<text x="%d" y="%d" text-anchor="end">%s</text>' % (L - 8, y + 14, name.replace("&", "&amp;")))
        wd = (W - L - 60) * r["docs"] / max(x["docs"] for x in rows)
        ws = (W - L - 60) * r["signals"] / max(x["docs"] for x in rows)
        out.append('<rect x="%d" y="%d" width="%.1f" height="16" fill="#d9d9d9"/>' % (L, y + 2, wd))
        out.append('<rect x="%d" y="%d" width="%.1f" height="16" fill="#111"/>' % (L, y + 2, ws))
        out.append('<text x="%.1f" y="%d">%d / %d</text>' % (L + wd + 6, y + 14, r["signals"], r["docs"]))
    out.append("</svg>")
    Path(path).write_text("\n".join(out), encoding="utf-8")


def to_markdown(st):
    s = st["summary"]
    L = ["# 집계 결과 (2단계)", "",
         "범위: %s(%d건) · 연도 기준 = 최선일(우선일→출원일) · %d년 이후는 공개 미완결" % (
             "기술동향 분석대상" if st["scope"] == "trend" else "전체 모집단", st["scope_docs"], st["lag_start_year"] or 0), "",
         "## 연도별(전체 모집단 %d건 — 기술계보 포함, 디자인 제외)" % sum(d["docs"] for d in st["trend"].values()), "", "| 연도 | 문헌 | 기술신호 | " + " | ".join(COUNTRIES) + " | 비고 |", "|---" * (len(COUNTRIES) + 4) + "|"]
    for y in sorted(st["trend"]):
        d = st["trend"][y]
        L.append("| %d | %d | %d | %s | %s |" % (y, d["docs"], d["signals"], " | ".join(str(d["by_country"].get(c, "")) for c in COUNTRIES),
                                              "공개 미완결 — 증감 해석 금지" if d["incomplete"] else ""))
    L += ["", "## 출원인 그룹", "", "| 그룹 | 대표 표기 | 기술신호 | 문헌 | 동향대상 | 국가 | 최초 | 비고 |", "|---|---|---|---|---|---|---|---|"]
    for g in st["groups"]:
        L.append("| %s | %s | %d | %d | %d | %s | %s | %s |" % (
            g["group"], g["display"], g["signals"], g["docs"], g["trend_docs"],
            ", ".join("%s %d" % kv for kv in sorted(g["countries"].items())), g["first_date"] or "",
            "신규 진입" if g["new_entrant"] else ""))
    L += ["", "## 시장 신호(특허로 읽히는 것만)", "",
          "- 기술신호별 진출 국가 수: " + ", ".join("%d개국 %d건" % kv for kv in st["family_coverage"].items()),
          "- 3개국 이상 진출 신호(그룹별): " + (", ".join("%s %d" % kv for kv in st["multi_country_signals_by_group"].items()) or "없음"),
          "- 국가별 진출 신호 수: " + ", ".join("%s %d" % kv for kv in sorted(st["country_targets"].items())),
          "- 주의: 특허 출원국은 '권리를 확보하려는 시장'의 신호일 뿐 매출·점유율이 아니다. 시장 규모·점유율은 외부 시장자료로 따로 확인.", ""]
    if st["clusters"]:
        L += ["## 기술군과 등급 후보(정독 전 계산값)", "", "| 기술군 | 기술신호 | 독립 그룹 | 그룹별 신호 | 등급 후보 | 비고 |", "|---|---|---|---|---|---|"]
        for c, d in sorted(st["clusters"].items(), key=lambda kv: -kv[1]["signals"]):
            L.append("| %s | %d | %d | %s | %s | %s |" % (c, d["signals"], d["independent_groups"],
                                                     ", ".join("%s %d" % kv for kv in d["per_group"].items()), d["grade_candidate"], d["note"]))
        L.append("")
    if st["scores"]:
        L += ["## 중요도 점수와 정밀분석 후보(최대 %d건)" % MAX_CANDIDATES, "",
              "| 순위 | ID | 번호 | 출원인 | 점수(환산) | 원점수/만점 | 추천 | 근거 |", "|---|---|---|---|---|---|---|---|"]
        for x in st["scores"]:
            L.append("| %d | %s | %s | %s | %.1f | %g/%d%s | %s | %s |" % (
                x["rank"], x["id"], x["number"], x["applicant"], x["scaled"], x["raw"], x["full"],
                " (근접성 미확정)" if x["proximity_pending"] else "", "●" if x["recommend"] else "", x["basis"] or x["reason"]))
        L.append("")
    if st["issues"]:
        L += ["## 확인할 것", ""] + ["- [%s %s] %s" % (i["level"], i["code"], i["msg"]) for i in st["issues"]]
    return "\n".join(L) + "\n"


def main():
    utf8_console()
    ap = argparse.ArgumentParser(description="공개특허 모집단 집계")
    ap.add_argument("intake")
    ap.add_argument("--clusters")
    ap.add_argument("--scores")
    ap.add_argument("--threshold", type=float, default=60.0)
    ap.add_argument("--scope", choices=["trend", "all"], default="trend")
    ap.add_argument("--out", default="work/02_stats.json")
    a = ap.parse_args()
    intake = json.loads(Path(a.intake).read_text(encoding="utf-8"))
    st = stats(intake, a.clusters, a.scores, a.threshold, a.scope)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    out.with_suffix(".md").write_text(to_markdown(st), encoding="utf-8")
    svg_trend(st, out.parent / "chart_trend.svg")
    svg_groups(st, out.parent / "chart_groups.svg")
    rec = sum(1 for x in st["scores"] if x["recommend"])
    print("범위 %d건 · 연도 %d개(미완결 시작 %s) · 그룹 %d · 기술군 %d · 점수 %d건 · 추천 %d건 · 확인 %d"
          % (st["scope_docs"], len(st["trend"]), st["lag_start_year"], len(st["groups"]), len(st["clusters"]),
             len(st["scores"]), rec, len(st["issues"])))
    print("저장:", out, "·", out.with_suffix(".md"), "· chart_trend.svg · chart_groups.svg")


if __name__ == "__main__":
    main()
