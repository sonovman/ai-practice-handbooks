# Gemini Gem 만들기

## 준비물
- `gem-instructions.md` (이 폴더) — "요청 사항" 부분
- `../knowledge/` 의 3개 파일 — case-rules.md, research.md, output-template.md

## 순서
1. gemini.google.com → 왼쪽 **Gems 탐색하기** → **새 Gem**
2. 이름: **판례 원문 조사·심층 해설**
3. **요청 사항** 칸에 gem-instructions.md 의 "요청 사항" 전체를 붙여 넣습니다.
4. 지식 영역에서 **파일 업로드**로 knowledge 폴더의 3개 파일을 올립니다.
5. 오른쪽 미리보기에서 `../sample/textbook-excerpt.md` 를 첨부해 "이 문단에 인용된 판례를 심층 해설해 줘"라고 시험합니다.
6. 결과가 괜찮으면 반드시 **저장**을 누릅니다.

## Gemini에서의 강점과 한계
- 강점: 판결문 PDF를 통째로 첨부해 긴 원문을 한 번에 읽히기 좋습니다. 원문 PDF를 직접 첨부하면 [공식 원문]·[원문 사본] 근거가 가장 확실해집니다.
- 한계: Gem 안에서 check_report.py 같은 스크립트를 돌리는 것을 전제로 하지 않았습니다. 형식 점검은 지침 11번의 자기점검으로 대신하고, 필요하면 결과를 내려받아 스크립트를 따로 돌립니다.
- 회사 계정(Google Workspace)에서는 관리자 정책에 따라 Gem 만들기·파일 업로드·공유가 제한될 수 있습니다.
