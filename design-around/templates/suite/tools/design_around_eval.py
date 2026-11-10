#!/usr/bin/env python3
"""회피설계안 위험 평가기 (핸드북 32). 표준 라이브러리만.

회피안(options)마다, 모든 독립항에 대해 '문언 → 균등 제한 법리 → 균등 판단' 순서로
공개된 규칙을 적용해 위험(LOW / MED / HIGH)을 매깁니다. 미국(us)·한국(kr) 기준을 함께 냅니다.
판단 재료(작동 방식 차이, 포기 영역 여부 등)는 사람이 근거와 함께 입력하고, 도구는 집계·누락 점검만 합니다.

  python tools/design_around_eval.py sample/design_input.json
  python tools/design_around_eval.py sample/design_input.json --chart ../31편/chart_construed.json --out work/da_report.md
종료 코드: 입력 오류(E)가 있으면 1
"""
import argparse
import json
import sys

ORDER = {"LOW": 0, "MED": 1, "HIGH": 2}


def worst(*levels):
    return max(levels, key=lambda x: ORDER[x])


def best(levels):
    return min(levels, key=lambda x: ORDER[x]) if levels else "HIGH"


def eval_change(ch, lim, forum):
    """한 한정에 대한 한 변경의 위험과 이유 목록."""
    why = []
    # 1) 문언
    literal = ch.get("literal_met_after", True)
    if forum == "kr" and "literal_met_after" in ch.get("kr", {}):
        literal = ch["kr"]["literal_met_after"]
    if literal:
        if forum == "kr" and ch.get("kr", {}).get("free_art_whole_product"):
            return "LOW", ["자유실시기술: 확인대상 제품 전체가 공지기술(또는 그로부터 쉽게 실시)이면 문언침해 사안에도 권리범위 밖(2016후366)"]
        return "HIGH", ["문언 충족이 남음 — 이 변경으로는 이 한정을 벗어나지 못함"]
    why.append("문언 회피")
    if forum == "us" and lim.get("type") == "mpf" and ch.get("structure_disclosed_in_spec"):
        return "HIGH", ["기능식 한정: 명세서에 개시된 대응 구조(또는 그 구조적 균등물)는 문언 범위 안 — '명세서에 쓰였으니 헌납'이 아님"]
    # 2) 균등 제한 법리(먼저 본다)
    bars = []
    if forum == "us":
        if ch.get("in_surrendered_territory"):
            if (lim.get("amended_narrowing") or lim.get("argument_estoppel")) and lim.get("amendment_reason") == "patentability":
                if ch.get("rebuttal_risk"):
                    why.append("출원경과 금반언 추정 — 다만 번복 가능성(%s) 있어 한 단계 높임" % ch["rebuttal_risk"])
                    bars.append("MED")
                else:
                    bars.append("LOW")
                    why.append("출원경과 금반언: 특허성 관련 축소 보정·의견 진술로 생긴 포기 영역 안(Festo)")
        if ch.get("disclosed_unclaimed") and lim.get("type") != "mpf":
            bars.append("LOW"); why.append("공중헌납: 명세서에 개시하고 청구하지 않은 대안(Johnson & Johnston)")
        if ch.get("ensnares_prior_art"):
            bars.append("LOW"); why.append("가상 청구항이 선행기술을 포섭 — 균등 범위 밖(Wilson Sporting Goods)")
    else:
        k = ch.get("kr", {})
        if k.get("consciously_excluded"):
            bars.append("LOW"); why.append("의식적 제외: 출원경과 제반 사정상 제외 의사 인정(2014후638)")
        if k.get("free_art_whole_product"):
            bars.append("LOW"); why.append("자유실시기술(제품 전체 기준)")
    if ch.get("antithetical"):
        bars.append("LOW"); why.append("정반대 개념으로의 치환 — 균등을 인정하면 한정이 무의미해짐(형해화)")
    if ch.get("function_removed") and not ch.get("function_moved_to"):
        bars.append("LOW"); why.append("한정과 그 기능을 함께 제거 — 대응 구성·균등물 자체가 없음(Pennwalt)")
    if bars:
        return best(bars), why
    # 3) 균등 판단
    if ch.get("function_moved_to"):
        why.append("제거한 기능을 다른 부품(%s)이 수행 — 균등물은 제품 어딘가에 있으면 족함" % ch["function_moved_to"])
    if forum == "us":
        if ch.get("known_interchangeable"):
            return "HIGH", why + ["알려진 상호교환 가능성 — 균등의 강한 증거"]
        if ch.get("way_differs"):
            if (ch.get("way_evidence") or "").strip():
                return "LOW", why + ["작동 방식(Way)이 실질적으로 다름 + 근거(%s)" % ch["way_evidence"]]
            return "MED", why + ["작동 방식이 다르다고 했으나 근거(시험·도면·자료) 없음"]
        return "HIGH", why + ["기능·방식·결과가 실질적으로 같을 가능성"]
    k = ch.get("kr", {})
    if k.get("solution_principle_differs"):
        return "LOW", why + ["과제해결원리가 다름(공지기술 참작, 2018다267252·2017후424)"]
    if k.get("easy_substitution", True) and not ch.get("way_differs"):
        return "HIGH", why + ["과제해결원리 동일·작용효과 동일·치환 용이 가능성"]
    return "MED", why + ["균등 요건 일부 다툼 여지 — 근거 보강 필요"]


