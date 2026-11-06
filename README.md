# AI 실무 핸드북

현업에서 직접 써 보고 효과를 본 AI 활용 기법과 가이드를 한 편씩 정리해 공개합니다.

**웹사이트로 읽기:** https://sonovman.github.io/ai-practice-handbooks/

| 편 | 제목 | 읽기 | 자료 |
|---|---|---|---|
| 01 | 에이전트는 한 명이면 충분하다 — 단독 vs 멀티 에이전트 | [화면](https://sonovman.github.io/ai-practice-handbooks/agent-guide/) | [템플릿](agent-guide/templates/) |
| 02 | 보고서 초안을 AI에게 맡기는 프롬프트 5원칙 | [화면](https://sonovman.github.io/ai-practice-handbooks/prompt-basics/) | [CSV](data/prompt-templates.csv) |

## 폴더 구성

```
ai-practice-handbooks/
├── index.html          표지 (catalog.js 를 읽어 목록을 자동으로 그림)
├── catalog.js          ★ 핸드북 목록 — 새 글을 올릴 때 여기만 고침
├── style.css           모든 페이지 공통 디자인 (흑백)
├── _template/          새 핸드북을 만들 때 복사해 쓰는 뼈대
├── agent-guide/        01편
│   ├── index.html
│   └── templates/      내려받는 자료 (CLAUDE.md, 리뷰어 프롬프트)
├── prompt-basics/      02편
└── data/               공용 자료
```

새 편을 추가하는 절차는 [새-핸드북-추가하기.md](새-핸드북-추가하기.md)를 보세요.

## 질문·오류 제보
이 저장소의 **Issues** 탭에 남겨 주세요.

## 이용 조건
본문 CC BY-NC 4.0 — 출처를 밝히면 비영리 목적으로 자유롭게 쓰고 고칠 수 있습니다.
