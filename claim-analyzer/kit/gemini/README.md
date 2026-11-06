# Gemini Gem 만들기

## 준비물
- `gem-instructions.md` (이 폴더) — "요청 사항" 부분
- `../knowledge/` 의 3개 파일 — claim-rules.md, output-spec.md, design-around-types.md

## 순서
1. gemini.google.com → 왼쪽 **Gems 탐색하기** → **새 Gem**
2. 이름: **특허 구성특징 분석 도우미**
3. **요청 사항** 칸에 gem-instructions.md 의 "요청 사항" 전체를 붙여 넣습니다.
4. 지식 영역에서 **파일 업로드**로 knowledge 폴더의 3개 파일을 올립니다. (Drive에 둔 파일을 고를 수도 있습니다.)
5. 오른쪽 미리보기에서 `../sample/sample-patent.md` 와 `../sample/fig1.svg` 를 첨부해 "긴급 모드로 분석해 줘. 번호 10-9999001"이라고 시험합니다.
6. 결과가 괜찮으면 반드시 **저장**을 누릅니다. (미리보기만으로는 저장되지 않습니다.)

## Gemini에서의 강점과 한계
- 강점: 공보 PDF의 도면 페이지를 이미지로 직접 보고 부호를 대조하기 좋습니다. 지침 2번이 이를 요구합니다.
- 한계: Gem 안에서 `numeral_map.py` 같은 스크립트를 돌리는 것을 전제로 하지 않았습니다. 부호 점검은 지침 3번대로 Gem이 직접 표를 만듭니다. 결과 표는 사람이 원문과 한 번 더 대조하세요.
- 회사 계정(Google Workspace)에서는 관리자 정책에 따라 Gem 만들기·파일 업로드·공유가 제한될 수 있습니다.