def evaluate(doc, chart=None):
    errs = []
    claims = doc.get("claims", [])
    lims = {l["id"]: l for c in claims for l in c.get("limitations", [])}
    chart_lims = {l["id"]: l for l in (chart or {}).get("limitations", [])}
    chart_rows = {r["id"]: r for r in (chart or {}).get("rows", [])}
    for c in claims:
        for l in c.get("limitations", []):
            if l["id"] in chart_lims and chart_lims[l["id"]].get("construction") and l.get("construction") \
                    and l["construction"] != chart_lims[l["id"]]["construction"]:
                errs.append(("E10", l["id"], "회피안이 기댄 해석이 31편 해석과 다름 — 침해·회피에 같은 해석을 써야 합니다."))
    results = []
    for op in doc.get("options", []):
        notes = []
        for ch in op.get("changes", []):
            lid = ch.get("limitation")
            if lid not in lims:
                errs.append(("E01", op["id"], "없는 한정 ID: %s" % lid)); continue
            lim = lims[lid]
            if ch.get("in_surrendered_territory") and not (lim.get("amended_narrowing") or lim.get("argument_estoppel")):
                errs.append(("E05", op["id"], "%s: 포기 영역이라 했으나 원장에 축소 보정·의견 진술 기록이 없음" % lid))
            if ch.get("way_differs") and not (ch.get("way_evidence") or "").strip():
                notes.append("W08 %s: 작동 방식 차이의 근거(시험 데이터·도면)를 준비하세요." % lid)
            if chart_rows.get(lid, {}).get("needs_review"):
                notes.append("W12 %s: 31편에서 '재검토' 표시된 한정 — 해석·사실 확정 전에는 회피 근거로 쓰기 이릅니다." % lid)
            if lim.get("type") == "mpf" and ch.get("after_arising_tech"):
                notes.append("W06 %s: 등록 뒤 등장한 기술이면 §112(f) 구조적 균등이 아니어도 균등론 판단은 남습니다." % lid)
            if lim.get("type") == "negative" and ch.get("action") == "add_absent_feature":
                notes.append("I %s: 부정한정('…없이')은 그 구성을 추가하는 것만으로 문언을 벗어날 수 있습니다 — 추가 구성이 실제로 작동하는지 확인." % lid)
        per = {}
        for forum in ("us", "kr"):
            claim_risk = {}
            for c in claims:
                if not c.get("independent", True):
                    continue
                levels, reasons = [], []
                for ch in op.get("changes", []):
                    if ch.get("limitation") in [l["id"] for l in c.get("limitations", [])]:
                        lv, why = eval_change(ch, lims[ch["limitation"]], forum)
                        levels.append(lv)
                        reasons.append("[%s] %s: %s" % (ch["limitation"], lv, "; ".join(why)))
                if not levels:
                    claim_risk[c["claim"]] = ("HIGH", ["이 독립항의 어떤 한정도 건드리지 않음 — 다른 한정이 모두 충족되면 침해"])
                else:
                    claim_risk[c["claim"]] = (best(levels), reasons)
            overall = worst(*[v[0] for v in claim_risk.values()]) if claim_risk else "HIGH"
            per[forum] = {"overall": overall, "claims": claim_risk}
        if doc.get("meta", {}).get("pending_family"):
            notes.append("W11 계속출원·분할출원이 살아 있음 — 이 회피안을 겨냥한 새 청구항이 나올 수 있으니 패밀리를 감시하세요.")
        results.append({"id": op["id"], "name": op.get("name", ""), "result": per, "notes": notes,
                        "business": op.get("business", "")})
    return results, errs


def report(doc, results, errs):
    m = doc.get("meta", {})
    out = ["# 회피설계안 위험 평가 — %s" % m.get("patent", "?"), "",
           "- 대상 제품: %s · 단계: %s" % (m.get("product", "?"), m.get("stage", "?")),
           "- 규칙: 문언 → 균등 제한 법리(금반언·헌납·선행기술·형해화·기능 제거) → 균등 판단. 독립항마다 가장 낮은 위험의 회피 경로, 회피안 전체는 가장 높은 독립항 위험.", ""]
    if errs:
        out += ["## 입력 오류"] + ["- %s [%s] %s" % e for e in errs] + [""]
    out += ["| 회피안 | 미국 | 한국 | 사업 메모 |", "|---|---|---|---|"]
    for r in results:
        out.append("| %s %s | **%s** | **%s** | %s |" % (r["id"], r["name"], r["result"]["us"]["overall"],
                                                       r["result"]["kr"]["overall"], r["business"].replace("|", "/")))
    for r in results:
        out += ["", "## %s %s" % (r["id"], r["name"])]
        for forum, lab in (("us", "미국"), ("kr", "한국")):
            out.append("- **%s: %s**" % (lab, r["result"][forum]["overall"]))
            for cl, (lv, reasons) in r["result"][forum]["claims"].items():
                out.append("  - 청구항 %s → %s" % (cl, lv))
                for x in reasons:
                    out.append("    - " + x)
        for n in r["notes"]:
            out.append("- " + n)
    out += ["", "위험 등급은 입력된 판단 재료를 공개 규칙으로 집계한 것이며 법적 결론이 아닙니다. 채택안은 설계 동결 전에 변리사·변호사의 비침해 의견으로 확인하세요."]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="회피설계안 위험 평가")
    ap.add_argument("design_json")
    ap.add_argument("--chart", help="31편 해석 반영 차트(chart_construed.json) — 해석 일치·재검토 행 확인")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    with open(a.design_json, encoding="utf-8") as f:
        doc = json.load(f)
    chart = None
    if a.chart:
        with open(a.chart, encoding="utf-8") as f:
            chart = json.load(f)
    results, errs = evaluate(doc, chart)
    rep = report(doc, results, errs)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(rep)
    sys.stdout.write(rep)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
