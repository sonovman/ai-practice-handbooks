# 판례 원문 조사·심층 해설 — 4개 플랫폼 키트

AI 실무 핸드북 09편의 배포 키트입니다. 같은 해설 규칙을 Claude·ChatGPT·Gemini·Copilot 네 곳에서 쓸 수 있게 만들었습니다.

| 폴더 | 무엇 | 설치 안내 |
|---|---|---|
| `claude/case-study-research/` | Claude 스킬 (형식 점검 스크립트 포함) | claude/README.md |
| `claude/agents/case-reviewer.md` | Claude Code 검수 에이전트 (해설과 분리된 독립 검수) | claude/README.md |
| `chatgpt/` | 플러그인 스킬 지침 + Plugin Creator 요청문 + 플러그인 원본 폴더 | chatgpt/README.md |
| `gemini/` | Gemini Gem 요청 사항 | gemini/README.md |
| `copilot/` | Copilot Studio 에이전트 설명·지침·공식 법원 사이트 목록 | copilot/README.md |
| `knowledge/` | ChatGPT·Gemini·Copilot에 함께 올리는 공통 파일 3개 | — |
| `sample/` | 가상 교재 발췌 + Alice 판결 해설 결과 + 형식 점검 결과 | — |
| `tools/check_versions.py` | 4개 버전이 핵심 규칙을 모두 담고 있는지 점검 | — |

## 규칙을 고칠 때
1. `claude/case-study-research/SKILL.md` 를 고칩니다.
2. `knowledge/case-rules.md` 를 같은 내용으로 맞추고, references 파일을 고쳤다면 `knowledge/` 와 `chatgpt/plugin-source/` 로 다시 복사합니다.
3. `python tools/check_versions.py` 로 일치를 확인합니다.

## 주의
- 해설은 학습·연구용 초안입니다. 판례의 현재 유효성, 사건 확정, 원문 접근을 보장하지 않습니다.
- 유료 법률 DB 접근권을 주지 않습니다. 각 플랫폼에서 웹 검색·파일 첨부가 켜져 있어야 원문 조사가 됩니다.
- 의뢰인 자료·미공개 서면은 회사가 승인한 AI 환경에만 넣으세요.
