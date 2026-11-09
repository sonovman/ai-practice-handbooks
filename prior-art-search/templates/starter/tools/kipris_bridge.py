#!/usr/bin/env python3
"""28편 검색식(build_queries.py)과 10편 KIPRIS Plus 클라이언트(kipris_client.py)를 잇는 다리.

plan.json → build_queries.py가 만든 KIPRIS 식(TL=[..] AB=[..] CL=[..] IPC=[..])을
KIPRIS Plus 항목별 검색(getAdvancedSearch) 입력값으로 바꿔 kipris_client.py로 호출하고,
결과를 imports/ 에 CSV로 저장한다. 표준 라이브러리만.

준비: 이 파일과 kipris_client.py(10편)를 starter/tools/ 에 함께 둔다. 인증키는 환경변수 KIPRIS_KEY.
사용:
  python tools/kipris_bridge.py sample/plan.json               # 계획만(호출 0건)
  python tools/kipris_bridge.py sample/plan.json --probe --run # 첫 쿼리 1건만 호출, XML 태그 확인
  python tools/kipris_bridge.py sample/plan.json --run         # 전체 실행
  python tools/kipris_bridge.py sample/plan.json --nolimit --run  # 확대선출원용(기준일 제한 없음)

주의(추정 — 첫 사용 때 확인): 입력값 이름(inventionTitle·astrtCont·claimScope·ipcNumber)과
API가 * + 연산자·근접(^n)을 웹 KIPRIS처럼 해석하는지는 상품 명세서와 --probe 결과로 확인한다.
"""
import argparse, csv, json, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    import kipris_client as kc  # 10편
except ImportError:
    sys.exit("kipris_client.py가 tools/ 에 없습니다. 10편 템플릿에서 받아 이 폴더에 넣으세요:\n"
             "https://sonovman.github.io/ai-practice-handbooks/kipris-plus/templates/")
import build_queries  # 28편

FIELD_MAP = {"TL": "inventionTitle", "AB": "astrtCont", "CL": "claimScope", "IPC": "ipcNumber"}
DATE_COLS = ("openDate", "publicationDate")  # 공개일·공고일(추정 태그명) — 실제 응답으로 확인


def split_segments(expr):
    """'TL=[a]+AB=[b]' → ([('TL','a'),('AB','b')], '+') ; '*'면 한 호출에 함께 넣는다."""
    segs, joins, i = [], [], 0
    pat = re.compile(r"(TL|AB|CL|IPC)=\[")
    while True:
        m = pat.search(expr, i)
        if not m:
            break
        depth, j = 1, m.end()
        while j < len(expr) and depth:
            depth += {"[": 1, "]": -1}.get(expr[j], 0)
            j += 1
        segs.append((m.group(1), expr[m.end():j - 1]))
        rest = expr[j:j + 1]
        if rest in "+*" and rest:
            joins.append(rest)
        i = j
    if not segs:  # 필드 표시 없는 식 → 초록으로
        segs = [("AB", expr)]
    return segs, ("+" if "+" in joins else "*")


def to_calls(rows, near_to_and=True):
    calls, notes = [], []
    for r in rows:
        segs, join = split_segments(r["expr"])
        params_list = []
        if join == "+":  # 필드 간 OR → 필드마다 따로 호출해 합친다
            params_list = [{FIELD_MAP[c]: v} for c, v in segs]
        else:
            params_list = [{FIELD_MAP[c]: v for c, v in segs}]
        for p in params_list:
            for k, v in list(p.items()):
                if re.search(r"\^\d+", v) and near_to_and:
                    p[k] = re.sub(r"\^\d+", "*", v)
                    notes.append("{}: 근접(^n)을 AND(*)로 바꿨습니다(API 근접 지원 미확인).".format(r["id"]))
            calls.append({"id": r["id"], "purpose": r.get("purpose", ""), "params": p})
    return calls, notes


def cutoff_check(row, cutoff):
    dates = [re.sub(r"\D", "", row.get(c, "")) for c in DATE_COLS]
    dates = [d for d in dates if len(d) == 8]
    if not cutoff:
        return ""
    if not dates:
        return "날짜없음(확인)"
    return "이전" if min(dates) < cutoff else "이후(확대선출원 검토)"


