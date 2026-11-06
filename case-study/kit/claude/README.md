# Claude 스킬·에이전트 설치

```
claude/
├── case-study-research/            스킬
│   ├── SKILL.md                    지침 (필수)
│   ├── references/research.md      조사·신뢰성 기준, 해설 검수 10항목
│   ├── references/output-template.md 출력 양식 (헤더 7 + 11개 항목)
│   └── scripts/check_report.py     해설 형식 점검
└── agents/case-reviewer.md         Claude Code 검수 에이전트
```

## A. claude.ai · Claude Desktop 채팅
1. 설정에서 **웹 검색**과 **코드 실행(파일 만들기)** 을 켭니다. 웹 검색이 꺼져 있으면 원문 조사를 못 하고 "원문 미확보"로 해설합니다.
2. **Customize → Skills → + → Create skill → Upload a skill** 에서 `case-study-research.zip` 을 올립니다.
3. 교재 PDF나 문단을 첨부하고 "이 문단에 인용된 판례를 심층 해설해 줘"라고 요청합니다.

## B. Claude Code · Desktop Code 탭
1. 스킬: `~/.claude/skills/case-study-research/` (모든 프로젝트) 또는 작업 폴더의 `.claude/skills/` 로 폴더째 복사합니다.
2. 검수 에이전트: `agents/case-reviewer.md` 를 `~/.claude/agents/` 또는 `.claude/agents/` 에 복사합니다.
3. 실행 예:
   ```
   /case-study-research sample/textbook-excerpt.md 의 판례를 해설해서 output/에 저장해 줘
   case-reviewer 에이전트로 output/alice-case-study.md 를 검수해 줘
   ```
   해설을 쓴 대화와 검수 에이전트의 맥락이 분리되어, 작성자가 자기 글을 채점하는 문제를 줄입니다(핸드북 01편).

## 형식 점검만 따로
```
python case-study-research/scripts/check_report.py output/alice-case-study.md
```
