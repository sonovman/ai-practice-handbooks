---
name: polish-en
description: 영어 문서의 AI 티(not X but Y 대조, 한 줄 마무리, 과장된 의미 부여, 상투 어휘, 장식용 굵은 글씨·대시 등)를 의미를 바꾸지 않고 덜어 내고 점검 보고서를 만든다. 영어 이메일·칼럼·논문·의견서 윤문, "humanize this", "make this sound less like AI" 요청에 사용. 번역이나 내용 추가에는 쓰지 않는다.
---

# 영어 보수적 윤문

blader/humanizer(MIT)의 26개 패턴을 쓰되, 전문 문서의 의미 보존을 우선합니다.
명령은 Windows에서는 `python`, macOS·Linux에서는 `python3`.

## 0. 준비
- `.agents/skills/humanizer/SKILL.md`가 없으면 `python tools/setup_skills.py --only en` 실행을 안내하고 멈춥니다.
- 원본을 `work/YYYY-MM-DD-title/original.md`로 복사합니다. 원본은 건드리지 않습니다.
- 문서 종류(email, column, paper, legal opinion, patent)를 묻습니다. 사용자가 자기 글 2~3문단을 주면 그 리듬·어휘·구두점을 따릅니다. 주지 않으면 중립적인 전문 문체로 둡니다.
- 특허·법률 문서이면 `.agents/rules/legal-protect.md`를 적용합니다. claims, defined terms, quotations, citations는 고치지 않습니다.
- 바꾸면 안 되는 용어를 `terms.txt`에 적고 확인받습니다.

## 1. 윤문
- `.agents/skills/humanizer/SKILL.md`의 절차(표시 → 초안 → 자체 비평 → 최종)를 따르되 `prompts/protect.md`와 legal-protect가 우선합니다.
- 특히 전문 문서에서 주의할 패턴:
  - #9 stacked qualifiers, #11 passive voice: 법률·특허에서는 한정어와 피동이 의미일 수 있으므로 **자동으로 줄이지 않습니다.** 반복된 같은 한정어만 정리합니다.
  - #6 forced triads: 원문이 실제로 세 가지를 말하면 그대로 둡니다.
  - may/shall/must/comprising/consisting of/at least/substantially/about은 바꾸지 않습니다.
- 결과를 `work/…/polished.md`로 저장합니다.

## 2. 점검 (생략 금지)
`python tools/polish_check.py work/…/original.md work/…/polished.md --terms work/…/terms.txt --report work/…/report.md`
- 종료 코드 2면 채택하지 않고 실패 항목을 되돌려 한 번만 다시 합니다.

## 3. 보고 (설명은 한국어)
판정 한 줄 → 윤문본 → 주요 변경 5개(전 → 후, 패턴 번호) → 그대로 둔 표현 → 점검표의 실패·경고 항목.
Humanizer는 AI 탐지기 통과를 목표로 하지 않습니다. 그런 요청에는 목적이 다르다고 알립니다.
