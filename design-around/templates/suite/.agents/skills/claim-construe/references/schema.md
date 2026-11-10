# 해석 기록 JSON과 점검 코드

## 형식
```json
{
  "meta": {"patent": "…", "claim": 1, "forum": "district | itc | ptab | appeal | ex_parte | reexam | reissue | kr_court | kr_trial | kr_kipo",
           "standard": "phillips | bri | kr", "petition_date": "(PTAB) YYYY-MM-DD", "stage": "trial | appeal"},
  "dependent_limitations": [{"id": "2a", "parent": "1", "text": "종속항이 더한 한정"}],
  "terms": [{
    "term": "다툼 용어", "ledger_id": "30편 원장 ID", "claim_text": "그 용어가 든 청구 문언",
    "disputed": true, "construction": "해석 문장",
    "evidence": [{"type": "claim | spec | drawing | prosecution | ipr | dictionary | expert | treatise | article | inventor",
                  "cite": "위치", "contradicts_intrinsic": false}],
    "basis": "intrinsic | extrinsic",
    "lexicography": {"quote": "정의 문장", "cite": "¶…"},
    "disclaimer": {"quote": "진술", "cite": "서류·쪽", "source": "spec | prosecution | ipr", "clarity": "clear | ambiguous", "is_estoppel_only": false},
    "imports_embodiment": false,
    "mpf": {"applies": true, "function": "", "structure": "", "structure_cite": "", "software": false, "algorithm": ""},
    "objective_standard": "(정도 표현) 명세서 기준",
    "preamble_limiting": false, "preamble_reason": "",
    "product_by_process": {"infringement_limited_to_process": true, "validity_limited_to_process": false, "clearly_unreasonable_reason": ""},
    "indefinite": false, "added_words": [], "stipulated": false, "definite_because_stipulated": false,
    "requires": [{"text": "해석이 더한 확인 조건", "evidence_hint": "대응 사실에서 찾을 단어"}],
    "used_for": {"infringement": "…", "validity": "…"},
    "new_on_appeal": false, "forfeiture_exception": "", "claim_specific_reason": ""
  }]
}
```

## 점검 코드 (construe_check.py)
| 코드 | 확인 | 종류 |
|---|---|---|
| C01 | 절차↔기준(Phillips·BRI·한국), 기준 미기재 | E/W |
| C02 | 내재적 근거·근거 위치, 내재적 기록과 충돌하는 외재적 증거 | E/W |
| C03 | 실시예 한정 수입(정의·포기 없이) | E |
| C04 | 자기 정의에 정의 문장·위치 | E |
| C05 | 권리 포기의 진술·위치·명백성, IPR 진술, 금반언과 구분 | E/W |
| C06 | 기능식: 기능·대응 구조·알고리즘 / 한국 절차 주의 | E/W |
| C07 | 정도 표현의 객관적 기준 | W |
| C08 | 종속항 한정과 겹치는 해석(청구항 차별화) | W |
| C09 | 같은 용어 다른 해석 | W |
| C10 | 침해·유효성에 다른 해석(대칭성) | E |
| C11 | 실질적 다툼을 '통상의 의미'로 덮음, 결론 없음 | E |
| C12 | 인위적 불명확성 | E |
| C13 | 의미 합의를 명확성으로 착각 | W |
| C14 | 제법한정물건(미국/한국 방향) | E |
| C15 | 항소심 새 해석(실권), 예외 사유 | E/W |
| C16 | 전제부 한정 근거 | W |

`apply_to_ledger.py`는 `requires`의 단서가 30편 차트 행의 사실에 없으면 그 행을 '재검토'(needs_review)로 표시합니다.
