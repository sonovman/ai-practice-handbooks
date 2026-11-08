# 올리기 전 점검 (가장 먼저)

> 비밀정보가 한 번 올라가면 지워도 이력에 남습니다. 올리기 전에 반드시 점검하세요.

```
python tools/secret_scan.py .            # 현재 폴더 점검 (실패가 있으면 올리지 않기)
python tools/secret_scan.py . --report work/secret.md
python tools/secret_scan.py --suggest-gitignore > .gitignore   # 추천 .gitignore 만들기
```

클로드 코드/에이전트에게 말로 시킬 때:
```
이 폴더를 깃허브에 올리기 전에 점검만 해 줘. 구현·실행·커밋은 하지 말고,
API 키·비밀번호·DB 접속정보·개인키가 코드나 설정에 들어 있는지, .env 같은 민감 파일이 있는지 확인해서 목록으로 알려줘.
비밀값은 전체를 보여주지 말고 가려서 알려줘.
```
