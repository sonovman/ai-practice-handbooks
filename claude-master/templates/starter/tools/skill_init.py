#!/usr/bin/env python3
"""나만의 스킬 뼈대 만들기 (핸드북 23). 표준 라이브러리만 사용.

매번 길게 치던 지시문이나 서식 변환 요청을, 다시 쓰기 좋게 '스킬(SKILL.md)' 폴더 뼈대로 찍어 줍니다.
SSR Plus의 'Skills(스킬)' 단계를, 빈 화면 대신 검증된 틀에서 시작하기 위한 도구입니다.

  python tools/skill_init.py my-skill                       # ./my-skill/ 생성
  python tools/skill_init.py invoice-clean --out ~/skills    # 지정 폴더에 생성
  python tools/skill_init.py invoice-clean --desc "엑셀 송장에서 개인정보 칼럼을 지운다" --with-tool

만들어지는 것:
  my-skill/SKILL.md            프런트매터(name·description)+ 본문 틀
  my-skill/references/notes.md 자세한 규칙·예시를 넣는 참조 문서(선택)
  my-skill/tools/run.py        (--with-tool 일 때) 표준 라이브러리 뼈대 스크립트

왜 틀부터인가(초기 접근 → 개선):
  처음엔 긴 지시문을 그때그때 복사해 붙여 씁니다. 그러면 매번 조금씩 달라지고 품질이 들쭉날쭉해집니다.
  반복되는 지시문은 '스킬'로 고정해 두면 이름만 부르면 같은 품질로 재사용됩니다.
  다만 description(설명)이 핵심입니다. '언제 이 스킬을 쓰는지'가 거기서 결정되므로 200자 안쪽으로, 쓰임새를 또렷하게.

주의: description은 200자 이내 권장(길면 트리거가 흐려짐). 이름은 영문 소문자·숫자·하이픈만.
"""
import argparse
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DESC_MAX = 200

SKILL_MD = """---
name: {name}
description: {desc}
---

# {title}

## 언제 쓰나
- ✏️ 이 스킬을 불러야 하는 상황을 한두 줄로. (description과 맞추세요)

## 준비물(입력)
- ✏️ 필요한 파일·정보

## 절차
1. ✏️ 첫 단계
2. ✏️ 다음 단계
3. ✏️ 완료 기준(무엇이 되면 끝인가)

## 하지 말 것
- ✏️ 예: 개인정보가 담긴 원본은 수정하지 말고 사본으로 작업

## 참조
- `references/notes.md` — 자세한 규칙·예시
"""

NOTES_MD = """# {title} — 참조 메모

여기에는 자세한 규칙, 예시, 자주 쓰는 표현을 모아 둡니다.
SKILL.md 본문은 짧게 유지하고, 길어지는 내용은 이 파일로 넘기세요.

## 예시
- ✏️ 입력 예 / 출력 예
"""

TOOL_PY = '''#!/usr/bin/env python3
"""{name} 보조 스크립트 뼈대. 표준 라이브러리만 사용.

  python tools/run.py <입력>
"""
import argparse
import sys


def main(argv=None):
    ap = argparse.ArgumentParser(description="{name} 보조 스크립트")
    ap.add_argument("input", nargs="?", default="", help="입력(파일 경로 등)")
    a = ap.parse_args(argv)
    # ✏️ 여기에 실제 처리를 작성하세요.
    sys.stdout.write("입력: {{}}\\n".format(a.input))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def titleize(name):
    return name.replace("-", " ")


def main(argv=None):
    ap = argparse.ArgumentParser(description="나만의 스킬 뼈대 만들기")
    ap.add_argument("name", help="스킬 이름(영문 소문자·숫자·하이픈)")
    ap.add_argument("--desc", default="", help="description(언제 쓰는지, 200자 이내 권장)")
    ap.add_argument("--out", default=".", help="생성 위치(기본: 현재 폴더)")
    ap.add_argument("--with-tool", action="store_true", help="tools/run.py 뼈대도 생성")
    ap.add_argument("--force", action="store_true", help="이미 있어도 덮어쓰기")
    a = ap.parse_args(argv)

    if not NAME_RE.match(a.name):
        sys.exit("이름은 영문 소문자·숫자·하이픈만 됩니다(예: invoice-clean): {}".format(a.name))
    desc = a.desc.strip() or "✏️ 언제 이 스킬을 쓰는지 한 줄로 (200자 이내)"
    if len(desc) > DESC_MAX:
        sys.stderr.write("주의: description이 {}자입니다. {}자 안쪽으로 줄이면 트리거가 또렷해집니다.\n"
                         .format(len(desc), DESC_MAX))

    base = Path(a.out).expanduser().resolve() / a.name
    if base.exists() and not a.force:
        sys.exit("이미 있습니다: {}  — 덮어쓰려면 --force".format(base))
    title = titleize(a.name)

    (base / "references").mkdir(parents=True, exist_ok=True)
    (base / "SKILL.md").write_text(
        SKILL_MD.format(name=a.name, desc=desc, title=title), encoding="utf-8")
    (base / "references" / "notes.md").write_text(
        NOTES_MD.format(title=title), encoding="utf-8")
    made = ["SKILL.md", "references/notes.md"]
    if a.with_tool:
        (base / "tools").mkdir(parents=True, exist_ok=True)
        (base / "tools" / "run.py").write_text(TOOL_PY.format(name=a.name), encoding="utf-8")
        made.append("tools/run.py")

    sys.stdout.write("생성: {}\n".format(base))
    for m in made:
        sys.stdout.write("  - {}\n".format(m))
    sys.stdout.write("다음: SKILL.md의 ✏️ 자리를 채우고, description을 또렷하게 다듬으세요.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
