#!/usr/bin/env python3
"""CLAUDE.md 슬림화 점검 (핸드북 26). 표준 라이브러리만 사용.

CLAUDE.md는 '강제 설정'이 아니라 매 턴 주입되는 '참고 텍스트(부탁)'입니다. 길고 모호해질수록
진짜 중요한 규칙이 잡음에 묻혀 무시됩니다. 이 도구는 지침 파일이 '짧고·기계적으로 판별 가능한지'를 점검합니다.

  python tools/claude_md_lint.py CLAUDE.md
  python tools/claude_md_lint.py CLAUDE.md --max-lines 200 --max-rules 10 --report work/lint.md

판정  PASS  분량·규칙 수 기준을 지키고 모호한 자명 지시가 없음
      WARN  모호/자명 지시가 섞임(기계적 판별 어려움)
      FAIL  분량 초과 또는 상시 규칙 수 초과

무엇을 보나:
  - 전체 줄 수(권장 200줄 이하) · 상시 운영 규칙 수(권장 4~10개)
  - 모호해서 '어겼는지'를 기계적으로 판별하기 어려운 표현(신중히/깨끗한 코드/적절히/최대한 등)
  - 모델이 이미 아는 자명한 조언(주석 잘 달기/가독성 좋게 등)

주의: 규칙의 '내용'이 옳은지는 판단하지 않습니다. 오직 '짧고 또렷하고 기계적으로 검증 가능한가'만 봅니다.
      규칙 수는 번호(1. 2.)나 불릿(-, *)으로 시작하는 줄로 셉니다.
"""
import argparse
import re
import sys
from pathlib import Path

# 기계적으로 '어겼는지' 판별이 어려운 모호한 표현
VAGUE = ["신중", "주의해", "적절히", "최대한", "가능한 한", "가능하면", "잘 ", "깔끔",
         "깨끗한 코드", "클린", "클린코드", "좋게", "알아서", "센스", "유의", "성실",
         "carefully", "clean code", "properly", "best practice", "as needed"]
# 모델이 이미 아는 자명한 조언
OBVIOUS = ["주석을 잘", "주석을 달", "가독성", "읽기 좋게", "변수명을 잘", "네이밍을 잘",
           "테스트를 작성하는 것이 좋", "문서화를 잘", "보안에 유의", "에러를 잘 처리"]
RULE_PREFIX = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+")


def analyze(text, max_lines, max_rules):
    lines = text.splitlines()
    n_lines = len(lines)
    rules = [l for l in lines if RULE_PREFIX.match(l)]
    n_rules = len(rules)

    vague_hits, obvious_hits = [], []
    for i, l in enumerate(lines, 1):
        low = l.lower()
        for v in VAGUE:
            if v.lower() in low:
                vague_hits.append((i, v.strip(), l.strip()[:60]))
                break
        for o in OBVIOUS:
            if o in l:
                obvious_hits.append((i, o, l.strip()[:60]))
                break

    over_lines = n_lines > max_lines
    over_rules = n_rules > max_rules
    if over_lines or over_rules:
        status = "FAIL"
    elif vague_hits or obvious_hits:
        status = "WARN"
    else:
        status = "PASS"
    return {"n_lines": n_lines, "n_rules": n_rules, "max_lines": max_lines, "max_rules": max_rules,
            "over_lines": over_lines, "over_rules": over_rules,
            "vague": vague_hits, "obvious": obvious_hits, "status": status}


def to_markdown(r):
    mark = {"PASS": "통과", "WARN": "통과(정리 권장)", "FAIL": "미통과(다이어트 필요)"}
    L = ["# CLAUDE.md 슬림화 점검", "",
         "- 전체 줄: {}줄 (권장 {}줄 이하){}".format(r["n_lines"], r["max_lines"], " ⚠️ 초과" if r["over_lines"] else ""),
         "- 상시 규칙(번호·불릿): {}개 (권장 {}개 이하){}".format(r["n_rules"], r["max_rules"], " ⚠️ 초과" if r["over_rules"] else ""),
         "- 판정: **{}**".format(mark[r["status"]]), ""]
    if r["vague"]:
        L += ["## 모호한 표현(기계적 판별 어려움)"]
        L += ["- {}행: ‘{}’ — `{}`".format(i, v, s) for i, v, s in r["vague"][:20]]
        L.append("")
    if r["obvious"]:
        L += ["## 자명한 조언(지워도 됨)"]
        L += ["- {}행: ‘{}’ — `{}`".format(i, o, s) for i, o, s in r["obvious"][:20]]
        L.append("")
    L += ["> 팁: 상시 규칙은 과거 2번 이상 틀린 것만, 어겼는지 0/1로 판별 가능한 문장으로.",
          "> 자세한 절차는 스킬로 분리하고, 세션이 길어지면 /clear 로 비우세요."]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="CLAUDE.md 슬림화 점검")
    ap.add_argument("path")
    ap.add_argument("--max-lines", type=int, default=200)
    ap.add_argument("--max-rules", type=int, default=10)
    ap.add_argument("--report")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    text = Path(a.path).read_text(encoding="utf-8", errors="replace")
    r = analyze(text, a.max_lines, a.max_rules)
    if a.json:
        import json
        sys.stdout.write(json.dumps(r, ensure_ascii=False, indent=1) + "\n")
    else:
        md = to_markdown(r)
        sys.stdout.write(md)
        if a.report:
            Path(a.report).parent.mkdir(parents=True, exist_ok=True)
            Path(a.report).write_text(md, encoding="utf-8")
    return {"PASS": 0, "WARN": 1, "FAIL": 2}[r["status"]]


if __name__ == "__main__":
    sys.exit(main())
