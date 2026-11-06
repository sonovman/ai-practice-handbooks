# Claude 스킬 설치

`claim-design-around/` 폴더가 스킬입니다. 4개 버전 중 가장 기능이 많습니다(부호 점검 스크립트, 도면 보조자료 HTML 템플릿 포함).

```
claim-design-around/
├── SKILL.md                         지침 (필수)
├── references/output-spec.md        출력 형식
├── references/design-around-types.md 회피설계 유형
├── scripts/numeral_map.py           도면부호 점검
└── assets/drawing-aid-template.html 도면 읽기 보조자료 뼈대
```

## A. claude.ai · Claude Desktop 채팅
1. 설정에서 코드 실행(파일 만들기)을 켭니다.
2. **Customize → Skills → + → Create skill → Upload a skill** 에서 `claim-design-around.zip` 을 올립니다.
3. 공보 PDF를 첨부하고 "긴급 모드로 분석해 줘. 번호 ○○"라고 요청합니다.

## B. Claude Code · Desktop Code 탭
1. 작업 폴더에 `.claude/skills/claim-design-around/` 로 폴더째 복사합니다.
2. `/claim-design-around 긴급 모드, 번호 10-9999001, 자료 sample/` 처럼 실행합니다.

## 부호 점검만 따로
```
python claim-design-around/scripts/numeral_map.py 명세서.txt --figure-numerals 10,11,20,30
```
