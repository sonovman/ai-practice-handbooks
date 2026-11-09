#!/usr/bin/env python3
"""구성대비 결과(mapping.json) → 최근접 선행문헌 산정 (핸드북 28). 표준 라이브러리만 사용.

판단(개시 여부·동일 분야/과제·차이 극복 난이도)은 사람·AI가 mapping.json에 '근거와 함께' 적고,
이 도구는 그 판단을 '같은 규칙으로' 집계해 순위·분류·결합 경로를 만듭니다(재현·검토 가능).
AI가 "이게 가장 비슷하다"고 한 번에 결론 내리면 근거 검증이 안 되므로, 판단과 집계를 나눕니다.

  python tools/rank_closest.py plan.json mapping.json
  python tools/rank_closest.py plan.json mapping.json --report work/closest.md --min-coverage 0.6

분류
  A 신규성 부정 후보 : 모든 특징 ●, 저해요인 없음, 기준일 전 공개
  B 주인용발명 후보  : 같은 분야 또는 같은 과제 + 가중 개시율 ≥ --min-coverage, 저해요인 없음
  C 보조 문헌        : 상위 B의 부족 특징을 ●로 개시
  X 기준일 이후 공개 : 선행문헌 자격 없음(확대된 선출원 검토 대상으로 따로 표시)
점수(B 순위) = 100 × 관련성 × (1 − 수정부담/총가중치)
  관련성: 분야·과제 둘 다 1.0 / 하나 0.8 / 없음 0.5
  개시도: ● 1 · ◐ 0.5 · ○ 0      수정부담 = Σ 가중치 × (1−개시도) × 난이도
  난이도: design 0.25 · secondary 0.5 · hard 1.0 (미기재 시 다른 문헌이 ●면 0.5, 아니면 1.0)

주의: 점수는 mapping.json 판단의 집계일 뿐 법적 결론이 아닙니다. 효과의 현저성 등은 보고서에서 따로 검토하세요.
      근거 위치(evidence) 없이 ●·◐를 적으면 산정이 중단됩니다(사후고찰 방지).
"""
import argparse
import json
import sys
from pathlib import Path

GRADE = {"●": 1.0, "◐": 0.5, "○": 0.0}
DIFF = {"design": 0.25, "secondary": 0.5, "hard": 1.0}


def load(plan_p, map_p):
    plan = json.loads(Path(plan_p).read_text(encoding="utf-8"))
    mp = json.loads(Path(map_p).read_text(encoding="utf-8"))
    fids = [f["id"] for f in plan["features"]]
    errs = []
    for d in mp["documents"]:
        for fid in fids:
            e = d.get("features", {}).get(fid)
            if e is None:
                errs.append("{}: {} 대비 누락".format(d["pub"], fid)); continue
            if e.get("grade") not in GRADE:
                errs.append("{}: {} grade는 ●/◐/○".format(d["pub"], fid))
            elif GRADE[e["grade"]] > 0 and not e.get("evidence"):
                errs.append("{}: {} 근거 위치(evidence) 없음".format(d["pub"], fid))
    if errs:
        raise SystemExit("mapping.json 검증 실패:\n - " + "\n - ".join(errs))
    return plan, mp, fids


