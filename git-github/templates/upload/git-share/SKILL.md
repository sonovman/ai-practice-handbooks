---
name: git-share
description: 바이브 코딩으로 만든 스킬·에이전트·코드를 Git·GitHub로 안전하게 올리고 협업한다. 올리기 전 비밀정보·민감 파일을 점검하고, .gitignore·README를 준비하고, 커밋·푸시·브랜치·PR을 단계별로 안내한다. 비밀이 이미 올라갔을 때의 응급 조치 포함. "깃허브에 올려", "공유", "커밋/푸시", "pull" 요청에 사용.
---

# Git·GitHub 안전 공유

바이브 코딩 결과를 깃허브로 공유·협업한다. 비개발자도 따라올 수 있게 한 단계씩, 국문으로 설명한다.
저장소를 바꾸는 동작(커밋·푸시·브랜치·강제 푸시)은 **무엇을 할지 먼저 말하고 승인 후** 실행한다.

## 0. 올리기 전 — 비밀정보 사전 차단 (가장 먼저, 건너뛰지 않음)
1. `python tools/secret_scan.py <폴더> --report work/secret.md` 실행.
2. '실패'가 있으면 **올리지 않는다.** 유형별 조치:
   - 코드에 하드코딩된 키/비밀번호 → 환경 변수(os.environ)나 .env로 옮기고 코드에서 제거. (.gitignore만으로는 못 막는다 — 파일 전체만 제외되기 때문.)
   - .env·*.pem·credentials.json 등 민감 파일 → `.gitignore`에 추가(gitignore-template.txt 참고). 공유용은 .env.example(빈 양식)만.
3. 공개 범위를 확인: 민감하면 Private. 사내 자료·고객 정보·영업비밀이 섞였는지 눈으로도 확인.

## 1. 준비 파일
- `.gitignore`(references/gitignore-template.txt 기반), `README.md`(프로젝트 목적·실행법·기능), 필요 시 requirements.txt/package.json.
- (권장) pre-commit 훅으로 매 커밋 전 자동 점검: pre-commit.sample을 .git/hooks/pre-commit 로 복사.

## 2. 올리기 (init → add → commit → push)
- 개념: add(올릴 파일 고르기=스테이징) → commit(세이브 포인트, 스냅샷) → push(원격 저장소로). 커밋은 '이력'으로 남아 되돌릴 수 있다.
- GitHub Desktop 사용자: 저장소 추가 → 변경 확인 → Summary 작성 → Commit → Publish/Push. (끌어 올리기는 숨김 파일 누락 위험 → GitHub Desktop 권장)
- 명령으로: `git init` → `git add .`(단, 점검 통과 후) → `git commit -m "..."` → 원격 연결 후 `git push`.

## 3. 받아오기·협업 (clone / pull)
- clone: 저장소를 처음 통째로 내려받기. pull: 남이 올린 최신 변경만 가져와 합치기.
- 루틴: **작업 시작 전 git pull → 작업 → 커밋 → push.**
- 충돌(merge conflict): 당황하지 말고 `git merge --abort`로 되돌리거나, 충돌 부분을 확인해 양쪽을 합친다.

## 4. 브랜치·PR (여럿이 협업)
- main은 그대로 두고 `feature/<기능>` 브랜치에서 작업 → push → GitHub에서 Pull Request → 리뷰 → Merge → 모두 `git pull`.
- main 보호: 저장소 Settings → Branches/Rules → PR 필수·리뷰 승인·상태 검사 통과. (실수로 main 직접 푸시 방지)
- CI 자동 테스트(GitHub Actions)와 Secrets(비밀을 코드가 아닌 저장소 보안함에 두고 실행 시 주입)는 본문 참고.

## 5. 응급 — 비밀이 이미 올라갔을 때 (references/secret-incident.md)
1. **먼저** 해당 키를 제공자 사이트에서 즉시 폐기·재발급. (올라간 순간 수집됐다고 가정)
2. 이력에서 제거: `git filter-repo`(권장) 또는 BFG로 해당 파일/문자열을 전체 커밋에서 삭제.
3. `git push --force`로 덮어쓰기.
4. 팀원에게 알리고 기존 폴더 삭제 후 재클론하도록 안내.
5. 재발 방지: .gitignore·환경변수·GitHub Secret scanning/Push protection.

## 주의
- 비밀값은 가려서 표시. 점검 도구는 100% 탐지를 보장하지 않으니 사람도 확인.
- 저장소 변경 동작은 되돌리기 어려우므로 승인 후 실행. 강제 푸시·이력 재작성은 특히 신중히.
