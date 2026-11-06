# 플랫폼별 설치 안내

스킬 본문(`SKILL.md`)은 3,400자 정도라 네 플랫폼 모두 지침 칸에 그대로 들어갑니다.
함께 올릴 파일은 `references/framework.md`, `references/output-template.md` 두 개이고, 코드를 실행할 수 있는 곳에는 `smc_tool.py`도 올립니다.

## Claude

1. `smart-money-chart-analyst.zip`을 설정의 스킬 메뉴(Customize → Skills → Upload a skill)에 올립니다.
2. Claude Code는 `smart-money-chart-analyst/` 폴더를 `~/.claude/skills/`에 복사합니다.
3. 대화에 CSV를 첨부하고 "일봉·60분봉으로 분석해 줘"라고 하면 스킬이 `scripts/smc_tool.py facts`를 실행해 사실 표부터 만듭니다(코드 실행 기능이 켜져 있어야 함).

## ChatGPT

1. 새 프로젝트(또는 GPT)를 만들고 지침 칸에 `SKILL.md`의 `---` 아래 본문을 붙여 넣습니다.
2. 파일 칸에 `framework.md`, `output-template.md`, `smc_tool.py`를 올립니다.
3. 대화에 CSV를 첨부하고 "smc_tool.py로 facts를 먼저 만든 뒤 분석해 줘"라고 요청합니다. 데이터 분석(코드 실행)이 꺼져 있으면 내 PC에서 돌린 `facts` 출력을 붙여 넣습니다.

## Gemini

1. 스킬을 쓸 수 있는 계정(개인 계정은 2026-11-17부터 순차 전환)은 Gemini 앱의 스킬 메뉴에서 `smart-money-chart-analyst.zip`을 올리고 대화창에서 `/smart-money-chart-analyst`로 부릅니다.
2. 스킬 전환 전이면 새 Gem의 요청 사항 칸에 본문을, 지식 칸에 `framework.md`, `output-template.md`를 넣습니다.
3. 스킬 안의 스크립트 실행은 제한이 있으므로, 내 PC에서 `python smc_tool.py facts 파일.csv`를 돌려 출력을 함께 붙여 넣는 방식을 기본으로 합니다.

## Copilot

1. Copilot Studio에서 에이전트를 만들고 지침 칸(최대 8,000자)에 본문을 붙여 넣습니다.
2. 지식에 `framework.md`, `output-template.md`를 올립니다.
3. 코드 실행 기능을 켤 수 없는 환경이면 `facts` 출력을 붙여 넣어 분석을 요청합니다.

## 어느 플랫폼에서나 — 요청 예

```
/smart-money-chart-analyst
종목: 가상종목A
시간대: 일봉(HTF), 60분봉(LTF)
포지션: 없음
자본금 1,000만 원, 1회 허용 손실 1%
이벤트: 모름
(daily.csv, hourly.csv 첨부 — 또는 facts 출력 붙여 넣기)
```
