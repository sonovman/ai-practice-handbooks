# Claude 스킬·에이전트 설치

```
claude/
├── decision-council/               스킬
│   ├── SKILL.md                    절차 (필수)
│   ├── references/roles.md         위원 5인
│   ├── references/output-template.md 결론 양식
│   └── scripts/check_verdict.py    결론 형식 점검
└── agents/
    ├── council-advisor.md          위원 (관점을 받아 독립 의견·검토·반박 수행)
    └── council-chair.md            의장 (합의 판정·결론)
```

## A. claude.ai · Claude Desktop 채팅 — 단일 대화 순차
1. 설정에서 **코드 실행(파일 만들기)** 을 켭니다(형식 점검용, 없어도 동작).
2. **Customize → Skills → + → Create skill → Upload a skill** 에서 `decision-council.zip` 을 올립니다.
3. "협의체로 검토해 줘: [결정할 것과 선택지]"라고 요청합니다.

## B. Claude Code — 병렬 서브에이전트 (독립성 가장 높음)
1. 스킬: `~/.claude/skills/decision-council/` 로 폴더째 복사.
2. 에이전트: `agents/*.md` 를 `~/.claude/agents/` 로 복사.
3. 실행 예:
   ```
   /decision-council 사무소 공용 AI 도구로 A안과 B안 중 무엇을 고를지 협의체로 검토하고 결론을 council-20261107.md 로 저장해 줘
   ```
   스킬이 council-advisor를 관점별로 5번 동시에 띄우고, 익명 검토·반박을 거쳐 council-chair가 결론을 씁니다.

## 형식 점검만 따로
```
python decision-council/scripts/check_verdict.py council-20261107.md
```
