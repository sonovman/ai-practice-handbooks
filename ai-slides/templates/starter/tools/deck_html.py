#!/usr/bin/env python3
"""슬라이드 개요 → 미리보기 HTML 덱 (핸드북 24). 표준 라이브러리만 사용.

발표자료_초안.md(슬라이드 개요)를 '눈으로 볼 수 있는' 한 장짜리 HTML 덱으로 바꿔 줍니다.
비주얼 QA(글자 겹침·줄바꿈·여백 쏠림)를 사람이 바로 확인하기 위한 보조 도구입니다. PPTX를 만들진 않습니다.

  python tools/deck_html.py 발표자료_초안.md --out work/deck.html
  python tools/deck_html.py 초안.md               # 화면(표준출력)으로 HTML

입력 형식: 슬라이드는 '# [Slide N] 제목'으로 시작, 그 아래 '- key: value' 또는 '- 내용' 줄들.
  Layout: Type X 줄은 좌상단 배지로 표시됩니다. 외부 글꼴·스크립트·네트워크를 쓰지 않습니다.

주의: 실제 PPTX 변환이 아니라 '검토용 미리보기'입니다. 색·폰트는 디자인.md를 그대로 반영하지 않습니다
      (개요가 레이아웃대로 배치됐는지, 글이 넘치지 않는지 확인하는 용도).
"""
import argparse
import html
import re
import sys
from pathlib import Path

CSS = """
:root{--navy:#1A2B4C;--ink:#1f2430;--line:#e3e6ec;--bg:#f8f9fa;--accent:#FF6B35}
*{box-sizing:border-box}
body{margin:0;background:#eceff3;font-family:system-ui,-apple-system,'Segoe UI','Malgun Gothic',sans-serif;color:var(--ink)}
.wrap{max-width:980px;margin:0 auto;padding:24px 16px}
h1.deck{font-size:18px;color:#5b6472;font-weight:600;margin:4px 0 16px}
.slide{position:relative;background:#fff;border:1px solid var(--line);border-radius:10px;
  aspect-ratio:16/9;margin:0 0 18px;padding:34px 38px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.badge{position:absolute;top:12px;right:14px;font-size:12px;color:#8a93a3;border:1px solid var(--line);
  border-radius:999px;padding:2px 10px;background:var(--bg)}
.snum{position:absolute;bottom:12px;right:16px;font-size:12px;color:#aab2bf}
.slide h2{margin:0 0 6px;font-size:25px;color:var(--navy);line-height:1.25}
.slide .sub{color:#5b6472;font-size:15px;margin:0 0 14px}
.rows{display:flex;flex-direction:column;gap:7px}
.row{font-size:15px;line-height:1.5}
.row b{color:var(--navy)}
.cols{display:flex;gap:14px;margin-top:6px}
.col{flex:1;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:12px 14px;font-size:14px;line-height:1.5}
.hl{color:var(--accent);font-weight:700}
"""


def parse(text):
    """[(title, layout, [(key,val) or (None,line)]), ...]"""
    # 제목 줄 전체를 경계로 소비(제목이 본문 행으로 새지 않게)
    parts = re.split(r"(?m)^#\s*\[[Ss]lide[^\]]*\].*$\n?", text)
    heads = re.findall(r"(?m)^#\s*\[[Ss]lide[^\]]*\]\s*(.*)$", text)
    slides = []
    bodies = parts[1:] if len(parts) > 1 else []
    for i, body in enumerate(bodies):
        title = heads[i].strip() if i < len(heads) else "(제목 없음)"
        layout = None
        rows = []
        for raw in body.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            line = re.sub(r"^[-*]\s*", "", line)
            m = re.match(r"(?i)^(Layout)\s*[:：]\s*(.+)$", line)
            if m:
                layout = m.group(2).strip()
                continue
            km = re.match(r"^([^:：]{1,24})[:：]\s*(.+)$", line)
            if km:
                rows.append((km.group(1).strip(), km.group(2).strip()))
            else:
                rows.append((None, line))
        slides.append((title, layout, rows))
    return slides


def emph(s):
    s = html.escape(s)
    # 괄호 안 수치/퍼센트 강조
    s = re.sub(r"(\d[\d,\.]*\s*(?:%|억|만|일|배))", r"<span class='hl'>\1</span>", s)
    return s


def render_rows(rows):
    # 좌/우(Left/Right) 또는 Card 가 있으면 2열/카드로, 아니면 목록으로
    cols = [v for k, v in rows if k and re.search(r"(?i)left|right|col|card|좌|우", k)]
    out = []
    if len(cols) >= 2:
        out.append("<div class='cols'>")
        for k, v in rows:
            if k and re.search(r"(?i)left|right|col|card|좌|우", k):
                out.append("<div class='col'><b>{}</b><br>{}</div>".format(html.escape(k), emph(v)))
        out.append("</div>")
        # 나머지 일반 줄
        for k, v in rows:
            if not (k and re.search(r"(?i)left|right|col|card|좌|우", k)):
                lbl = "<b>{}</b> ".format(html.escape(k)) if k else ""
                out.append("<div class='row'>{}{}</div>".format(lbl, emph(v)))
    else:
        out.append("<div class='rows'>")
        for k, v in rows:
            lbl = "<b>{}</b> ".format(html.escape(k)) if k else ""
            out.append("<div class='row'>{}{}</div>".format(lbl, emph(v)))
        out.append("</div>")
    return "\n".join(out)


def build(slides, title="슬라이드 미리보기"):
    H = ["<!doctype html><html lang='ko'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width, initial-scale=1'>",
         "<title>{}</title><style>{}</style></head><body><div class='wrap'>".format(html.escape(title), CSS),
         "<h1 class='deck'>{} · 검토용 미리보기(실제 PPTX 아님)</h1>".format(html.escape(title))]
    for i, (t, layout, rows) in enumerate(slides, 1):
        sub = ""
        keep = []
        for k, v in rows:
            if k and re.search(r"(?i)subtitle|sub|부제", k):
                sub = "<p class='sub'>{}</p>".format(emph(v)); continue
            if k and re.search(r"(?i)^title$|제목", k):
                continue
            keep.append((k, v))
        badge = "<div class='badge'>{}</div>".format(html.escape(layout)) if layout else ""
        H.append("<section class='slide'>{}<h2>{}</h2>{}{}<div class='snum'>{}</div></section>"
                 .format(badge, emph(t), sub, render_rows(keep), i))
    H.append("</div></body></html>")
    return "\n".join(H)


def main(argv=None):
    ap = argparse.ArgumentParser(description="슬라이드 개요 → 미리보기 HTML")
    ap.add_argument("path")
    ap.add_argument("--out")
    ap.add_argument("--title", default="슬라이드 미리보기")
    a = ap.parse_args(argv)
    text = Path(a.path).read_text(encoding="utf-8", errors="replace")
    slides = parse(text)
    if not slides:
        sys.exit("슬라이드를 찾지 못했습니다. '# [Slide N] 제목' 형식인지 확인하세요.")
    doc = build(slides, a.title)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(doc, encoding="utf-8")
        sys.stdout.write("생성: {} ({}장)\n".format(a.out, len(slides)))
    else:
        sys.stdout.write(doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
