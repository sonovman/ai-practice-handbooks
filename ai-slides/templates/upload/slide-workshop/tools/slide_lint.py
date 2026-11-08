#!/usr/bin/env python3
"""슬라이드 품질 게이트 + 취향 점검 (핸드북 24). 표준 라이브러리만 사용.

1차로 만든 슬라이드 개요(발표자료_초안.md)를 그대로 쓰기 전에, 객관적으로 잴 수 있는 것부터 걸러 줍니다.
'품질(Quality)'은 Pass/Fail로 판정하고, '취향(Taste)'은 경고로만 환기합니다 — 취향엔 정답이 없으니까요.

  python tools/slide_lint.py 발표자료_초안.md
  python tools/slide_lint.py 초안.md --slides 5 --require "3대,로드맵,기대효과" --body 본문.md --design 디자인.md
  python tools/slide_lint.py 초안.md --report work/qa.md

슬라이드 구분: 줄 '---' 또는 '# [Slide N]' 머리글. 각 슬라이드의 'Layout: Type X' 줄에서 레이아웃을 읽습니다.

판정  PASS 모든 품질 게이트 통과(취향 경고는 있을 수 있음)
      FAIL 품질 게이트 중 하나라도 미통과
종료 코드 0(PASS) / 1(취향 경고만) / 2(FAIL)

주의: 이 도구는 '객관적으로 잴 수 있는 것'만 봅니다. 레이아웃이 예쁜지, 흐름이 설득력 있는지 같은
      진짜 취향·논리는 사람(또는 비주얼 QA)이 봅니다. 숫자 일치 검사는 '본문에 없는 수치'를 알려 줄 뿐,
      사실 여부를 보증하지 않습니다.
"""
import argparse
import re
import sys
from pathlib import Path

# 흔한 AI 클리셰(원고가 지목한 'A가 아니라 B' 포함). 필요하면 늘리세요.
CLICHES = [
    (re.compile(r"[가-힣A-Za-z0-9]+\s*(?:이|가)\s*아니라\s*[가-힣A-Za-z0-9]+"), "‘A가 아니라 B’ 식 진부한 프레이징"),
    (re.compile(r"뿐만\s*아니라"), "‘뿐만 아니라’ 남발 주의"),
    (re.compile(r"획기적|혁신적인\s*변화|패러다임\s*전환"), "과장 수식어"),
    (re.compile(r"것이\s*중요합니다|라고\s*할\s*수\s*있습니다"), "줄글형 맺음(핵심 명사형 권장)"),
]
NUM_RE = re.compile(r"\d[\d,\.]*\s*(?:%|억|만|천|일|시간|분|Q[1-4]|년|곳|배)?")
DENSITY_WARN = 400   # 슬라이드 1장 본문 글자수 경고 기준(여백 확보)
DIVERSITY_MAX = 0.5  # 한 레이아웃 타입이 전체의 이 비율을 넘으면 경고


def split_slides(text):
    """'# [Slide'를 우선 경계로, 없으면 '---'로 나눈다."""
    if "# [Slide" in text or "# [slide" in text.lower():
        parts = re.split(r"(?m)^#\s*\[[Ss]lide", text)
        return [("# [Slide" + p).strip() for p in parts[1:]] if parts[1:] else [text]
    chunks = [c.strip() for c in re.split(r"(?m)^---\s*$", text)]
    return [c for c in chunks if c]


def layout_of(slide):
    m = re.search(r"(?im)^\s*[-*]?\s*Layout\s*[:：]\s*(Type\s*[A-Za-z0-9]+)", slide)
    return m.group(1).replace(" ", "") if m else None


def numbers(text):
    out = set()
    for m in NUM_RE.finditer(text):
        tok = m.group(0).strip()
        digits = re.sub(r"[^\d]", "", tok)
        if digits:
            out.add(digits)
    return out


def design_types(design_path):
    if not design_path:
        return None
    p = Path(design_path)
    if not p.exists():
        return None
    s = p.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"Type\s*([A-Za-z0-9]+)", s))


