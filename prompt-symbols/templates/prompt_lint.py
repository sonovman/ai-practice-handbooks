#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prompt_lint.py — 프롬프트 템플릿의 기호 사용을 점검하고, 변수를 채워 보낼 프롬프트를 만드는 도구

두 가지 명령
  check  템플릿을 읽고 기호 약속(핸드북 12편)에 어긋나는 곳을 알려 줍니다.
  fill   {변수}를 값으로 바꾸고, 하나라도 안 채워졌으면 멈춥니다(빈칸 그대로 보내는 실수 방지).

사용 예
  python prompt_lint.py check 내프롬프트.md
  python prompt_lint.py fill 이메일답장.md --set 수신자=김부장 --set 톤=정중한 --set 받은메일=@받은메일.txt --out 보낼프롬프트.md
  (값 앞에 @를 붙이면 그 파일의 내용을 넣습니다)

필요한 것: Python 3.8 이상 (추가 설치 없음)
점검은 기계적 규칙입니다. '주의'는 틀렸다는 뜻이 아니라 다시 한 번 보라는 뜻입니다.
"""
import argparse
import re
import sys
from pathlib import Path

VAR = re.compile(r"\{([^{}\n]{1,40})\}")
TAG = re.compile(r"<(/?)([A-Za-z_][\w.-]*|[가-힣_][가-힣\w.-]*)(\s[^<>]*)?>")
ANGLE_PLACEHOLDER = re.compile(r"<([^<>/\n]*[\s가-힣][^<>\n]*)>")
OPTIONS = re.compile(r"\[([^\[\]\n]+/[^\[\]\n]+)\]")
QUOTED = re.compile(r"[\"“]([^\"“”\n]{1,20})[\"”]")
CHOICE_WORDS = ("고르", "선택", "중 하나", "중에서", "가능한 값", "고를 수 있는", "허용 값")
MEANING_WORDS = ("뜻", "의미", "그대로", "만 가리", "만 뜻", "으로만", "로만", "만 쓴", "정의", "라는 ")
SHOUT = re.compile(r"\b(MUST|NEVER|ALWAYS|CRITICAL|IMPORTANT)\b|절대로|무조건|반드시")


def strip_code(text):
    """```로 감싼 예시 블록은 점검에서 뺀다(예시 안의 기호까지 경고하지 않도록)."""
    return re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)


def check(text):
    out = []
    add = lambda level, rule, detail: out.append((level, rule, detail))
    body = strip_code(text)
    lines = body.splitlines()

    # 1. 구조
    has_md = any(re.match(r"^#{1,4}\s+\S", l) for l in lines)
    tags = [(m.group(1), m.group(2)) for m in TAG.finditer(body)]
    has_xml = any(close == "" for close, _ in tags)
    if len(body.strip()) > 200 and not (has_md or has_xml):
        add("주의", "구조", "200자가 넘는데 # 제목이나 XML 태그가 없습니다. 역할·자료·작업·출력 형식을 나누세요.")
    if has_md and has_xml:
        md_sections = sum(1 for l in lines if re.match(r"^#{1,4}\s+\S", l))
        add("정보", "형식 섞임", "# 제목 {}개와 XML 태그를 함께 씁니다. 섹션은 #, 자료 덩어리는 태그처럼 역할을 나눴다면 괜찮습니다.".format(md_sections))

    # 2. XML 태그 짝
    stack = []
    for close, name in tags:
        if close == "":
            stack.append(name)
        elif stack and stack[-1] == name:
            stack.pop()
        else:
            add("실패", "태그 짝", "</{}>의 여는 태그가 없거나 순서가 어긋났습니다.".format(name))
    for name in stack:
        add("실패", "태그 짝", "<{}>를 닫는 </{}>가 없습니다.".format(name, name))

    # 3. 꺾쇠를 빈칸 표시로 쓴 곳
    paired = {n for c, n in tags if c == "/"}
    for m in ANGLE_PLACEHOLDER.finditer(body):
        inner = m.group(1).strip()
        first = inner.split()[0] if inner.split() else inner
        if first.startswith("/") or first in paired:
            continue
        add("주의", "꺾쇠 빈칸", "<{}> — 꺾쇠는 XML 태그와 헷갈립니다. 채울 값은 {{{}}}처럼 중괄호로 쓰세요.".format(inner, inner.replace(" ", "_")))

    # 4. 변수
    names = []
    for m in VAR.finditer(body):
        n = m.group(1).strip()
        if "/" in n:
            add("주의", "변수 속 선택지", "{{{}}} — 선택지는 [ ]에, 변수 이름은 {{ }}에 나눠 쓰세요.".format(n))
        names.append(n)
    if names:
        add("정보", "변수", "채울 값 {}개: {}".format(len(set(names)), ", ".join(sorted(set(names)))))

    # 5. 선택지에 선택 규칙이 있는지
    for i, l in enumerate(lines, 1):
        for m in OPTIONS.finditer(l):
            window = " ".join(lines[max(0, i - 2):i + 1])
            if not any(w in window for w in CHOICE_WORDS):
                add("주의", "선택지 규칙", "{}행 [{}] — 누가 무엇을 고르는지 문장으로 적으세요(예: '아래 중 하나를 고르고 고른 것을 첫 줄에 밝힌다').".format(i, m.group(1)))

    # 6. 따옴표만으로 의미를 고정하려는 곳
    for i, l in enumerate(lines, 1):
        for m in QUOTED.finditer(l):
            if not any(w in l for w in MEANING_WORDS):
                add("주의", "따옴표 의미", "{}행 \"{}\" — 따옴표는 '이 글자'를 가리킬 뿐입니다. 뜻을 고정하려면 무슨 뜻으로만 쓰는지 문장으로 적으세요.".format(i, m.group(1)))

    # 7. 강조 남용
    bold = len(re.findall(r"\*\*[^*\n]+\*\*", body))
    shout = len(SHOUT.findall(body))
    if bold > 3:
        add("주의", "강조 남용", "굵게 표시 {}곳 — 모두 강조하면 아무것도 강조되지 않습니다. 정말 중요한 1~2곳만.".format(bold))
    if shout >= 3:
        add("주의", "강한 어조", "'반드시·절대·MUST' 같은 표현 {}곳 — 최신 모델은 지나치게 따를 수 있습니다. 이유를 설명하는 문장으로 바꿔 보세요.".format(shout))

    # 8. 출력 형식
    if not re.search(r"^#{1,4}\s*(출력|결과|응답|output)", body, re.M | re.I) and not re.search(r"<(output|출력)[\s>]", body, re.I):
        add("주의", "출력 형식", "출력 형식 섹션이 없습니다. 무엇을 어떤 모양으로 받을지 적으세요.")

    # 9. 태그 밖의 긴 자료
    inside = 0
    for i, l in enumerate(lines, 1):
        opens = len(re.findall(r"<[A-Za-z가-힣_][^<>/]*>", l))
        closes = len(re.findall(r"</[^<>]+>", l))
        if inside == 0 and len(l) > 150 and not VAR.search(l):
            add("주의", "자료 경계", "{}행 — 150자가 넘는 줄이 태그 밖에 있습니다. 붙여 넣은 자료라면 <자료>…</자료>처럼 감싸세요.".format(i))
        inside = max(0, inside + opens - closes)
    return out


def fill(text, values):
    missing = []

    def rep(m):
        n = m.group(1).strip()
        if n in values:
            return values[n]
        missing.append(n)
        return m.group(0)

    # 코드 블록 안은 건드리지 않는다
    parts = re.split(r"(```.*?```)", text, flags=re.S)
    done = "".join(p if p.startswith("```") else VAR.sub(rep, p) for p in parts)
    return done, sorted(set(missing))


