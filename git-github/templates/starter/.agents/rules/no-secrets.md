---
trigger: model_decision
description: 깃허브 업로드·커밋·푸시·공유, .gitignore·README 생성, 저장소 초기화 등 Git/GitHub 작업을 할 때 적용
---

# 비밀정보 차단 규칙

- 올리기·커밋 전 `python tools/secret_scan.py` 로 점검하고 '실패'가 있으면 멈춘다.
- API 키·비밀번호·토큰·개인키·DB 접속정보를 커밋에 포함하지 않는다. 발견하면 환경 변수/.env 분리 또는 삭제를 먼저 안내한다.
- `.gitignore`는 파일 '전체'만 제외한다. 코드 안에 하드코딩된 비밀은 .gitignore로 막지 못하므로 코드 수정이 필요하다고 알린다.
- 공개(Public)/비공개(Private)를 올리기 전에 확인한다. 민감하면 Private를 권한다.
- 이미 유출된 키: ① 즉시 폐기·재발급 ② 이력 제거(git filter-repo/BFG) ③ 강제 푸시 ④ 팀원 재클론 ⑤ 재발 방지(.gitignore·환경변수·Secret scanning)를 순서대로 안내한다.
- 비밀값은 가려서 표시한다.
