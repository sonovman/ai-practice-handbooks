# ORDER 템플릿

```json
{
  "goal": "src/calc.py에 add(a, b)를 만들고 테스트를 추가한다",
  "allowed_paths": ["src/calc.py", "tests/test_calc.py"],
  "max_files": 2,
  "acceptance": [
    "add(1, 2) == 3",
    "기존 테스트를 지우거나 약하게 바꾸지 않는다"
  ],
  "tests": "python -m pytest -q",
  "human_required": []
}
```

## 칸 설명
| 칸 | 뜻 | 좋은 예 | 피할 예 |
|---|---|---|---|
| goal | 한 문장 목표 | "로그인 실패 시 3회 후 잠금" | "보안 강화" |
| allowed_paths | 쓸 수 있는 파일·폴더 | `src/auth/*.py` | `**`, `.` |
| max_files | 바뀔 파일 수 상한 | 3 | 50 |
| acceptance | 사람이 확인할 수 있는 완료 기준 | "잠금 후 15분 뒤 해제" | "잘 동작" |
| tests | 검증 명령(프로젝트 밖 설정에 둠) | `python -m pytest -q` | 빈칸 |
| human_required | 사람이 정할 일 | "실제 결제 키 입력" | — |

`tools/mini_triad.py`는 이 중 goal · allowed_paths · max_files 를 읽는다(필드 이름 `max_files`).
