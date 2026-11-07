#!/usr/bin/env python3
"""내 PC의 Ollama로 윤문하기 (핸드북 18). 표준 라이브러리만 사용.

문서를 밖으로 보내지 않는 구성입니다. 접속 주소는 이 PC(127.0.0.1·localhost·::1)만 허용합니다.

  python tools/ollama_polish.py 원문.md                       # 언어 자동 판별, 결과: 원문.polished.md
  python tools/ollama_polish.py 원문.md --legal --terms terms.txt
  python tools/ollama_polish.py 원문.md --model qwen3.5:9b --num-ctx 8192

동작
  1) prompts/protect.md (+ --legal 이면 prompts/legal-addon.md) 와 언어별 참고 규칙을 시스템 지시로 넣고
  2) 문단 묶음(기본 1,200자) 단위로 윤문을 요청한 뒤 (제목·코드 블록은 그대로 통과)
  3) 결과를 저장하고 tools/polish_check.py 로 의미 보존 점검 보고서를 만듭니다.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import polish_check  # noqa: E402

DEFAULT_RULES = {
    "ko": ROOT / ".agents/skills/humanize-korean/references/quick-rules.md",
    "en": ROOT / ".agents/skills/humanizer/SKILL.md",
}
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
START, END = "<<<윤문본>>>", "<<<끝>>>"


def out(msg):
    sys.stderr.write(msg + "\n")


def check_local(url):
    host = urllib.parse.urlparse(url).hostname or ""
    if host not in LOCAL_HOSTS:
        raise SystemExit("거부: {} — 이 도구는 내 PC의 Ollama(127.0.0.1)에만 접속합니다. "
                         "다른 사람이 운영하는 서버로 문서를 보내지 마세요.".format(host or url))


def split_blocks(text, limit):
    """제목·코드 블록은 ('keep', 원문), 본문은 문단을 묶어 ('edit', 묶음)으로."""
    blocks, buf, in_code, code = [], [], False, []

    def flush():
        if buf:
            blocks.append(("edit", "\n\n".join(buf)))
            buf.clear()

    size = 0
    for para in re.split(r"\n\s*\n", text.strip("\n")):
        if in_code or para.lstrip().startswith("```"):
            code.append(para)
            fences = sum(p.count("```") for p in code)
            in_code = fences % 2 == 1
            if not in_code:
                flush(); size = 0
                blocks.append(("keep", "\n\n".join(code)))
                code = []
            continue
        if re.match(r"^\s{0,3}#{1,6}\s", para) and "\n" not in para.strip():
            flush(); size = 0
            blocks.append(("keep", para))
            continue
        if size + len(para) > limit and buf:
            flush(); size = 0
        buf.append(para)
        size += len(para)
    if code:
        blocks.append(("keep", "\n\n".join(code)))
    flush()
    return blocks


def build_system(lang, legal, rules_path, max_rules):
    parts = [(ROOT / "prompts" / "protect.md").read_text(encoding="utf-8")]
    if legal:
        parts.append((ROOT / "prompts" / "legal-addon.md").read_text(encoding="utf-8"))
    rp = Path(rules_path) if rules_path else DEFAULT_RULES[lang]
    if rp.is_file():
        rules = rp.read_text(encoding="utf-8")
        rules = re.sub(r"<!--.*?-->", "", rules, flags=re.S)
        if len(rules) > max_rules:
            rules = rules[:max_rules] + "\n…(이하 생략)"
        parts.append("참고 윤문 규칙\n" + rules)
    else:
        out("참고 규칙 파일이 없어 보호 지침만으로 진행합니다: " + str(rp) +
            "  (python tools/setup_skills.py 로 설치하면 함께 쓰입니다)")
    parts.append("이번 작업의 출력은 윤문본만 {} 와 {} 사이에 넣는다. 변경 설명은 쓰지 않는다. "
                 "고칠 곳이 없으면 원문을 그대로 넣는다.".format(START, END))
    return "\n\n".join(parts)


def chat(host, model, system, user, num_ctx, timeout):
    body = json.dumps({
        "model": model, "stream": False, "think": False,
        "options": {"temperature": 0.2, "num_ctx": num_ctx},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }).encode("utf-8")
    req = urllib.request.Request(host.rstrip("/") + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    # 프록시 환경 변수가 있어도 로컬 주소는 직접 접속
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise SystemExit("Ollama에 연결하지 못했습니다({}). Ollama 앱이 켜져 있는지, "
                         "'ollama list'에 {} 가 있는지 확인하세요.".format(e.reason, model))
    return data.get("message", {}).get("content", "")


def extract(reply, original):
    reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.S)
    m = re.search(re.escape(START) + r"\s*(.*?)\s*" + re.escape(END), reply, flags=re.S)
    if m:
        return m.group(1).strip()
    if START in reply:
        return reply.split(START, 1)[1].strip()
    out("  주의: 표지를 찾지 못해 이 묶음은 원문을 유지합니다.")
    return original


def main(argv=None):
    ap = argparse.ArgumentParser(description="로컬 Ollama 윤문 + 의미 보존 점검")
    ap.add_argument("input")
    ap.add_argument("--out", help="결과 파일 (기본: 입력이름.polished.md)")
    ap.add_argument("--model", default="gemma4", help="ollama list 에 있는 모델 (기본 gemma4)")
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    ap.add_argument("--lang", choices=["auto", "ko", "en"], default="auto")
    ap.add_argument("--legal", action="store_true", help="특허·법률 추가 보호 규칙 사용")
    ap.add_argument("--rules", help="참고 규칙 파일 직접 지정")
    ap.add_argument("--terms", help="바꾸면 안 되는 용어 목록 (점검에 사용)")
    ap.add_argument("--chunk", type=int, default=1200, help="한 번에 보낼 본문 글자 수")
    ap.add_argument("--num-ctx", type=int, default=8192, help="문맥 길이(기본 Ollama 4096보다 넉넉히)")
    ap.add_argument("--max-rules", type=int, default=9000, help="참고 규칙 최대 글자 수")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args(argv)

    check_local(a.host)
    src = Path(a.input)
    text = src.read_text(encoding="utf-8-sig")
    lang = a.lang if a.lang != "auto" else ("ko" if polish_check.is_korean(text) else "en")
    system = build_system(lang, a.legal, a.rules, a.max_rules)
    blocks = split_blocks(text, a.chunk)
    edits = sum(1 for k, _ in blocks if k == "edit")
    out("언어 {} · 모델 {} · 윤문 묶음 {}개".format(lang, a.model, edits))

    result, n = [], 0
    for kind, body in blocks:
        if kind == "keep":
            result.append(body)
            continue
        n += 1
        out("  [{}/{}] {}자".format(n, edits, len(body)))
        reply = chat(a.host, a.model, system, "원문:\n" + body, a.num_ctx, a.timeout)
        result.append(extract(reply, body))

    dst = Path(a.out) if a.out else src.with_suffix(".polished.md")
    dst.write_text("\n\n".join(result) + "\n", encoding="utf-8")
    report = dst.with_suffix(".report.md")
    res = polish_check.check(text, dst.read_text(encoding="utf-8"), polish_check.load_terms(a.terms))
    report.write_text(polish_check.to_markdown(res, str(src), str(dst)), encoding="utf-8")
    label = {"OK": "통과", "WARN": "경고 — 사람이 확인", "FAIL": "실패 — 채택하지 말 것"}[res["status"]]
    out("저장: {}\n점검: {} ({})".format(dst, report, label))
    return {"OK": 0, "WARN": 1, "FAIL": 2}[res["status"]]


if __name__ == "__main__":
    sys.exit(main())
