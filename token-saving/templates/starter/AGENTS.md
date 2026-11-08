# AGENTS.md — 이 폴더에서 에이전트가 항상 지킬 것

이 폴더는 핸드북 27편 '클로드 코드 토큰·비용 절약' 키트입니다.

## 항상
- 한국어, 초보자도 따라 하기 쉽게 단계별로.
- '어디서 돈이 나가는지'를 먼저 숫자로(token_cost.py·session_sim.py), 그다음 통제.
- 세션은 짧게·/clear, 모델·에포트는 시작에 고정(중간 변경 = 캐시 깨짐).
- 출력·사고 토큰이 비싸다 — 간결 출력·낮은 사고 예산으로 단순 작업 절약.

## 보안
- 검증 안 된 외부 스킬·`curl|bash`는 프롬프트 주입·정보 유출 위험. 출처 확인, deny/샌드박스 설정.
- 단가·명령·캐시 정책은 바뀌니 공식 문서로 확인.

## 도구(표준 라이브러리)
- `tools/token_cost.py` — 한 요청의 토큰 비용.
- `tools/session_sim.py` — N턴 세션 누적 비용(캐시·/clear 효과).
- 시험: `python tools/test_token_cost.py`, `python tools/test_session_sim.py`.
