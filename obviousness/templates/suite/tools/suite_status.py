#!/usr/bin/env python3
"""사건 폴더 상태 점검·다음 단계 안내 — 청구항 분석 통합 오케스트레이터 v2 (핸드북 30~33). 표준 라이브러리만.

사건 폴더의 표준 파일을 보고 목적(purpose)별 단계 중 어디까지 왔는지, 관문(G1~G6)을 통과했는지,
다음에 어떤 스킬을 불러야 하는지 알려 줍니다. --run을 주면 각 단계의 점검 도구를 실제로 돌립니다.

  python tools/suite_status.py cases/example            # 상태만
  python tools/suite_status.py cases/example --run      # 점검 도구 실행 + work/reports/ 작성

사건 폴더 표준
  case.json                     목적·관할·특허·대상
  inbox/                        청구항·명세서·출원경과·제품/선행문헌 자료(원본)
  work/01_ledger.json           claim-decompose  — 한정 원장(claim_parse.py 출력을 사람이 확정)
  work/02_chart.json            claim-chart      — Claim Chart(침해·무효)
  work/03_construction.json     claim-construe   — 다툼 용어 해석표
  work/04_chart_construed.json  claim-construe   — 해석 반영 차트(apply_to_ledger.py가 생성)
  work/05_design_input.json     design-around    — 회피안 입력
  work/06_obviousness.json      obviousness      — 진보성 판단 재료(A/B/C 분류·차이점×기술상식·결합)
  work/reports/                 점검 결과
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FILES = {
    "ledger": "work/01_ledger.json",
    "chart": "work/02_chart.json",
    "construction": "work/03_construction.json",
    "construed": "work/04_chart_construed.json",
    "design": "work/05_design_input.json",
    "obviousness": "work/06_obviousness.json",
}

# 목적별 단계(순서대로). 각 단계: (키, 스킬, 설명, 산출 파일 키)
STAGES = {
    "infringement": [
        ("S1", "claim-decompose", "청구항 분해 → 한정 원장", "ledger"),
        ("S2", "claim-chart", "침해 Claim Chart 초안", "chart"),
        ("S3", "claim-construe", "다툼 용어 해석", "construction"),
        ("S4", "claim-construe", "해석 반영·차트 재점검", "construed"),
    ],
    "invalidity": [
        ("S1", "claim-decompose", "청구항 분해 → 한정 원장", "ledger"),
        ("S3", "claim-construe", "해석(절차별 기준) — 무효 차트 전에", "construction"),
        ("S6", "obviousness", "A/B/C 분류 → 차이점×기준일 기술상식 → 결합 논리", "obviousness"),
        ("S2", "claim-chart", "신규성·진보성 차트(--run이 06의 결합에서 생성)", "chart"),
        ("S4", "claim-construe", "해석 반영·차트 재점검", "construed"),
    ],
    "fto": [
        ("S1", "claim-decompose", "청구항 분해 → 한정 원장", "ledger"),
        ("S2", "claim-chart", "자사 제품 대비 차트", "chart"),
        ("S3", "claim-construe", "다툼 용어 해석", "construction"),
        ("S4", "claim-construe", "해석 반영·차트 재점검", "construed"),
        ("S5", "design-around", "회피안 평가(모든 독립항)", "design"),
    ],
    "construction": [
        ("S1", "claim-decompose", "청구항 분해 → 한정 원장", "ledger"),
        ("S3", "claim-construe", "다툼 용어 해석", "construction"),
    ],
}
STAGES["design-around"] = STAGES["fto"]
STAGES["obviousness"] = STAGES["invalidity"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def ids_of(doc):
    return [x["id"] for x in (doc or {}).get("limitations", [])]


def status(case_dir, run=False):
    case = load(os.path.join(case_dir, "case.json"))
    purpose = case.get("purpose", "infringement")
    if purpose not in STAGES:
        raise SystemExit("case.json purpose는 %s 중 하나여야 합니다." % ", ".join(sorted(STAGES)))
    p = {k: os.path.join(case_dir, v) for k, v in FILES.items()}
    have = {k: os.path.exists(v) for k, v in p.items()}
    docs = {k: load(v) for k, v in p.items() if have[k]}
    rep_dir = os.path.join(case_dir, "work", "reports")
    gates, notes = {}, []

    # 일관성(행 ID)
    if have["ledger"] and have["chart"]:
        miss = [i for i in ids_of(docs["ledger"]) if i not in ids_of(docs["chart"])]
        if miss:
            notes.append("원장 ID가 차트에 없음: %s — 차트는 원장 행을 모두 가져야 합니다." % ", ".join(miss))
    if have["construction"] and have["chart"]:
        bad = [t.get("ledger_id") for t in docs["construction"].get("terms", []) if t.get("ledger_id") not in ids_of(docs["chart"])]
        if bad:
            notes.append("해석표의 ledger_id가 차트에 없음: %s" % ", ".join(sorted(set(map(str, bad)))))

    if have["ledger"] and have["obviousness"]:
        miss = [i for i in ids_of(docs["ledger"]) if i not in ids_of(docs["obviousness"])]
        if miss:
            notes.append("원장 ID가 06_obviousness.json에 없음: %s — 진보성 대비도 원장 행을 모두 가져야 합니다." % ", ".join(miss))

    results = {}
    if run:
        os.makedirs(rep_dir, exist_ok=True)
        import construe_check as cc
        import apply_to_ledger as al
        import chart_lint as cl
        import design_around_eval as da
        import obviousness_check as oc
        if have["construction"]:
            e, w = cc.check(docs["construction"])
            with open(os.path.join(rep_dir, "construction_check.md"), "w", encoding="utf-8") as f:
                f.write(cc.report(docs["construction"], e, w))
            results["construction"] = (len(e), len(w))
        if have["obviousness"]:
            ob = oc.analyze(docs["obviousness"])
            with open(os.path.join(rep_dir, "obviousness.md"), "w", encoding="utf-8") as f:
                f.write(oc.report(docs["obviousness"], ob))
            clean = [c["id"] for c in ob["combos"] if not c["errors"]]
            results["obviousness"] = (len(ob["errors"]), len(ob["warnings"]), clean)
            pick = case.get("obviousness_combo") or (clean[0] if clean else None)
            if not have["chart"] and not ob["errors"] and pick:
                ch = oc.to_chart(docs["obviousness"], pick)
                with open(p["chart"], "w", encoding="utf-8") as f:
                    json.dump(ch, f, ensure_ascii=False, indent=2)
                docs["chart"], have["chart"] = ch, True
                notes.append("02_chart.json을 06의 결합 %s에서 새로 만들었습니다(obviousness_check --chart)." % pick)
        if have["chart"] and have["construction"] and not have["construed"]:
            out, impact = al.apply(docs["chart"], docs["construction"])
            with open(p["construed"], "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            with open(os.path.join(rep_dir, "impact.md"), "w", encoding="utf-8") as f:
                f.write(al.impact_md(impact, docs["construction"].get("meta", {})))
            docs["construed"], have["construed"] = out, True
            notes.append("04_chart_construed.json을 새로 만들었습니다(apply_to_ledger).")
        target = docs.get("construed") or docs.get("chart")
        if target:
            e, w = cl.lint(target)
            with open(os.path.join(rep_dir, "chart_lint.md"), "w", encoding="utf-8") as f:
                f.write(cl.report(target, e, w))
            review = sum(1 for r in target.get("rows", []) if r.get("needs_review"))
            results["chart"] = (len(e), len(w), review)
        if have["design"]:
            res, errs = da.evaluate(docs["design"], docs.get("construed"))
            with open(os.path.join(rep_dir, "design_around.md"), "w", encoding="utf-8") as f:
                f.write(da.report(docs["design"], res, errs))
            low = [r["id"] for r in res if r["result"]["us"]["overall"] == "LOW" and r["result"]["kr"]["overall"] == "LOW"]
            results["design"] = (len(errs), low)

    # 관문
    gates["G1 원장 확정"] = have["ledger"] and bool(case.get("ledger_approved"))
    if "construction" in results:
        gates["G2 해석 점검 오류 0"] = results["construction"][0] == 0
    if "obviousness" in results:
        gates["G6 진보성 점검 오류 0"] = results["obviousness"][0] == 0
    if "chart" in results:
        gates["G3 차트 오류 0 · 재검토 0"] = results["chart"][0] == 0 and results["chart"][2] == 0
    if "design" in results:
        gates["G4 모든 독립항 LOW인 회피안"] = results["design"][0] == 0 and bool(results["design"][1])
    gates["G5 사람 최종 검토"] = bool(case.get("human_signoff"))

    # 다음 단계
    nxt = None
    for sid, skill, desc, key in STAGES[purpose]:
        if not have[key]:
            nxt = (sid, skill, desc, FILES[key])
            break
    if nxt and nxt[3] == FILES["chart"] and results.get("obviousness", (0,))[0]:
        nxt = ("G6", "obviousness", "진보성 점검 오류를 고쳐야 진보성 차트를 만들 수 있습니다(work/reports/obviousness.md)", FILES["obviousness"])
    if nxt is None:
        if not gates["G1 원장 확정"]:
            nxt = ("G1", "claim-decompose", "원장을 사람이 확인하고 case.json에 ledger_approved: true", FILES["ledger"])
        elif results.get("construction", (0,))[0]:
            nxt = ("G2", "claim-construe", "해석 점검 오류를 고치세요(work/reports/construction_check.md)", FILES["construction"])
        elif results.get("obviousness", (0,))[0]:
            nxt = ("G6", "obviousness", "진보성 점검 오류를 고치세요(work/reports/obviousness.md)", FILES["obviousness"])
        elif results.get("chart") and (results["chart"][0] or results["chart"][2]):
            nxt = ("G3", "claim-chart", "차트 오류·'재검토' 행을 고치세요(work/reports/chart_lint.md, impact.md)", FILES["construed"])
        elif "design" in results and not gates.get("G4 모든 독립항 LOW인 회피안"):
            nxt = ("G4", "design-around", "모든 독립항이 LOW인 회피안(결합안 포함)을 찾으세요(work/reports/design_around.md)", FILES["design"])
        elif not gates["G5 사람 최종 검토"]:
            nxt = ("G5", "claim-suite", "변리사·변호사 검토 후 case.json에 human_signoff: true, out/에 최종 보고", "out/")
        else:
            nxt = ("DONE", "-", "모든 단계·관문 통과", "-")
    return {"case": case, "purpose": purpose, "have": have, "gates": gates, "results": results, "notes": notes, "next": nxt}


def to_md(st):
    c = st["case"]
    out = ["# 사건 상태 — %s" % c.get("title", c.get("patent", "?")), "",
           "- 목적: %s · 관할: %s · 특허: %s · 대상: %s" % (st["purpose"], c.get("forum", "?"), c.get("patent", "?"), c.get("target", "?")), "",
           "## 단계", "| 단계 | 스킬 | 할 일 | 파일 | 상태 |", "|---|---|---|---|---|"]
    for sid, skill, desc, key in STAGES[st["purpose"]]:
        out.append("| %s | %s | %s | `%s` | %s |" % (sid, skill, desc, FILES[key], "있음" if st["have"][key] else "—"))
    out += ["", "## 관문"]
    for g, ok in st["gates"].items():
        out.append("- %s %s" % ("통과" if ok else "미통과", g))
    if st["results"]:
        out += ["", "## 점검 결과"]
        r = st["results"]
        if "construction" in r:
            out.append("- 해석 점검: 오류 %d · 경고 %d" % r["construction"])
        if "chart" in r:
            out.append("- 차트 점검: 오류 %d · 경고 %d · 재검토 행 %d" % r["chart"])
        if "obviousness" in r:
            out.append("- 진보성 점검: 오류 %d · 경고 %d · 오류 없는 결합: %s" % (r["obviousness"][0], r["obviousness"][1], ", ".join(r["obviousness"][2]) or "없음"))
        if "design" in r:
            out.append("- 회피안: 입력 오류 %d · 미국·한국 모두 LOW: %s" % (r["design"][0], ", ".join(r["design"][1]) or "없음"))
    if st["notes"]:
        out += ["", "## 메모"] + ["- " + n for n in st["notes"]]
    sid, skill, desc, f = st["next"]
    out += ["", "## 다음 할 일", "**[%s] %s** — 스킬 `%s` · 파일 `%s`" % (sid, desc, skill, f)]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="사건 폴더 상태 점검·다음 단계 안내")
    ap.add_argument("case_dir")
    ap.add_argument("--run", action="store_true", help="점검 도구를 실행하고 work/reports/에 결과 저장")
    a = ap.parse_args(argv)
    st = status(a.case_dir, a.run)
    md = to_md(st)
    if a.run:
        with open(os.path.join(a.case_dir, "work", "reports", "status.md"), "w", encoding="utf-8") as f:
            f.write(md)
    sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
