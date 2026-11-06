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
    id: "excel-analysis",
    no: "06",
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
