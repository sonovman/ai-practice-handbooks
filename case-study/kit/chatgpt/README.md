# ChatGPT 플러그인(스킬) 만들기

> 맞춤형 GPT는 2026. 12. 11. 지원 종료 예정이며, OpenAI는 GPT를 **플러그인**으로 옮기도록 안내하고 있습니다. 플러그인 안에 지침은 **스킬**로, 지식 파일은 **참조 파일**로 들어갑니다. (핸드북 06편에서 확인한 절차)

## 준비물
- `skill-instructions.md` (이 폴더)
- `../knowledge/` 의 3개 파일 — case-rules.md, research.md, output-template.md
- 참고: `plugin-source/` — 작성자가 만든 플러그인 원본 폴더(plugin.json, .codex-plugin/plugin.json, skills/). 플러그인 폴더를 직접 올리거나 Codex에서 쓸 수 있는 환경이면 이 폴더를 그대로 씁니다.

## 순서 (Plugin Creator)
1. ChatGPT 설정에서 **웹 검색**이 가능한지 확인합니다. 원문 조사는 웹 검색에 달려 있습니다.
2. 사이드바 **플러그인** → 디렉터리에서 **Plugin Creator** 설치 (또는 플러그인 → 추가(+))
3. 새 대화에서 4개 파일을 첨부하고 아래 요청문을 보냅니다.
4. 만들어진 플러그인을 `@플러그인이름` 으로 불러 `../sample/textbook-excerpt.md` 로 시험합니다. 헤더 7개와 11개 항목이 나오고 8번에 심급 표가 있으면 정상입니다.
5. 필요하면 `@plugin-creator` 와 플러그인 이름을 멘션해 고칠 점을 말합니다.

## Plugin Creator 요청문
```
@plugin-creator
"판례 원문 조사·심층 해설" 플러그인을 만들어 줘. 연결 앱은 필요 없고 스킬 하나만 넣어.
- 스킬 지침: 첨부한 skill-instructions.md 의 "지침" 전체를 그대로 사용
- 스킬 이름·설명: skill-instructions.md 의 "스킬 이름과 설명"
- 참조 파일: case-rules.md, research.md, output-template.md 를 그대로 포함
지침 문장을 요약하거나 바꾸지 말고 그대로 넣어 줘.
```

## 참고
- 플러그인 만들기·공유·업로드 가능 여부는 요금제와 워크스페이스 권한에 따라 다릅니다. 회사 워크스페이스는 관리자 설정을 확인하세요.
- 기존 GPT가 있다면 **내 GPT → 플러그인으로 마이그레이션**을 쓴 뒤 지침을 이 파일 내용으로 바꿔도 됩니다.
