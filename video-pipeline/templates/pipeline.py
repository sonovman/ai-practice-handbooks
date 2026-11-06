#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline.py — AI 영상 제작 파이프라인(핸드북 13편)의 계산·점검·묶음 도구

세 가지 명령
  check-script  대본이 음성 합성(TTS)에 바로 넣을 수 있는지 점검하고 낭독 시간을 어림합니다.
  plan          녹음 길이와 영상 도구의 클립 길이로 장면 수·장면별 시간·생성할 클립 길이를 계산하고
                제작표(CSV)와 에셋 생성기 입력문을 만듭니다. (계산은 AI에게 맡기지 않습니다)
  pack          지식 노트 6개를 두 스킬의 references/에 넣어 업로드용 ZIP을 만들고, 갱신 시기를 알려 줍니다.

사용 예
  python pipeline.py check-script example/script.txt --target 36
  python pipeline.py plan --seconds 36 --script example/script.txt --tool veo31-lite --out plan.csv --asset-input asset-input.md
  python pipeline.py pack --knowledge knowledge --skills skills --out dist

필요한 것: Python 3.8 이상 (추가 설치 없음)
도구별 클립 길이는 2026. 11. 7. 확인 값입니다. 도구 화면에서 다시 확인하고 PRESETS를 고쳐 쓰세요.
"""
import argparse
import csv
import datetime as dt
import math
import re
import sys
import zipfile
from pathlib import Path

# ---------------------------------------------------------------- 도구별 클립 길이
# allowed: 생성할 수 있는 클립 길이(초). range는 정수 초 단위로 고를 수 있는 구간.
PRESETS = {
    "omni-flash-free": {"label": "Flow · Omni Flash 1.2 (무료)", "range": (3, 10)},
    "omni-flash-paid": {"label": "Flow · Omni Flash 1.2 (유료)", "range": (3, 15)},
    "veo31-lite": {"label": "Flow · Veo 3.1 Lite", "allowed": [4, 6, 8]},
    "kling3": {"label": "Kling 3.0", "range": (3, 15)},
    "seedance2": {"label": "Seedance 2.0", "range": (4, 15)},
}

KO_CPS = 4.5   # 한국어 내레이션: 1초에 약 4.5자(공백 제외) — 어림값
EN_WPS = 2.5   # 영어 내레이션: 1초에 약 2.5단어(분당 150단어) — 어림값

SENT_SPLIT = re.compile(r"(?<=[.!?。？！])\s+|\n+")
HANGUL = re.compile(r"[가-힣]")
LABEL = re.compile(r"^\s*(장면|씬|컷|scene|shot|narrator|내레이션|나레이션|vo)\s*\d*\s*[:：)\]]", re.I)
FILLER = ("이 영상에서는", "이번 영상에서는", "오늘 영상에서는", "in this video", "today we will", "today we're going")
BRACKETS = re.compile(r"[\(\)\[\]\{\}<>（）【】]")
SYMBOLS = re.compile(r"[%$₩&/~#@*+=]")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")

PLACEHOLDER = "<!-- 붙여 넣기 전 -->"
ALLOWED_EXT = {".md", ".txt", ".csv", ".json", ".py", ".pdf", ".png", ".jpg", ".jpeg", ".webp"}
SKILL_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# 스킬마다 넣을 지식 노트 (파일 이름 앞 두 자리)
SKILL_KNOWLEDGE = {
    "story-engine": ["01", "02", "03", "04", "05"],
    "asset-generator": ["04", "05", "06"],
}
# 갱신 주기(일): 01~03은 경쟁·트렌드가 빨리 변하고, 06은 도구가 바뀔 때마다 고친다
REFRESH_DAYS = {"01": 90, "02": 90, "03": 90, "04": 365, "05": 365, "06": 120}


def out(s=""):
    print(s)


# ---------------------------------------------------------------- 대본
def sentences(text):
    return [s.strip() for s in SENT_SPLIT.split(text.strip()) if s and s.strip()]


def is_korean(text):
    letters = re.findall(r"[A-Za-z가-힣]", text)
    return bool(letters) and len(HANGUL.findall(text)) / len(letters) > 0.3


def units(s, ko):
    """낭독 분량 단위: 한국어는 공백 뺀 글자 수, 영어는 단어 수"""
    return len(re.sub(r"\s", "", s)) if ko else len(s.split())


def speak_seconds(text, ko=None):
    ko = is_korean(text) if ko is None else ko
    n = units(text, ko)
    return n / (KO_CPS if ko else EN_WPS)


def check_script(text, target=None):
    rows = []
    add = lambda level, rule, detail: rows.append((level, rule, detail))
    ko = is_korean(text)
    sents = sentences(text)
    if not sents:
        add("실패", "대본", "내용이 없습니다.")
        return rows, 0.0
    for i, s in enumerate(sents, 1):
        if LABEL.search(s):
            add("실패", "장면 라벨", "{}번 문장 '{}' — 라벨·화자 표시는 그대로 읽힙니다. 지우세요.".format(i, s[:20]))
        if BRACKETS.search(s):
            add("주의", "괄호", "{}번 문장 — 괄호 속 지시문도 소리 내 읽힙니다.".format(i))
        if any(f in s.lower() for f in FILLER):
            add("주의", "군더더기 오프닝", "{}번 문장 — 첫 5초를 쓰는 말은 시청 이탈을 부릅니다. 바로 핵심으로 들어가세요.".format(i))
        if ko and len(s) > 40:
            add("주의", "긴 문장", "{}번 문장 {}자 — 한 호흡(약 30자, 공백 포함)으로 나누세요.".format(i, len(s)))
        if not ko and len(s.split()) > 12:
            add("주의", "긴 문장", "{}번 문장 {}단어 — 12단어 이내로 나누세요.".format(i, len(s.split())))
        sym = sorted(set(SYMBOLS.findall(s)))
        if sym:
            add("주의", "기호 읽기", "{}번 문장 {} — TTS가 읽는 방식을 들어 보거나 글자로 풀어 쓰세요(예: % → 퍼센트).".format(i, " ".join(sym)))
        if EMOJI.search(s):
            add("주의", "이모지", "{}번 문장 — 이모지는 지우세요.".format(i))
    secs = speak_seconds(text, ko)
    if target:
        gap = (secs - target) / target
        if abs(gap) > 0.15:
            add("주의", "길이", "어림 {:.0f}초 / 목표 {}초 ({:+.0%}) — 녹음 후 실제 길이로 다시 확인하세요.".format(secs, target, gap))
    return rows, secs


# ---------------------------------------------------------------- 장면 계획
def allowed_clips(tool=None, clip=None):
    if tool:
        p = PRESETS[tool]
        if "allowed" in p:
            return list(p["allowed"])
        lo, hi = p["range"]
        return list(range(lo, hi + 1))
    return [clip or 5]


def pick_clip(need, allowed):
    """need초를 덮는 가장 짧은 클립. 없으면 가장 긴 클립(None 표시)."""
    for c in sorted(allowed):
        if c + 1e-9 >= need:
            return c, True
    return max(allowed), False


def min_scenes(seconds, usable):
    return max(1, math.ceil(seconds / usable - 1e-9))


def plan(seconds, script=None, tool=None, clip=None, transition=0.5, stretch=0.15):
    allowed = allowed_clips(tool, clip)
    if clip is not None and clip not in allowed:
        raise ValueError("{}초 클립은 이 도구에서 고를 수 없습니다. 가능한 값: {}".format(clip, allowed))
    base = clip if clip is not None else pick_clip(5, allowed)[0]
    usable = base - transition
    if usable <= 0:
        raise ValueError("클립 길이가 전환 여유보다 짧습니다.")
    n_min = min_scenes(seconds, usable)
    # 한 문장을 한 장면에 담을 수 있는 최대 길이: 가장 긴 클립을 속도 조절(stretch)까지 해서 덮는 길이
    longest = (max(allowed) - transition) * (1 + stretch)
    scenes = []
    if script:
        sents = sentences(script)
        ko = is_korean(script)
        w = [max(1, units(s, ko)) for s in sents]
        scale = seconds / sum(w)
        durs = [x * scale for x in w]
        # 문장 경계에서 자르되, 한 장면이 사용 가능 길이를 넘지 않게 묶는다
        group, gdur = [], 0.0
        groups = []
        for s, d in zip(sents, durs):
            if d > usable:                      # 기준보다 긴 문장은 혼자 한 장면
                if group:
                    groups.append((group, gdur))
                    group, gdur = [], 0.0
                k = 1 if d <= longest + 1e-9 else math.ceil(d / (max(allowed) - transition) - 1e-9)
                for j in range(k):              # 그래도 넘치면 같은 문장을 컷 두 개 이상으로(B컷)
                    groups.append(([s if j == 0 else "(같은 문장 · 다음 컷)"], d / k))
                continue
            if group and gdur + d > usable + 1e-9:
                groups.append((group, gdur))
                group, gdur = [], 0.0
            group.append(s)
            gdur += d
        if group:
            groups.append((group, gdur))
        t = 0.0
        for g, d in groups:
            scenes.append({"text": " ".join(g), "start": t, "end": t + d, "dur": d})
            t += d
    else:
        per = seconds / n_min
        for k in range(n_min):
            scenes.append({"text": "", "start": k * per, "end": (k + 1) * per, "dur": per})
    for s in scenes:
        c, ok = pick_clip(s["dur"] + transition, allowed)
        s["speed"] = 1.0
        if not ok:
            speed = (c - transition) / s["dur"]
            if speed >= 1 / (1 + stretch) - 1e-9:   # 편집기에서 조금 느리게 재생하면 덮인다
                s["speed"], ok = speed, True
        s["clip"], s["fits"] = c, ok
    return {"allowed": allowed, "base": base, "usable": usable, "n_min": n_min, "scenes": scenes,
            "tool": PRESETS[tool]["label"] if tool else "클립 {}초 고정".format(base), "transition": transition,
            "seconds": seconds}


def write_csv(p, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(["장면", "시작(초)", "끝(초)", "길이(초)", "생성할 클립(초)", "재생 속도", "대본 구간", "이미지 프롬프트", "비디오 프롬프트", "사실적 인물·장소"])
        for i, s in enumerate(p["scenes"], 1):
            wr.writerow([i, "{:.1f}".format(s["start"]), "{:.1f}".format(s["end"]), "{:.1f}".format(s["dur"]),
                         s["clip"], "{:.0%}".format(s["speed"]), s["text"], "", "", ""])


def asset_input(p, script, style=None):
    lines = ["/asset-generator", "", "대본:", script.strip(), "",
             "녹음 길이: {:g}초".format(p["seconds"]),
             "영상 도구: {} (고를 수 있는 클립 {}초, 전환 여유 {:g}초)".format(
                 p["tool"], _fmt_allowed(p["allowed"]), p["transition"])]
    if style:
        lines.append("비주얼 스타일(고정): " + style)
    lines += ["", "장면 계획 — pipeline.py로 계산을 마쳤으니 장면 수와 시간은 다시 계산하지 말고 그대로 따를 것:", "",
              "| 장면 | 시작 | 끝 | 길이 | 생성할 클립 | 대본 구간 |", "|---|---|---|---|---|---|"]
    for i, s in enumerate(p["scenes"], 1):
        clip = "{}초".format(s["clip"]) + ("" if s["speed"] == 1.0 else " ({:.0%} 속도)".format(s["speed"]))
        lines.append("| {} | {:.1f} | {:.1f} | {:.1f}초 | {} | {} |".format(
            i, s["start"], s["end"], s["dur"], clip, s["text"] or "(직접 나눔)"))
    return "\n".join(lines) + "\n"


def _fmt_allowed(a):
    if len(a) > 4 and a == list(range(a[0], a[-1] + 1)):
        return "{}~{}".format(a[0], a[-1])
    return "/".join(str(x) for x in a)


# ---------------------------------------------------------------- 지식 노트 묶기
def read_date(text):
    m = re.search(r"갱신일\s*[:：]\s*(\d{4}-\d{2}-\d{2})", text)
    return dt.date.fromisoformat(m.group(1)) if m else None


def skill_name(skill_md):
    m = re.search(r"^---\s*\n(.*?)\n---", skill_md, re.S)
    if not m:
        return None
    n = re.search(r"^name:\s*(\S+)", m.group(1), re.M)
    return n.group(1).strip() if n else None


def pack(knowledge, skills, dest, today=None, strict=False):
    today = today or dt.date.today()
    rows = []
    add = lambda level, rule, detail: rows.append((level, rule, detail))
    knowledge, skills, dest = Path(knowledge), Path(skills), Path(dest)
    notes = {}
    for f in sorted(knowledge.glob("*.md")):
        key = f.name[:2]
        if key.isdigit():
            notes[key] = f
    for key in sorted(REFRESH_DAYS):
        f = notes.get(key)
        if not f:
            add("실패", "지식 노트", "{}번 노트 파일이 없습니다.".format(key))
            continue
        text = f.read_text(encoding="utf-8-sig")
        if PLACEHOLDER in text:
            add("실패" if strict else "주의", "지식 노트", "{} — 아직 보고서를 붙여 넣지 않았습니다.".format(f.name))
        d = read_date(text)
        if not d:
            add("주의", "갱신일", "{} — '갱신일: YYYY-MM-DD' 줄이 없습니다.".format(f.name))
        else:
            age = (today - d).days
            if age > REFRESH_DAYS[key]:
                add("주의", "갱신 시기", "{} — {}일 지났습니다(주기 {}일). 노트북을 다시 돌려 보고서를 바꾸세요.".format(f.name, age, REFRESH_DAYS[key]))
            else:
                add("정보", "갱신 시기", "{} — {}일 전 갱신(주기 {}일)".format(f.name, age, REFRESH_DAYS[key]))
    dest.mkdir(parents=True, exist_ok=True)
    made = []
    for name, keys in SKILL_KNOWLEDGE.items():
        sdir = skills / name
        md = sdir / "SKILL.md"
        if not md.exists():
            add("실패", "스킬", "{}가 없습니다.".format(md))
            continue
        declared = skill_name(md.read_text(encoding="utf-8-sig"))
        if declared != name or not SKILL_NAME.match(name):
            add("실패", "스킬 이름", "{} — name은 폴더 이름과 같은 영문 소문자·하이픈이어야 합니다(지금: {}).".format(name, declared))
        zpath = dest / (name + ".zip")
        total = 0
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(sdir.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts:
                    if f.suffix.lower() not in ALLOWED_EXT:
                        add("주의", "파일 형식", "{} — 스킬에 넣기 어려운 형식입니다(.docx·.xlsx는 PDF·CSV로 바꾸기).".format(f.name))
                        continue
                    z.write(f, (Path(name) / f.relative_to(sdir)).as_posix())
                    total += f.stat().st_size
            for key in keys:
                f = notes.get(key)
                if f:
                    z.write(f, (Path(name) / "references" / f.name).as_posix())
                    total += f.stat().st_size
        if total > 100 * 1024 * 1024:
            add("실패", "용량", "{} — 100MB를 넘습니다.".format(zpath.name))
        made.append(zpath)
        add("정보", "묶음", "{} ← SKILL.md + 노트 {}".format(zpath.name, ", ".join(keys)))
    return rows, made


# ---------------------------------------------------------------- 실행
def report(title, rows):
    out(title + "\n")
    if not rows:
        out("[통과] 지적할 곳이 없습니다.")
    for level, rule, detail in rows:
        out("[{}] {:<8} {}".format(level, rule, detail))
    fails = sum(1 for r in rows if r[0] == "실패")
    warns = sum(1 for r in rows if r[0] == "주의")
    out("\n실패 {}건 · 주의 {}건".format(fails, warns))
    return fails


def main(argv=None):
    ap = argparse.ArgumentParser(description="AI 영상 제작 파이프라인 도구")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check-script", help="대본 점검")
    c.add_argument("file")
    c.add_argument("--target", type=float, help="목표 길이(초)")
    p = sub.add_parser("plan", help="장면 계획")
    p.add_argument("--seconds", type=float, required=True, help="녹음한 음성의 실제 길이(초)")
    p.add_argument("--script", help="대본 파일(있으면 문장 경계에서 장면을 나눔)")
    p.add_argument("--tool", choices=sorted(PRESETS), help="영상 도구")
    p.add_argument("--clip", type=int, help="기준 클립 길이(초). 생략하면 5초에 가장 가까운 값")
    p.add_argument("--transition", type=float, default=0.5, help="전환 여유(초), 기본 0.5")
    p.add_argument("--stretch", type=float, default=0.15, help="편집에서 느리게 재생해 늘일 수 있는 비율, 기본 0.15")
    p.add_argument("--style", help="고정할 비주얼 스타일")
    p.add_argument("--out", help="제작표 CSV 저장 경로")
    p.add_argument("--asset-input", help="에셋 생성기에 붙여 넣을 입력문 저장 경로")
    k = sub.add_parser("pack", help="스킬 묶기")
    k.add_argument("--knowledge", default="knowledge")
    k.add_argument("--skills", default="skills")
    k.add_argument("--out", default="dist")
    k.add_argument("--strict", action="store_true", help="빈 노트가 있으면 실패로 처리")
    k.add_argument("--today", help="기준일 YYYY-MM-DD (시험용)")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if a.cmd == "check-script":
        text = Path(a.file).read_text(encoding="utf-8-sig")
        rows, secs = check_script(text, a.target)
        fails = report("대본 점검 — {}".format(a.file), rows)
        out("문장 {}개 · 어림 낭독 {:.0f}초 (실제 길이는 녹음 후 측정)".format(len(sentences(text)), secs))
        return 1 if fails else 0

    if a.cmd == "plan":
        script = Path(a.script).read_text(encoding="utf-8-sig") if a.script else None
        try:
            r = plan(a.seconds, script, a.tool, a.clip, a.transition, a.stretch)
        except ValueError as e:
            out("오류: " + str(e))
            return 2
        out("장면 계획 — {} · 녹음 {:g}초".format(r["tool"], a.seconds))
        out("기준 클립 {}초 − 전환 {:g}초 = 장면당 최대 {:g}초".format(r["base"], a.transition, r["usable"]))
        out("최소 장면 수 = {:g} ÷ {:g} → 올림 {}개".format(a.seconds, r["usable"], r["n_min"]))
        if script:
            out("문장 경계 기준 장면 수 {}개".format(len(r["scenes"])))
        out("")
        for i, s in enumerate(r["scenes"], 1):
            mark = "" if s["fits"] else "  ← 클립이 모자람: 장면을 나누거나 마지막 프레임을 늘이세요"
            if s["speed"] != 1.0:
                mark = "  (편집에서 {:.0%} 속도)".format(s["speed"])
            out("{:>2}. {:>5.1f}~{:>5.1f}초 ({:.1f}초) 클립 {}초  {}{}".format(
                i, s["start"], s["end"], s["dur"], s["clip"], s["text"][:26], mark))
        total_clip = sum(s["clip"] for s in r["scenes"])
        out("\n생성할 클립 합계 {}초 (녹음 {:g}초)".format(total_clip, a.seconds))
        if a.out:
            write_csv(r, a.out)
            out("저장: " + a.out)
        if a.asset_input:
            if not script:
                out("알림: --asset-input은 --script가 있어야 만듭니다.")
            else:
                Path(a.asset_input).write_text(asset_input(r, script, a.style), encoding="utf-8")
                out("저장: " + a.asset_input)
        return 0

    today = dt.date.fromisoformat(a.today) if a.today else None
    rows, made = pack(a.knowledge, a.skills, a.out, today, a.strict)
    fails = report("스킬 묶기 — {} + {} → {}".format(a.knowledge, a.skills, a.out), rows)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
