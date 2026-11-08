#!/usr/bin/env python3
"""컨텍스트 예산 추정 (핸드북 26). 표준 라이브러리만 사용.

LLM은 매 턴 [시스템 지침 + 규칙 파일 + 데이터 + 지금까지의 대화]를 처음부터 다시 읽습니다.
전체가 커지면 어텐션이 분산돼 초기 규칙을 놓칩니다. 이 도구는 각 구성요소가 컨텍스트 창을 얼마나
차지하는지 대략 추정해, 언제 /clear 하거나 스킬·서브에이전트로 분리할지 판단을 돕습니다.

  python tools/context_budget.py CLAUDE.md data/*.md --window 200000
  python tools/context_budget.py --window 200000 --text-tokens system=1200 CLAUDE.md
  python tools/context_budget.py CLAUDE.md --json

토큰 추정(근사): 한글·한자 등 CJK 글자는 토큰을 많이 먹으므로 CJK ≈ 1.6자/토큰, 그 외 ≈ 4자/토큰으로
  섞어 계산합니다. 실제 토큰 수는 모델 토크나이저에 따라 다르니 '가늠용'입니다.

판정  OK   총 점유 50% 이하
      WARN 50~80% (슬림화·분리 고려)
      HIGH 80% 초과 (/clear 또는 스킬·서브에이전트로 분원화 권장)
"""
import argparse
import glob
import re
import sys
from pathlib import Path

CJK = re.compile(r"[　-鿿가-힣豈-﫿]")


def est_tokens(text):
    cjk = len(CJK.findall(text))
    other = len(text) - cjk
    return int(cjk / 1.6 + other / 4.0)


def analyze(items, window):
    """items: [(label, tokens)]"""
    total = sum(t for _, t in items)
    pct = total / window * 100 if window > 0 else 0
    if pct > 80:
        status = "HIGH"
    elif pct > 50:
        status = "WARN"
    else:
        status = "OK"
    return {"items": items, "total": total, "window": window, "pct": round(pct, 1), "status": status}


def to_markdown(r):
    mark = {"OK": "여유", "WARN": "주의(정리 고려)", "HIGH": "높음(분원화 권장)"}
    L = ["# 컨텍스트 예산 추정", "",
         "- 창 크기: {:,} 토큰".format(r["window"]),
         "- 합계: **{:,} 토큰** (점유 {}%)".format(r["total"], r["pct"]),
         "- 판정: **{}**".format(mark[r["status"]]), "",
         "| 구성요소 | 추정 토큰 | 점유 |", "|---|---:|---:|"]
    for label, t in r["items"]:
        p = t / r["window"] * 100 if r["window"] else 0
        L.append("| {} | {:,} | {:.1f}% |".format(label, t, p))
    L.append("")
    if r["status"] != "OK":
        L += ["## 권고",
              "- 긴 지침은 CLAUDE.md에서 빼 스킬로 분리(필요할 때만 로딩).",
              "- 무거운 데이터 분석·검색은 서브에이전트(독립 창)로 위임하고 요약만 받기.",
              "- 주제가 바뀌면 /compact 대신 /clear 로 비우기(스킬 목록 유실·토큰 비용 방지).", ""]
    L.append("> 토큰 수는 토크나이저에 따라 다른 근사치입니다. 비율의 '감'을 잡는 용도입니다.")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="컨텍스트 예산 추정")
    ap.add_argument("paths", nargs="*", help="추정할 파일들(글롭 가능)")
    ap.add_argument("--window", type=int, default=200000, help="컨텍스트 창 토큰(기본 200000)")
    ap.add_argument("--text-tokens", action="append", default=[],
                    help="파일이 아닌 항목을 label=tokens 로 직접 추가(예: system=1200)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    items = []
    for spec in a.text_tokens:
        if "=" not in spec:
            sys.exit("--text-tokens 는 label=tokens 형식")
        label, val = spec.split("=", 1)
        items.append((label, int(val)))
    files = []
    for p in a.paths:
        files.extend(sorted(glob.glob(p)) or [p])
    for f in files:
        fp = Path(f)
        if not fp.is_file():
            sys.stderr.write("건너뜀(파일 아님): {}\n".format(f))
            continue
        items.append((fp.name, est_tokens(fp.read_text(encoding="utf-8", errors="replace"))))
    if not items:
        sys.exit("추정할 파일이나 --text-tokens 항목을 주세요.")

    r = analyze(items, a.window)
    if a.json:
        import json
        sys.stdout.write(json.dumps(r, ensure_ascii=False, indent=1) + "\n")
    else:
        sys.stdout.write(to_markdown(r))
    return {"OK": 0, "WARN": 1, "HIGH": 2}[r["status"]]


if __name__ == "__main__":
    sys.exit(main())
