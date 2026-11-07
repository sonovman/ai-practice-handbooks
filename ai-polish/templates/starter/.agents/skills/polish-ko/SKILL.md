---
name: polish-ko
description: 한국어 문서의 AI 티(번역투, 기계적 나열, 상투적 결론, 이중 피동, 접속사 남발, 연결어미 뒤 쉼표 등)를 의미를 바꾸지 않고 보수적으로 덜어 내고, 의미 보존 점검 보고서까지 만든다. "AI 티 없애줘", "윤문해줘", "번역투 고쳐줘", "자연스럽게 다듬어줘" 같은 한국어 문서 요청에 사용. 맞춤법만 고치기, 번역, 내용을 보태는 재작성에는 쓰지 않는다.
---

# 한국어 보수적 윤문

im-not-ai(Humanize KR, MIT)의 규칙과 점검 스크립트를 쓰되, 의미 보존을 우선하는 순서로 진행합니다.
명령은 Windows에서는 `python`, macOS·Linux에서는 `python3`으로 실행합니다.

## 0. 준비
- `.agents/skills/humanize-korean/` 가 없으면 사용자에게 `python tools/setup_skills.py` 실행을 안내하고 멈춥니다.
- 입력이 파일이면 원본을 `work/YYYY-MM-DD-제목/original.md`로 **복사**합니다. 붙여 넣은 글이면 그 파일로 저장합니다. 원본은 건드리지 않습니다.
- 장르(보고서·칼럼·블로그·논문 초록·공문·특허/법률)와 강도(약하게·보통)를 묻습니다. 답이 없으면 장르는 첫 300자로 추정하고 강도는 **약하게**로 합니다.
- 특허·법률 문서이면 `.agents/rules/legal-protect.md`를 적용하고, 청구항·조문·계약 조항·인용 구간을 목록으로 보여 준 뒤 윤문 대상에서 뺍니다.
- 바꾸면 안 되는 용어(구성요소명, 정의 용어, 당사자명)를 뽑아 `terms.txt`에 한 줄씩 쓰고 사용자에게 확인받습니다.

## 1. 진단 (선택)
`python .agents/skills/humanize-korean/scripts/prepare_monolith_input.py --run-dir work/… --genre report|column|blog|essay|abstract`
는 `01_input.txt`가 있는 폴더를 받습니다. 필요하면 `original.md`를 `01_input.txt`로 복사해 실행하고 `00_metrics.json`의 route_hint와 지배 패턴을 짧게 보고합니다. 수치는 참고용이며 AI 작성 여부의 판정이 아닙니다.

## 2. 윤문
- `.agents/skills/humanize-korean/references/quick-rules.md`를 읽고, `prompts/protect.md`의 1~8번 제한을 그 위에 둡니다. 둘이 부딪히면 protect가 이깁니다.
- 탐지된 구간만 고칩니다. 문제없는 문장, 제목, 목록 구조는 그대로 둡니다.
- 장르와 높임 정도를 유지합니다(보고서를 수필로, `했다`를 `하였다`로 바꾸지 않음).
- 결과를 `work/…/polished.md`로 저장합니다.
- 길고 정밀한 처리가 필요하면 `.agents/skills/humanize-korean/SKILL.md`의 standard·heavy 경로를 따라도 됩니다(산출물은 cwd의 `_workspace/`).

## 3. 점검 (생략 금지)
```
python .agents/skills/humanize-korean/scripts/verify_gates.py --before work/…/original.md --after work/…/polished.md --genre report
python tools/polish_check.py work/…/original.md work/…/polished.md --terms work/…/terms.txt --report work/…/report.md
```
- polish_check 종료 코드 2(실패) 또는 verify_gates의 `gate: FAIL`이면 결과를 채택하지 않습니다. 실패 항목을 되돌리고 더 약한 강도로 한 번만 다시 합니다. 두 번째도 실패면 멈추고 사용자에게 넘깁니다.
- 경고(1)는 해당 항목을 원문과 나란히 보여 주고 사용자 판단을 받습니다.

## 4. 보고
1. 판정 한 줄: `통과/경고/실패 · 변경률 N% · 경로 work/…`
2. 윤문본 (짧으면 본문, 길면 파일 경로)
3. 주요 변경 5개 이내: 전 → 후, 이유(패턴 ID가 있으면 함께)
4. 의미가 달라질 우려가 있어 그대로 둔 표현
5. 점검표 요약(실패·경고 항목만)

"이미 충분히 자연스럽습니다"도 정상 결과입니다. 고칠 곳을 억지로 만들지 않습니다.
