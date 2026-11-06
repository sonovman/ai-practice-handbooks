"""도면부호 지도 만들기 — 명세서에서 '명칭(부호)'를 뽑아 점검표를 만든다

사용법
  python numeral_map.py <명세서.md|txt> [--figure-numerals 10,11,20] [--json]

하는 일
  1. 본문에서 "하우징(10)", "회전 브러시(40a)" 같은 '명칭(부호)' 표기를 모두 찾는다.
  2. 부호별로 쓰인 명칭과 횟수를 정리한다.
  3. 아래를 점검해 표시한다.
     - 한 부호에 서로 다른 명칭      → 오기·표현 흔들림 후보
     - 한 명칭에 서로 다른 부호      → 부호 오기 후보
     - (도면 부호 목록을 주면) 본문에만 있는 부호 / 도면에만 있는 부호
     - 청구항 1의 각 구성(; 로 구분)에 대응 부호가 있는지
  결과는 '후보'다. 최종 판단은 원문 도면을 보고 사람이 한다.
  Python 표준 라이브러리만 쓴다.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PAIR = re.compile(r"([가-힣A-Za-z][가-힣A-Za-z0-9·\-]*(?:[ \t]+[가-힣A-Za-z][가-힣A-Za-z0-9·\-]*){0,3})[ \t]*\((\d{1,4}[a-z]?'?)\)")
STOP = {"상기", "및", "또는", "그", "이", "각", "때", "각각", "하나의", "복수의", "통해", "따라", "의해", "그리고"}
# 명칭 앞에 붙은 낱말이 조사·어미로 끝나면 명칭이 아닌 것으로 본다
ENDING = ("은", "는", "을", "를", "가", "에", "의", "로", "와", "과", "고", "며", "도", "만", "게", "어", "아", "여", "면", "된", "한", "던", "니", "다")


def clean_name(raw):
    tokens = raw.split()
    name = [tokens[-1]]
    for t in reversed(tokens[:-1]):
        if t in STOP or t.endswith(ENDING) or len(name) == 3:
            break
        name.insert(0, t)
    return " ".join(name)


def claim1_elements(text):
    m = re.search(r"청구항\s*1\s*[.:]?\s*(.+?)(?=\n\s*\**\s*청구항\s*2|\n#|\Z)", text, re.S)
    if not m:
        return []
    body = re.sub(r"\*+", "", m.group(1))
    parts = []
    for e in re.split(r";", body):
        e = re.sub(r"\s+", " ", e).strip(" ;")
        e = re.sub(r"^(및|그리고)\s+", "", e)
        if not e or re.match(r"^[을를]\s*포함", e):  # '를 포함하는 …' 같은 연결 문구는 구성요소가 아님
            continue
        parts.append(e)
    return parts


def build(text, figure_numerals):
    by_num = defaultdict(Counter)
    for raw, num in PAIR.findall(text):
        by_num[num][clean_name(raw)] += 1

    rows, issues = [], []
    name_to_nums = defaultdict(set)
    for num in sorted(by_num, key=lambda n: (int(re.match(r"\d+", n).group()), n)):
        names = by_num[num]
        main = names.most_common(1)[0][0]
        rows.append({"부호": num, "명칭": main, "횟수": sum(names.values()),
                     "다른 표기": [n for n in names if n != main]})
        for n in names:
            name_to_nums[n].add(num)
        others = [n for n in names if n != main and main not in n and n not in main]
        if others:
            issues.append(f"부호 ({num}) 에 서로 다른 명칭: {main} / {', '.join(others)}")
    for name, nums in name_to_nums.items():
        if len(nums) > 1:
            issues.append(f"명칭 '{name}' 에 서로 다른 부호: {', '.join(sorted(nums))} → 오기 후보")

    text_nums = set(by_num)
    if figure_numerals:
        only_text = sorted(text_nums - figure_numerals, key=lambda n: int(re.match(r"\d+", n).group()))
        only_fig = sorted(figure_numerals - text_nums, key=lambda n: int(re.match(r"\d+", n).group()))
        if only_text:
            issues.append("본문에는 있으나 도면 부호 목록에 없음: " + ", ".join(only_text))
        if only_fig:
            issues.append("도면에는 있으나 본문에서 '명칭(부호)'로 설명되지 않음: " + ", ".join(only_fig))

    known = sorted({r["명칭"] for r in rows} | {n for r in rows for n in r["다른 표기"]}, key=len, reverse=True)
    claim = []
    for i, el in enumerate(claim1_elements(text), 1):
        pairs = PAIR.findall(el)
        if pairs:  # 청구항에 부호가 적혀 있으면: 끝에 오는 것이 그 요소의 주 부호, 나머지는 인용
            main = pairs[-1][1]
            refs = sorted({n for _, n in pairs[:-1]} - {main})
        else:      # 부호 없는 청구항이면: 명세서에서 찾은 명칭 중 문언 끝에 가장 가까운 것
            found = [(el.rfind(n), n) for n in known if n in el]
            if found:
                name = max(found)[1]
                main = "/".join(sorted(name_to_nums[name]))
            else:
                main = "독립항상 특정 부호 없음(후보)"
            refs = []
        claim.append({"요소": f"1-E{i}", "청구항 문언": el, "주 부호": main, "함께 언급된 부호": refs})
    return rows, issues, claim


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1
    fig = set()
    if "--figure-numerals" in sys.argv:
        i = sys.argv.index("--figure-numerals")
        fig = {x.strip() for x in sys.argv[i + 1].split(",") if x.strip()}
        args = [a for a in args if a != sys.argv[i + 1]]
    text = Path(args[0]).read_text(encoding="utf-8-sig")
    rows, issues, claim = build(text, fig)

    if "--json" in sys.argv:
        print(json.dumps({"부호표": rows, "점검": issues, "청구항1": claim}, ensure_ascii=False, indent=2))
        return 0

    print("## 도면부호 지도\n")
    print("| 부호 | 명칭 | 횟수 | 다른 표기 |\n|---|---|---|---|")
    for r in rows:
        print(f"| {r['부호']} | {r['명칭']} | {r['횟수']} | {', '.join(r['다른 표기']) or '-'} |")
    print("\n## 청구항 1 구성요소별 대응 부호 (후보)\n")
    print("| 요소 | 청구항 문언 | 주 부호 | 함께 언급된 부호 |\n|---|---|---|---|")
    for c in claim:
        print(f"| {c['요소']} | {c['청구항 문언']} | {c['주 부호']} | {', '.join(c['함께 언급된 부호']) or '-'} |")
    print("\n## 점검 결과\n")
    for s in issues or ["발견된 문제 없음"]:
        print("-", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
