# 비밀이 이미 깃허브에 올라갔을 때 (응급 5단계)

단순히 파일을 지우고 새로 커밋해도, 과거 커밋 이력에 비밀이 그대로 남습니다.

1. 폐기·재발급 (1순위): 제공자(OpenAI·Anthropic·AWS 등)에서 그 키를 즉시 삭제하고 새로 발급. 올라간 순간 자동 수집됐다고 가정.
2. 이력에서 제거:
   - git filter-repo (권장):  pip install git-filter-repo  →  git filter-repo --invert-paths --path .env
     특정 문자열만:  replace.txt 에 `옛키==>[REDACTED]` 적고  git filter-repo --replace-text replace.txt
   - BFG (대안):  bfg --delete-files .env   /   bfg --replace-text passwords.txt
3. 강제 푸시:  git push origin main --force   (커밋 해시가 모두 바뀜)
4. 팀원 공유: 이력이 바뀌었으니 각자 기존 폴더를 지우고 git clone 으로 새로 받도록 안내.
5. 재발 방지: .gitignore 등록 · 코드에서 환경 변수로 분리 · GitHub Settings → Security 에서 Secret scanning/Push protection 확인.

주의: 이력 재작성은 되돌리기 어렵습니다. 중요한 저장소라면 먼저 백업하고, 자신 없으면 전문가·동료와 함께 진행하세요.
