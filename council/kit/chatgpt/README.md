# ChatGPT 플러그인(스킬) 만들기

> 맞춤형 GPT는 2026. 12. 11. 지원 종료 예정이며, OpenAI는 GPT를 플러그인으로 옮기도록 안내하고 있습니다(핸드북 06편에서 확인한 절차).

## 준비물
- `skill-instructions.md` (이 폴더)
- `../knowledge/` 의 3개 파일 — council-rules.md, roles.md, output-template.md

## 순서
1. 사이드바 **플러그인** → 디렉터리에서 **Plugin Creator** 설치 (또는 플러그인 → 추가(+))
2. 새 대화에서 4개 파일을 첨부하고 아래 요청문을 보냅니다.
3. `@플러그인이름` 으로 불러 `../sample/question.md` 내용으로 시험합니다. 1~7번 항목과 합의 수준·신뢰도가 나오면 정상입니다.

## Plugin Creator 요청문
```
@plugin-creator
"합의 협의체" 플러그인을 만들어 줘. 연결 앱은 필요 없고 스킬 하나만 넣어.
- 스킬 지침: 첨부한 skill-instructions.md 의 "지침" 전체를 그대로 사용
- 스킬 이름·설명: skill-instructions.md 의 "스킬 이름과 설명"
- 참조 파일: council-rules.md, roles.md, output-template.md 를 그대로 포함
지침 문장을 요약하거나 바꾸지 말고 그대로 넣어 줘.
```

## 참고
- 플러그인 만들기·공유 가능 여부는 요금제와 워크스페이스 권한에 따라 다릅니다.
- 플러그인을 만들 수 없는 환경이면 프로젝트(Projects)의 지침 칸에 "지침"을, 파일 칸에 3개 파일을 넣어도 같은 방식으로 동작합니다.
