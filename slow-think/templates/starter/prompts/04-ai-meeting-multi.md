# AI 회의 — 여러 대화·여러 모델 버전 (중요한 결정)

같은 모델끼리의 토론보다 **서로 다른 모델**의 독립 의견을 모으는 쪽이 효과가 큽니다.
수작업으로도 되지만, 작업 폴더의 도구가 역할별 프롬프트를 만들어 줍니다.

```
python tools/meeting_pack.py new inbox/안건.md                 # 기본 역할 4명
python tools/meeting_pack.py new inbox/안건.md --roles roles/patent.md
```

1. `work/meeting-…/01-…md` 파일을 하나씩 새 대화에 붙여 넣습니다.
   역할마다 모델을 바꿉니다 — 예) 기획자: Claude, 마케터: ChatGPT, CFO: Gemini, CEO: Copilot
   (Antigravity라면 Agent Manager에서 대화를 새로 열 때마다 모델을 고릅니다)
2. 답을 `opinions/<역할>.md`로 저장합니다.
3. `python tools/meeting_pack.py collect work/meeting-…` → `90-red-team.md`를 새 대화에 → 답을 `opinions/_red-team.md`로 저장
4. 한 번 더 `collect` → `99-chair.md`를 새 대화에(의장은 가장 신중한 설정의 모델로)
5. 의장 결론의 '확인할 사실'은 사람이 확인합니다.

11편 「AI 합의 협의체」는 같은 원리를 여러 모델이 서로 익명 평가하는 방식으로 다룹니다.
