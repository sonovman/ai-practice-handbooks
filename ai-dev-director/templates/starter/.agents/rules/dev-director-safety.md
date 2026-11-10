---
trigger: model_decision
description: AI DEV DIRECTOR나 mini_triad를 설치·설정·실행하거나, 세 AI CLI(claude·codex·agy)를 역할로 나눠 쓰는 작업일 때 적용
---

# 삼권분립 개발 안전 규칙

1. **설치 전 점검**: `python tools/director_preflight.py --director <디렉터 폴더> --project <프로젝트>`를 먼저 돌리고 `[중단]`이 있으면 멈춘다.
2. **첫 3회는 자동 반영 끄기**: `config.yaml`의 `autonomy.auto_apply: off`, 실행은 `director.py do ... --no-apply`. 결과는 작업본에서 확인한다.
3. **역할 독립성**: `python tools/role_matrix.py --head <> --builder <> --reviewer <>`가 BLOCK이면 배치를 바꾼다. BUILDER와 REVIEWER는 다른 회사.
4. **반영 직전 관문**: `python tools/apply_gate.py --worktree <작업본>`이 `HUMAN_REVIEW`/`BLOCK`이면 사람이 파일을 직접 열어 본다.
5. **AI가 쓴 코드는 내 PC에서 실행된다**: 검증 단계의 테스트는 AI가 만든 코드다. 비밀값이 없는 프로젝트·별도 사용자 계정·가상 머신에서 돌린다.
6. **믿지 않는 저장소는 대상에서 제외**: 남이 만든 저장소에 `.claude/settings.json`·`.mcp.json`이 있으면 비대화 CLI가 확인 창 없이 실행할 수 있다.
7. **권한 우회 플래그 금지**: CLI에 skip-permissions·yolo·full-access 계열을 붙이지 않는다.
8. **외부 발주(솔로몬 브리지)**: 쓰지 않으면 `companion.json`의 `allowed_projects`를 비워 두고, `config.yaml`의 `solomon.allowed_roots`도 실제 쓰는 폴더만 남긴다.
