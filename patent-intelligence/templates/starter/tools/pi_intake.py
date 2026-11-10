#!/usr/bin/env python3
"""1단계 자료 검증 (핸드북 34). WIPSON 엑셀/CSV → 정리된 문헌 목록 + 검증 보고.

  python tools/pi_intake.py inbox/this_round.xlsx --project config/project.json \
      --previous inbox/prev_round.xlsx --pdf-dir inbox/pdf --out work/01_intake.json

하는 일 (계산은 도구, 판단은 사람·AI):
  - 열 이름 별칭으로 표준 필드에 맞추기, 국가·권리유형(발명/실용/디자인)·단계(공개/등록) 판정
  - 같은 출원번호 중복 합치기, 공개·등록번호 둘 다 없는 문헌 표시(핵심근거 불가)
  - 출원인 정규화(별칭표) → 그룹(계열사 묶음)·영문명·영문명 상태
  - 패밀리 묶기(패밀리번호 → 우선권번호 → 단독)
  - 중국 발명·실용신안 병행출원 '후보' 찾기(확정은 사람)
  - 이번 회차 신규 관측(신규 표시 열 또는 직전 회차 목록과 비교)
  - 기술동향 분석대상(공개·등록일 ≥ 기준일) 분리
  - 공개 지연 구간(자료일 기준 최근 18개월 출원) 표시
  - 공보 PDF 파일과 번호 대조 → 누락 공보 목록
"""
import argparse
import csv
import json
import os
import re
from collections import defaultdict
from pathlib import Path

from pi_common import (compact, doc_type, jaccard, kind_code, load_aliases, months_between,
                       norm_country, parse_date, read_table, tokens, utf8_console)

HERE = Path(__file__).resolve().parent
DEFAULT_ALIASES = HERE.parent / "config" / "column_aliases.csv"
DEFAULT_APPLICANTS = HERE.parent / "config" / "applicant_aliases.csv"
TRUTHY = {"y", "yes", "o", "v", "1", "true", "신규", "new", "●", "○", "✓", "√", "*"}


def load_applicants(path):
    table = {}
    if path and os.path.exists(path):
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                v = (row.get("variant") or "").strip()
                if v:
                    table[_akey(v)] = {k: (row.get(k) or "").strip() for k in
                                       ("canonical", "group", "english_official", "english_status", "source")}
    return table


def _akey(name):
    s = str(name).upper()
    s = re.sub(r"\(주\)|주식회사|㈜|CO\.?|LTD\.?|INC\.?|CORP\.?|CORPORATION|GMBH|株式会社|有限公司", "", s)
    return re.sub(r"[^0-9A-Z가-힣ぁ-んァ-ン一-龥]", "", s)


def split_applicants(s):
    parts = re.split(r"\s*[;|\n]\s*|\s*,\s*(?=[가-힣A-Z一-龥ぁ-んァ-ン])", str(s or ""))
    return [p.strip() for p in parts if p.strip()]


def resolve_applicant(raw, raw_en, rep, table):
    names = split_applicants(raw) or ["(출원인 없음)"]
    first = names[0]
    hit = table.get(_akey(first)) or (table.get(_akey(rep)) if rep else None)
    if hit:
        canon = hit["canonical"] or first
        group = hit["group"] or canon
        en = hit["english_official"]
        status = hit["english_status"] or ("official" if en else "unverified")
    else:
        canon = rep or first
        group = canon
        en = ""
        status = "unverified"
        if raw_en:
            en = split_applicants(raw_en)[0]
            status = "data_provided"  # WIPSON 등 데이터 제공 영문명 — 공식 여부 확인 필요
        elif re.fullmatch(r"[0-9A-Z .,&'\-()]+", first.upper()) and re.search(r"[A-Z]", first.upper()):
            en = first
            status = "official_original"  # 원문 자체가 영문
    return {"applicants": names, "applicant_canon": canon, "group": group,
            "applicant_en": en, "en_status": status, "alias_hit": bool(hit)}