def main(argv=None):
    ap = argparse.ArgumentParser(description="프롬프트 기호 점검·변수 채우기")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("file")
    f = sub.add_parser("fill")
    f.add_argument("file")
    f.add_argument("--set", action="append", default=[], help="이름=값 (값 앞 @는 파일 내용)")
    f.add_argument("--out")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    text = Path(a.file).read_text(encoding="utf-8-sig")

    if a.cmd == "check":
        rows = check(text)
        print("프롬프트 기호 점검 — {}\n".format(a.file))
        if not rows:
            print("[통과] 지적할 곳이 없습니다.")
        for level, rule, detail in rows:
            print("[{}] {:<8} {}".format(level, rule, detail))
        fails = sum(1 for r in rows if r[0] == "실패")
        warns = sum(1 for r in rows if r[0] == "주의")
        print("\n실패 {}건 · 주의 {}건".format(fails, warns))
        return 1 if fails else 0

    values = {}
    for s in a.set:
        if "=" not in s:
            print("오류: --set 은 이름=값 형식입니다: " + s)
            return 2
        k, v = s.split("=", 1)
        if v.startswith("@"):
            v = Path(v[1:]).read_text(encoding="utf-8-sig").strip()
        values[k.strip()] = v
    done, missing = fill(text, values)
    if missing:
        print("멈춤: 채우지 않은 값이 있습니다 → " + ", ".join(missing))
        return 1
    if a.out:
        Path(a.out).write_text(done, encoding="utf-8")
        print("저장: " + a.out)
    else:
        print(done)
    return 0


if __name__ == "__main__":
    sys.exit(main())
