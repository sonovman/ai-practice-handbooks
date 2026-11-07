#!/usr/bin/env python3
"""윤문 전후 '의미 보존' 점검기 (핸드북 18). 표준 라이브러리만 사용.

윤문이 자연스러워졌는지가 아니라 '바뀌면 안 되는 것이 그대로인지'를 봅니다.

  python tools/polish_check.py 원문.md 윤문본.md
  python tools/polish_check.py 원문.md 윤문본.md --terms terms.txt --report report.md
  python tools/polish_check.py 원문.md 윤문본.md --json

검사 항목
  FAIL  큰따옴표·낫표 인용문 변경 / 수치·날짜·단위 소실·추가 / 문헌·조문·청구항 번호 변경
        법률·특허 한정 표현(적어도, 이상, 다만, may, shall, comprising …) 감소
        정의 용어 소실 / 제목 소실 / 변경률 50% 이상
  WARN  변경률 30% 이상 / 정의 용어 등장 횟수 감소 / 완곡·당위 표현 감소 / 부정 표현 수 변화
  INFO  문체 지표(문장 길이 분산, 연결어미 뒤 쉼표, AI 상투어) 전후 비교

종료 코드  0 = 통과, 1 = 경고(사람 확인), 2 = 실패(채택 금지)
"""
import argparse
import difflib
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

WARN_RATE, FAIL_RATE = 0.30, 0.50  # im-not-ai 과윤문 가드와 같은 기준

QUOTE_RE = re.compile(r'"([^"\n]{2,})"|“([^”\n]{2,})”|「([^」\n]{2,})」|『([^』\n]{2,})』')
URL_RE = re.compile(r"https?://\S+")
DOCNO_RE = re.compile(r"\b(?:KR|US|EP|JP|CN|WO|PCT)[\s\-/]?[0-9][0-9A-Z\-/,. ]{4,}[0-9A-Z]\b")
STATUTE_RE = re.compile(r"제\s*\d+\s*조(?:의\s*\d+)?(?:\s*제\s*\d+\s*항)?(?:\s*제\s*\d+\s*호)?|청구항\s*\d+|"
                        r"\bclaims?\s+\d+(?:\s*(?:-|to|and)\s*\d+)?|\b(?:Article|Section|§)\s*\d+[a-z]?",
                        re.I)
UNIT = r"(?:%|퍼센트|년|월|일|시|분|초|개|건|명|원|달러|배|회|차|항|조|호|mm|cm|nm|μm|m|km|kg|g|mg|℃|°C|K|V|A|W|Hz|kHz|MHz|GHz|ms|s)?"
NUM_RE = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?\s?" + UNIT)
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", re.M)

# 법률·특허에서 범위·조건·의무를 정하는 표현 — 줄면 의미가 바뀐 것으로 본다.
LIMITERS_KO = ["적어도", "최소한", "이상", "이하", "초과", "미만", "내지", "다만", "단,", "한하여", "한하여야",
               "제외", "포함하는", "포함한다", "만으로", "에 한정", "반드시", "실질적으로", "약 ", "및", "또는", "각각"]
LIMITERS_EN = ["at least", "at most", "no more than", "no less than", "comprising", "consisting of",
               "consisting essentially of", "including", "wherein", "provided that", "unless", "except",
               "only", "substantially", "about", "approximately", "and/or", "respectively", "shall", "must"]
HEDGE_KO = ["수 있", "수도 있", "가능성", "것으로 보", "판단되", "판단된", "추정", "듯하", "여지가"]
OBLIG_KO = ["하여야", "해야", "되어야", "돼야", "필요가 있", "필요하", "금지", "해서는 안", "하여서는 아니"]
HEDGE_EN = ["may", "might", "could", "can", "likely", "possibly", "appear", "suggest"]
OBLIG_EN = ["shall", "must", "required", "should", "may not", "shall not", "must not"]
NEG_KO = re.compile(r"않|없[다는고어었을음지]|아니|못하|못한|못 |불가|금지|말아야")
NEG_EN = re.compile(r"\b(?:not|no|never|none|neither|nor|cannot|without)\b|n't\b", re.I)

CLICHE_KO = ["결론적으로", "시사하는 바가 크", "주목할 만하", "혁신적인", "획기적인", "전례 없는", "새로운 지평",
             "에 있어서", "를 통해", "을 통해", "되어진", "되어지", "가지고 있", "첫째,", "둘째,", "셋째,",
             "중요한 역할을", "하는 것이 중요", "에 대해", "나아가", "또한,", "따라서,", "즉,"]
