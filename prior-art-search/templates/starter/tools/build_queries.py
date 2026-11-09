#!/usr/bin/env python3
"""개념 조사식(plan.json) → DB별 검색식 변환 (핸드북 28). 표준 라이브러리만 사용.

한 번 만든 '개념 조사식'을 KIPRIS·Google Patents·Espacenet·PATENTSCOPE 문법으로 자동 변환합니다.
DB마다 손으로 다시 쓰면 문법 오류가 나고 결과 비교가 어렵기 때문입니다. 네트워크는 쓰지 않습니다(식만 생성).

  python tools/build_queries.py plan.json                 # 화면으로
  python tools/build_queries.py plan.json --sheet work/search_sheet.md

plan.json(요지):
  { "title","cutoff_date":"YYYYMMDD",
    "features":[{"id":"F1","ko":["스크루"],"en":["screw","auger"],"core":true?}],
    "classes":{"cpc":["A47J19/025"]},
    "queries":[{"id":"Q1","features":["F1","F3"],"field":"ta","near":10?,"use_class":true?}] }

필드: ta(명칭+요약)·title·abstract·claims. 언어: KIPRIS=한국어, 그 외=영어.
날짜: 신규성용은 cutoff 이전으로 자동 한정. KR은 cutoff 없는 식도 함께 만듭니다(확대된 선출원·선출원 검토용).

주의: DB 문법·URL·내보내기 한도는 바뀔 수 있습니다. 첫 사용 때 각 DB에서 식이 실제로 실행되는지 확인하세요.
      웹 DB(Google·Espacenet·PATENTSCOPE·KIPRIS 웹)는 약관상 자동 수집을 하지 않습니다 — 링크/식을 사람이 실행합니다.
"""
import argparse
import json
import sys
import urllib.parse
from pathlib import Path

# DB별 문법 (원고 문법표 기준)
DB = {
    # quote=True: 여러 단어로 된 표현(예: juice extractor)을 큰따옴표로 감싸 구문 검색(개선 제안 반영)
    "KIPRIS": {"and": "*", "or": "+", "near": "^{n}", "quote": False,
               "field": {"ta": ("TL=[", "]"), "title": ("TL=[", "]"), "abstract": ("AB=[", "]"), "claims": ("CL=[", "]")},
               "lang": "ko"},
    "GooglePatents": {"and": " AND ", "or": " OR ", "near": " NEAR/{n} ", "quote": True,
                      "field": {"ta": ("TAC=(", ")"), "title": ("TI=(", ")"), "abstract": ("AB=(", ")"), "claims": ("CL=(", ")")},
                      "lang": "en"},
    "Espacenet": {"and": " and ", "or": " or ", "near": " prox/distance<{n} ", "quote": True,
                  "field": {"ta": ("ta=(", ")"), "title": ("ti=(", ")"), "abstract": ("ab=(", ")"), "claims": ("ta=(", ")")},
                  "lang": "en"},
    "PATENTSCOPE": {"and": " AND ", "or": " OR ", "near": " NEAR{n} ", "quote": True,
                    "field": {"ta": ("EN_AB:(", ")"), "title": ("EN_TI:(", ")"), "abstract": ("EN_AB:(", ")"), "claims": ("EN_CL:(", ")")},
                    "lang": "en"},
}


def kw(feat, lang):
    return feat.get(lang) or feat.get("en") or feat.get("ko") or [feat["id"]]


def group(feat, db, lang):
    """한 특징 = 키워드들의 OR 묶음. quote=True면 여러 단어 표현을 큰따옴표로 감싼다."""
    words = kw(feat, lang)
    if db.get("quote"):
        words = ['"{}"'.format(w) if " " in w else w for w in words]
    return "(" + db["or"].join(words) + ")"


