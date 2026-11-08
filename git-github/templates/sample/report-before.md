# 업로드 전 비밀정보 점검

- 대상: `/mnt/attach/outputs/git-github/templates/sample/demo-project`
- 판정: **올리기 전 조치**

| 판정 | 항목 | 경로 | 조치 |
|---|---|---|---|
| 실패 | 민감 파일(추적 대상) | `.env` | .gitignore에 추가하거나 폴더 밖으로 옮기세요 |
| 실패 | 비밀로 보이는 값: OpenAI 키 | `.env` | 'sk-pro…op' |
| 실패 | 비밀로 보이는 값: AWS 액세스 키 | `.env` | 'AKIAFA…XY' |
| 실패 | 비밀로 보이는 값: OpenAI 키 | `app.py` | 'sk-pro…op' |
| 실패 | 비밀로 보이는 값: 비밀번호·키 대입 | `app.py` | 'API_KE…op' |
| 실패 | 비밀로 보이는 값: DB 접속 문자열 | `app.py` | 'postgr…3@' |

> 이 도구는 사전 차단 보조이며 100% 탐지를 보장하지 않습니다. 이미 올라간 비밀은 즉시 폐기·재발급하고,
> 커밋 이력에서 제거하려면 git filter-repo 등 별도 조치가 필요합니다(본문 참고).
