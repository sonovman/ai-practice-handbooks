# Google Antigravity에서 '삼권분립 개발'을 구축하는 프롬프트

Antigravity에서 이 starter 폴더를 작업 공간(Workspace)으로 연 뒤, 에이전트 창에 붙여 넣습니다.
AGENTS.md와 `.agents/rules`, `.agents/skills`는 Antigravity가 자동으로 읽습니다.

---

## 1단계 — 점검과 배치

이 작업 공간의 AGENTS.md와 `.agents/rules/dev-director-safety.md`를 읽고 그대로 따르라.
1. `python tools/test_director_tools.py` 와 `python tools/test_mini_triad.py` 를 돌려 모두 통과하는지 보여 줘라.
2. 내 PC에서 `claude`, `codex`, `agy` 중 무엇이 설치돼 있는지 `--version` 으로 확인하라(로그인 화면이 뜨면 멈추고 나에게 맡겨라).
3. `python tools/role_matrix.py --available <찾은 CLI>` 로 역할 배치를 추천하라.

## 2단계 — 첫 미션을 작은 연습 저장소에서

1. `work/demo` 에 빈 git 저장소를 만들고 README.md 하나로 첫 커밋을 하라.
2. `inbox/order-example.json` 을 `work/order.json` 으로 복사하라.
3. 1단계 배치대로 BUILDER·REVIEWER 명령 배열을 만들어 보여 줘라. 각 CLI의 `--help` 로 비대화 실행 옵션을 확인해서 써라.
   - 권한 우회 플래그는 쓰지 않는다.
   - REVIEWER는 읽기 전용 옵션이 있으면 쓴다(Codex는 `--sandbox read-only`).
4. 내가 확인하면 다음을 실행하라:
   `python tools/mini_triad.py --project work/demo --order work/order.json --builder '<배열>' --reviewer '<배열>' --test "python -m pytest -q"`
5. 보고서(`work/demo/.mini_triad/*.report.json`)를 단계별 표로 요약하고, PASS면 `git merge` 명령만 알려 줘라. 실행은 내가 한다.

## 3단계 — 스킬로 검수만 따로 쓰기

다른 AI가 만든 diff를 붙여 넣을 테니 `triad-dev-review` 스킬의 B(독립 검수) 절차로 판정하라.
마지막 줄은 반드시 verdict JSON 한 줄이다.