def display_applicant(rec):
    st = rec["en_status"]
    if st in ("official", "official_original"):
        return "%s (%s)" % (rec["applicant_canon"], rec["applicant_en"]) if rec["applicant_en"] != rec["applicant_canon"] else rec["applicant_canon"]
    if st == "unofficial":
        return "%s (%s · 비공식 번역)" % (rec["applicant_canon"], rec["applicant_en"])
    if st == "data_provided":
        return "%s (%s · 데이터 제공 영문명, 공식 확인 필요)" % (rec["applicant_canon"], rec["applicant_en"])
    return "%s (영문명 미확인)" % rec["applicant_canon"]


def is_truthy(v):
    return str(v or "").strip().lower() in TRUTHY


def load_previous(path, aliases, sheet=None):
    _, _, _, rows = read_table(path, aliases, sheet)
    keys = set()
    for r in rows:
        c = norm_country(r.get("country"), r.get("app_no"), r.get("pub_no"), r.get("reg_no"))
        if r.get("app_no"):
            keys.add((c, compact(r.get("app_no"))))
    return keys


def pdf_index(pdf_dir):
    idx = {}
    if pdf_dir and os.path.isdir(pdf_dir):
        for name in os.listdir(pdf_dir):
            if name.lower().endswith(".pdf"):
                idx[compact(os.path.splitext(name)[0])] = name
    return idx


def find_pdf(rec, idx):
    for num in (rec.get("pub_no"), rec.get("reg_no")):
        c = compact(num)
        if not c:
            continue
        core = re.sub(r"[A-Z]\d?$", "", c)  # 문헌종류 기호 없는 파일명도 허용
        for key, name in idx.items():
            if key == c or key == core or key.startswith(core) and len(core) >= 8:
                return name
    return None


