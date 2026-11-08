# 업로드 전 비밀정보 점검

- 대상: `/mnt/attach/outputs/git-github/templates/sample/demo-project`
- 판정: **올리기 전 조치**

| 판정 | 항목 | 경로 | 조치 |
|---|---|---|---|
| 경고 | 민감 파일(.gitignore로 제외됨) | `.env` | 제외돼 있지만 값 자체는 노출 위험이 없는지 확인 |
| 경고 | 비밀로 보이는 값: OpenAI 키 | `.env` | 'sk-pro…op' (단, .gitignore로 제외됨 — 값은 폐기·회전 권장) |
| 경고 | 비밀로 보이는 값: AWS 액세스 키 | `.env` | 'AKIAFA…XY' (단, .gitignore로 제외됨 — 값은 폐기·회전 권장) |
| 실패 | 비밀로 보이는 값: OpenAI 키 | `app.py` | 'sk-pro…op' |
| 실패 | 비밀로 보이는 값: 비밀번호·키 대입 | `app.py` | 'API_KE…op' |
| 실패 | 비밀로 보이는 값: DB 접속 문자열 | `app.py` | 'postgr…3@' |
| 실패 | 비밀로 보이는 값: 비밀번호·키 대입 | `config.json` | 'passwo…r2' |

> 이 도구는 사전 차단 보조이며 100% 탐지를 보장하지 않습니다. 이미 올라간 비밀은 즉시 폐기·재발급하고,
> 커밋 이력에서 제거하려면 git filter-repo 등 별도 조치가 필요합니다(본문 참고).
