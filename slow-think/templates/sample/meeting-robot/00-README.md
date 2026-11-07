# 진행 순서

1. 01~04 파일을 하나씩 **새 대화**에 붙여 넣습니다. 가능하면 역할마다 다른 모델을 씁니다
   (예: Claude · ChatGPT · Gemini · Copilot, Antigravity에서는 대화마다 모델 선택).
2. 각 답을 `opinions/<역할>.md` 로 저장합니다. 파일 이름은 roles.txt의 역할명과 같게.
3. `python tools/meeting_pack.py collect meeting-robot` → 90-red-team.md, 99-chair.md 완성
4. 90을 새 대화에 → 답을 `opinions/_red-team.md` 로 저장 → collect 한 번 더 → 99를 새 대화에
5. 의장 결론의 '확인할 사실'은 사람이 확인합니다.
