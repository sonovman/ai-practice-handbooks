# 한정 원장(Limitation Ledger) 형식

한정 원장은 분해 결과를 침해·유효성 판단에 연결하는 '장부'입니다. 같은 행 ID를 Claim Chart가 그대로 씁니다.

## 표 (9열)
| 한정 ID | 청구 문언 | 원자적 한정 명제 | 유형 | 명세서·도면 근거 | 출원경과 | 문언침해 | 균등침해 | 유효성(§102/§103) |
|---|---|---|---|---|---|---|---|---|
| [1c.2] | "a gap … decreases toward a lower end" | 날개–내벽 간격이 하단으로 갈수록 줄어든다 | 관계 | ¶[0016], 도3 | 거절 극복 보정으로 추가 | 충족 | – | D1 미개시, D2 개시 → 차이점 |

유형: 전제부 / 구조 / 단계 / 기능 / 관계 / 조건 / 수치 / 대안 / 부정 / 기능식(mpf).

## JSON (도구가 읽는 형식)
```json
{
  "meta": {"patent": "…", "claim": 1, "priority_date": "YYYY-MM-DD",
           "chart_type": "infringement | non_infringement | invalidity_102 | invalidity_103 | domestic_industry",
           "stage": "pic | final",
           "target": {"name": "제품명/문헌", "version": "…", "date": "YYYY-MM-DD",
                      "representative": false, "representative_basis": ""}},
  "limitations": [
    {"id": "1e", "text": "청구 문언", "type": "mpf", "proposition": "원자적 명제",
     "intrinsic": "¶[0021]", "prosecution": "…", "sam": "(기능식일 때) 명세서 대응 구조", "construction": "(해석이 쟁점일 때)"}
  ],
  "rows": [
    {"id": "1e", "theory": "literal | doe", "assertion": "…",
     "facts": [{"source": "자료명", "pin": "쪽·단락·도면 부호·파일/함수/행", "date": "YYYY-MM-DD", "text": "고유 명칭으로 쓴 사실",
                "product": "(다른 제품 자료일 때)", "ref": "(무효 차트 문헌 ID)", "executed": true}],
     "sam_match": "(기능식) 대응 구조와 SAM의 같음·균등 설명",
     "fwr": {"function": "", "way": "", "result": "", "why_insubstantial": "", "linking": ""},
     "prosecution_check": "(균등론) 금반언·공중헌납·형해화 점검",
     "explanation": "… 왜냐하면 …",
     "literal": "충족/불충족", "doe": "–/균등/불성립", "validity": "개시/미개시/차이점"}
  ],
  "combination": {"motivation": "(진보성)", "expectation": "(진보성)"},
  "symmetry": "(넓힌 해석을 유효성에도 적용했는지)"
}
```

## 사례로 보는 대안 한정 — Kustom Signals (U.S. Pat. No. 5,528,246, 교통단속 레이더)
청구항: 저장된 도플러 신호 데이터를 "미리 선택된 크기(magnitude) **또는** 주파수(frequency) 기준"으로 검색. 피고 제품은 최강 신호와 최고속 신호를 **항상 둘 다** 검색해 표시.

| ID | 원자적 한정 명제 | 유형 | 출원경과 | 문언 | 균등 | 유효성 |
|---|---|---|---|---|---|---|
| L1 | 도플러 신호 스펙트럼 데이터를 메모리에 저장 | 단계 | – | 충족 | – | (사건별) |
| L2 | 크기 기준 또는 주파수 기준 중 **하나**로 검색(둘 다는 아님) | 대안·조건 | 운영자의 선택을 강조한 보정·의견 | 불충족 | 불성립: 둘 다 자동 검색은 실질적으로 다른 '방식' + 출원경과 금반언 | 대안 중 한 종이 선행기술에 있으면 위험 |
| L3 | 운영자가 두 검색 중 하나를 선택 | 기능·상호작용 | 같음 | 불충족 | 불성립(같은 이유) | – |

배울 점: ① 'or'는 독립 요소로 세지 않는다(법원도 그렇게 봤다). ② 그러나 or가 만든 '배타적 선택' 관계는 L2 전체의 범위를 정해 침해 여부를 갈랐다. ③ comprising(개방형)이라도 "청구항을 그 자신의 한정에서 풀어 주지는 않는다." ④ 반대의견(Mayer 판사)은 or를 '하나 또는 둘 다'로 읽었다 — 대안의 포괄/배타 해석은 다툼이 될 수 있으니 명세서·출원경과 근거를 원장에 남긴다.
