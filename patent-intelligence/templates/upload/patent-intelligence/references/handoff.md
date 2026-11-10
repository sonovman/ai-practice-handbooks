# 정밀분석 인계 패킷 (work/05_handoff.json)

후보 관문에서 승인된 문헌만 담는다. 다음 단계는 **claim-suite(핸드북 30~33편)** — 분해 → 해석 → Claim Chart → 진보성·회피설계. 패킷 + 공보 원문 + (있으면) 당사 청구항·제품자료를 함께 넘긴다.

```json
{
  "project": "스마트 음식물 처리기 경쟁기술 (가상)",
  "round": "2026-R4",
  "data_date": "2026-11-01",
  "baseline": {"file": "work/03_analysis.md", "version": 2, "approved_how": "묵시 승인('계속')"},
  "items": [
    {
      "document_id": "D007",
      "application_number": "18/990031",
      "publication_number": "US 2025/0900031 A1",
      "registration_number": "US 12,990,031 B2",
      "applicant_original": "ALPHA HOME INC.",
      "applicant_english": "ALPHA HOME INC.",
      "english_name_status": "official_original",
      "selection_reason": "주력 구조(동시 건조·분쇄)와 같은 축의 등록특허 [B01]",
      "approved_analysis_objectives": ["독립항 한정 분해", "당사 제품 대비 Claim Chart", "회피설계 방향"],
      "trend_grade": "T1",
      "design_around_type": null,
      "priority_claims_and_figures": ["Claim 1", "Fig. 2"],
      "our_materials": {"claims": false, "product_spec": false},
      "required_additional_materials": ["당사 제품 구조도", "US 출원경과(File Wrapper)"],
      "confirmed_facts": ["분쇄실 둘레 가열 덕트(Claim 1)"],
      "analytical_inferences": ["동시 건조·분쇄 제품을 겨냥한 권리로 보임"],
      "unverified_items": ["EP 4 990 031 A1의 청구범위 차이"],
      "user_modifications": ["긴급도 높음으로 상향"]
    }
  ]
}
```
- 필드 이름은 바꾸지 않는다(다음 스킬이 그대로 읽음). 모르는 값은 `null`과 `unverified_items`로.
- 확정사실·추론·미확인을 섞지 않는다.
