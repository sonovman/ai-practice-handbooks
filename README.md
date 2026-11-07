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
| 11 | AI 합의 협의체 — 관점이 다른 에이전트의 토론과 합의 (4개 플랫폼) | [화면](https://sonovman.github.io/ai-practice-handbooks/council/) | [배포 키트](council/kit/) |
| 12 | 정밀한 지시를 위한 AI 프롬프트 기호 사용법 | [화면](https://sonovman.github.io/ai-practice-handbooks/prompt-symbols/) | [템플릿](prompt-symbols/templates/) |
| 13 | 지식 노트 6개와 Gemini 스킬 2개로 만드는 지속 가능한 AI 영상 제작 파이프라인 | [화면](https://sonovman.github.io/ai-practice-handbooks/video-pipeline/) | [템플릿](video-pipeline/templates/) |
| 14 | 스마트 머니 관점으로 차트를 읽는 AI 스킬 | [화면](https://sonovman.github.io/ai-practice-handbooks/smart-money/) | [템플릿](smart-money/templates/) |
| 15 | 텍스트 쌍 특허 분석을 범용 LLM에서 — 유사 특허 판별과 FTO | [화면](https://sonovman.github.io/ai-practice-handbooks/patent-pair/) | [템플릿](patent-pair/templates/) |
| 16 | Google Antigravity 입문 — 에이전트에게 일을 맡기는 개발 환경 | [화면](https://sonovman.github.io/ai-practice-handbooks/antigravity/) | [템플릿](antigravity/templates/) |
| 17 | AI 화이트보드 애니메이션 영상 자동 제작 — 대본에서 완성 영상까지 | [화면](https://sonovman.github.io/ai-practice-handbooks/whiteboard-video/) | [템플릿](whiteboard-video/templates/) |
| 18 | AI 티 지우는 윤문 스킬 — 만들고, 설치하고, 점검까지 | [화면](https://sonovman.github.io/ai-practice-handbooks/ai-polish/) | [템플릿](ai-polish/templates/) |
| 19 | Slow Think와 AI 회의 — 정확도를 올리는 생각 설계 | [화면](https://sonovman.github.io/ai-practice-handbooks/slow-think/) | [템플릿](slow-think/templates/) |
| 20 | 경영진용 논문·보고서·판례 요약 — 추출, 점검, 결론, 검증 | [화면](https://sonovman.github.io/ai-practice-handbooks/exec-brief/) | [템플릿](exec-brief/templates/) |
| 21 | REA로 역공학 하기 — 근거로 이해하고, 적법 범위에서 재구현 | [화면](https://sonovman.github.io/ai-practice-handbooks/rea-reverse-engineering/) | [템플릿](rea-reverse-engineering/templates/) |

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
├── council/            11편 (kit/ 4개 플랫폼 버전·위원·의장 에이전트·형식 점검기·실 사용 예제, downloads/ ZIP 2종)
├── prompt-symbols/     12편 (templates/ 업무 템플릿 4종·기호 약속표·점검 도구·A/B 시험표, downloads/ ZIP)
├── video-pipeline/     13편 (templates/ 노트북 요청문·스킬 2개·pipeline.py·도구 지도·실행 예, downloads/ ZIP)
├── smart-money/        14편 (templates/ 스킬·smc_tool.py·가상 데이터 시범·매매 기록표·플랫폼 안내, downloads/ ZIP 2종)
├── patent-pair/        15편 (templates/ 스킬·pairkit.py·chart_check.py·미세 조정 참고 코드·시범 자료·플랫폼 설정, downloads/ ZIP 2종)
├── antigravity/        16편 (templates/ starter 작업 폴더·MCP 일정 서버·check_workspace.py·요청문, downloads/ ZIP)
├── whiteboard-video/   17편 (templates/ starter 작업 폴더·wbkit.py·키 저장 도구·시범 자료, downloads/ ZIP)
├── ai-polish/          18편 (templates/ starter 작업 폴더·upload 웹 앱용 스킬·polish_check.py·ollama_polish.py·시범 자료, downloads/ ZIP)
├── slow-think/         19편 (templates/ starter 작업 폴더·스킬 4개·prompts·meeting_pack.py·evidence_check.py·시범 자료, upload/ 웹 앱용, downloads/ ZIP)
├── exec-brief/         20편 (templates/ starter 작업 폴더·스킬 2개·분야별 틀·관할별 판례 구조·용어집·evidence/cite/term_check·시범 자료, upload/ 웹 앱용, downloads/ ZIP)
├── rea-reverse-engineering/  21편 (templates/ starter 작업 폴더·reverse-engineer 스킬·scope_check·evidence_log·자작 바이너리 시범, upload/ 웹 앱용, downloads/ ZIP)
└── data/               공용 자료
```

새 편을 추가하는 절차는 [새-핸드북-추가하기.md](새-핸드북-추가하기.md)를 보세요.

## 질문·오류 제보
이 저장소의 **Issues** 탭에 남겨 주세요.

## 이용 조건
본문 CC BY-NC 4.0 — 출처를 밝히면 비영리 목적으로 자유롭게 쓰고 고칠 수 있습니다.