def run(table_path, project, previous=None, pdf_dir=None, aliases_path=None, applicants_path=None, sheet=None):
    aliases = load_aliases(aliases_path or DEFAULT_ALIASES)
    applicants = load_applicants(applicants_path or DEFAULT_APPLICANTS)
    header, fields, unknown_cols, rows = read_table(table_path, aliases, sheet)
    data_date = project.get("data_date")
    base_date = project.get("trend_base_date")
    lag = float(project.get("lag_months", 18))
    prev_keys = load_previous(previous, aliases, sheet) if previous else None
    pidx = pdf_index(pdf_dir)

    issues = []
    merged = {}
    order = []
    for r in rows:
        c = norm_country(r.get("country"), r.get("app_no"), r.get("pub_no"), r.get("reg_no"))
        key = (c, compact(r.get("app_no"))) if r.get("app_no") else ("ROW", r["_row"])
        if key in merged:
            m = merged[key]
            m["_rows"].append(r["_row"])
            for k, v in r.items():
                if k != "_row" and not m.get(k):
                    m[k] = v
            issues.append({"code": "I02", "level": "info", "rows": m["_rows"][:],
                           "msg": "같은 출원번호 중복 행을 하나로 합침(공개·등록 문헌이 따로 실린 경우 정상)"})
            continue
        r = dict(r)
        r["country"] = c
        r["_rows"] = [r.pop("_row")]
        merged[key] = r
        order.append(key)

    recs = []
    for i, key in enumerate(order, start=1):
        r = merged[key]
        rec = {"id": "D%03d" % i, "rows": r["_rows"], "country": r["country"]}
        for f in ("title", "app_no", "pub_no", "reg_no", "kind", "ipc", "cpc", "priority_no",
                  "family_id", "family_countries", "status", "cluster", "abstract", "claim", "inventor"):
            if r.get(f):
                rec[f] = r[f]
        for f in ("app_date", "pub_date", "reg_date", "priority_date"):
            d = parse_date(r.get(f))
            if d:
                rec[f] = d
            elif r.get(f):
                issues.append({"code": "I05", "level": "warn", "id": rec["id"], "msg": "%s 날짜를 읽지 못함: %s" % (f, r.get(f))})
        rec["doc_type"] = doc_type(rec["country"], r.get("kind"), r.get("app_no"), r.get("pub_no"), r.get("reg_no"))
        rec["stage"] = "등록" if rec.get("reg_no") else ("공개" if rec.get("pub_no") else "번호없음")
        rec["kind_codes"] = [k for k in (kind_code(rec.get("pub_no")), kind_code(rec.get("reg_no"))) if k]
        rec.update(resolve_applicant(r.get("applicant"), r.get("applicant_en"), r.get("rep_applicant"), applicants))
        rec["applicant_display"] = display_applicant(rec)
        rec["first_date"] = rec.get("priority_date") or rec.get("app_date")
        rec["evidence_ok"] = bool(rec.get("pub_no") or rec.get("reg_no"))
        if not rec["evidence_ok"]:
            issues.append({"code": "I01", "level": "error", "id": rec["id"],
                           "msg": "공개번호·등록번호가 모두 없음 → 본문 핵심근거로 쓰지 말 것(출원번호로 대체 금지)"})
        if rec["en_status"] in ("unverified",):
            issues.append({"code": "I06", "level": "warn", "id": rec["id"],
                           "msg": "출원인 영문명 미확인: %s → 공식 출처 확인 전에는 '영문명 미확인'으로 표기" % rec["applicant_canon"]})
        if rec["doc_type"] == "design":
            issues.append({"code": "I07", "level": "warn", "id": rec["id"], "msg": "디자인 문헌 — 기술동향 집계에서 빼는지 확인"})
        # 신규 관측
        if prev_keys is not None:
            rec["is_new"] = (rec["country"], compact(rec.get("app_no"))) not in prev_keys
            rec["new_basis"] = "직전 회차 목록과 비교"
        else:
            rec["is_new"] = is_truthy(r.get("new_flag"))
            rec["new_basis"] = "신규 표시 열" if "new_flag" in fields else "근거 없음"
        # 기술동향 분석대상
        pd_ = rec.get("pub_date") or rec.get("reg_date")
        rec["in_trend_scope"] = bool(base_date and pd_ and pd_ >= base_date)
        # 공개 지연 구간
        if data_date and rec.get("first_date"):
            rec["lag_zone"] = months_between(rec["first_date"], data_date) < lag
        else:
            rec["lag_zone"] = False
        # 공보 PDF
        if pdf_dir:
            rec["pdf"] = find_pdf(rec, pidx)
            if rec["evidence_ok"] and not rec["pdf"]:
                issues.append({"code": "I03", "level": "warn", "id": rec["id"],
                               "msg": "공보 PDF 없음: %s" % (rec.get("pub_no") or rec.get("reg_no"))})
        recs.append(rec)

    # 패밀리
    fam_of = {}
    for rec in recs:
        if rec.get("family_id"):
            fk = "F:" + compact(rec["family_id"])
        elif rec.get("priority_no"):
            fk = "P:" + compact(re.split(r"[;,]", rec["priority_no"])[0])
        else:
            fk = "S:" + rec["id"]
        rec["family_key"] = fk
        fam_of.setdefault(fk, []).append(rec["id"])
    singles = sum(1 for k in fam_of if k.startswith("S:"))
    if singles == len(recs) and recs:
        issues.append({"code": "I08", "level": "warn",
                       "msg": "패밀리번호·우선권번호 열이 없어 패밀리를 묶지 못함 → 기술신호 수가 부풀 수 있음(다운로드 항목에 추가 권장)"})

    # 중국 발명·실용 병행출원 후보
    cn = [r for r in recs if r["country"] == "CN" and r["doc_type"] in ("invention", "utility")]
    pairs = []
    for a in cn:
        if a["doc_type"] != "invention":
            continue
        for b in cn:
            if b["doc_type"] != "utility" or a["group"] != b["group"]:
                continue
            if not (a.get("app_date") and b.get("app_date")):
                continue
            gap = abs(months_between(a["app_date"], b["app_date"])) * 31
            sim = jaccard(tokens(a.get("title", "") + " " + a.get("abstract", "")),
                          tokens(b.get("title", "") + " " + b.get("abstract", "")))
            if gap <= 1.5 and sim >= 0.35:
                pairs.append({"invention": a["id"], "utility": b["id"], "same_day": gap < 0.5,
                              "title_similarity": round(sim, 2), "status": "CN Dual-filing Candidate",
                              "confirm_with": "출원일·출원인·명세서·독립청구항·보호대상·상태 비교 후 사람이 확정"})
                a.setdefault("cn_pair", []).append(b["id"])
                b.setdefault("cn_pair", []).append(a["id"])
    # 같은 발명 개념은 기술신호 1개 — 병행 후보는 같은 신호키로 묶음
    signal = {r["id"]: r["family_key"] for r in recs}
    for p in pairs:
        signal[p["utility"]] = signal[p["invention"]]
    for r in recs:
        r["signal_key"] = signal[r["id"]]

    n_lag = sum(1 for r in recs if r["lag_zone"])
    summary = {
        "source": os.path.basename(str(table_path)),
        "rows_read": len(rows),
        "documents": len(recs),
        "by_country": _count(recs, "country"),
        "by_doc_type": _count(recs, "doc_type"),
        "by_stage": _count(recs, "stage"),
        "families": len(fam_of),
        "tech_signals": len(set(signal.values())),
        "new_observed": sum(1 for r in recs if r["is_new"]),
        "new_basis": recs[0]["new_basis"] if recs else "",
        "trend_scope": sum(1 for r in recs if r["in_trend_scope"]),
        "lag_zone_docs": n_lag,
        "no_number_docs": sum(1 for r in recs if not r["evidence_ok"]),
        "cn_dual_candidates": len(pairs),
        "unknown_columns": unknown_cols,
        "data_date": data_date, "trend_base_date": base_date, "lag_months": lag,
    }
    if summary["new_basis"] == "근거 없음":
        issues.append({"code": "I04", "level": "warn",
                       "msg": "신규 표시 열도 직전 회차 목록도 없음 → '이번 회차 신규 관측'을 셀 수 없음(--previous 권장)"})
    return {"summary": summary, "records": recs, "cn_dual_candidates": pairs, "issues": issues,
            "project": project}


