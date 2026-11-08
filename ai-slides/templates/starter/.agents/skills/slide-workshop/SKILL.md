---
name: slide-workshop
description: AI로 수준 높은 슬라이드를 꾸준히 만들기 위한 워크플로우. 우수 레퍼런스에서 취향 명세서(디자인.md)를 뽑고, 본문을 슬라이드 개요로 만들고, 품질 게이트와 비주얼 QA 루프로 검수한다. 품질(객관)과 취향(스타일)을 분리.
---

# 슬라이드 제작 워크플로우(취향 명세서 + 품질/취향 분리)

단발성 프롬프트("예쁘게 만들어줘") 대신, 역할을 나눈 에이전트와 워크플로우로 품질을 일정하게 유지한다.
핵심 원칙: **품질(객관·Pass/Fail)과 취향(스타일·정답 없음)을 분리**한다.

## 1단계: 취향 명세서(디자인.md) 추출 — 순차
- 사람이 직접 만든 우수 레퍼런스 슬라이드(AI 냄새 없는 것)를 입력한다.
- 컬러·폰트 비율·레이아웃 다양성(여러 Type)·강약 전개·정보 밀도를 마크다운 루브릭으로 뽑는다.
- 목적은 '재현성(Robustness)' — 다른 주제에도 같은 스타일을 재현할 수 있게.
- 프롬프트: `prompts/01-extract-taste.md`

## 2단계: 본문 → 슬라이드 개요 생성 — 병렬 가능
- 본문.md와 디자인.md를 함께 주고, 정의된 레이아웃 Type을 섞어 개요를 만든다.
- 긴 문서는 챕터로 나눠 병렬 생성 후 합친다.
- 단조로운 표 반복과 'A가 아니라 B' 같은 AI 클리셰를 금지한다.
- 프롬프트: `prompts/02-generate-slides.md`

## 3단계: 품질 게이트 + 비주얼 QA — 루프
- **품질 게이트(객관)**: `python tools/slide_lint.py 초안.md --slides N --require "..." --body 본문.md --design 디자인.md`
  분량·요구 키워드·본문 대비 수치·AI 클리셰를 Pass/Fail로 판정.
- **비주얼 QA(눈)**: `python tools/deck_html.py 초안.md --out work/deck.html` 로 미리보기를 만들어
  글자 겹침·줄바꿈·여백 쏠림을 사람이 확인. (실제 PPTX가 아니라 검토용)
- 프롬프트: `prompts/03-quality-gate.md`, `prompts/04-visual-qa.md`

## 4단계: 사람 리터치 → 루브릭 고도화 — Human-in-the-loop
- 사람이 2차 리터치한 결과와 1차 AI 결과를 대조해, 바뀐 취향 포인트를 디자인.md에 반영.
- 프롬프트: `prompts/05-retouch-diff.md`

## 실제 PPTX로 만들기
- Claude에서 바로 발표 자료를 만들 땐 Slides(슬라이드) 기능을 쓰면 .pptx로 내려받을 수 있다.
- 개요(발표자료_초안.md)와 디자인.md를 근거로 주고, 품질 게이트를 통과한 개요만 PPTX로 올린다.

## 참조
- `references/checklist.md` — 품질 게이트 vs 취향 루브릭 구분표, 체크리스트
- `references/platforms.md` — Claude·ChatGPT·Gemini·Copilot·Antigravity 대응