def rank(plan, mp, fids, min_coverage=0.6, top=3):
    feats = {f["id"]: f for f in plan["features"]}
    w = {k: float(feats[k].get("weight", 3 if feats[k].get("core") else 1)) for k in fids}
    wsum = sum(w.values())
    cutoff = str(plan.get("cutoff_date", ""))
    docs = mp["documents"]

    def late(d):
        return bool(cutoff and str(d.get("publication_date", "")) >= cutoff)

    full_by_feat = {k: [d["pub"] for d in docs if GRADE[d["features"][k]["grade"]] == 1.0 and not late(d)] for k in fids}

    res = []
    for d in docs:
        g = {k: GRADE[d["features"][k]["grade"]] for k in fids}
        cov = sum(w[k] * g[k] for k in fids) / wsum
        effort, gaps = 0.0, []
        for k in fids:
            if g[k] >= 1.0:
                continue
            e = d["features"][k]
            others = [p for p in full_by_feat[k] if p != d["pub"]]
            diff = DIFF.get(e.get("gap_type"), 0.5 if others else 1.0)
            effort += w[k] * (1 - g[k]) * diff
            gaps.append({"feature": k, "grade": e["grade"], "difficulty": diff, "secondary": others,
                         "note": e.get("gap_note", "")})
        rel = {2: 1.0, 1: 0.8, 0: 0.5}[int(bool(d.get("same_field"))) + int(bool(d.get("same_problem")))]
        score = round(100 * rel * (1 - effort / wsum), 1)
        ta = bool(d.get("teaching_away"))
        if late(d):
            cls = "X 기준일 이후 공개"
        elif all(v == 1.0 for v in g.values()) and not ta:
            cls = "A 신규성 부정 후보"
        elif (d.get("same_field") or d.get("same_problem")) and cov >= min_coverage and not ta:
            cls = "B 주인용발명 후보"
        else:
            cls = "-"
        res.append(dict(pub=d["pub"], title=d.get("title", ""), date=d.get("publication_date", ""), cls=cls,
                        coverage=round(cov, 3), relevance=rel, effort=round(effort, 2), score=score,
                        teaching_away=ta, gaps=gaps, grades={k: d["features"][k]["grade"] for k in fids}))
    order = {"A": 0, "B": 1, "-": 2, "X": 3}
    res.sort(key=lambda r: (order[r["cls"][0]], -r["score"], -r["coverage"]))
    # 보조 문헌(C): 상위 A/B의 부족 특징을 ●로 메우는 문헌
    sec = set()
    for r in [x for x in res if x["cls"][0] in "AB"][:top]:
        for gp in r["gaps"]:
            sec.update(gp["secondary"])
    for r in res:
        if r["cls"] == "-" and r["pub"] in sec:
            r["cls"] = "C 보조 문헌"
    return res, w, cutoff


def to_markdown(plan, res, w, cutoff, fids):
    L = ["# 최근접 선행문헌 분석 — {}".format(plan.get("title", "")), "",
         "- 기준일(cutoff): {} · 특징 가중치: {}".format(cutoff or "(없음)", ", ".join("{}={:g}".format(k, w[k]) for k in fids)), "",
         "| 순위 | 문헌 | 분류 | 점수 | 가중개시율 | 관련성 | " + " | ".join(fids) + " |",
         "|---|---|---|---:|---:|---:|" + "|".join(["---"] * len(fids)) + "|"]
    for i, r in enumerate(res, 1):
        L.append("| {} | {} | {} | {} | {:.0%} | {:g} | {} |".format(
            i, r["pub"], r["cls"], r["score"] if r["cls"][0] != "X" else "–", r["coverage"], r["relevance"],
            " | ".join(r["grades"][k] for k in fids)))
    L.append("")
    b = [r for r in res if r["cls"].startswith("B")]
    if b:
        top = b[0]
        gapline = ", ".join("{}({})".format(g["feature"], g["grade"]) for g in top["gaps"]) or "없음"
        L += ["## 주인용 후보: {}".format(top["pub"]),
              "- 부족 특징: {}".format(gapline)]
        for g in top["gaps"]:
            if g["secondary"]:
                L.append("- 결합 경로: {}를 {}로 보완 가능".format(g["feature"], "·".join(g["secondary"])))
        L.append("")
    L += ["> 점수는 mapping.json 판단의 집계일 뿐 법적 결론이 아닙니다. 효과의 현저성·청구항 해석은 따로 검토하세요.",
          "> 저해요인(teaching away) 문헌은 주인용 후보에서 제외됩니다. 기준일 이후 공개는 확대된 선출원 검토 대상입니다."]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="최근접 선행문헌 산정")
    ap.add_argument("plan")
    ap.add_argument("mapping")
    ap.add_argument("--min-coverage", type=float, default=0.6)
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--report")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    plan, mp, fids = load(a.plan, a.mapping)
    res, w, cutoff = rank(plan, mp, fids, a.min_coverage, a.top)
    if a.json:
        sys.stdout.write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
        return 0
    md = to_markdown(plan, res, w, cutoff, fids)
    sys.stdout.write(md)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
