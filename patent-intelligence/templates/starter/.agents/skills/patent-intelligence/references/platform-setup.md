# 플랫폼별 설치·설정 (Claude·ChatGPT·Gemini·Microsoft 365 Copilot·Antigravity)

원본은 `starter` 하나. `python build_upload.py` → `dist/patent-intelligence.zip`(폴더가 ZIP 최상위: Claude·ChatGPT·Copilot Cowork), `dist/patent-intelligence-flat.zip`(SKILL.md가 최상위), `dist/patent-intelligence/`(펼친 폴더: Gemini 업로드·내용 보기). 업로드 묶음에는 도구(`tools/`)와 설정 예시(`config/`)가 함께 들어간다.

| 플랫폼 | 등록 | 도구 실행 | 이렇게 쓰면 좋다 |
|---|---|---|---|
| Claude 웹·데스크톱 | 설정에서 코드 실행·파일 생성 켜기 → Skills에 zip 업로드. 프로젝트를 만들어 `PROJECT_INSTRUCTIONS.md`를 지침 칸에 | 가능 | 회차마다 같은 프로젝트에서 엑셀·공보를 올리고 관문 진행. DOCX 최종본까지 |
| Claude Code·데스크톱 폴더 작업 | `.agents/skills/patent-intelligence`를 `.claude/skills/`로 복사, CLAUDE.md에 `@AGENTS.md` | 가능(로컬) | 공보 수백 건·여러 회차 폴더를 로컬에서 |
| ChatGPT | 워크스페이스에서 Skills가 켜져 있으면 업로드, 아니면 프로젝트 지침에 PROJECT_INSTRUCTIONS + 파일에 SKILL.md·references | 대체로 가능(파일 분석 기능) | 업로드 후 "test_pi_tools.py를 실행해" 로 먼저 확인 |
| Gemini 앱 | 맞춤설정 → Skills → 만들기, 또는 SKILL.md 폴더 업로드(폴더 이름 = 스킬 이름). 개인 계정은 2026-11-17부터 Gem이 skills로 전환, 업무 계정은 2027년 3월 예정 | 제한적 | 공보 판독·요약·초안. 숫자는 도구를 돌린 결과 파일(01_intake.md·02_stats.md)을 함께 올려 그것만 쓰게 |
| Microsoft 365 Copilot | **SharePoint 회차 폴더 방식**: 엑셀·공보를 `PatentIntel/rounds/<회차>`에 모으고, 에이전트 빌더에서 지침 = `COPILOT_AGENT_INSTRUCTIONS.md`, 지식 = 그 폴더 주소. 도구는 OneDrive로 동기화한 폴더에서 돌리고 `export_for_copilot.py`로 .html·.xlsx·.txt 결과를 둔다 → `copilot-sharepoint.md` | 에이전트는 읽기·작성, 숫자는 도구 | 회사 권한·민감도 레이블 안에서 팀이 같은 폴더를 봄 |
| Google Antigravity | starter 폴더를 작업 공간으로 열기(`.agents/skills`·`.agents/rules`·`AGENTS.md` 자동 인식). 전역으로 쓰려면 `~/.gemini/config/skills/`에 복사 | 가능(로컬) | 'AI 도움으로 구축' 절차는 아래 |

## 공통 첫 확인
1. `python tools/test_pi_tools.py` → 33개 통과.
2. `python tools/make_sample.py sample/inbox` → `python tools/pi_intake.py sample/inbox/this_round.xlsx --previous sample/inbox/prev_round.csv --pdf-dir sample/inbox/pdf --out work/01_intake.json` → 문헌 20 · 신규 7 · 동향대상 16 · 오류 1(번호 없음) · 경고 4.
3. `python tools/pi_stats.py work/01_intake.json --clusters sample/inbox/clusters.csv --scores sample/inbox/scores.csv` → 추천 5건, 2025년 미완결.

## Antigravity에서 AI 도움으로 구축하기
1. starter 폴더를 열고 에이전트에게: "AGENTS.md와 patent-intelligence 스킬을 읽고, tools 시험을 실행해 결과를 보여 줘."(명령 실행은 승인 후)
2. WIPSON 엑셀을 `inbox/`, 공보를 `inbox/pdf/`에 넣고: "config/project.json을 이번 회차에 맞게 같이 채우자. 모르는 칸은 나에게 하나씩 물어봐."
3. "pi_intake로 자료 검증 → 결과 오류·경고를 표로 보여 주고 멈춰."
4. "1차 선별해서 clusters.csv와 scores.csv 초안을 만들고, pi_stats 결과로 분석결과서를 써. ANALYSIS 관문에 제출하고 멈춰."
5. 관문마다 답(승인/수정)을 주면 보고서 → report_lint 오류 0 → render_report로 HTML/PDF.
6. 다음 회차: "rounds/2026-R4를 복사해 2027-R1을 만들고 직전 회차 목록을 --previous로 써."

## 정기 실행(예약)
- Claude·ChatGPT의 예약 작업 기능을 쓰면 "inbox에 새 파일이 있으면 1단계 검증과 분석결과서 초안까지 만들고 관문에서 멈춰"처럼 맡길 수 있다. WIPSON 다운로드 자체는 로그인·포인트가 걸려 사람이 하는 편이 안전하다.
- 예약 실행은 관문을 넘지 않는다(무응답 = 대기).

## 주의
- 메뉴·요금제별 기능은 자주 바뀐다. 각 서비스의 현재 안내를 확인한다.
- 공개특허 자체는 공개 정보지만 **당사 청구항·제품 로드맵·관심 경쟁사 목록은 기밀**이다. 회사가 승인한 계정(학습 제외·데이터 보호 설정)에서만 올리고, 개인이 운영하는 공개 중계 서버·확장 프로그램을 거치지 않는다.
- AI가 말한 영문 출원인명·법적상태·시장 수치는 원문으로 확인 전까지 '미확인'.
