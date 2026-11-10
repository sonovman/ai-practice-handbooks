# Microsoft 365 Copilot — SharePoint 경로에 모아 두고 그 경로를 분석하기

Copilot에서는 파일을 대화창에 매번 올리지 않는다. **SharePoint 문서 라이브러리의 정해진 경로**에 회차별로 엑셀·공보 PDF를 모아 두고, Copilot 에이전트의 지식(knowledge)을 그 경로로 지정한다. 회사 권한·민감도 레이블이 그대로 적용되고, 팀원이 같은 자료를 보며, 회차가 쌓여도 경로 규칙만 지키면 된다.

## 1. 폴더 규칙 (예: 사이트 `IP-Intel` › 문서 › `PatentIntel`)
```
PatentIntel/
├── 00_설정/                    project.json · applicant_aliases.csv · column_aliases.csv (도구용)
│   └── 지침/                   COPILOT_AGENT_INSTRUCTIONS.md 사본, report-spec 등 참고 문서(.docx/.pdf로)
└── rounds/
    └── 2026-R4/                ← 회차 폴더 (정기: 2026-R4 · 수시: 2026-11-urgent-가나신제품)
        ├── 01_원자료/           this_round.xlsx (WIPSON 원본, 한 시트) · prev_round.xlsx
        ├── 02_공보/             공개·등록공보 PDF — 파일 이름 = 공개·등록번호 (예: KR1020250990021A.pdf)
        ├── 03_검증집계/          export_for_copilot.py 결과: 01_intake.html · 02_stats.html · scores.xlsx · clusters.xlsx · state.txt
        ├── 04_분석/             분석결과서(.docx) — 관문 A
        ├── 05_보고서/           보고서 초안·최종본(.docx/.pdf) — 관문 B
        └── 06_인계/             정밀분석 후보·인계 패킷 — 관문 C
```
- 파일·폴더 이름에 공백 대신 `_`를 쓰면 주소(URL)로 지정할 때 편하다.
- WIPSON 엑셀은 **한 시트**로 둔다(Copilot은 한 시트일 때 엑셀 데이터에 가장 잘 답한다). 원본은 고치지 않는다.

## 2. 숫자는 도구로, 읽기와 쓰기는 Copilot으로
Copilot은 지식 경로에서 **검색해 관련 부분을 읽는** 방식이라, 수백 건 엑셀·공보를 빠짐없이 세거나 전수 대조하는 일에는 맞지 않는다. 그래서:
1. SharePoint 라이브러리를 PC에 **OneDrive 동기화**(라이브러리의 '동기화' 또는 '내 파일에 바로 가기 추가')한다. 회사 PC의 탐색기에 `PatentIntel` 폴더가 생긴다.
2. 그 동기화 폴더를 대상으로 도구를 돌린다(파이썬은 PC에서, 결과는 자동으로 SharePoint에 올라감).
```
cd "<동기화 폴더>\PatentIntel"
python <키트>\tools\pi_intake.py rounds\2026-R4\01_원자료\this_round.xlsx --project 00_설정\project.json --previous rounds\2026-R4\01_원자료\prev_round.xlsx --pdf-dir rounds\2026-R4\02_공보 --out rounds\2026-R4\work\01_intake.json
python <키트>\tools\pi_stats.py rounds\2026-R4\work\01_intake.json --clusters rounds\2026-R4\work\clusters.csv --scores rounds\2026-R4\work\scores.csv --out rounds\2026-R4\work\02_stats.json
python <키트>\tools\export_for_copilot.py rounds\2026-R4\work rounds\2026-R4\03_검증집계
```
3. Copilot은 `.md·.json·.csv·.svg`를 지식으로 읽지 못하므로 `export_for_copilot.py`가 `.html·.xlsx·.txt`로 바꿔 `03_검증집계/`에 둔다. `work/` 폴더는 도구 전용(지식에서 빼도 됨).
4. 파이썬을 설치할 수 없는 PC라면 Claude·ChatGPT·Antigravity에서 도구를 돌린 결과 파일만 `03_검증집계/`에 올려도 된다.

## 3. 에이전트 만들기 (Copilot 에이전트 빌더)
1. Microsoft 365 Copilot 앱 → 에이전트 → **새 에이전트 만들기** → 구성(Configure) 탭.
2. 이름: `경쟁기술 인텔리전스` · 설명: `PatentIntel 회차 폴더의 공개특허를 분석해 승인 관문을 거쳐 경영진 보고서를 만든다`.
3. 지침(Instructions): `COPILOT_AGENT_INSTRUCTIONS.md` 내용을 붙여 넣는다(지침 칸 길이 제한에 맞춘 짧은 판).
4. 지식(Knowledge): **회차 폴더 주소**를 넣는다. 예: `https://<회사>.sharepoint.com/sites/IP-Intel/Shared Documents/PatentIntel/rounds/2026-R4` — 에이전트는 그 주소와 하위 폴더를 검색한다. `00_설정/지침`도 함께 넣으면 기준 문서를 참조한다. 주소에는 사이트 경로가 있어야 하고 `?` 뒤 매개변수는 빼야 한다.
5. 기능(Capabilities): 조직에서 허용되면 코드 인터프리터(문서·차트·계산)를 켠다. 그래도 문헌 수는 `02_stats.html` 값을 쓰게 지침에 못 박아 두었다.
6. 시작 프롬프트(Starter prompts): "자료 검증 결과 보여 줘" · "분석결과서 초안" · "보고서 초안" · "현재 관문 상태".
7. 만들기 → 테스트 창에서 "state.txt 기준으로 지금 어느 관문이야?"로 지식 연결을 확인한다.

## 4. 회차 운영
- 새 회차: 회차 폴더를 복사해 이름을 바꾸고 → 에이전트 지식 주소를 새 회차로 바꾸거나(한 에이전트), 상위 `rounds/`를 지정하고 질문마다 "2026-R4 폴더 기준"이라고 말한다(회차가 섞이지 않게 앞쪽 방식 권장).
- 새로 올린 파일은 반영까지 몇 분 걸릴 수 있다(지식 상태가 '준비 중'이면 기다리거나 새로 고침).
- 관문: 에이전트는 SharePoint에 상태 파일을 직접 쓰지 못할 수 있다. 사람이 답(승인/수정)을 주면 담당자가 `pi_gate.py reply`로 기록하고 export를 다시 돌려 `state.txt`를 갱신한다. 쓸 수 없는 환경이면 회차 폴더의 `state.txt`를 손으로 고친다.
- 분석결과서·보고서는 Copilot이 만든 Word 초안을 `04_분석/`·`05_보고서/`에 저장하고, 보고서 점검은 그 내용을 report.md로 저장해 `report_lint.py`로 확인한다.

## 5. 주의
- 에이전트는 **사용자가 볼 권한이 있는 파일만** 근거로 쓴다. 보고서를 받을 사람(경영진)이 회차 폴더 권한이 없으면 같은 질문에 다른 답이 나올 수 있다 — 최종본은 PDF로 고정해 배포.
- 조직이 'Restricted SharePoint Search'를 켜 두었으면 SharePoint를 지식으로 쓸 수 없다. IT 담당에게 확인.
- 당사 청구항·제품 로드맵은 별도 하위 폴더에 두고 권한을 IP팀으로 제한한다(같은 에이전트라도 권한 없는 사람에게는 보이지 않음).
- 기능·메뉴·라이선스별 차이는 바뀐다. 회사의 Copilot 안내를 확인한다.
