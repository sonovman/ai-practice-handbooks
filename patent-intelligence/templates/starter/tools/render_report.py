#!/usr/bin/env python3
"""보고서 마크다운 → 인쇄용 HTML 한 장 (핸드북 34). 표준 라이브러리만.

  python tools/render_report.py work/reports/report.md --out out/report.html
브라우저로 열고 Ctrl+P → 'PDF로 저장'. DOCX가 필요하면 Word에서 이 HTML을 열어 .docx로 저장하거나,
Claude·ChatGPT·Copilot의 문서 기능으로 report.md를 DOCX로 만드세요(원본은 언제나 report.md 하나).
지원: # 제목, 문단, - / 1. 목록, | 표 |, ![설명](그림.svg), **굵게**, `코드`, > 인용.
"""
import argparse
import html
import re
from pathlib import Path

from pi_common import utf8_console

CSS = """body{font-family:'Pretendard','Malgun Gothic','Apple SD Gothic Neo',sans-serif;max-width:820px;margin:32px auto;padding:0 20px;color:#111;line-height:1.7;font-size:15px;word-break:keep-all}
h1{font-size:26px;margin:0 0 6px}h2{font-size:19px;margin:34px 0 8px;padding-top:10px;border-top:2px solid #111}h3{font-size:16px;margin:22px 0 6px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0}th,td{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left;vertical-align:top}
thead th{border-bottom:2px solid #111}blockquote{margin:12px 0;padding:8px 14px;border-left:3px solid #111;color:#444;background:#f6f6f6}
img{max-width:100%}code{background:#f2f2f2;padding:0 4px;border-radius:3px}
@media print{body{margin:0;font-size:11pt}h2{break-after:avoid}table,img{break-inside:avoid}}"""


def inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"!\[(.*?)\]\((.+?)\)", r'<img alt="\1" src="\2">', s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
    return s


def render(md, title="보고서"):
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        l = lines[i]
        m = re.match(r"^(#{1,4})\s+(.*)", l)
        if m:
            n = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (n, inline(m.group(2)), n))
            i += 1
        elif l.strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], [r for r in rows[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]
            out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
                "".join("<th>%s</th>" % inline(c) for c in head),
                "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r) for r in body)))
        elif re.match(r"^\s*([-*]|\d+\.)\s+", l):
            tag = "ol" if re.match(r"^\s*\d+\.", l) else "ul"
            items = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]))
                i += 1
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(x) for x in items), tag))
        elif l.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> "))
                i += 1
            out.append("<blockquote>%s</blockquote>" % inline(" ".join(buf)))
        elif l.strip():
            buf = []
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||>|\s*([-*]|\d+\.)\s)", lines[i]):
                buf.append(lines[i])
                i += 1
            out.append("<p>%s</p>" % inline(" ".join(buf)))
        else:
            i += 1
    return ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            "<title>%s</title><style>%s</style></head><body>%s</body></html>" % (html.escape(title), CSS, "\n".join(out)))


def main():
    utf8_console()
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--out", default="out/report.html")
    a = ap.parse_args()
    md = Path(a.report).read_text(encoding="utf-8")
    m = re.search(r"^#\s+(.*)", md, re.M)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(md, m.group(1) if m else "보고서"), encoding="utf-8")
    print("저장:", out, "(그림 파일은 같은 폴더 기준 상대경로)")


if __name__ == "__main__":
    main()
