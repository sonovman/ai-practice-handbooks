# 올리기 (init → commit → push)

> 먼저 01 점검을 통과했는지 확인. 공개 범위(Public/Private)를 정하세요.

클로드 코드/에이전트:
```
점검을 통과했으면 이 폴더를 깃허브에 올려 줘.
- 먼저 secret_scan을 한 번 더 돌려 실패가 없는지 확인.
- 저장소 이름과 공개 범위(Private 권장)를 나에게 물어봐.
- git init → add → commit → push 를 순서대로 하고, 완료되면 저장소 주소를 알려줘.
- main 브랜치에 바로 올리되, 커밋 메시지는 내가 한 작업을 요약해 줘.
```

GitHub Desktop(권장): 저장소 추가 → 변경 확인 → Summary 작성 → Commit to main → Publish/Push.
명령으로: git init · git add .(점검 후) · git commit -m "..." · 원격 연결 · git push
