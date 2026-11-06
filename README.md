# AI 실무 핸드북

현업에서 직접 써 보고 효과를 본 AI 활용 기법과 가이드를 한 편씩 정리해 공개합니다.

**웹사이트로 읽기:** https://sonovman.github.io/ai-practice-handbooks/

| 편 | 제목 | 읽기 | 자료 |
|---|---|---|---|
| 01 | 에이전트는 한 명이면 충분하다 — 단독 vs 멀티 에이전트 | [화면](https://sonovman.github.io/ai-practice-handbooks/agent-guide/) | [템플릿](agent-guide/templates/) |
| 02 | 보고서 초안을 AI에게 맡기는 프롬프트 5원칙 | [화면](https://sonovman.github.io/ai-practice-handbooks/prompt-basics/) | [CSV](data/prompt-templates.csv) |
| 03 | AI에게 일을 시키는 5가지 방법의 진화 — 프롬프트에서 하네스·루프·그래프까지 | [화면](https://sonovman.github.io/ai-practice-handbooks/engineering-evolution/) | [템플릿](engineering-evolution/templates/) |
| 04 | 개인 AI 에이전트, 챗봇과 무엇이 다른가 — 구축 5단계 | [화면](https://sonovman.github.io/ai-practice-handbooks/personal-agent/) | [템플릿](personal-agent/templates/) |
| 05 | AI를 손발처럼 쓰는 SSR Plus 4단계 — Claude 실행 환경 구축 | [화면](https://sonovman.github.io/ai-practice-handbooks/ssr-plus/) | [구축 키트](ssr-plus/kit/) |
| 06 | 특허 구성특징 분석 도우미 — 도면이 읽히는 청구항 분석 (4개 플랫폼) | [화면](https://sonovman.github.io/ai-practice-handbooks/claim-analyzer/) | [배포 키트](claim-analyzer/kit/) |
| 07 | AI 리서치, 인용은 사람이 확인한다 — 판례·심결 리서치와 인용 검증 5단계 | [화면](https://sonovman.github.io/ai-practice-handbooks/cite-check/) | [템플릿](cite-check/templates/) |
| 08 | 법제처에 직접 연결해 Claude로 법령·판례 리서치하기 — Korean Law MCP 로컬 설치 | [화면](https://sonovman.github.io/ai-practice-handbooks/korean-law-mcp/) | [템플릿](korean-law-mcp/templates/) |
| 09 | 판례 심층 해설 도우미 — 원문·논증·소송 경과 검증 (4개 플랫폼) | [화면](https://sonovman.github.io/ai-practice-handbooks/case-study/) | [배포 키트](case-study/kit/) |
| 10 | KIPRIS Plus 특허 API 활용과 Python 연동 | [화면](https://sonovman.github.io/ai-practice-handbooks/kipris-plus/) | [템플릿](kipris-plus/templates/) |

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
├── engineering-evolution/  03편 (templates/ 에 IP 분석 템플릿 8종)
├── personal-agent/     04편 (templates/ 에 지침·스킬·감시 스크립트)
├── ssr-plus/           05편 (kit/ 구축 사례 폴더, downloads/ ZIP 2종)
├── claim-analyzer/     06편 (kit/ 4개 플랫폼 버전, downloads/ ZIP 2종)
├── cite-check/         07편 (templates/ 프롬프트·인용 목록·점검기·스킬, downloads/ ZIP 2종)
├── korean-law-mcp/     08편 (templates/ 프롬프트·지침·설정 예시·설정 점검기·자료 검증표, downloads/ ZIP)
├── case-study/         09편 (kit/ 4개 플랫폼 버전·검수 에이전트·형식 점검기·Alice 예제, downloads/ ZIP 3종)
├── kipris-plus/        10편 (templates/ Python 클라이언트·오프라인 시험·API 목록, downloads/ ZIP)
└── data/               공용 자료
```

새 편을 추가하는 절차는 [새-핸드북-추가하기.md](새-핸드북-추가하기.md)를 보세요.

## 질문·오류 제보
이 저장소의 **Issues** 탭에 남겨 주세요.

## 이용 조건
본문 CC BY-NC 4.0 — 출처를 밝히면 비영리 목적으로 자유롭게 쓰고 고칠 수 있습니다.
