# IP팀 업무 시스템 스타터 키트

AI 실무 핸드북 05편 「SSR Plus 4단계」의 구축 사례입니다.
이 폴더를 통째로 내려받아 이름을 바꾸고, [대괄호] 부분만 회사 사정에 맞게 고쳐 쓰세요.

## 들어 있는 것
| 단계 | 파일 |
|---|---|
| 1. 스킬 | `skills/patent-brief/` (공보 브리프), `skills/skill-improver/` (스킬 개선) |
| 2. 세컨드 브레인 | `CLAUDE.md` (대문), `docs/` (업무별 길잡이) |
| 3. 루틴 | `docs/루틴_안내.md` (예약 작업에 붙여 넣을 문장) |
| 4. 연결 | `docs/연결_안내.md` (커넥터 사용 원칙) |
| 점검 | `tools/check_links.py` (길잡이 링크 점검) |
| 연습 | `input/sample-patent.md` (가상 공보), `output/` (실행 결과 예시) |

## 설치
### A. Claude Desktop의 Code 탭 / Claude Code
1. 이 폴더를 작업 폴더로 엽니다. `CLAUDE.md` 는 자동으로 읽힙니다.
2. 스킬을 쓰려면 `skills/` 안의 두 폴더를 `.claude/skills/` 로 옮깁니다.
   ```
   .claude/skills/patent-brief/SKILL.md
   .claude/skills/skill-improver/SKILL.md
   ```
3. `/patent-brief input/sample-patent.md` 로 시험합니다.

### B. claude.ai 웹 / Claude Desktop 채팅
1. 설정에서 코드 실행(파일 만들기)을 켭니다.
2. **Customize → Skills → + → Create skill → Upload a skill** 에서 `patent-brief.zip` 을 올립니다.
3. 대화창에 `sample-patent.md` 를 첨부하고 "이 공보 브리프로 정리해 줘"라고 요청합니다.

## 점검
```
python tools/check_links.py
```
길잡이 파일을 고친 뒤에는 링크가 끊기지 않았는지 이 명령으로 확인하세요.
