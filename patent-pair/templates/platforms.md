# 플랫폼별 설정 — Claude · ChatGPT · Gemini · Microsoft 365 Copilot

공통 준비물
- 스킬: `claim-chart-fto.zip` (또는 `SKILL.md`의 `---` 아래 본문, 약 2,400자라 어느 지침 칸에도 들어갑니다)
- 도구: `pairkit.py`(전처리), `chart_check.py`(점검)
- 자료: 관심 특허 전문(가능하면 KIPRIS·USPTO의 텍스트나 XML), 대상 문서(제품 설명서·선행 문헌)

> 기밀 주의 — FTO에 쓰는 미공개 제품 사양은 영업비밀입니다. 조직이 계약한 업무용 요금제(데이터를 모델 학습에 쓰지 않는 조건)인지 먼저 확인하고, 그렇지 않으면 공개 문헌만 올리고 제품 쪽은 내 PC에서 `pairkit.py bundle`로 필요한 문단만 골라 넣습니다.

---

## Claude

**A. 프로젝트로 (분야별 작업 공간)**
1. claude.ai → Projects → 새 프로젝트 (예: "FTO — 이차전지 열관리").
2. 프로젝트 지침(Instructions)에 `SKILL.md` 본문을 붙여 넣습니다.
3. 프로젝트 지식(Knowledge)에 관심 특허 전문, 분야 용어집, 지난 차트 예시를 올립니다. 같은 분야의 다음 사건에서도 그대로 이어 씁니다.

**B. 스킬로 (어느 대화에서나)**
1. 설정의 스킬 메뉴(Customize → Skills → Upload a skill)에 `claim-chart-fto.zip`을 올립니다.
2. 코드 실행 기능을 켜 두면 스킬이 `scripts/pairkit.py`, `scripts/chart_check.py`를 직접 돌려 분설·근거 후보·인용 점검까지 합니다.
3. Claude Code는 `claim-chart-fto/` 폴더를 `~/.claude/skills/`에 복사합니다. 특허 폴더 전체를 돌리는 대량 작업에 알맞습니다.

요청 예: `KR1020250013094.txt 청구항 1과 product-A.txt로 FTO 클레임 차트를 만들어 줘. 끝나면 chart_check로 점검해 줘.`

## ChatGPT

1. 새 프로젝트를 만들고 프로젝트 지침에 `SKILL.md` 본문을 붙여 넣습니다(또는 GPT를 만들어 지침 칸에).
2. 프로젝트 파일에 `pairkit.py`, `chart_check.py`, 관심 특허 전문을 올립니다.
3. 데이터 분석(코드 실행)이 켜져 있으면 "pairkit.py로 bundle을 만든 뒤 차트를 작성하고, chart_check.py verify로 점검해 줘"라고 요청합니다. 꺼져 있으면 내 PC에서 만든 `request.md`를 붙여 넣습니다.

## Gemini

1. 스킬 전환 계정(개인 계정 2026-11-17부터 순차)은 Gemini 앱의 스킬 메뉴에서 `claim-chart-fto.zip`을 올리고 `/claim-chart-fto`로 부릅니다(13편 3장). 전환 전이면 새 Gem의 요청 사항 칸에 본문을 넣습니다.
2. 비교할 특허가 많으면 NotebookLM 노트북에 특허 전문을 소스로 모아 두고 "청구항 1의 구성요소 E3에 해당하는 문장을 식별번호와 함께 찾아 줘"처럼 근거 후보를 찾는 데 씁니다. 찾은 문장을 스킬 요청에 붙여 넣습니다.
3. 스킬 안 스크립트 실행은 제한이 있으므로 `pairkit.py bundle` 결과를 붙여 넣는 방식을 기본으로 합니다.

## Microsoft 365 Copilot

**Agent Builder로 사내 FTO 에이전트 만들기**
1. Microsoft 365 Copilot → **New agent** → **Skip to configure**(직접 설정).
2. **Name**(30자 이내): 예 "FTO 클레임 차트".
3. **Description**(1,000자 이내): "청구항과 제품 설명서를 구성요소별로 비교해 근거 인용이 있는 클레임 차트를 만든다."
4. **Instructions**(8,000자 이내): `SKILL.md` 본문을 붙여 넣습니다.
5. **Knowledge**: 특허 공보와 제품 사양서를 모아 둔 SharePoint 폴더를 연결합니다. 에이전트는 사용자가 원래 열람 권한을 가진 문서만 참조하므로, 기밀 사양서는 권한이 정리된 폴더에 둡니다.
6. **Capabilities**: "Create documents, charts, and code"(코드 해석기)를 켜면 업로드한 CSV·텍스트를 코드로 다룰 수 있습니다. 스크립트 실행이 막힌 환경이면 PC에서 만든 `request.md`를 붙여 넣습니다.
7. 테넌트에서 스킬 기능이 열려 있으면 Agent Builder에 스킬 패키지(`claim-chart-fto.zip`)를 추가할 수도 있습니다.
8. **Try it** 탭에서 양성 대조(관심 특허 자신의 설명)와 음성 대조(무관한 특허)로 시험한 뒤 만들고, 팀에 공유합니다.
9. 결재·알림 같은 업무 흐름이 필요하면 에이전트를 Copilot Studio로 복사해 확장합니다.

---

## 어디서나 공통 — 진행 순서

```
1) python pairkit.py extract 관심특허.txt --out A.json        # 청구항·문단 분리
2) python pairkit.py bundle --claims A.json --claim 1 --target 제품설명.txt --out request.md
3) request.md를 스킬(또는 지침을 넣은 프로젝트·에이전트)에 붙여 넣기 → 차트 + JSON
4) 출력을 chart.md로 저장 → python chart_check.py verify chart.md --target 제품설명.txt --elements 6
5) 실패 항목을 LLM에 돌려주며 고치기 → 변리사 검토
```