def scan(text, slides_expected=None, require=None, body=None, design=None):
    slides = split_slides(text)
    gates, tastes = [], []

    def gate(name, ok, detail):
        gates.append({"name": name, "ok": ok, "detail": detail})

    # GATE-분량
    if slides_expected is not None:
        gate("분량(슬라이드 수)", len(slides) == slides_expected,
             "요구 {}장 / 실제 {}장".format(slides_expected, len(slides)))
    # GATE-요구 키워드
    if require:
        miss = [k for k in require if k and k not in text]
        gate("요구사항(키워드 포함)", not miss,
             "모두 포함" if not miss else "누락: " + ", ".join(miss))
    # GATE-사실관계(본문 대비 수치) — 본문에 없는 수치는 FAIL 후보
    if body:
        bp = Path(body)
        if bp.exists():
            bnums = numbers(bp.read_text(encoding="utf-8", errors="replace"))
            snums = numbers(text)
            extra = sorted(n for n in snums if n not in bnums and len(n) >= 2)
            gate("사실관계(본문에 없는 수치)", not extra,
                 "본문과 일치" if not extra else "본문에 없음: " + ", ".join(extra[:12]))
        else:
            gate("사실관계(본문 대비)", False, "본문 파일을 찾지 못함: " + body)
    # GATE-AI 클리셰
    hits = []
    for rx, label in CLICHES:
        for m in rx.finditer(text):
            hits.append("{} — ‘{}’".format(label, m.group(0).strip()))
    gate("문체(AI 클리셰 없음)", not hits, "없음" if not hits else " / ".join(dict.fromkeys(hits))[:300])

    # TASTE-정보 밀도(슬라이드별 글자수)
    heavy = []
    for i, s in enumerate(slides, 1):
        body_len = len(re.sub(r"\s", "", s))
        if body_len > DENSITY_WARN:
            heavy.append("Slide {}({}자)".format(i, body_len))
    if heavy:
        tastes.append("정보 밀도 높음(여백 확보 권장): " + ", ".join(heavy))

    # TASTE-레이아웃 다양성
    layouts = [layout_of(s) for s in slides]
    named = [l for l in layouts if l]
    if named:
        from collections import Counter
        c = Counter(named)
        top, n = c.most_common(1)[0]
        if n / len(named) > DIVERSITY_MAX and len(named) >= 3:
            tastes.append("레이아웃 쏠림({}이 {}/{}): 다양한 Type 섞기 권장".format(top, n, len(named)))
        dt = design_types(design)
        if dt:
            undefined = sorted({re.sub(r"Type", "", l) for l in named} - dt)
            if undefined:
                tastes.append("디자인.md에 없는 레이아웃: " + ", ".join("Type" + u for u in undefined))
    if not named and len(slides) >= 2:
        tastes.append("Layout: Type 표기가 없어 다양성 점검 불가(각 슬라이드에 Layout 지정 권장)")

    status = "FAIL" if any(not g["ok"] for g in gates) else ("WARN" if tastes else "PASS")
    return {"status": status, "slides": len(slides), "gates": gates, "tastes": tastes}


def to_markdown(res):
    mark = {"PASS": "통과", "WARN": "통과(취향 경고)", "FAIL": "미통과"}
    L = ["# 슬라이드 품질 게이트 점검", "",
         "- 슬라이드 수: {}장".format(res["slides"]),
         "- 판정: **{}**".format(mark[res["status"]]), "",
         "## 품질 게이트 (Pass/Fail)", "", "| 판정 | 항목 | 내용 |", "|---|---|---|"]
    for g in res["gates"]:
        L.append("| {} | {} | {} |".format("PASS" if g["ok"] else "FAIL", g["name"], g["detail"]))
    L += ["", "## 취향 경고 (참고)", ""]
    if res["tastes"]:
        L += ["- " + t for t in res["tastes"]]
    else:
        L.append("- 특이사항 없음")
    L += ["", "> 품질 게이트는 객관적으로 잴 수 있는 것만 봅니다. 레이아웃·논리·설득력 같은 ‘취향’은",
          "> 사람 또는 비주얼 QA가 최종 확인하세요."]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="슬라이드 품질 게이트 + 취향 점검")
    ap.add_argument("path")
    ap.add_argument("--slides", type=int)
    ap.add_argument("--require", default="")
    ap.add_argument("--body")
    ap.add_argument("--design")
    ap.add_argument("--report")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    text = Path(a.path).read_text(encoding="utf-8", errors="replace")
    require = [k.strip() for k in a.require.split(",") if k.strip()]
    res = scan(text, a.slides, require, a.body, a.design)
    if a.json:
        import json
        sys.stdout.write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    else:
        md = to_markdown(res)
        sys.stdout.write(md)
        if a.report:
            Path(a.report).parent.mkdir(parents=True, exist_ok=True)
            Path(a.report).write_text(md, encoding="utf-8")
    return {"PASS": 0, "WARN": 1, "FAIL": 2}[res["status"]]


if __name__ == "__main__":
    sys.exit(main())
