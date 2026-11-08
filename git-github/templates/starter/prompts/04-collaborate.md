# 협업 (pull · 브랜치 · PR)

받아오기:
```
작업 시작 전에 깃허브의 최신 변경을 가져와 합쳐 줘(git pull). 무엇이 바뀌었는지 알려줘.
```
브랜치로 작업:
```
main은 그대로 두고 feature/<기능> 브랜치를 만들어 이동해 줘. 작업이 끝나면 그 브랜치를 push 하고,
PR(Pull Request)에 넣을 요약 설명을 작성해 줘.
```
충돌:
```
git pull 했더니 merge conflict가 났어. git status로 충돌 파일을 확인하고,
내 코드와 팀원 코드를 안전하게 합치는 방법을 알려줘. 자신 없으면 git merge --abort로 되돌리는 법도.
```
main 보호: 저장소 Settings → Branches/Rules → PR 필수·리뷰 승인·상태 검사 통과를 켜면 실수로 main에 직접 푸시하는 것을 막습니다.
