# 플랫폼별 설치·설정 (Claude·ChatGPT·Gemini·Microsoft 365 Copilot·Antigravity)

원본은 `starter` 하나입니다. `python build_upload.py` → `dist/obviousness.zip`(Claude·ChatGPT), `dist/obviousness-flat.zip`(Copilot 등), `dist/obviousness/`(Gemini).
30편(claim-decompose·claim-chart)·31편(claim-construe) 스킬과 함께 쓰면 분해 → 해석 → 진보성 → 차트가 이어집니다. 한 번에 쓰려면 통합 키트(claim-suite v2)를 쓰세요.

| 플랫폼 | 등록 | 도구 실행 | 메모 |
|---|---|---|---|
| Claude 웹·데스크톱 | 설정에서 코드 실행·파일 생성 켜기 → Skills에 obviousness.zip(+30·31편 zip) | 가능 | 프로젝트 지식에 특허·선행문헌·기술상식 자료 |
| Claude Code·Cowork | `.agents/skills/obviousness`를 `.claude/skills/`로, CLAUDE.md에 `@AGENTS.md` | 가능(로컬) | 같은 사건 폴더 |
| ChatGPT | Skills(지원 요금제)에 zip, 또는 프로젝트 지침에 SKILL.md | 대체로 가능 | 파일 업로드 후 도구 실행 확인 |
| Gemini 앱(Gem) / CLI | Gem 지침에 SKILL.md+AGENTS.md / CLI는 GEMINI.md에 `@AGENTS.md` | Gem 제한적 / CLI 가능 | Gem은 대비·동기 정리용 |
| M365 Copilot | 에이전트 지침에 SKILL.md 요약, 지식에 references / 조직이 허용하면 flat.zip | 환경에 따라 확인 | 의뢰인 문서 접근 권한 확인 |
| Google Antigravity | starter 폴더를 작업 공간으로 | 가능(로컬) | `.agents/rules/obviousness.md`가 요청 시 적용 |

## 공통 첫 확인
1. `python tools/test_obviousness_check.py` → 29개 통과.
2. `python tools/obviousness_check.py sample/obviousness.json` → 오류 0 · 경고 8, D3=B, D2=C, D1=-, D4=X.
3. `python tools/obviousness_check.py sample/obviousness.json --chart C1 --chart-out work/02_chart.json` 후 `python tools/chart_lint.py work/02_chart.json` → 오류 0.

## Antigravity에서 AI 도움으로 구축하기
1. starter 폴더를 열고 "tools 시험을 모두 실행해 결과를 보여 줘"(명령 실행은 승인 후).
2. `inbox/`에 청구항·명세서·선행문헌(PDF·텍스트)을 넣고 요청: "30편 원장 → 31편 해석 → 문헌별 ●◐○ 대비(위치 포함) → A/B/C 분류 → 상위 B 차이점마다 기준일 기술상식 조사 계획과 검색어 → 06_obviousness.json → obviousness_check 오류 0까지 → C1을 진보성 차트로".
3. 기술상식 증거는 사람이 원문을 열어 날짜·위치를 확인한 뒤에만 established로 바꿉니다.
4. 사람이 결합 동기·저해 사유·2차적 고려사항을 검토하고 결론을 씁니다.

## 주의
- 메뉴·요금제별 기능은 바뀝니다. 각 서비스의 현재 안내를 확인하세요.
- 의뢰인·상대방 자료는 승인된 환경에서만, 개인 운영 중계 서버 연동은 쓰지 않습니다.
- AI가 찾은 "기술상식"은 출처가 실제로 있는지, 날짜가 기준일 전인지 반드시 원문으로 확인합니다(없는 문헌을 지어낼 수 있습니다).