def _count(recs, key):
    d = defaultdict(int)
    for r in recs:
        d[r[key]] += 1
    return dict(sorted(d.items()))


def to_markdown(res):
    s = res["summary"]
    L = ["# 자료 검증 결과 (1단계)", "",
         "- 원본: `%s` · 읽은 행 %d · 문헌 %d건(중복 합침 후)" % (s["source"], s["rows_read"], s["documents"]),
         "- 국가: " + ", ".join("%s %d" % kv for kv in s["by_country"].items()),
         "- 권리유형: " + ", ".join("%s %d" % kv for kv in s["by_doc_type"].items()) +
         " · 단계: " + ", ".join("%s %d" % kv for kv in s["by_stage"].items()),
         "- 패밀리 %d개 · 기술신호 %d개(중국 병행출원 후보를 1개로 셈) · 권리화 활동 %d건" % (s["families"], s["tech_signals"], s["documents"]),
         "- 이번 회차 신규 관측 %d건(근거: %s) — '이번 달 출원'과 다른 개념" % (s["new_observed"], s["new_basis"]),
         "- 기술동향 분석대상 %d건(공개·등록일 ≥ %s)" % (s["trend_scope"], s["trend_base_date"]),
         "- 공개 지연 구간 문헌 %d건(자료일 %s 기준 최근 %d개월 출원 — 이 구간의 '감소'는 해석 금지)" % (s["lag_zone_docs"], s["data_date"], int(s["lag_months"])),
         "- 번호 없는 문헌 %d건 · 중국 병행출원 후보 %d쌍" % (s["no_number_docs"], s["cn_dual_candidates"]), ""]
    if s["unknown_columns"]:
        L += ["- 별칭표에 없는 열(무시됨): " + ", ".join(s["unknown_columns"]), ""]
    errs = [i for i in res["issues"] if i["level"] == "error"]
    warns = [i for i in res["issues"] if i["level"] == "warn"]
    L += ["## 확인할 것 (오류 %d · 경고 %d)" % (len(errs), len(warns)), ""]
    for i in errs + warns:
        L.append("- [%s %s] %s%s" % (i["level"], i["code"], (i.get("id") + " · ") if i.get("id") else "", i["msg"]))
    if res["cn_dual_candidates"]:
        L += ["", "## 중국 발명·실용신안 병행출원 후보 (확정 전)", "",
              "| 발명 | 실용신안 | 같은 날 출원 | 명칭 유사도 | 상태 |", "|---|---|---|---|---|"]
        by = {r["id"]: r for r in res["records"]}
        for p in res["cn_dual_candidates"]:
            a, b = by[p["invention"]], by[p["utility"]]
            L.append("| %s %s | %s %s | %s | %.2f | %s |" % (a["id"], a.get("pub_no") or a.get("reg_no", ""), b["id"],
                                                         b.get("reg_no") or b.get("pub_no", ""),
                                                         "예" if p["same_day"] else "아니오", p["title_similarity"], p["status"]))
    L += ["", "## 문헌 목록", "",
          "| ID | 국가 | 유형 | 번호 | 출원인 (영문) | 최선일 | 신규 | 동향대상 | 지연구간 |", "|---|---|---|---|---|---|---|---|---|"]
    for r in res["records"]:
        num = " / ".join(x for x in (r.get("pub_no"), r.get("reg_no")) if x) or "번호 없음"
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["id"], r["country"], {"invention": "발명", "utility": "실용", "design": "디자인"}[r["doc_type"]], num,
            r["applicant_display"], r.get("first_date", ""), "●" if r["is_new"] else "", "●" if r["in_trend_scope"] else "",
            "△" if r["lag_zone"] else ""))
    return "\n".join(L) + "\n"


