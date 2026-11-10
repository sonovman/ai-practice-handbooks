# 플랫폼별 설치·설정 (Claude·ChatGPT·Gemini·Microsoft 365 Copilot·Antigravity)

원본은 `starter` 하나입니다. `python build_upload.py` → `dist/claim-construe.zip`(Claude·ChatGPT), `dist/claim-construe-flat.zip`(Copilot 등), `dist/claim-construe/`(Gemini).
30편 키트(claim-decompose·claim-chart)와 함께 쓰면 분해 → 해석 → 차트 반영이 이어집니다.

| 플랫폼 | 등록 | 도구 실행 | 메모 |
|---|---|---|---|
| Claude 웹·데스크톱 | 설정에서 코드 실행·파일 생성 켜기 → Skills에 claim-construe.zip(+30편 zip 2개) | 가능 | 프로젝트 지식에 명세서·출원경과 PDF, 지침에 AGENTS.md |
| Claude Code·Cowork | `.agents/skills/claim-construe`를 `.claude/skills/`로 복사, CLAUDE.md에 `@AGENTS.md` | 가능(로컬) | 30편 starter와 같은 사건 폴더에 두면 편함 |
| ChatGPT | Skills(지원 요금제)에 zip 업로드, 또는 프로젝트 지침에 SKILL.md | 대체로 가능 | 출원경과 서류를 프로젝트 파일로 |
| Gemini 앱(Gem) / CLI | Gem 지침에 SKILL.md+AGENTS.md, 지식에 references / CLI는 starter에서 GEMINI.md에 `@AGENTS.md` | Gem 제한적 / CLI 가능 | Gem은 해석표 초안용 |
| M365 Copilot | 에이전트 지침에 SKILL.md 요약, 지식에 references·사건 문서(SharePoint) / 조직이 허용하면 flat.zip 스킬 업로드 | 환경에 따라 확인 | 기밀 등급·공유 범위 확인 |
| Google Antigravity | starter 폴더를 작업 공간으로 | 가능(로컬) | `.agents/rules/claim-construe.md`가 요청 시 적용 |

## 공통 첫 확인
1. `python tools/test_construe_check.py` → 10개, `python tools/test_apply_to_ledger.py` → 6개 통과.
2. `python tools/construe_check.py sample/construction_good.json` → 오류 0, `construction_bad.json` → 오류 13·경고 4, `construction_kr.json` → 오류 0·경고 2.
3. `python tools/apply_to_ledger.py sample/chart_from_30.json sample/construction_good.json` → [1d] 재검토 1건.

## Antigravity에서 AI 도움으로 구축하기
1. 30편 starter와 31편 starter를 한 사건 폴더 아래 나란히 풀고, 그 상위 폴더를 Antigravity 작업 공간으로 엽니다.
2. "두 키트의 시험을 모두 실행해 결과를 보여 줘" → 30편 20개 + 31편 16개 통과 확인(명령 실행은 승인 후).
3. `inbox/`에 청구항·명세서·출원경과를 넣고: "30편 원장에서 다툼 용어를 골라 claim-construe로 해석표(JSON) 초안 → construe_check 오류 0 → apply_to_ledger로 30편 차트에 반영 → 재검토 행 목록"을 요청합니다.
4. 사람이 해석표와 영향 보고를 검토하고, 재검토 행의 사실을 보강한 뒤 30편 chart_lint를 다시 돌립니다.

## 주의
- 메뉴·요금제별 기능은 바뀝니다. 각 서비스의 현재 안내를 확인하세요.
- 출원경과·의뢰인 자료는 승인된 환경에서만. 개인 운영 중계 서버 연동은 쓰지 않습니다.
