# 모델별 스킬·프로젝트 설정 (Claude·ChatGPT·Copilot·Gemini)

이 키트는 하나의 원본(starter)에서 플랫폼별 묶음을 만들어 씁니다. 다만 플랫폼마다 '할 수 있는 범위'가 다릅니다.

| 플랫폼 | 스킬 등록 | 도구 실행(build_queries·rank_closest) | KIPRIS Plus API 호출 |
|---|---|---|---|
| Claude 웹 | prior-art.zip 업로드 | 가능(코드 실행) | 불가(외부 접속 제한) |
| Claude Code·Cowork | 폴더 복사(.claude/skills) | 가능 | 가능(로컬) |
| ChatGPT 웹 | prior-art.zip 업로드 | 대체로 가능(Python) | 불가 |
| M365 Copilot Cowork | flat.zip 업로드 | 확인 필요 | 확인 필요 |
| GitHub Copilot(VS Code) | starter 폴더 열면 자동 인식 | 가능(터미널) | 가능(로컬) |
| Gemini 앱(Gem) | SKILL.md 붙여넣기 | 제한적 | 불가 |
| Gemini CLI·Antigravity | starter 폴더 그대로 | 가능 | 가능(로컬) |

두 도구는 표준 라이브러리만 쓰고 인터넷이 필요 없어 웹 앱의 코드 실행 환경에서도 돌아갑니다.
반면 KIPRIS Plus API 호출은 로컬 실행 환경에서만 됩니다(웹 채팅 앱은 외부 API 접속 차단).

## 공통 준비
1. 전체 ZIP(prior-art-kit.zip)으로 받아 압축을 풉니다(숨김 .agents 폴더 보이게).
2. 동작 확인: `python tools/test_build_queries.py`, `python tools/test_rank_closest.py`,
   `python tools/build_queries.py sample/plan.json`, `python tools/rank_closest.py sample/plan.json sample/mapping.json`
   (US…02 1위·97.5점이 나오면 정상).
3. 업로드 묶음: `python build_upload.py` → dist/ 에 prior-art.zip(Claude·ChatGPT)·prior-art-flat.zip(Copilot)·prior-art/(Gemini).
   SKILL.md를 고치면 다시 실행해 묶음을 갱신합니다(원본은 starter 하나).

## 플랫폼별 요점
- **Claude 웹**: 설정에서 코드 실행·파일 생성을 켠 뒤 Skills에 prior-art.zip 업로드. 프로젝트 지침에 AGENTS.md,
  지식에 prompts·sample·사건 청구항. 사건마다 새 대화.
- **Claude Code·Cowork**: `.agents/skills/prior-art`를 `.claude/skills/prior-art`로 복사, CLAUDE.md에 `@AGENTS.md`.
  같은 계정이면 claude.ai에 올린 스킬이 /skills의 'claude.ai sync'로도 로드될 수 있습니다(버전에 따라).
- **ChatGPT**: Skills에 prior-art.zip 업로드(스캔 후 사용). 프로젝트 지침 AGENTS.md, Python 실행으로 도구 구동.
- **M365 Copilot Cowork**: Customize → Skills → Upload로 flat.zip(압축 10MB·해제 50MB·100파일 한도). 키트는 ~수십 KB.
  Python 실행 여부는 확인; 안 되면 판단 보조에만 쓰고 도구는 로컬에서.
- **GitHub Copilot(VS Code)**: starter 폴더를 열면 `.agents/skills`·루트 AGENTS.md를 인식. 터미널로 도구·KIPRIS 연동까지.
- **Gemini 앱(Gem)**: 지침에 SKILL.md+AGENTS.md, 지식에 references·sample·prompts. 판단 보조용.
- **Gemini CLI·Antigravity**: starter 폴더 그대로. GEMINI.md에 `@AGENTS.md`. Antigravity는 `.agents/rules/prior-art.md`(model_decision).

## 사건 폴더 표준(모든 플랫폼)
```
사건_2026-001/
  plan.json              ← 01 프롬프트, G1 승인
  work/search_sheet.md   ← 02: build_queries.py
  imports/               ← 웹 DB·KIPRIS Plus 결과 CSV
  fulltext/              ← 상위 후보 공보 텍스트
  mapping.json           ← 03 프롬프트(근거 위치 필수)
  work/closest.md        ← 04: rank_closest.py, G4 검토
```

## 주의
- 각 플랫폼의 요금제·관리자 권한(스킬 업로드 허용)·동기화 여부는 다릅니다. 메뉴·정책은 바뀌니 공식 안내 확인.
- 사건 폴더를 OneDrive·SharePoint로 공유해 여러 도구가 같은 plan·mapping을 쓸 때는 버전 충돌·기밀 관리에 유의.
