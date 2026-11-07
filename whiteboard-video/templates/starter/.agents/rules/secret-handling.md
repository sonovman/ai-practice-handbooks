---
trigger: model_decision
description: API 키, 토큰, .env, 환경 변수, 비밀번호를 다루거나 외부 API를 호출하는 코드를 쓸 때 적용
---

# 비밀값 다루기

- 코드에는 `os.environ["GEMINI_API_KEY"]`처럼 이름만 씁니다. 값을 문자열로 넣지 않습니다.
- 새 비밀값이 필요하면 `.env.example`에 이름만 추가하고, 사용자에게 직접 `.env`나 키체인에 넣으라고 안내합니다.
- 오류 메시지·로그를 보여 줄 때 키가 섞여 있으면 `***`로 가립니다.
- `.gitignore`에 `.env`가 있는지 확인하고, 없으면 추가를 제안합니다.
- 키가 노출된 것 같으면 즉시 알리고, Google AI Studio에서 키를 삭제·재발급하라고 안내합니다.
