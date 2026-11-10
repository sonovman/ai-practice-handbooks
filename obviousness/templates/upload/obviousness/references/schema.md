# 입력 JSON(work/06_obviousness.json)과 점검 코드

## 형식
```json
{
  "meta": {"patent": "…", "claim": 1, "priority_date": "YYYY-MM-DD", "forum": "us | kr | us+kr",
           "proceeding": "exam | litigation | ipr | kr_trial", "field": "…", "problem": "…",
           "min_coverage": 0.6, "invention_type": "selection | crystal | numeric | medical_use (선택)", "symmetry": "침해 쪽 해석과 같은 넓이로 봤다는 기록"},
  "posita": {"definition": "통상의 기술자 수준", "basis": ["근거1", "근거2"]},
  "limitations": [{"id": "30편 원장 ID", "text": "…", "type": "…", "proposition": "…", "core": true,
                   "construction": "31편 해석", "sam": "(기능식) 대응 구조", "needs_review": false}],
  "references": [{"id": "D1", "pub": "공개번호", "date": "YYYY-MM-DD", "kind": "patent | publication | product | aapa",
                  "applicant": "…", "same_field": true, "same_problem": true, "pertinent_problem": "",
                  "map": {"1a": {"grade": "● | ◐ | ○", "pin": "¶[0010], 도1 부호 100", "text": "\"원문 인용\"",
                                 "why": "왜 같은지(차트 설명에 들어감)", "note": "", "teaches_away": "",
                                 "ta_kind": "discourage | inoperable | principle | preference | tradeoff", "sam_match": ""}}}],
  "cgk": [{"id": "K1", "limitations": ["1f"], "status": "established | not_found | disputed", "statement": "…",
           "evident_to_public": false,
           "evidence": [{"source": "…", "type": "textbook | handbook | standard | review | patent | product | article | declaration | aapa",
                         "date": "YYYY-MM-DD", "pin": "…", "text": "…", "applicant": "…"}]}],
  "combinations": [{"id": "C1", "base": "D3", "analogous": {"D2": "유사 분야 근거"},
                    "steps": [{"limitation": "1c.2", "from": "D2 또는 K1", "rationale": "MPEP 2143(G)",
                               "motivation": "…", "motivation_source": "위치", "expectation": "…",
                               "ott": {"finite": "(시도 자명일 때) 유한한 해결책", "guidance": "방향 지침", "predictable": "예측 가능성"}}]}],
  "secondary": {"reviewed": true, "items": [{"type": "commercial_success | long_felt_need | failure_of_others | unexpected_results | copying | praise | licensing",
                                             "fact": "…", "source": "…", "nexus": "…",
                                             "coextensive": false, "feature_known_in": ["D3"]}]},
  "effects": {"claimed": "…", "evidence": "명세서 위치", "remarkable": "yes | no | unknown"}
}
```
- `core`: 발명의 요지(핵심 한정). 가중치 3, 아니면 1(`weight`로 직접 지정 가능).
- 차이점의 출처는 `from`에 문헌 ID(references) 또는 기술상식 ID(cgk)를 쓴다.

## 점검 코드
| 코드 | 수준 | 뜻 |
|---|---|---|
| O01 | E/W | 기준일·통상의 기술자 수준 없음 / 그 근거 없음 |
| O02 | E | 대비 누락, grade 오류, ●·◐인데 위치 없음 |
| O03 | E | 기준일 이후 문헌을 주인용·결합에 씀 |
| O04 | E | 주인용 후보와의 차이점인데 기술상식 조사 기록 없음 |
| O05 | E/W | 기술상식 증거가 기준일 이후·날짜 없음·위치 없음·증거 없음 / '누구나 아는 사실' 처리 |
| O06 | W | 증거가 특허 한두 건뿐(약함) |
| O07 | W | 핵심 한정을 기술상식으로 메움(Arendi·2012후436) |
| O08 | E/W | IPR에서 AAPA를 근거로 씀 / 기술상식 증거로 씀 |
| O09 | E | 보조 문헌이 그 한정을 ●로 개시하지 않음, 불성립 기술상식, 없는 출처 |
| O10 | E | 결합해도 빠지는 한정 |
| O11 | E | 동기 또는 근거 위치 없음 / 근거가 대상 특허(사후적 고찰) |
| O12 | E | (미국) 성공에 대한 합리적 기대 없음 |
| O13 | W | 저해 사유·목적 충돌·작동 원리 파괴(ta_kind가 preference·tradeoff면 참고로만) |
| O14 | E | 보조 문헌의 유사 분야 근거 없음 |
| O15 | W | 주인용이 B 후보가 아님 / B 후보 없음 |
| O16 | W | 근거 4개 이상 엮음(짜 맞추기 위험) |
| O17 | E/W | 2차적 고려사항 검토 기록·근거 없음 / nexus 없음 / 성공 특징이 이미 선행기술에 있음(Yita) |
| O18 | W | 31편 '재검토' 한정 |
| O19 | W | (한국) 효과 판단 미정·근거 없음 |
| O20 | W | 기능식 한정인데 대응 구조 비교(sam_match) 없음 |
| O21 | W | 보조 문헌의 유사성 근거가 다른 선행문헌과의 비교뿐(Sanofi-Aventis 2023) |
| O22 | E | 시도의 자명성 주장에 유한한 해결책·방향 지침·예측 가능성 근거 없음(O'Farrell·Kubin) |
| O23 | W | '결합할 수 있었다(could)'만 있고 이유(would)가 없음 |
| O25 | E | 다른 결합의 논증을 설명 없이 원용(Magnum Oil Tools) |
| I | 참고 | A 없음, 한국 상업적 성공은 참고 자료, 단순 선호·장단점은 저해 아님, coextensive nexus 추정, 특수 발명 유형 안내 |

## 차트 변환 규칙(--chart)
- 주인용이 ●인 한정 → 주인용의 위치·인용으로 행. 차이점 → 보조 문헌의 행 또는 기술상식 증거(최대 3개)로 행.
- 결합 동기·성공 기대는 차이점별로 이어 `combination`에 넣는다. `meta.symmetry`가 있으면 그대로 옮긴다.
- 결과는 30편 `chart_lint.py`로 다시 점검한다(E08 동기·기대, E10 날짜 등).
