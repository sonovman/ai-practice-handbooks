# AI DEV DIRECTOR 점검 기록 (2026-11-10)

대상: github.com/digilogd-cmd/ai-dev-director · 커밋 `d2541ad` (v3.1.8, MIT)
환경: Linux 샌드박스, Python 3.13, git 2.43 — **실제 claude·codex·agy 로그인 세션 없이** 정적 분석과 저장소 자체 시험(스텁 CLI)으로 확인.

## 1. 정적 점검 요약

| 항목 | 확인한 곳 | 결과 |
|---|---|---|
| 외부 통신 | 전체 .py/.js 의 URL·urllib·requests·socket | 127.0.0.1 외 송신 코드 없음(텔레메트리 없음) |
| 콘솔 노출 | companion_server.py, dashboard_server.py | 127.0.0.1 고정, 다른 주소면 실행 거부 |
| 브라우저 공격(CSRF·DNS 리바인딩) | is_request_origin_allowed | Host·Origin 검사 + 상태 변경 API는 토큰(data/solomon-bridge.token) 요구 |
| 권한 우회 플래그 | agents/*.py, core/research_runner.py | skip-permissions·yolo·full-access 사용 없음. Codex는 `--sandbox read-only`, Claude는 `--print`(승인 필요한 도구는 거부), agy는 `--sandbox` |
| BUILDER 기본 방식 | config.yaml `builder.mode: proposal` | BUILDER는 임시 폴더에서 파일 내용을 JSON으로 '제안'만 하고, 쓰기는 Director가 Scope Guard 검사 후 수행 |
| 셸 실행 | verifier.py | shell=True 없음, 검증 명령은 argv로 분리 실행 |
| 종량제 차단 | core/env_utils.py | 5개 키만 제거(OPENAI/ANTHROPIC/GEMINI/GOOGLE/AZURE_OPENAI_API_KEY). CODEX_API_KEY, Bedrock·Vertex 전환 변수는 남음 |
| 솔로몬 | core/solomon_bridge.py | 본체(127.0.0.1:8710 서비스)는 저장소에 없음. 브리지는 토큰 + 허용 프로젝트 목록(기본 빈 목록) |
| 의존성 | requirements.txt | 시험 1개가 쓰는 `requests` 누락(실행에는 영향 없음) |

## 2. 저장소 자체 시험

```
pip install -r requirements.txt requests
python -m pytest -q
→ 593 passed, 11 failed, 1 error (약 3분 15초, Linux)
```
실패는 윈도우 경로(C:/…)·codex.cmd·프로세스 트리 종료를 전제한 시험이 대부분입니다
(제작자 기준 윈도우 601/604 통과, macOS/Linux 미검증 — 같은 경향).
리눅스에서 '자식 프로세스까지 종료' 시험(test_process_tree_kill)이 실패했으므로
맥·리눅스에서는 정지 버튼이 손자 프로세스까지 끊는지 직접 확인해야 합니다.

## 3. Scope Guard 실측 — 명세가 넓을 때 통과하는 파일

`SafetyPolicy.check_pre_tool_file_write(path, ws, allowed_paths, [])` 결과:

| 경로 | allowed `["**"]` | allowed `["src/**"]` |
|---|---|---|
| src/a.py | 통과 | 통과 |
| .agents/x | **막힘** | 막힘 |
| .claude/settings.json | 통과 | 막힘 |
| .mcp.json | 통과 | 막힘 |
| .codex/config.toml | 통과 | 막힘 |
| .github/workflows/ci.yml | 통과 | 막힘 |
| .vscode/tasks.json | 통과 | 막힘 |
| conftest.py | 통과 | 막힘 |

그리고 `assess_order_for_auto_run`은 `["**"]`, `[".claude/**"]` 명세를 사람 승인 없이 통과시켰습니다.
→ 명세가 좁으면 안전하지만, 넓게 열리면 AI 설정 파일이 작업본(그리고 auto_apply 시 원본)에 들어갈 수 있습니다.
Claude Code 공식 문서에 따르면 `--bare` 없이 `-p`로 실행하면 그 폴더의 `.claude/settings.json` 훅과 `.mcp.json` 서버가
확인 창 없이 실행·연결됩니다. REVIEWER(claude)는 작업본 폴더에서 실행되므로 보조 관문이 필요합니다.

## 4. 선택 패치 시험 (로컬 사본)

`core/safety.py` 두 줄:
```python
CONTROL_PLANE_DIRS = {".git", ".agents", ".director_worktrees", ".claude", ".codex", ".gemini", ".vscode", ".github"}
CONTROL_PLANE_FILES = {"gemini.md", ".mcp.json", "claude.md", "agents.md"}
```
→ 위 표의 `["**"]` 열에서 .claude·.mcp.json·.codex·.github·.vscode 가 모두 막힘(conftest.py는 그대로 통과 — apply_gate로 확인).
→ 안전 관련 시험(-k "safety or scope or guard or control") 52개 중 51개 통과, 실패 1개는 패치 전에도 실패하던 리눅스 전용 시험.
→ 전체 시험: 패치 전과 실패 목록이 같음. 차이 1건(test_resumed_run_with_failed_verification_continues_to_repair)은
  패치하지 않은 원본에서도 4회 중 3회 실패하는 '흔들리는 시험'으로 확인 — 패치로 생긴 회귀는 없음.
→ 대가: 이 패치를 넣으면 Director가 CLAUDE.md·AGENTS.md·.github/workflows 를 고치는 작업도 막습니다(사람이 직접 고칠 것).

## 5. 키트 도구 시험

```
python tools/test_director_tools.py   → 17 OK
python tools/test_mini_triad.py       → 7 OK
python tools/test_build_upload.py     → 3 OK
```
mini_triad 전 과정 시범(가짜 BUILDER/REVIEWER 스크립트): `mini-triad-run-good.txt`(PASS), `mini-triad-run-plant.txt`(.mcp.json을 심으면 FAIL).
