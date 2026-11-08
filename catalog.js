/*
  ┌──────────────────────────────────────────────────────────┐
  │  핸드북 목록 — 새 글을 올릴 때는 이 파일만 고치면 됩니다.   │
  │  아래 { ... } 묶음 하나가 표지의 카드 하나가 됩니다.        │
  │  맨 위에 넣은 것이 맨 위에 보입니다.                        │
  └──────────────────────────────────────────────────────────┘

  항목 설명
    id        : 폴더 이름과 같게 (영문 소문자·하이픈)
    no        : 번호 (표지에 "01"처럼 표시)
    category  : 분류. 같은 이름끼리 필터 버튼으로 묶입니다.
    title     : 제목
    subtitle  : 부제 (한 줄)
    summary   : 소개 (두세 문장)
    reader    : 대상 독자
    version   : 판 번호
    date      : 공개·수정일 (YYYY-MM-DD)
    length    : 분량 안내
    status    : "published" (공개) 또는 "draft" (준비 중, 흐리게 표시)
    links     : 버튼 목록. label 은 버튼 글자, href 는 연결할 주소
                primary: true 를 넣으면 검은 버튼
*/
window.CATALOG = [
  {
    id: "agent-guide",
    no: "01",
    category: "에이전트",
    title: "에이전트는 한 명이면 충분하다",
    subtitle: "단독 에이전트와 멀티 에이전트 팀, 구축과 활용",
    summary: "실제 테스트 결과로 두 방식을 비교하고, 일반 업무와 IP 업무에 맞게 단독 에이전트 + 리뷰어 + 사람 승인 체계를 구축하는 방법을 정리했습니다. CLAUDE.md와 리뷰어 프롬프트 템플릿을 함께 제공합니다.",
    reader: "AI 에이전트를 업무에 들이려는 기업 실무자, IP 부서 담당자",
    version: "1.0",
    date: "2026-11-06",
    length: "읽기 약 20분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "agent-guide/", primary: true },
      { label: "템플릿 내려받기", href: "agent-guide/templates/" }
    ]
  },
  {
    id: "prompt-basics",
    no: "02",
    category: "프롬프트",
    title: "보고서 초안을 AI에게 맡기는 프롬프트 5원칙",
    subtitle: "역할 · 맥락 · 형식 · 예시 · 검증",
    summary: "“요약해 줘” 한 줄 대신 다섯 가지만 넣으면 결과물이 달라집니다. 회의록 요약을 예로 완성형 프롬프트까지 만들어 봅니다.",
    reader: "보고서·기획서를 자주 쓰는 실무자 (AI 경험 없어도 됨)",
    version: "1.0",
    date: "2026-11-06",
    length: "읽기 약 10분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "prompt-basics/", primary: true },
      { label: "템플릿(CSV)", href: "data/prompt-templates.csv" }
    ]
  },
  {
    id: "engineering-evolution",
    no: "03",
    category: "에이전트",
    title: "AI에게 일을 시키는 5가지 방법의 진화",
    subtitle: "프롬프트 엔지니어링에서 하네스·루프·그래프 엔지니어링까지",
    summary: "AI 활용법이 프롬프트 → 컨텍스트 → 하네스 → 루프 → 그래프로 어떻게 발전했는지 비개발자 눈높이로 정리하고, 청구항 대비 분석 업무에 다섯 단계를 적용한 워크플로우와 템플릿 8종을 제공합니다.",
    reader: "“하네스 엔지니어링”이 궁금한 비개발 실무자, IP 분석 담당자",
    version: "1.0",
    date: "2026-11-06",
    length: "읽기 약 25분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "engineering-evolution/", primary: true },
      { label: "템플릿 내려받기", href: "engineering-evolution/templates/" }
    ]
  },
  {
    id: "personal-agent",
    no: "04",
    category: "에이전트",
    title: "개인 AI 에이전트, 챗봇과 무엇이 다른가",
    subtitle: "개념부터 구축 5단계까지 — 자체 서버(Hermes)와 플랫폼 에이전트",
    summary: "챗봇과 에이전트의 네 가지 차이, 자체 서버 에이전트와 플랫폼 에이전트 비교, Hermes Agent로 24시간 텔레그램 알림 에이전트를 만드는 5단계를 공식 문서로 확인한 명령어로 안내합니다. 바뀌었을 때만 알리는 감시 스킬과 실행 검증한 스크립트를 제공합니다.",
    reader: "코딩 경험 없이 에이전트를 처음 만들어 보려는 실무자",
    version: "1.0",
    date: "2026-11-06",
    length: "읽기 약 20분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "personal-agent/", primary: true },
      { label: "템플릿 내려받기", href: "personal-agent/templates/" }
    ]
  },
  {
    id: "ssr-plus",
    no: "05",
    category: "Claude 활용",
    title: "AI를 손발처럼 쓰는 SSR Plus 4단계",
    subtitle: "스킬 · 세컨드 브레인 · 루틴 · 익스텐션으로 Claude 실행 환경 세팅하기",
    summary: "AI 성능보다 실행 환경이 업무 부담을 줄입니다. 네 단계를 초급·중급·고급으로 나눠 설명하고, IP팀 업무 시스템을 실제 폴더로 만든 구축 키트(공보 브리프 스킬·대문 파일·루틴·링크 점검기)를 공식 검증 도구로 확인해 제공합니다.",
    reader: "Claude를 매일 쓰지만 매번 같은 설명을 반복하고 있는 실무자",
    version: "1.0",
    date: "2026-11-06",
    length: "읽기 약 20분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "ssr-plus/", primary: true },
      { label: "구축 키트 받기", href: "ssr-plus/kit/" }
    ]
  },
  {
    id: "claim-analyzer",
    no: "06",
    category: "IP 실무",
    title: "특허 구성특징 분석 도우미",
    subtitle: "도면이 읽히는 청구항 분석 — Claude·ChatGPT·Gemini·Copilot 4개 버전",
    summary: "급하게 청구항을 해석하고 FTO·침해 검토를 준비할 때, 독립항 구성요소와 공보 도면부호를 짝지어 도면이 바로 읽히게 하는 분석 스킬·에이전트입니다. 문헌 잠금·부호 점검·회피설계·중단 조건을 갖췄고, 4개 플랫폼 버전의 일치를 점검 스크립트로 확인했습니다.",
    reader: "청구항 해석·FTO·침해 검토를 준비하는 IP 담당자, 변리사, 개발 엔지니어",
    version: "1.0",
    date: "2026-11-06",
    length: "읽기 약 20분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "claim-analyzer/", primary: true },
      { label: "배포 키트 받기", href: "claim-analyzer/kit/" }
    ]
  },
  {
    id: "cite-check",
    no: "07",
    category: "IP 실무",
    title: "AI 리서치, 인용은 사람이 확인한다",
    subtitle: "판례·심결·선행문헌 리서치와 인용 검증 5단계",
    summary: "AI는 없는 판례 번호와 원문에 없는 문장도 그럴듯하게 만듭니다. 쟁점 정리부터 미검증 표, 원문·효력 확인, 확인된 근거만으로 쓰는 메모까지 5단계를 국내 IP 실무에 맞게 정리하고, 인용 점검 스크립트와 프롬프트·지침·Claude 스킬을 함께 제공합니다.",
    reader: "심판·소송·의견서 준비에 AI를 쓰는 변리사, IP 담당자, 사내 법무",
    version: "1.0",
    date: "2026-11-07",
    length: "읽기 약 20분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "cite-check/", primary: true },
      { label: "템플릿 내려받기", href: "cite-check/templates/" }
    ]
  },
  {
    id: "korean-law-mcp",
    no: "08",
    category: "Claude 활용",
    title: "법제처에 직접 연결해 Claude로 법령·판례 리서치하기",
    subtitle: "Korean Law MCP 로컬 설치 — 공개 서버 없이, 내 인증키로, 버전 고정",
    summary: "오픈소스 Korean Law MCP를 내 컴퓨터에 버전 고정 설치해 중간 서버 없이 법제처 Open API에 직접 연결하는 방법을 소스 코드와 실행 시험으로 확인했습니다. 설치·Claude Desktop/Code 연결·사용법·검증 범위와 설정 점검기를 제공하고, 처음 설정하고 쓸 때 헷갈리기 쉬운 14가지 주의할 점도 정리했습니다.",
    reader: "Claude에 법령·판례 조회를 붙이려는 사내 법무·IP 담당자, 실무자",
    version: "1.0",
    date: "2026-11-07",
    length: "읽기 약 20분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "korean-law-mcp/", primary: true },
      { label: "템플릿 내려받기", href: "korean-law-mcp/templates/" }
    ]
  },
  {
    id: "case-study",
    no: "09",
    category: "IP 실무",
    title: "판례 심층 해설 도우미",
    subtitle: "원문·법원 논증·소송 경과 검증 — Claude·ChatGPT·Gemini·Copilot 4개 버전",
    summary: "교재·논문·서면에 인용된 판례의 공식 원문을 먼저 찾아 당사자 주장과 인정 사실을 나누고, 법원의 논증과 심급 이력, 교재 설명을 11개 항목으로 해설하는 스킬·에이전트입니다. 근거마다 출처 등급과 쪽수를 붙이고, Alice 판결로 실제 사용 예제를 보이며, 형식 점검기와 4개 버전 일치 점검을 제공합니다.",
    reader: "판례를 공부하거나 서면·강의에 인용하는 변리사, IP·법무 담당자, 수험생",
    version: "1.0",
    date: "2026-11-07",
    length: "읽기 약 20분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "case-study/", primary: true },
      { label: "배포 키트 받기", href: "case-study/kit/" }
    ]
  },
  {
    id: "kipris-plus",
    no: "10",
    category: "데이터",
    title: "KIPRIS Plus 특허 API 활용과 Python 연동",
    subtitle: "개요 · 구성 · 요금 · 신청 · Python 호출 — 특허기술거래·국유특허 데이터까지",
    summary: "KIPRIS Plus와 공공데이터포털의 특허·기술거래 Open API를 공식 이용 가이드 기준으로 정리했습니다. 무료 한도(월 1,000건)와 속도 제한, 신청부터 인증키·브라우저 시험까지 안내하고, 키 노출·한도 초과를 막는 표준 라이브러리 Python 클라이언트와 오프라인 시험을 제공합니다.",
    reader: "특허 데이터를 직접 받아 분석하려는 IP·기술이전 담당자, 중소기업 실무자, 연구자",
    version: "1.0",
    date: "2026-11-07",
    length: "읽기 약 20분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "kipris-plus/", primary: true },
      { label: "템플릿 내려받기", href: "kipris-plus/templates/" }
    ]
  },
  {
    id: "council",
    no: "11",
    category: "에이전트",
    title: "AI 합의 협의체",
    subtitle: "관점이 다른 에이전트들이 토론해 결론을 내게 하기 — Claude·ChatGPT·Gemini·Copilot 4개 버전",
    summary: "LLM Council 계열 저장소 6곳을 보안·비용·구축·사용 기준으로 비교하고, 추가 키·중계 서버 없이 위원 5인이 독립 의견·익명 검토·반박을 거쳐 합의 수준을 밝힌 결론을 내는 스킬·에이전트를 만들었습니다. 이 추천 자체를 협의체에 올려 검증한 실 사용 예제와 형식 점검기를 제공합니다.",
    reader: "중요한 결정·계획·문안을 다각도로 검증하고 싶은 실무자, IP·법무 담당자, 팀 리더",
    version: "1.0",
    date: "2026-11-07",
    length: "읽기 약 20분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "council/", primary: true },
      { label: "배포 키트 받기", href: "council/kit/" }
    ]
  },
  {
    id: "prompt-symbols",
    no: "12",
    category: "프롬프트",
    title: "정밀한 지시를 위한 AI 프롬프트 기호 사용법",
    subtitle: "#, -, *, {}, [], <>, \"\" 7가지 기호와 XML 태그 — 원리·약속·템플릿·점검 도구",
    summary: "기호가 AI 지시를 정밀하게 만드는 이유를 토크나이저·Self-Attention·사전 학습 데이터·임베딩의 네 가지 원리와 근거 수준으로 설명하고, 7가지 기호와 XML 태그의 활용법을 처음 접근과 개선 방식으로 정리했습니다. 팀 공통 기호 약속표, 업무 템플릿 4종, 점검·변수 채우기 도구를 제공합니다.",
    reader: "보고서·메일·분석을 AI에게 맡기는 실무자, 팀 공용 프롬프트를 관리하는 담당자",
    version: "1.0",
    date: "2026-11-07",
    length: "읽기 약 20분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "prompt-symbols/", primary: true },
      { label: "템플릿 내려받기", href: "prompt-symbols/templates/" }
    ]
  },
  {
    id: "video-pipeline",
    no: "13",
    category: "콘텐츠",
    title: "지식 노트 6개와 Gemini 스킬 2개로 만드는 지속 가능한 AI 영상 제작 파이프라인",
    subtitle: "조사는 한 번, 계산은 코드로, 생성은 도구가 바뀌어도",
    summary: "NotebookLM 노트북 6개에 니치 조사를 쌓고, 그 보고서를 넣은 Gemini 스킬 2개(스토리 엔진·에셋 생성기)로 대본과 장면 프롬프트를 계속 만들어 냅니다. Gems → Skills 전환과 2026년 영상 도구 생태계, 장면 계산·스킬 묶음 도구를 함께 담았습니다.",
    reader: "유튜브·쇼츠 운영자, 홍보 영상을 직접 만드는 실무자",
    version: "1.0",
    date: "2026-11-07",
    length: "읽기 약 25분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "video-pipeline/", primary: true },
      { label: "템플릿 내려받기", href: "video-pipeline/templates/" }
    ]
  },
  {
    id: "smart-money",
    no: "14",
    category: "투자",
    title: "스마트 머니 관점으로 차트를 읽는 AI 스킬 — 시장의 큰 물결을 감지하기",
    subtitle: "숫자는 데이터에서, 판단은 시나리오로, 실력은 기록으로",
    summary: "차트를 넣으면 다우 이론·와이코프·SMC 관점에서 추세와 시장 단계, 큰 자금의 흔적(오더 블록·FVG·유동성 스윕·거래량)을 정리하고 무효 조건이 있는 조건부 매매 시나리오를 만듭니다. 사실 추출·수량 계산·매매 기록 검증 도구와 가상 데이터 시범을 함께 담았습니다. 투자 권유가 아닙니다.",
    reader: "주식·코인 개인 투자자, 차트 분석을 공부하는 사람",
    version: "1.0",
    date: "2026-11-07",
    length: "읽기 약 25분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "smart-money/", primary: true },
      { label: "템플릿 내려받기", href: "smart-money/templates/" }
    ]
  },
  {
    id: "patent-pair",
    no: "15",
    category: "특허",
    title: "텍스트 쌍 특허 분석을 범용 LLM에서 — 유사 특허 판별과 FTO",
    subtitle: "청구항 × 발명의 설명, 구성요소별 근거 인용, 모든 구성요소 원칙",
    summary: "청구항과 발명의 설명을 짝지은 텍스트 쌍으로 특허를 판단하는 출원발명(공개 10-2025-0013094)의 아이디어를 Claude·ChatGPT·Gemini·Microsoft 365 Copilot에서 유사 특허 판별과 FTO에 쓰는 방법. 전처리·클레임 차트·인용 점검 도구, 자동 레이블 평가 세트, 소형 모델 미세 조정 경로를 담았습니다.",
    reader: "변리사·특허 담당자, 특허 분석 도구 개발자",
    version: "1.0",
    date: "2026-11-07",
    length: "읽기 약 30분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "patent-pair/", primary: true },
      { label: "템플릿 내려받기", href: "patent-pair/templates/" }
    ]
  },
  {
    id: "antigravity",
    no: "16",
    category: "개발 도구",
    title: "Google Antigravity 입문 — 에이전트에게 일을 맡기는 개발 환경",
    subtitle: "규칙은 파일로, 반복 작업은 스킬로, 외부 도구는 MCP로, 실행 범위는 권한으로",
    summary: "Google Antigravity를 처음 쓰는 사람을 위한 따라 하기 안내. 2.0 앱·IDE·CLI·SDK 구조, 규칙·스킬·워크플로·MCP·아티팩트·권한 설정, 스네이크 게임과 MCP 일정 서버 실습, 2026년 11월 기준 요금제와 모델을 담았습니다.",
    reader: "Antigravity를 처음 쓰는 사람, 에이전트로 업무를 자동화하려는 실무자",
    version: "1.0",
    date: "2026-11-07",
    length: "읽기 약 25분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "antigravity/", primary: true },
      { label: "템플릿 내려받기", href: "antigravity/templates/" }
    ]
  },
  {
    id: "whiteboard-video",
    no: "17",
    category: "콘텐츠",
    title: "AI 화이트보드 애니메이션 영상 자동 제작 — 대본에서 완성 영상까지",
    subtitle: "목소리를 먼저 만들고, 그 실제 길이에 손그림을 맞춘다",
    summary: "오픈소스 srt-whiteboard-animation과 HyperFrames, Gemini TTS를 Google Antigravity에서 엮어 대본 한 장으로 손그림 화이트보드 설명 영상을 만드는 방법. API 키를 키체인에 보관하는 법, 자막·그리기 시간 자동 맞춤 도구(wbkit.py), 실제 렌더 시범을 담았습니다.",
    reader: "설명·강의 영상을 직접 만드는 사람, 16편으로 Antigravity를 설치한 초보자",
    version: "1.0",
    date: "2026-11-07",
    length: "읽기 약 30분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "whiteboard-video/", primary: true },
      { label: "템플릿 내려받기", href: "whiteboard-video/templates/" }
    ]
  },
  {
    id: "ai-polish",
    no: "18",
    category: "글쓰기",
    title: "AI 티 지우는 윤문 스킬 — 만들고, 설치하고, 점검까지",
    subtitle: "적게 고치고, 무엇이 바뀌었는지 확인할 수 있는 윤문 절차",
    summary: "한국어 im-not-ai, 영어 humanizer, 한국어 AI 문체 연구 KatFishNet을 바탕으로 의미를 지키며 AI 티를 덜어 내는 윤문 스킬을 Google Antigravity에서 구축하는 방법. Claude·ChatGPT·Gemini·Microsoft 365 Copilot 설정, 비밀 문서용 로컬 Ollama 구성, 인용·수치·한정 표현을 대조하는 점검 도구를 담았습니다.",
    reader: "AI 초안을 보고서·의견서·칼럼으로 다듬는 실무자, 특허·법률 문서를 다루는 사람",
    version: "1.0",
    date: "2026-11-07",
    length: "읽기 약 30분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "ai-polish/", primary: true },
      { label: "템플릿 내려받기", href: "ai-polish/templates/" }
    ]
  },
  {
    id: "slow-think",
    no: "19",
    category: "프롬프트",
    title: "Slow Think와 AI 회의 — 정확도를 올리는 생각 설계",
    subtitle: "마법의 문구 대신 생각 설정과 점검 항목, 연기 대신 독립 의견과 보류 사유",
    summary: "Slow Think 기법과 AI 회의 모듈화 전략을 2026년 추론 모델 기준으로 다시 설계했습니다. 전제 점검·질문 다듬기·독립 의견→반론→의장 종합·원문 근거 대조형 논문 요약을 스킬과 도구로 만들어 Antigravity·Claude·ChatGPT·Gemini·Microsoft 365 Copilot에서 쓰는 방법을 담았습니다.",
    reader: "기획안·전략·논문 검토에 AI를 쓰는 실무자와 관리자",
    version: "1.0",
    date: "2026-11-08",
    length: "읽기 약 30분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "slow-think/", primary: true },
      { label: "템플릿 내려받기", href: "slow-think/templates/" }
    ]
  },
  {
    id: "exec-brief",
    no: "20",
    category: "리서치",
    title: "경영진용 논문·보고서·판례 요약 — 추출, 점검, 결론, 검증",
    subtitle: "원문 사실을 먼저 뽑고, 증거의 한계를 따지고, 결론부터 1쪽에, 인용·판례번호·용어는 기계로 대조",
    summary: "학술 논문·연구 보고서·전 세계 판례를 경영진과 전문가가 바로 의사결정에 쓰는 1쪽 브리핑으로 만드는 방법. 분야별 틀과 관할별 판례 구조, Slow Think 기반 증거 한계 점검, 인용·판례번호·전문 용어 대조 도구를 스킬로 구현해 Antigravity·Claude·ChatGPT·Gemini·Microsoft 365 Copilot에서 씁니다.",
    reader: "논문·보고서·판례를 경영진에게 보고하는 연구·기획·법무·IP 담당자",
    version: "1.0",
    date: "2026-11-08",
    length: "읽기 약 35분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "exec-brief/", primary: true },
      { label: "템플릿 내려받기", href: "exec-brief/templates/" }
    ]
  },
  {
    id: "rea-reverse-engineering",
    no: "21",
    category: "개발 도구",
    title: "REA로 역공학 하기 — 근거로 이해하고, 적법 범위에서 재구현",
    subtitle: "오픈소스 MCP 도구 REA를 Claude Code에 연결해, 권한 있는 대상만 근거 기반으로 분석",
    summary: "소스 코드가 없는 프로그램의 동작 원리를 디컴파일러(Ghidra·IDA·Hopper)를 연결하는 오픈소스 MCP 도구 REA로 파악하는 방법. 내가 만든·오픈소스·분석 권한이 있는 대상에 한정하고, 저작권법 역분석 요건과 적법 범위 점검 도구, 근거 규율, 자작 바이너리 시범을 담았습니다. Antigravity 연계.",
    reader: "레거시·독자 포맷에서 내 데이터를 꺼내거나 호환성·보안 연구·교육 목적으로 바이너리를 분석하려는 개발자, IP 실무자",
    version: "1.0",
    date: "2026-11-08",
    length: "읽기 약 30분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "rea-reverse-engineering/", primary: true },
      { label: "템플릿 내려받기", href: "rea-reverse-engineering/templates/" }
    ]
  },
  {
    id: "git-github",
    no: "22",
    category: "개발 도구",
    title: "바이브 코딩을 위한 Git·GitHub — 안전하게 공유하고 함께 고치기",
    subtitle: "올리기 전에 비밀을 막고, 커밋·브랜치·PR로 함께 고도화",
    summary: "비개발자가 바이브 코딩으로 만든 스킬·에이전트를 Git·GitHub로 안전하게 공유·협업하는 법. 커밋·브랜치의 내부 동작, 올리기 전 비밀정보 사전 차단(점검 도구·.gitignore·pre-commit), 충돌·PR·브랜치 보호, 유출 시 응급 조치까지 초보자용 단계별로 담았습니다.",
    reader: "바이브 코딩·에이전트·스킬을 만들어 공유하려는 비개발자, Git을 처음 쓰는 사람",
    version: "1.0",
    date: "2026-11-08",
    length: "읽기 약 30분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "git-github/", primary: true },
      { label: "템플릿 내려받기", href: "git-github/templates/" }
    ]
  },
  {
    id: "claude-master",
    no: "23",
    category: "Claude 활용",
    title: "초보자를 위한 Claude 마스터 가이드 — 개념 정리부터 AI 업무 시스템까지",
    subtitle: "다 깔지 말고 작게 시작해 나만의 AI 업무 시스템으로",
    summary: "Claude를 업무에 처음 붙이는 사람을 위한 완전 가이드. 쓰는 3가지 방법(모드 통합)·모델 고르기·꼭 아는 7가지 기능·SSR Plus로 AI 업무 시스템 만들기·책상(컨텍스트) 관리·예스맨 방지 검증까지. CLAUDE.md·스킬 자동 초안 도구를 포함해 초보자용 단계별로 담았습니다.",
    reader: "Claude를 제대로 활용하고 싶은 초보자, 개념이 뒤섞여 어디서 시작할지 막막한 사람",
    version: "1.0",
    date: "2026-11-08",
    length: "읽기 약 20분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "claude-master/", primary: true },
      { label: "템플릿 내려받기", href: "claude-master/templates/" }
    ]
  },
  {
    id: "ai-slides",
    no: "24",
    category: "콘텐츠",
    title: "AI 디자인 에이전트로 PPT 슬라이드 만들기 — 취향 명세서와 워크플로우",
    subtitle: "단발성 프롬프트 대신 디자인.md와 품질/취향 분리로",
    summary: "AI로 수준 높은 슬라이드를 꾸준히 만드는 법. 우수 레퍼런스에서 취향 명세서(디자인.md)를 뽑고, 본문을 슬라이드 개요로 만들고, 품질 게이트(Pass/Fail)와 비주얼 QA 루프로 검수합니다. 품질과 취향의 분리, 순차·병렬·루프 워크플로우, Antigravity·Claude Code 비교까지 실사례로 담았습니다.",
    reader: "AI로 보고용·발표용 슬라이드를 자주 만들고 싶은 사람, 'AI 티'가 고민인 사람",
    version: "1.0",
    date: "2026-11-08",
    length: "읽기 약 20분",
    status: "published",
    links: [
      { label: "화면으로 읽기", href: "ai-slides/", primary: true },
      { label: "템플릿 내려받기", href: "ai-slides/templates/" }
    ]
  }
];
