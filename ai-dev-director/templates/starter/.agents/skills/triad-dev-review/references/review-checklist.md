# 독립 검수 체크리스트

판정 규칙: 하나라도 "아니오"면 FAIL. 모르겠으면 FAIL.

## 범위
- [ ] 바뀐 파일이 모두 ORDER의 allowed_paths 안에 있는가
- [ ] 바뀐 파일 수가 max_files 이하인가
- [ ] AI 설정·테스트 설정 파일(.claude/, .mcp.json, conftest.py, pytest.ini, package.json, .github/workflows/ 등)이 바뀌지 않았는가

## 테스트
- [ ] 테스트 출력에 실행 개수와 통과 기록이 실제로 있는가
- [ ] 기존 테스트를 지우거나, 단언(assert)을 약하게 바꾸거나, skip을 추가하지 않았는가
- [ ] 새 기능에 대응하는 테스트가 있는가

## 코드
- [ ] acceptance(완료 기준)를 하나씩 충족하는가
- [ ] 기존 함수·클래스를 이유 없이 지우지 않았는가
- [ ] 네트워크 호출·파일 삭제·셸 실행이 새로 생겼다면 목표에 필요한가
- [ ] 비밀값(키·토큰·비밀번호)이 코드에 들어가지 않았는가

## 출력 형식(마지막 줄)
```
{"verdict": "FAIL", "reasons": ["tests/test_calc.py: assertTrue(True)로 바뀌어 검증이 무력화됨"]}
```
