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
    id: "excel-analysis",
    no: "11",
    category: "데이터",
    title: "엑셀 데이터를 AI로 분석하고 그래프까지 받기",
    subtitle: "준비 중",
    summary: "다음에 공개할 예정입니다.",
    reader: "",
    version: "",
    date: "",
    length: "",
    status: "draft",
    links: []
  }
];
