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
    id: "excel-analysis",
    no: "03",
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
