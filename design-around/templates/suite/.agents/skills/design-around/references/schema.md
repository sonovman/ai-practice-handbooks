# 입력 JSON과 평가 규칙 (design_around_eval.py)

## 형식
```json
{
  "meta": {"patent": "…", "product": "…", "stage": "설계 동결 전", "pending_family": true},
  "claims": [{
    "claim": 1, "independent": true,
    "limitations": [{
      "id": "30편 원장 ID", "text": "…", "type": "structure | relation | numeric | mpf | alternative | negative | step",
      "construction": "31편 해석 문장(그대로 복사)",
      "amended_narrowing": false, "argument_estoppel": false, "amendment_reason": "patentability | formal",
      "prosecution": "출원경과 위치", "spec_alternatives": "(기능식) 명세서의 대안 구조"
    }]
  }],
  "options": [{
    "id": "O1", "name": "…", "business": "성능·원가·일정 메모",
    "changes": [{
      "limitation": "1d", "action": "remove | substitute | modify | add_absent_feature",
      "literal_met_after": false,
      "function_removed": false, "function_moved_to": "",
      "way_differs": false, "way_evidence": "", "known_interchangeable": false, "antithetical": false,
      "in_surrendered_territory": false, "rebuttal_risk": "",
      "disclosed_unclaimed": false, "ensnares_prior_art": false,
      "structure_disclosed_in_spec": false, "after_arising_tech": false,
      "kr": {"literal_met_after": null, "consciously_excluded": false, "free_art_whole_product": false,
             "solution_principle_differs": false, "easy_substitution": true}
    }]
  }]
}
```

## 평가 규칙(한 한정 × 한 변경, 관할별)
1. 문언: `literal_met_after`(한국은 `kr.literal_met_after`가 있으면 그것)가 참이면 HIGH. 단 한국에서 `free_art_whole_product`면 LOW. 미국 기능식에서 `structure_disclosed_in_spec`이면 HIGH.
2. 균등 제한 법리(하나라도 있으면 LOW, 미국 금반언에 `rebuttal_risk`가 있으면 MED):
   - 미국: 포기 영역(축소 보정·의견 진술 + 특허성 관련), 공중헌납(기능식 제외), 선행기술 포섭.
   - 한국: 의식적 제외, 자유실시기술.
   - 공통: 정반대 개념, 기능 완전 제거(기능을 옮기지 않은 경우).
3. 균등 판단:
   - 미국: 알려진 상호교환 → HIGH / 방식 차이+근거 → LOW / 방식 차이·근거 없음 → MED / 그 외 HIGH.
   - 한국: 과제해결원리 다름 → LOW / 치환 용이하고 방식 차이 없음 → HIGH / 그 외 MED.
4. 독립항 위험 = 그 독립항에 걸린 변경 중 가장 낮은 위험(변경이 없으면 HIGH). 회피안 위험 = 독립항 위험 중 가장 높은 것.

## 점검 코드
| 코드 | 뜻 |
|---|---|
| E01 | 없는 한정 ID |
| E05 | 포기 영역이라 했으나 축소 보정·의견 진술 기록 없음 |
| E10 | 31편 해석과 다른 해석에 기댐(`--chart`) |
| W06 | 기능식 + 등록 뒤 기술 → 균등론 판단 남음 |
| W08 | 방식 차이의 근거 없음 |
| W11 | 계속·분할출원 진행 중 |
| W12 | 31편 '재검토' 한정에 기댐 |
| I | 부정한정은 구성 추가로 문언 회피 가능 — 작동 확인 |
