# Copilot Studio 에이전트 만들기

## 준비물
- `agent-instructions.md` (이 폴더) — 설명과 지침
- `../knowledge/` 의 3개 파일 — claim-rules.md, output-spec.md, design-around-types.md
- 분석할 공보·도면·제품자료가 들어 있는 SharePoint 폴더

## 순서
1. copilotstudio.microsoft.com → 홈에서 에이전트 만들기 → 이름: **특허 구성특징 분석 도우미**
2. Overview 의 **Description** 에 agent-instructions.md 의 "에이전트 설명", **Instructions** 에 "지침" 전체를 붙여 넣습니다.
3. **Knowledge** → Add → 지식 파일 3개를 올립니다. 공보가 있는 **SharePoint 폴더**도 지식 원본으로 추가합니다.
4. 아래 **추천 프롬프트**(Suggested prompts / Conversation starters)를 등록합니다.
5. 오른쪽 테스트 창에서 `../sample/sample-patent.md` 를 올린 SharePoint 폴더로 시험합니다. 문헌 잠금 표가 맨 위에 나오고 마지막 줄이 Recommended Next Action 이면 정상입니다.
6. **Publish** → **Channels** → Microsoft 365 and Microsoft Teams 로 팀에 배포합니다.

## 추천 프롬프트
| 제목 | 프롬프트 |
|---|---|
| 긴급 분석 | 긴급 모드로 분석해 줘. 경로: [SharePoint 경로], 번호: [등록번호] |
| 전체 분석 | 전체 모드로 분석해 줘. 경로: [SharePoint 경로], 번호: [번호], 기준: 최신 등록청구항 |
| 도면 읽기 표 | [번호]의 독립항 구성요소를 도면부호와 대응시킨 도면 읽기 표만 만들어 줘 |
| 회피설계 | [번호] 청구항 1의 한정사항별 회피설계안을 최소변경·강한 회피·조합안으로 |
| 공개·등록 비교 | [번호]의 공개청구항과 등록청구항 차이를 표로 비교해 줘 |

## 참고
- 지침 칸이 짧게 제한되는 환경이면 "지침"의 1·2·5·6·7번만 남기고 나머지는 지식 파일(claim-rules.md)에 맡기세요. 절차는 지식 파일에 모두 들어 있습니다.
- 메일 발송·승인 단계가 필요하면 Tools → Add a tool → Agent flow(Power Automate)로 연결합니다(핸드북 01편 9장 참고).
- 메뉴와 기능은 회사 라이선스·관리자 설정에 따라 다를 수 있습니다.