def main(argv=None, opener=None, usage=None):
    ap = argparse.ArgumentParser(description="28편 KIPRIS 식 → 10편 kipris_client로 호출")
    ap.add_argument("plan")
    ap.add_argument("--out", default="imports")
    ap.add_argument("--rows", type=int, default=30, help="쿼리당 건수(numOfRows)")
    ap.add_argument("--pages", type=int, default=1, help="쿼리당 최대 페이지")
    ap.add_argument("--max-calls", type=int, default=30, help="이번 실행 호출 상한")
    ap.add_argument("--nolimit", action="store_true", help="확대선출원용(_KR_no_cutoff) 식 사용")
    ap.add_argument("--keep-near", action="store_true", help="^n 근접을 바꾸지 않고 그대로 보냄")
    ap.add_argument("--probe", action="store_true", help="첫 호출 1건만 하고 XML 원문 앞부분 출력")
    ap.add_argument("--run", action="store_true", help="실제 호출(없으면 계획만)")
    ap.add_argument("--per-second", type=float, default=5.0)
    a = ap.parse_args(argv)

    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    out, cutoff = build_queries.build_all(plan)
    rows = out["_KR_no_cutoff"] if a.nolimit else out["KIPRIS"]
    calls, notes = to_calls(rows, near_to_and=not a.keep_near)
    if a.probe:
        calls = calls[:1]
    need = len(calls) * (1 if a.probe else a.pages)
    usage = usage or kc.Usage()
    print("KIPRIS 식 {}개 → API 호출 최대 {}건 | 이번 달 기록 {}건 / 무료 {}건".format(
        len(rows), need, usage.count, kc.FREE_MONTHLY))
    for c in calls:
        print(" - {} {}".format(c["id"], c["params"]))
    for n in sorted(set(notes)):
        print(" ※ " + n)
    if need > a.max_calls:
        sys.exit("호출 상한(--max-calls {}) 초과. 쿼리·페이지를 줄이거나 상한을 조정하세요.".format(a.max_calls))
    if usage.count + need > kc.FREE_MONTHLY:
        print("※ 무료 한도를 넘을 수 있습니다.")
    if not a.run:
        print("계획만 표시했습니다. 실제 호출은 --run 을 붙이세요.")
        return 0

    client = kc.Client(os.environ.get("KIPRIS_KEY", ""), per_second=a.per_second, usage=usage,
                       **({"opener": opener} if opener else {}))
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    merged = {}
    tag = "nolimit" if a.nolimit else "kipris"
    for c in calls:
        got = []
        for page in range(1, (1 if a.probe else a.pages) + 1):
            try:
                body = client.get(kc.PATH_SEARCH, dict(c["params"], numOfRows=a.rows, pageNo=page))
            except kc.ApiError as e:
                print("{} 오류: {}".format(c["id"], kc.mask(e)))
                break
            if a.probe:
                print("── XML 앞부분(태그 이름 확인용) ──")
                print(body.decode("utf-8", "replace")[:1500])
            try:
                items, total = kc.parse_items(body)
            except kc.ApiError as e:
                print("{} 응답 오류: {}".format(c["id"], kc.mask(e)))
                break
            for it in items:
                it["query_id"] = c["id"]
                it["cutoff_check"] = cutoff_check(it, "" if a.nolimit else cutoff)
            got += items
            print("{} p{}: {}건 (전체 {})".format(c["id"], page, len(items), total))
            if len(items) < a.rows:
                break
        if got:
            kc.write_csv(got, str(outdir / "{}_{}.csv".format(tag, c["id"])))
        for it in got:
            key = it.get("applicationNumber") or json.dumps(it, ensure_ascii=False)
            m = merged.setdefault(key, dict(it, hit_queries=""))
            hits = [h for h in m["hit_queries"].split(";") if h]
            if c["id"] not in hits:
                hits.append(c["id"])
            m["hit_queries"] = ";".join(hits)
    if merged:
        allrows = sorted(merged.values(), key=lambda r: -len(r["hit_queries"].split(";")))
        kc.write_csv(allrows, str(outdir / "{}_all.csv".format(tag)))
        print("저장: {} (고유 {}건, 여러 쿼리에 걸린 문헌이 위)".format(outdir / "{}_all.csv".format(tag), len(allrows)))
    w = usage.warn_text()
    if w:
        print("※ " + w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
