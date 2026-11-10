---
name: triad-dev-review
description: 개발 목표를 지휘·구현·검수로 나눠 ORDER 명세를 쓰거나, 남이 만든 코드 diff를 독립 검수해 PASS/FAIL JSON으로 판정할 때 사용. 애매하면 FAIL.
---

# 삼권분립 개발 — ORDER 작성과 독립 검수

이 스킬은 두 가지 일 중 하나를 한다. 사용자가 무엇을 원하는지 먼저 정한다.

- **A. 지휘(HEAD)**: 목표 한 줄 → ORDER 명세
- **B. 검수(REVIEWER)**: 다른 AI가 만든 diff·테스트 결과 → PASS/FAIL 판정

구현(BUILDER)은 이 스킬의 일이 아니다. 구현은 다른 회사 모델이나 CLI에 맡긴다.

## A. ORDER 작성
1. 목표에서 바꿀 파일을 최소로 고른다. 모르면 사용자에게 파일 구조를 묻는다.
2. `references/order-template.md` 형식으로 쓴다. 필수 칸: goal, allowed_paths, max_files, acceptance(완료 기준), tests(검증 명령), human_required(사람 결정 항목).
3. allowed_paths는 좁게(`src/calc.py`, `tests/test_calc.py`). `**`, 저장소 전체는 쓰지 않는다.
4. 다음은 allowed_paths에 넣지 않는다: `.claude/` `.mcp.json` `.codex/` `.gemini/` `.agents/` `AGENTS.md` `CLAUDE.md` `.github/workflows/` `conftest.py` `pytest.ini` `package.json` `.env*`.
5. 돈·자격증명·되돌릴 수 없는 외부 행동이 끼면 human_required에 적고 진행하지 않는다.

## B. 독립 검수
1. 입력: ORDER, diff, 테스트 출력. 하나라도 없으면 FAIL("입력 부족").
2. `references/review-checklist.md`의 항목을 차례로 본다.
3. 테스트 출력에 실제 통과 기록이 없으면 FAIL. "통과했다"는 말만으로 통과시키지 않는다.
4. 출력의 **마지막 줄**은 반드시 JSON 한 줄:
   `{"verdict": "PASS" 또는 "FAIL", "reasons": ["..."]}`
5. 확신이 없으면 FAIL. 이유는 고칠 수 있게 구체적으로(파일·줄·무엇이 문제인지).

## 지키는 것
- 자기가 만든 코드는 검수하지 않는다(같은 대화·같은 회사 모델이면 "독립성 낮음"을 이유에 적는다).
- 비밀값·키가 diff에 보이면 내용은 옮겨 적지 말고 위치만 적고 FAIL.
