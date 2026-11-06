# 합의 협의체 — 4개 플랫폼 키트

AI 실무 핸드북 11편의 배포 키트입니다. 서로 다른 관점의 위원 5인이 독립 의견 → 익명 상호 검토 → 반박·수정 → 합의 판정을 거쳐 결론을 내는 스킬·에이전트를 Claude·ChatGPT·Gemini·Copilot에서 쓸 수 있게 만들었습니다. 추가 API 키·중계 서비스·설치가 필요 없습니다.

| 폴더 | 무엇 | 설치 안내 |
|---|---|---|
| `claude/decision-council/` | Claude 스킬 (형식 점검 스크립트 포함) | claude/README.md |
| `claude/agents/` | Claude Code 위원·의장 에이전트 (병렬 진행용) | claude/README.md |
| `chatgpt/` | 플러그인 스킬 지침 + Plugin Creator 요청문 | chatgpt/README.md |
| `gemini/` | Gem 요청 사항 | gemini/README.md |
| `copilot/` | Copilot Studio 에이전트 설명·지침·추천 프롬프트 | copilot/README.md |
| `knowledge/` | ChatGPT·Gemini·Copilot에 올리는 공통 파일 3개 | — |
| `sample/` | 실 사용 예제: 질문, 진행 기록, 결론, 형식 점검 결과 | — |
| `comparison.csv` | 참고 저장소 6곳 비교표 | — |
| `tools/check_versions.py` | 4개 버전 핵심 규칙 16개 일치 점검 | — |

## 규칙을 고칠 때
1. `claude/decision-council/SKILL.md` 를 고치고 `knowledge/council-rules.md` 를 맞춥니다.
2. 위원·양식을 고쳤다면 `claude/decision-council/references/` 를 고치고 `knowledge/` 로 복사합니다.
3. 플랫폼 지침 3개(chatgpt·gemini·copilot)의 규칙 목록을 같은 내용으로 고칩니다.
4. `python tools/check_versions.py` 로 확인합니다.

## 주의
- 협의체는 판단을 돕는 도구입니다. 사실 확인은 원문 대조(07편)로, 법률 판단은 전문가가 합니다.
- 의뢰인 자료·미공개 정보는 회사가 승인한 AI 환경에만 넣으세요.
