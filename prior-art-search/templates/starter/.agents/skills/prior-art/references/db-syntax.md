# DB별 문법 대응표

하나의 '개념'을 각 DB 문법으로 변환합니다. 문법·URL은 바뀔 수 있으니 첫 사용 때 실제 실행을 확인하세요.

| 개념 | KIPRIS | Google Patents | Espacenet/OPS | PATENTSCOPE |
|---|---|---|---|---|
| AND / OR | `*` / `+` | `AND` / `OR` | `and` / `or` | `AND` / `OR` |
| 근접(proximity) | `^n` | `NEAR/n` | `prox/distance<n` | `NEARn` |
| 필드 | `TL=[]` `AB=[]` `CL=[]` | `TI=` `AB=` `CL=` `TAC=` | `ti=` `ab=` `ta=` | `EN_TI:` `EN_AB:` `EN_CL:` |
| 날짜 | 공개일 항목 칸 | URL `before=publication:` | `pd<` | `DP:[ TO ]` |

## 주의점(초기 접근 → 개선/주의)
- **KIPRIS 근접은 단어 단위**: 그룹끼리의 근접은 지원이 제한적이라 AND로 대체하고 시트에 표시한다.
- **Google 괄호 안 NEAR**: `TI=()`·`AB=()`·`CL=()` 괄호 안에서 NEAR/ADJ가 제대로 안 먹을 수 있어 첫 시험 항목으로 둔다.
- **Espacenet 절단기호**: ti·ab·ta·pa·in 필드에서만, ipc·cpc에서는 오류.
- **PATENTSCOPE 필드**: 언어별 필드(EN_TI 등)를 쓴다. 언어 구분 없는 TI·AB·CL은 더 이상 지원 안 될 수 있다.
- **내보내기 한도**: Espacenet은 상위 500건 등 한도가 있어, 넘치면 조사식을 쪼개 내려받는다.
