# 웹 앱만으로 해 보는 '삼권분립' 릴레이 (Claude · ChatGPT · Gemini · Microsoft 365 Copilot)

CLI를 설치하지 않아도 개념은 그대로 연습할 수 있습니다. 세 앱을 탭 세 개로 열고 결과를 손으로 옮깁니다.
같은 회사 앱에서 구현과 검수를 하지 않는 것이 핵심입니다.

| 역할 | 추천 앱(예시) | 붙여 넣을 프롬프트 |
|---|---|---|
| HEAD | Claude | ① ORDER 작성 |
| BUILDER | Gemini 또는 ChatGPT | ② 구현 |
| REVIEWER | BUILDER와 **다른 회사** 앱 | ③ 독립 검수 |

스킬을 올려 두었다면(triad-dev-review) ①과 ③은 "triad-dev-review로 ORDER 써 줘 / 검수해 줘"만 말해도 됩니다.

---

## ① ORDER 작성 (HEAD)
목표: <한 줄 목표>
현재 파일 구조: <tree 결과나 파일 목록>
위 목표를 ORDER JSON으로 만들어라. 칸은 goal, allowed_paths, max_files, acceptance, tests, human_required.
allowed_paths는 꼭 필요한 파일만, `**`·저장소 전체 금지. 코드는 쓰지 마라.

## ② 구현 (BUILDER)
아래 ORDER의 allowed_paths 안 파일만 만들어라. 파일마다 전체 내용을 코드 블록으로, 첫 줄에 경로를 적어라.
테스트를 약하게 만들지 말고, ORDER에 없는 파일은 만들지 마라.
<ORDER 붙여 넣기>

## ③ 독립 검수 (REVIEWER)
너는 이 코드를 만들지 않은 독립 검수자다. ORDER, 코드, 내 PC에서 돌린 테스트 출력을 보고 판정하라.
테스트 출력에 실제 통과 기록이 없으면 FAIL, 확실하지 않으면 FAIL.
마지막 줄은 JSON 한 줄: {"verdict": "PASS" 또는 "FAIL", "reasons": ["..."]}
<ORDER> <코드> <테스트 출력>

---

주의: 웹 앱은 내 PC에서 테스트를 돌려 주지 않습니다. ②의 코드를 내 PC에 저장하고 테스트를 직접 돌린 출력을 ③에 넣어야
"말로만 통과"를 막을 수 있습니다.