def build_one(q, feats, db, cpc, cutoff, with_date):
    lang = db["lang"]
    groups = [group(feats[fid], db, lang) for fid in q["features"]]
    # 근접(near)은 두 그룹을 근접 연산자로, 아니면 AND
    if q.get("near") and len(groups) >= 2:
        near = db["near"].format(n=q["near"])
        body = groups[0] + near + db["and"].join(groups[1:]) if len(groups) > 2 else near.join(groups[:2])
    else:
        body = db["and"].join(groups)
    field = q.get("field", "ta")
    # KIPRIS에서 ta(명칭+요약)는 TL과 AB에 같은 식을 넣어 OR 결합(개선 제안 반영)
    if db is DB["KIPRIS"] and field == "ta":
        expr = "TL=[" + body + "]" + db["or"] + "AB=[" + body + "]"
    else:
        pre, post = db["field"][field]
        expr = pre + body + post
    if q.get("use_class") and cpc:
        expr = expr + db["and"] + "CPC=" + cpc[0] if db is DB["GooglePatents"] else expr
    if with_date and cutoff:
        # 날짜 한정(문법표): KIPRIS는 화면 항목칸이라 식에 주석으로, 그 외는 식/URL에서 처리
        pass
    return expr


def open_url(db_name, expr, cutoff):
    e = urllib.parse.quote(expr)
    if db_name == "GooglePatents":
        u = "https://patents.google.com/?q=" + e
        if cutoff:
            u += "&before=publication:" + cutoff
        return u
    if db_name == "Espacenet":
        return "https://worldwide.espacenet.com/patent/search?q=" + e
    if db_name == "PATENTSCOPE":
        return "https://patentscope.wipo.int/search/en/result.jsf?query=" + e
    return ""  # KIPRIS 웹은 공개 검색 URL 형식 미확인 → 식을 붙여넣기


def build_all(plan):
    feats = {f["id"]: f for f in plan["features"]}
    cpc = plan.get("classes", {}).get("cpc", [])
    cutoff = str(plan.get("cutoff_date", ""))
    out = {}
    for db_name, db in DB.items():
        rows = []
        for q in plan["queries"]:
            expr = build_one(q, feats, db, cpc, cutoff, with_date=True)
            rows.append({"id": q["id"], "purpose": q.get("purpose", ""), "expr": expr,
                         "url": open_url(db_name, expr, cutoff)})
        out[db_name] = rows
    # KR 확대선출원용: cutoff 없는 KIPRIS 식
    kr_nolimit = []
    for q in plan["queries"]:
        kr_nolimit.append({"id": q["id"] + "-nolimit",
                           "expr": build_one(q, feats, DB["KIPRIS"], cpc, "", with_date=False)})
    out["_KR_no_cutoff"] = kr_nolimit
    return out, cutoff


def to_sheet(plan, out, cutoff):
    L = ["# 검색 시트 — {}".format(plan.get("title", "")), "",
         "- 기준일(cutoff): {} · 신규성용 식은 이 날짜 이전으로 한정".format(cutoff or "(없음)"),
         "- 웹 DB는 약관상 자동 수집 금지 — 링크를 사람이 열고 결과 CSV를 `imports/`에 저장합니다.", ""]
    for db_name in ["KIPRIS", "GooglePatents", "Espacenet", "PATENTSCOPE"]:
        L.append("## {}".format(db_name))
        for r in out[db_name]:
            L.append("- **{}** {}".format(r["id"], r.get("purpose", "")))
            L.append("  - 식: `{}`".format(r["expr"]))
            if r["url"]:
                L.append("  - 열기: {}".format(r["url"]))
            else:
                L.append("  - 열기: (KIPRIS 웹 검색식 칸에 위 식을 붙여넣기)")
        L.append("")
    L.append("## KR 확대된 선출원·선출원 검토용 (cutoff 없이)")
    for r in out["_KR_no_cutoff"]:
        L.append("- `{}`".format(r["expr"]))
    L.append("")
    L.append("> 문법·URL·내보내기 한도는 바뀔 수 있습니다. 첫 사용 때 각 DB에서 실제 실행을 확인하세요.")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="개념 조사식 → DB별 검색식")
    ap.add_argument("plan")
    ap.add_argument("--sheet")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    out, cutoff = build_all(plan)
    if a.json:
        sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
        return 0
    sheet = to_sheet(plan, out, cutoff)
    sys.stdout.write(sheet)
    if a.sheet:
        Path(a.sheet).parent.mkdir(parents=True, exist_ok=True)
        Path(a.sheet).write_text(sheet, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
