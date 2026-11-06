# Copilot Studio 에이전트 만들기

## 준비물
- `agent-instructions.md` (이 폴더) — 설명과 지침
- `../knowledge/` 의 3개 파일 — council-rules.md, roles.md, output-template.md

## 순서
1. copilotstudio.microsoft.com → 에이전트 만들기 → 이름: **합의 협의체**
2. **Description** 에 "에이전트 설명", **Instructions** 에 "지침" 전체를 붙여 넣습니다.
3. **Knowledge** → Add → 지식 파일 3개를 올립니다. (사내 결정 자료가 있는 SharePoint 폴더를 추가하면 맥락을 읽고 질문을 정리합니다.)
4. 아래 추천 프롬프트를 등록합니다.
5. 테스트 창에서 `../sample/question.md` 내용으로 시험 → **Publish** → **Channels** → Teams로 배포합니다.

## 추천 프롬프트
| 제목 | 프롬프트 |
|---|---|
| 선택지 비교 | 협의체로 검토해 줘: [결정할 것], 선택지 [A/B/C], 기준 [2~4개] |
| 계획 검증 | 이 계획의 약점을 협의체로 찾아 줘: [계획] |
| 문안 검토 | 이 문안을 받는 사람 입장까지 협의체로 검토해 줘: [문안] |
| 교차 검증 | 다른 AI에서 받은 아래 의견을 위원 의견에 추가해 협의체를 진행해 줘: [붙여 넣기] |

## 참고
- 지침 칸이 짧게 제한되면 3·4·6·7·11번만 남기고 나머지는 council-rules.md에 맡기세요.
- 메뉴와 기능은 회사 라이선스·관리자 설정에 따라 다를 수 있습니다.
