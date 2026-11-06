# 특허 구성특징 분석 도우미 — 4개 플랫폼 키트

AI 실무 핸드북 06편의 배포 키트입니다. 같은 분석 규칙을 Claude·ChatGPT·Gemini·Copilot 네 곳에서 쓸 수 있게 만들었습니다.

| 폴더 | 무엇 | 설치 안내 |
|---|---|---|
| `claude/` | Claude 스킬 (스크립트·HTML 템플릿 포함, 기능 가장 많음) | claude/README.md |
| `chatgpt/` | ChatGPT 플러그인 스킬 지침 + Plugin Creator 요청문 | chatgpt/README.md |
| `gemini/` | Gemini Gem 요청 사항 | gemini/README.md |
| `copilot/` | Copilot Studio 에이전트 설명·지침·추천 프롬프트 | copilot/README.md |
| `knowledge/` | ChatGPT·Gemini·Copilot에 함께 올리는 공통 규칙 3개 | — |
| `sample/` | 연습용 가상 공보·도면, 실행 결과 예시 | — |
| `tools/check_versions.py` | 4개 버전이 핵심 규칙을 모두 담고 있는지 점검 | — |

## 규칙을 고칠 때
1. `knowledge/claim-rules.md` 와 `claude/claim-design-around/SKILL.md` 를 함께 고칩니다.
2. 출력 형식·회피 유형을 고쳤다면 `claude/.../references/` 의 파일을 고치고 `knowledge/` 로 다시 복사합니다.
3. `python tools/check_versions.py` 로 4개 버전이 모두 일치하는지 확인합니다.

## 주의
- 결과는 분석 초안입니다. 침해·FTO·무효에 관한 판단과 책임은 변리사·담당자에게 있습니다.
- 출원 전 발명, 의뢰인 자료, 미공개 제품자료는 회사가 승인한 AI 환경에만 넣으세요.
