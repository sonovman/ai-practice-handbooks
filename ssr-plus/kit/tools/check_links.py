"""길잡이 링크 점검기 — 세컨드 브레인의 링크가 끊기지 않았는지 확인

사용법
  python tools/check_links.py          # 이 폴더(작업 공간) 전체 점검
  python tools/check_links.py <폴더>

하는 일
  모든 .md 파일에서 [글자](경로) 형태의 링크를 찾아, 가리키는 파일·폴더가 실제로 있는지 봅니다.
  인터넷 주소(http…)와 페이지 안 이동(#…)은 건너뜁니다.
  끊긴 링크가 있으면 목록을 보여 주고 종료 코드 1로 끝납니다.
  Python 표준 라이브러리만 씁니다.
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    files = sorted(root.rglob("*.md"))
    broken, total = [], 0
    for md in files:
        text = md.read_text(encoding="utf-8-sig")
        text = re.sub(r"```.*?```", "", text, flags=re.S)  # 코드 블록 안은 무시
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            total += 1
            path = unquote(target.split("#")[0])
            if not (md.parent / path).exists():
                broken.append(f"{md.relative_to(root)} → {target}")
    print(f"점검한 파일 {len(files)}개 · 내부 링크 {total}개")
    if broken:
        print(f"끊긴 링크 {len(broken)}개:")
        for b in broken:
            print("  -", b)
        return 1
    print("끊긴 링크 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
