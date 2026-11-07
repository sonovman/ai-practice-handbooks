#!/usr/bin/env python3
"""AI 회의 준비물 만들기 (핸드북 19). 표준 라이브러리만 사용.

한 대화에서 AI 한 개가 모든 역할을 연기하면 의견이 빨리 한쪽으로 모입니다.
이 도구는 역할마다 '따로 붙여 넣을 프롬프트'를 만들어, 서로 다른 대화·서로 다른 모델에서
독립적으로 의견을 받은 뒤 의장 프롬프트로 모으게 합니다.

  python tools/meeting_pack.py new 안건.md                       # work/meeting-날짜-안건/ 생성
  python tools/meeting_pack.py new 안건.md --roles roles/patent.md --name 출원전략
  python tools/meeting_pack.py collect work/meeting-2026-11-08-안건   # opinions/*.md 를 모아 의장 프롬프트 완성

만들어지는 것
  01-<역할>.md …   역할별 프롬프트 (각각 새 대화에 붙여 넣기, 가능하면 모델도 바꾸기)
  opinions/        역할별 답을 <역할>.md 로 저장하는 곳
  90-red-team.md   모인 의견의 공통 결론을 반박하는 프롬프트 (collect 후 완성)
  99-chair.md      의장 종합 프롬프트 (collect 후 완성)
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROLES = ROOT / "roles" / "default.md"
RUBRIC = ROOT / "prompts" / "rubric.md"
SAFE = re.compile(r"[^0-9A-Za-z가-힣_-]+")


def out(msg):
    sys.stdout.write(msg + "\n")


def parse_roles(text):
    """'## 역할명' 아래 내용을 역할 설명으로 읽는다."""
    roles, name, buf = [], None, []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if name:
                roles.append((name, "\n".join(buf).strip()))
            name, buf = m.group(1), []
        elif name:
            buf.append(line)
    if name:
        roles.append((name, "\n".join(buf).strip()))
    if len(roles) < 2:
        raise SystemExit("역할이 2개 이상 필요합니다. 역할 파일에 '## 역할명' 제목을 2개 이상 두세요.")
    return roles


def slug(s):
    return SAFE.sub("-", s).strip("-")[:40] or "item"


ROLE_TMPL = """# AI 회의 — {role} 의견서 요청

이 대화에서 너는 아래 안건을 검토하는 회의 참석자 중 **{role}**의 관점을 맡는다.
다른 참석자의 의견은 보지 않은 상태에서 **독립적으로** 작성한다. 다른 사람이 동의할지 신경 쓰지 않는다.

## 이 역할이 보는 것
{role_desc}

## 평가 기준 (루브릭)
{rubric}

## 작성 순서
1. 안건에 깔린 전제를 3개 이내로 적고 각각 [사실/가정/의심] 중 하나로 표시한다. 의심이면 이유를 쓴다.
2. 이 관점에서 찬성 근거 (최대 3개)
3. 이 관점에서 **가장 강한 반대 논리** 1개 — 이 안건이 실패한다면 가장 그럴듯한 이유
4. 루브릭 항목별 점수와 그 점수를 준 근거 한 줄. 정보가 부족하면 점수 대신 "판단 보류: 필요한 정보"
5. 이 의견을 바꾸게 할 정보 (무엇을 알면 결론이 달라지는가)
6. 한 줄 결론: 진행 / 조건부 진행(조건) / 보류(사유)

안건에 없는 사실은 지어내지 말고 '확인 필요'로 표시한다. 답은 1,000자 안팎.

## 안건
{agenda}
"""

RED_TMPL = """# AI 회의 — 반론 전담(레드팀)

아래는 같은 안건에 대해 서로 다른 참석자가 독립적으로 쓴 의견서다.
너의 역할은 이 의견들이 **공통으로 기대고 있는 결론이나 전제**를 찾아 가장 강하게 반박하는 것이다.
동의하는 말은 쓰지 않는다.

1. 의견들이 공통으로 가정하는 것 3개
2. 그중 가장 위험한 가정 1개와, 그것이 틀렸을 때 벌어지는 일
3. 아무도 다루지 않은 위험 2개
4. 결론을 뒤집으려면 확인해야 할 사실 목록

## 안건
{agenda}

## 의견서
{opinions}
"""

CHAIR_TMPL = """# AI 회의 — 의장 종합

너는 회의 의장이다. 아래 독립 의견서{red_note}를 바탕으로 결론을 정리한다.
다수결로 정하지 않는다. 근거가 강한 쪽을 따르고, 근거가 부족한 부분은 '보류'로 남긴다.
의견서에 없는 새로운 사실을 보태지 않는다.

## 출력
1. **최종 합의안** — 지금 실행할 것 (누가·무엇을·언제까지 수준으로)
2. **보류 항목** — 표: 항목 | 보류 사유(어떤 위험) | 보류를 풀 조건(어떤 정보·지표가 확인되면)
3. **소수 의견** — 채택하지 않았지만 기록할 반대 논리
4. **점수표** — 루브릭 항목별로 역할별 점수를 나란히, 평균이 아니라 최저~최고 범위와 이견이 큰 항목 표시
5. **확인할 사실** — 결론의 전제 중 아직 확인되지 않은 것
6. **다음 행동** 3개 이내

