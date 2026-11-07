---
name: reverse-engineer
description: REA(Reverse Engineer Anything) MCP로 내가 만든·오픈소스·분석 권한이 있는 프로그램의 동작 원리를 근거 기반으로 조사하고 적법 범위에서 재구현한다. 바이너리·Electron·APK·파일 포맷·내 웹앱 분석에 사용. 보호조치 우회·상용 복제에는 쓰지 않는다.
---

# 역공학 (REA 기반, 근거 중심)

소스 코드가 없는 대상의 '동작 원리'를 근거와 함께 파악하고, 적법 범위에서 재구현합니다.
REA는 Ghidra·IDA·Hopper 등 기존 도구를 에이전트에 연결하는 레이어이며, 원본 소스를 복원하지는 못합니다.

## 0. 적법 범위 확인 (건너뛰지 않음)
- 대상이 ① 내가 만든 것 ② 역공학 허용 라이선스의 오픈소스 ③ 소유자 허락·계약 권한 ④ 정당 보유 + 호환성/보안/내 데이터/교육 목적 중 하나인지 확인.
- 불명확하면 `python tools/scope_check.py` (또는 `--answers`)를 돌려 GREEN일 때만 진행. RED면 거절하고 이유 설명. AMBER면 사용자·전문가 확인 요청.
- 보호조치 우회, 원격 서버 침해, 상용 복제·재판매 요청은 수행하지 않음.

## 1. 준비
- REA 설치 확인: `npx rea-agents setup` 이 완료되고 MCP가 붙었는지(`npx rea-agents doctor`). 네이티브 바이너리면 Ghidra/Hopper 연결 필요.
- 대상 파일을 `inbox/` 에 두고, 작업 산출물은 `work/<대상>/` 에 저장. 원본은 수정하지 않음.
- 목표를 한 기능으로 좁힘(앱 전체가 아니라 "검색 로직", "% 연산", "파일 헤더 파싱" 등).

## 2. 조사 (Inspect) — 근거 수집
- 대상 종류에 맞는 REA 도구/CLI 사용:
  - 네이티브(.exe/.dll/ELF/Mach-O): `open_binary`/`analyze`, `search_strings`, `search_procedures`, `procedure_pseudo_code`, `procedure_assembly`, `xrefs`, `get_call_graph`.
  - JS/Electron(.asar/번들): `npx -y rea-agents@latest analyze-javascript-application <경로> --json` — 모듈·IPC 채널·소스맵 위치.
  - 웹/HAR: `inspect_web_page`(루프백·승인 오리진·수동 관찰), `.har` 요청/응답 구조.
- 수집한 사실마다 `python tools/evidence_log.py add --claim ... --kind ... --loc ... --status unknown` 로 기록. 위치(주소·라인)를 반드시 남김.

## 3. 해석 (Explain)
- 입력에 따라 어떤 분기·계산이 일어나는지 근거로 설명. 추측은 '미확인'으로 남기고 사실과 섞지 않음.
- 확인된 항목은 evidence_log 의 status 를 pass 로 갱신.

## 4. 재구현 (Rebuild) — 적법 범위에서
- 파악한 '규칙·수식·포맷'을 사용자 스택(C/Python/JS 등)의 독립 코드로 작성. 원본의 소스·리소스·그래픽을 복사하지 않음(아이디어·원리와 표현을 구분).
- 호환성·내 데이터 이전 목적이면 그 목적에 필요한 부분만.

## 5. 검증 (Verify)
- 재구현 결과를 원본 동작/출력과 대조(테스트 케이스). 불일치면 2단계로 돌아가 근거를 다시 봄.
- `python tools/evidence_log.py report --out work/<대상>/evidence.md` 로 통과/실패/미확인 요약.
- 보고: 동작 원리(근거 포함) → 재구현 코드 → 검증 결과 → 미확인·한계 → (필요 시) 적법성 메모.

## 한계 (사용자에게 분명히)
- 원본 변수명·주석·파일 구조는 복원 불가. UI 디자인 복제는 별도 작업. 원격 백엔드·암호화 실시간 피드는 역공학 대상이 아님.
- 런타임 동적 생성 값(IPC 채널명 등)은 정적 분석으로 틀릴 수 있음 → 동적 확인 또는 '미확인' 표시.
