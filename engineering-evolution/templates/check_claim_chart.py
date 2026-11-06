"""청구항 대비표 형식 검사기 (루프의 '검증자' 역할)

사용법
  python check_claim_chart.py output/claim-chart.md          # 직접 검사
  python check_claim_chart.py output/claim-chart.md --hook   # Claude Code Stop Hook으로 사용

검사 항목 (형식만 봅니다. 법적 판단이 맞는지는 사람이 봅니다)
  1. 대비표에 구성요소 행(E1, E2 …)이 있는가
  2. 각 행의 대응 기재에 단락 번호【0000】나 도면 번호가 있는가 (또는 '미개시')
  3. '미개시' 행에 차이점 설명이 있는가
  4. 신규성·진보성 항목이 있고, 진보성에 '곤란성'과 '효과'가 모두 나오는가
  5. ____ 나 [구성 1] 같은 빈칸이 남아 있지 않은가

Hook 모드
  문제가 있으면 종료 코드 2로 끝나 에이전트가 멈추지 못하고 고치러 돌아갑니다.
  같은 파일로 3번 실패하면 더 붙잡지 않고 멈추게 두며, REVIEW_NEEDED.txt 를 남깁니다.
  Python 표준 라이브러리만 씁니다.
"""
import json
import re
import sys
from pathlib import Path

MAX_ATTEMPTS = 3
CITE = re.compile(r"【\d{4}】|도\s?\d+|도면\s?\d+")
ROW = re.compile(r"^\|\s*\**(E\d+)\**\s*\|")


def check(text):
    problems = []

    if re.search(r"_{3,}|\[구성\s*\d+\]", text):
        problems.append("빈칸(____ 또는 [구성 N])이 남아 있습니다.")

    rows = [line for line in text.splitlines() if ROW.match(line)]
    if not rows:
        problems.append("대비표에 구성요소 행(E1, E2 …)이 없습니다.")

    for line in rows:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            problems.append(f"{cells[0]}: 칸이 4개(ID·구성요소·대응 기재·차이점)보다 적습니다.")
            continue
        eid, _, disclosure, diff = cells[:4]
        eid = eid.strip("*")
        if "미개시" in disclosure:
            if len(diff) < 6 or "차이" not in diff:
                problems.append(f"{eid}: 미개시인데 차이점 설명이 없습니다.")
        elif not CITE.search(disclosure):
            problems.append(f"{eid}: 선행문헌 단락 번호【0000】나 도면 번호가 없습니다.")

    if "신규성" not in text:
        problems.append("신규성(제29조 제1항) 판단이 없습니다.")
    if "진보성" not in text:
        problems.append("진보성(제29조 제2항) 판단이 없습니다.")
    else:
        tail = text[text.index("진보성"):]
        if "곤란성" not in tail:
            problems.append("진보성 판단에 '구성의 곤란성' 근거가 없습니다.")
        if "효과" not in tail:
            problems.append("진보성 판단에 '효과의 현저성' 근거가 없습니다.")

    return problems


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    hook = "--hook" in sys.argv
    if not args:
        print("사용법: python check_claim_chart.py <대비표.md> [--hook]")
        return 1
    path = Path(args[0])

    if hook:
        try:
            json.load(sys.stdin)  # Claude Code가 넘겨주는 정보 (여기서는 쓰지 않음)
        except Exception:
            pass
        if not path.exists():
            return 0  # 아직 대비표를 만드는 작업이 아니면 통과

    if not path.exists():
        print(f"파일이 없습니다: {path}")
        return 1

    problems = check(path.read_text(encoding="utf-8"))

    if not hook:
        if problems:
            print("FAIL")
            for p in problems:
                print(" -", p)
            return 1
        print("PASS")
        return 0

    counter = path.with_name(".check_attempts")
    attempts = int(counter.read_text()) if counter.exists() else 0
    if not problems:
        counter.unlink(missing_ok=True)
        return 0
    attempts += 1
    if attempts >= MAX_ATTEMPTS:
        counter.unlink(missing_ok=True)
        path.with_name("REVIEW_NEEDED.txt").write_text(
            f"{MAX_ATTEMPTS}회 고쳐도 통과하지 못했습니다. 담당자 확인이 필요합니다.\n"
            + "\n".join("- " + p for p in problems),
            encoding="utf-8",
        )
        return 0
    counter.write_text(str(attempts))
    sys.stderr.write(
        f"[대비표 검수 {attempts}/{MAX_ATTEMPTS}회차 FAIL] 아래를 고친 뒤 끝내세요.\n"
        + "\n".join("- " + p for p in problems)
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