## 루브릭
{rubric}

## 안건
{agenda}

## 의견서
{opinions}
{red}
"""


def cmd_new(a):
    agenda_path = Path(a.agenda)
    agenda = agenda_path.read_text(encoding="utf-8-sig").strip()
    roles = parse_roles(Path(a.roles).read_text(encoding="utf-8-sig"))
    rubric = RUBRIC.read_text(encoding="utf-8").strip() if RUBRIC.is_file() else "(루브릭 없음)"
    name = a.name or agenda_path.stem
    d = Path(a.out) if a.out else ROOT / "work" / "meeting-{}-{}".format(datetime.date.today(), slug(name))
    (d / "opinions").mkdir(parents=True, exist_ok=True)
    (d / "agenda.md").write_text(agenda + "\n", encoding="utf-8")
    for i, (role, desc) in enumerate(roles, 1):
        f = d / "{:02d}-{}.md".format(i, slug(role))
        f.write_text(ROLE_TMPL.format(role=role, role_desc=desc, rubric=rubric, agenda=agenda), encoding="utf-8")
    (d / "roles.txt").write_text("\n".join(r for r, _ in roles) + "\n", encoding="utf-8")
    (d / "00-README.md").write_text(
        "# 진행 순서\n\n"
        "1. 01~{n:02d} 파일을 하나씩 **새 대화**에 붙여 넣습니다. 가능하면 역할마다 다른 모델을 씁니다\n"
        "   (예: Claude · ChatGPT · Gemini · Copilot, Antigravity에서는 대화마다 모델 선택).\n"
        "2. 각 답을 `opinions/<역할>.md` 로 저장합니다. 파일 이름은 roles.txt의 역할명과 같게.\n"
        "3. `python tools/meeting_pack.py collect {d}` → 90-red-team.md, 99-chair.md 완성\n"
        "4. 90을 새 대화에 → 답을 `opinions/_red-team.md` 로 저장 → collect 한 번 더 → 99를 새 대화에\n"
        "5. 의장 결론의 '확인할 사실'은 사람이 확인합니다.\n".format(n=len(roles), d=d.as_posix()),
        encoding="utf-8")
    out("만듦: {}  (역할 {}개)".format(d.as_posix(), len(roles)))
    for i, (role, _) in enumerate(roles, 1):
        out("  {:02d}-{}.md".format(i, slug(role)))
    out("다음: 각 프롬프트를 새 대화에 붙여 넣고 답을 opinions/<역할>.md 로 저장 → collect")
    return 0


def cmd_collect(a):
    d = Path(a.meeting)
    agenda = (d / "agenda.md").read_text(encoding="utf-8")
    rubric = RUBRIC.read_text(encoding="utf-8").strip() if RUBRIC.is_file() else "(루브릭 없음)"
    roles = [r for r in (d / "roles.txt").read_text(encoding="utf-8").splitlines() if r.strip()]
    found, missing = [], []
    for r in roles:
        f = d / "opinions" / (slug(r) + ".md")
        alt = d / "opinions" / (r + ".md")
        p = f if f.is_file() else alt if alt.is_file() else None
        if p:
            found.append("### {}\n\n{}".format(r, p.read_text(encoding="utf-8-sig").strip()))
        else:
            missing.append(r)
    if len(found) < 2:
        raise SystemExit("의견서가 2개 이상 필요합니다. 없는 역할: " + ", ".join(missing))
    opinions = "\n\n".join(found)
    (d / "90-red-team.md").write_text(RED_TMPL.format(agenda=agenda, opinions=opinions), encoding="utf-8")
    red_file = d / "opinions" / "_red-team.md"
    red = "\n## 반론(레드팀)\n\n" + red_file.read_text(encoding="utf-8-sig").strip() + "\n" if red_file.is_file() else ""
    (d / "99-chair.md").write_text(CHAIR_TMPL.format(
        rubric=rubric, agenda=agenda, opinions=opinions, red=red,
        red_note="와 반론" if red else ""), encoding="utf-8")
    out("의견서 {}개 모음{}".format(len(found), " · 반론 포함" if red else " · 반론 아직 없음(90-red-team.md 먼저 실행 권장)"))
    if missing:
        out("빠진 역할: " + ", ".join(missing))
    out("완성: {} · {}".format((d / "90-red-team.md").as_posix(), (d / "99-chair.md").as_posix()))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="AI 회의 프롬프트 묶음 만들기")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="안건으로 역할별 프롬프트 만들기")
    n.add_argument("agenda")
    n.add_argument("--roles", default=str(DEFAULT_ROLES))
    n.add_argument("--name")
    n.add_argument("--out")
    c = sub.add_parser("collect", help="opinions/ 를 모아 레드팀·의장 프롬프트 완성")
    c.add_argument("meeting")
    a = ap.parse_args(argv)
    return cmd_new(a) if a.cmd == "new" else cmd_collect(a)


if __name__ == "__main__":
    sys.exit(main())