CLICHE_EN = ["delve", "testament", "landscape", "pivotal", "showcasing", "seamless", "it's not just",
             "not just", "let that sink in", "at its core", "in today's", "game-changer", "navigate the",
             "underscore", "crucial role", "here's the thing", "honestly?", "—"]
# 연결어미 뒤 쉼표: KatFishNet(ACL 2025)이 한국어 AI 문장의 강한 신호로 보고한 쉼표 습관,
# im-not-ai의 C-11 패턴과 같은 대상. 사람마다 습관이 달라 '참고 지표'로만 쓴다.
CONNECTIVE_COMMA = re.compile(r"(?:고|며|면서|지만|는데|은데|ㄴ데|서|여|해|면|니|므로|도록|듯이|자),")


def read(p):
    return Path(p).read_text(encoding="utf-8-sig")


def is_korean(text):
    hangul = len(re.findall(r"[가-힣]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return hangul >= latin


def quotes(text):
    return [next(g for g in m.groups() if g) for m in QUOTE_RE.finditer(text)]


def norm_num(tok):
    return re.sub(r"[\s,]", "", tok)


def count_phrases(text, phrases, word=False):
    low = text.lower()
    c = Counter()
    for p in phrases:
        if word:
            n = len(re.findall(r"(?<![A-Za-z])" + re.escape(p.lower()) + r"(?![A-Za-z])", low))
        else:
            n = low.count(p.lower())
        if n:
            c[p] = n
    return c


def sentences(text):
    body = HEADING_RE.sub("", text)
    parts = re.split(r"(?<=[.!?。])\s+|(?<=다\.)|\n{2,}", body)
    return [s.strip() for s in parts if s and len(s.strip()) > 1]


def style(text, ko):
    sents = sentences(text)
    lens = [len(s) for s in sents] or [0]
    d = {
        "문장 수": len(sents),
        "평균 문장 길이": round(statistics.mean(lens), 1),
        "문장 길이 표준편차": round(statistics.pstdev(lens), 1) if len(lens) > 1 else 0.0,
    }
    if ko:
        commas = text.count(",")
        d["쉼표 수"] = commas
        d["연결어미 뒤 쉼표"] = len(CONNECTIVE_COMMA.findall(text))
        endings = Counter(re.findall(r"([가-힣]{2})다[.]", text))
        d["가장 잦은 종결(~다)"] = endings.most_common(1)[0][1] if endings else 0
        d["AI 상투어"] = sum(count_phrases(text, CLICHE_KO).values())
    else:
        d["AI 상투어"] = sum(count_phrases(text, CLICHE_EN, word=False).values())
    return d


def load_terms(path):
    if not path:
        return []
    terms = []
    for line in read(path).splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    return terms


def change_rate(a, b):
    sa, sb = re.sub(r"\s+", "", a), re.sub(r"\s+", "", b)
    if not sa and not sb:
        return 0.0
    return 1.0 - difflib.SequenceMatcher(None, sa, sb, autojunk=False).ratio()


def check(before, after, terms=()):
    ko = is_korean(before)
    items = []  # (level, 항목, 내용)

    def add(level, name, detail):
        items.append({"level": level, "item": name, "detail": detail})

    rate = change_rate(before, after)
    lvl = "FAIL" if rate >= FAIL_RATE else "WARN" if rate >= WARN_RATE else "OK"
    add(lvl, "변경률", "{:.1%} (경고 30% / 중단 50%)".format(rate))

    qa, qb = quotes(before), quotes(after)
    lost = [q for q in qa if q not in qb]
    add("FAIL" if lost else "OK", "인용문", "바뀌거나 사라짐: " + " | ".join(lost) if lost else "{}개 모두 그대로".format(len(qa)))

    for name, rx in (("수치·날짜·단위", NUM_RE), ("문헌 번호", DOCNO_RE), ("조문·청구항 번호", STATUTE_RE), ("URL", URL_RE)):
        ca = Counter(norm_num(m.group(0)) for m in rx.finditer(before))
        cb = Counter(norm_num(m.group(0)) for m in rx.finditer(after))
        miss, extra = ca - cb, cb - ca
        if miss or extra:
            detail = []
            if miss:
                detail.append("사라짐 " + ", ".join(sorted(miss.elements())))
            if extra:
                detail.append("새로 생김 " + ", ".join(sorted(extra.elements())))
            add("FAIL", name, " / ".join(detail))
        else:
            add("OK", name, "{}개 그대로".format(sum(ca.values())))

    heads_a = HEADING_RE.findall(before)
    heads_b = HEADING_RE.findall(after)
    lost_h = [h for h in heads_a if h not in heads_b]
    add("FAIL" if lost_h else "OK", "제목", "바뀌거나 사라짐: " + " | ".join(lost_h) if lost_h else "{}개 그대로".format(len(heads_a)))

    lim = LIMITERS_KO if ko else LIMITERS_EN
    la, lb = count_phrases(before, lim, word=not ko), count_phrases(after, lim, word=not ko)
    dec = {k: (la[k], lb.get(k, 0)) for k in la if lb.get(k, 0) < la[k]}
    add("FAIL" if dec else "OK", "한정·조건 표현",
        "줄어듦: " + ", ".join("'{}' {}→{}".format(k.strip(), a, b) for k, (a, b) in dec.items()) if dec
        else "{}개 유지".format(sum(la.values())))

    neg = NEG_KO if ko else NEG_EN
    na, nb = len(neg.findall(before)), len(neg.findall(after))
    add("WARN" if na != nb else "OK", "부정 표현", "{}→{}".format(na, nb) +
        (" — 수사적 대조('not X but Y', '~이 아니라')를 정리한 것인지, 부정의 의미가 바뀐 것인지 확인" if na != nb else ""))

    for name, lst in (("완곡(가능·추측) 표현", HEDGE_KO if ko else HEDGE_EN), ("당위·의무 표현", OBLIG_KO if ko else OBLIG_EN)):
        ca, cb = count_phrases(before, lst, word=not ko), count_phrases(after, lst, word=not ko)
        ta, tb = sum(ca.values()), sum(cb.values())
        if tb < ta:
            add("WARN", name, "{}→{} — 판단 강도가 세지지 않았는지 확인".format(ta, tb))
        else:
            add("OK", name, "{}→{}".format(ta, tb))

    if terms:
        lost_t, fewer = [], []
        for t in terms:
            a, b = before.count(t), after.count(t)
            if a and not b:
                lost_t.append(t)
            elif b < a:
                fewer.append("{} {}→{}".format(t, a, b))
        if lost_t:
            add("FAIL", "정의 용어", "사라짐: " + ", ".join(lost_t))
        elif fewer:
            add("WARN", "정의 용어", "횟수 감소: " + ", ".join(fewer) + " (동의어로 바뀌지 않았는지 확인)")
        else:
            add("OK", "정의 용어", "{}개 모두 유지".format(len(terms)))

    sa, sb = style(before, ko), style(after, ko)
    status = "FAIL" if any(i["level"] == "FAIL" for i in items) else "WARN" if any(i["level"] == "WARN" for i in items) else "OK"
    return {"language": "ko" if ko else "en", "status": status, "items": items,
            "style_before": sa, "style_after": sb}


def to_markdown(res, a_name, b_name):
    mark = {"OK": "통과", "WARN": "경고", "FAIL": "실패"}
    lines = ["# 윤문 점검 보고서", "", "- 원문: `{}`".format(a_name), "- 윤문본: `{}`".format(b_name),
             "- 판정: **{}**".format(mark[res["status"]]), "", "| 판정 | 항목 | 내용 |", "|---|---|---|"]
    for i in res["items"]:
        lines.append("| {} | {} | {} |".format(mark[i["level"]], i["item"], i["detail"].replace("|", "/")))
    lines += ["", "## 문체 지표 (참고용 — 판정에 쓰지 않음)", "", "| 지표 | 윤문 전 | 윤문 후 |", "|---|---|---|"]
    for k in res["style_before"]:
        lines.append("| {} | {} | {} |".format(k, res["style_before"][k], res["style_after"].get(k, "")))
    lines += ["", "> 이 보고서는 '바뀌면 안 되는 것'을 기계적으로 대조한 결과입니다. 통과여도 의미가 같다는 보증은 아니며,",
              "> 최종 채택은 원문과 나란히 놓고 사람이 판단합니다."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="윤문 전후 의미 보존 점검")
    ap.add_argument("before", help="원문 파일")
    ap.add_argument("after", help="윤문본 파일")
    ap.add_argument("--terms", help="바꾸면 안 되는 용어 목록(한 줄에 하나, #은 주석)")
    ap.add_argument("--report", help="보고서를 저장할 .md 경로")
    ap.add_argument("--json", action="store_true", help="JSON으로 출력")
    a = ap.parse_args(argv)
    res = check(read(a.before), read(a.after), load_terms(a.terms))
    if a.json:
        sys.stdout.write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    else:
        md = to_markdown(res, a.before, a.after)
        sys.stdout.write(md)
        if a.report:
            Path(a.report).write_text(md, encoding="utf-8")
    return {"OK": 0, "WARN": 1, "FAIL": 2}[res["status"]]


if __name__ == "__main__":
    sys.exit(main())