def main():
    utf8_console()
    ap = argparse.ArgumentParser(description="WIPSON 엑셀/CSV 자료 검증")
    ap.add_argument("table")
    ap.add_argument("--project", default=str(HERE.parent / "config" / "project.json"))
    ap.add_argument("--previous", help="직전 회차 목록(.xlsx/.csv) — 신규 관측 판정")
    ap.add_argument("--pdf-dir", help="공보 PDF 폴더")
    ap.add_argument("--sheet")
    ap.add_argument("--aliases")
    ap.add_argument("--applicants")
    ap.add_argument("--out", default="work/01_intake.json")
    a = ap.parse_args()
    project = json.loads(Path(a.project).read_text(encoding="utf-8"))
    res = run(a.table, project, a.previous, a.pdf_dir, a.aliases, a.applicants, a.sheet)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    md = out.with_suffix(".md")
    md.write_text(to_markdown(res), encoding="utf-8")
    s = res["summary"]
    e = sum(1 for i in res["issues"] if i["level"] == "error")
    w = sum(1 for i in res["issues"] if i["level"] == "warn")
    print("문헌 %d · 패밀리 %d · 기술신호 %d · 신규 %d · 동향대상 %d · 지연구간 %d · 병행후보 %d · 오류 %d · 경고 %d"
          % (s["documents"], s["families"], s["tech_signals"], s["new_observed"], s["trend_scope"],
             s["lag_zone_docs"], s["cn_dual_candidates"], e, w))
    print("저장:", out, "·", md)


if __name__ == "__main__":
    main()
