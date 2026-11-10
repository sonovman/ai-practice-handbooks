#!/usr/bin/env python3
"""Copilot(SharePoint 지식)용 내보내기 (핸드북 34). 표준 라이브러리만.

Microsoft 365 Copilot 에이전트는 SharePoint의 .docx·.pdf·.pptx·.txt·.xlsx·.html 등을 읽고
.md·.json·.csv·.svg는 지식으로 읽지 못한다. 그래서 도구 결과를 Copilot이 읽는 형식으로 바꿔
SharePoint(동기화 폴더)의 회차 폴더에 둔다.

  python tools/export_for_copilot.py work "<동기화된 SharePoint 경로>/rounds/2026-R4/03_검증집계"

만드는 것
  01_intake.html · 02_stats.html(SVG 차트를 본문에 넣음) · 03_analysis.html · report.html · lint*.html
  clusters.xlsx · scores.xlsx (한 시트)
  state.txt (관문 상태 — Copilot이 '지금 어느 관문인지' 읽게)
  copilot_manifest.txt (무엇이 어디서 왔는지, 숫자는 이 파일들에서만 쓰라는 안내)
"""
import argparse
import csv
import json
import re
from pathlib import Path

from pi_common import utf8_console, write_xlsx
from render_report import render
import pi_gate

MD_FILES = ["01_intake.md", "02_stats.md", "03_analysis.md", "04_candidates.md",
            "reports/report.md", "reports/lint_good.md", "reports/lint.md"]


def inline_svgs(html_text, base):
    def rep(m):
        p = (base / m.group(2)).resolve()
        if p.suffix.lower() == ".svg" and p.exists():
            return p.read_text(encoding="utf-8")
        return m.group(0)
    return re.sub(r'<img alt="(.*?)" src="(.+?)">', rep, html_text)


def export(work, out):
    work, out = Path(work), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for rel in MD_FILES:
        src = work / rel
        if not src.exists():
            continue
        md = src.read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.*)", md, re.M)
        h = render(md, m.group(1) if m else src.stem)
        if rel == "02_stats.md":
            charts = "".join((work / c).read_text(encoding="utf-8") for c in ("chart_trend.svg", "chart_groups.svg") if (work / c).exists())
            h = h.replace("</body>", charts + "</body>")
        h = inline_svgs(h, src.parent)
        dst = out / (Path(rel).stem + ".html")
        dst.write_text(h, encoding="utf-8")
        made.append(dst.name)
    for name in ("clusters.csv", "scores.csv"):
        for cand in (work / name, work.parent / "inbox" / name):
            if cand.exists():
                with open(cand, encoding="utf-8-sig", newline="") as f:
                    rows = list(csv.reader(f))
                write_xlsx(out / name.replace(".csv", ".xlsx"), rows, sheet_name=name[:-4])
                made.append(name.replace(".csv", ".xlsx"))
                break
    st = work / "state.json"
    if st.exists():
        (out / "state.txt").write_text(pi_gate.status_text(json.loads(st.read_text(encoding="utf-8"))) + "\n", encoding="utf-8")
        made.append("state.txt")
    manifest = ["Copilot용 내보내기 목록 (핸드북 34 · patent-intelligence)", "",
                "숫자(문헌·패밀리·기술신호·연도·점수)는 01_intake.html·02_stats.html에서만 인용한다.",
                "관문 상태는 state.txt를 따른다. 승인 전 단계의 산출물은 '초안'이다.", ""] + ["- " + x for x in made]
    (out / "copilot_manifest.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    made.append("copilot_manifest.txt")
    return made


def main():
    utf8_console()
    ap = argparse.ArgumentParser(description="Copilot(SharePoint)용 내보내기")
    ap.add_argument("work")
    ap.add_argument("out")
    a = ap.parse_args()
    made = export(a.work, a.out)
    print("내보냄 %d개 →" % len(made), a.out)
    for x in made:
        print("  -", x)


if __name__ == "__main__":
    main()
