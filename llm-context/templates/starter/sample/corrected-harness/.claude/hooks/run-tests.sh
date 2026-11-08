#!/usr/bin/env bash
# Stop 훅: Claude가 턴을 끝내려 할 때 실행. 테스트 실패면 exit 2 로 '종료를 차단'하고
# Claude가 스스로 고치도록 되돌린다. (원고의 'turnFinish' 는 실제로는 Stop 이벤트다)
if [ -f package.json ]; then
  npm test --silent || { echo "테스트 실패: 완료를 차단합니다. 실패한 테스트를 고치세요." >&2; exit 2; }
elif [ -f pytest.ini ] || [ -f pyproject.toml ]; then
  pytest -q || { echo "테스트 실패: 완료를 차단합니다." >&2; exit 2; }
fi
exit 0
