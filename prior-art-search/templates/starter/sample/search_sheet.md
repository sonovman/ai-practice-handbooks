# 검색 시트 — 예시: 수직 스크루 착즙기 - 드럼 내면 경사 리브(가상)

- 기준일(cutoff): 20200315 · 신규성용 식은 이 날짜 이전으로 한정
- 웹 DB는 약관상 자동 수집 금지 — 링크를 사람이 열고 결과 CSV를 `imports/`에 저장합니다.

## KIPRIS
- **Q1** F1*F3 넓은 검색
  - 식: `TL=[(스크루+스크류)*(착즙+주스+녹즙)]`
  - 열기: (KIPRIS 웹 검색식 칸에 위 식을 붙여넣기)
- **Q2** F1*F2*F3 핵심 조합
  - 식: `TL=[(스크루+스크류)*(리브+돌기)*(착즙+주스+녹즙)]`
  - 열기: (KIPRIS 웹 검색식 칸에 위 식을 붙여넣기)
- **Q3** F2*F1 근접 + 분류 한정
  - 식: `CL=[(리브+돌기)^10(스크루+스크류)]`
  - 열기: (KIPRIS 웹 검색식 칸에 위 식을 붙여넣기)

## GooglePatents
- **Q1** F1*F3 넓은 검색
  - 식: `TAC=((screw OR auger) AND (juicer OR juice extractor))`
  - 열기: https://patents.google.com/?q=TAC%3D%28%28screw%20OR%20auger%29%20AND%20%28juicer%20OR%20juice%20extractor%29%29&before=publication:20200315
- **Q2** F1*F2*F3 핵심 조합
  - 식: `TAC=((screw OR auger) AND (rib OR protrusion) AND (juicer OR juice extractor))`
  - 열기: https://patents.google.com/?q=TAC%3D%28%28screw%20OR%20auger%29%20AND%20%28rib%20OR%20protrusion%29%20AND%20%28juicer%20OR%20juice%20extractor%29%29&before=publication:20200315
- **Q3** F2*F1 근접 + 분류 한정
  - 식: `CL=((rib OR protrusion) NEAR/10 (screw OR auger)) AND CPC=A47J19/025`
  - 열기: https://patents.google.com/?q=CL%3D%28%28rib%20OR%20protrusion%29%20NEAR/10%20%28screw%20OR%20auger%29%29%20AND%20CPC%3DA47J19/025&before=publication:20200315

## Espacenet
- **Q1** F1*F3 넓은 검색
  - 식: `ta="(screw or auger) and (juicer or juice extractor)"`
  - 열기: https://worldwide.espacenet.com/patent/search?q=ta%3D%22%28screw%20or%20auger%29%20and%20%28juicer%20or%20juice%20extractor%29%22
- **Q2** F1*F2*F3 핵심 조합
  - 식: `ta="(screw or auger) and (rib or protrusion) and (juicer or juice extractor)"`
  - 열기: https://worldwide.espacenet.com/patent/search?q=ta%3D%22%28screw%20or%20auger%29%20and%20%28rib%20or%20protrusion%29%20and%20%28juicer%20or%20juice%20extractor%29%22
- **Q3** F2*F1 근접 + 분류 한정
  - 식: `ta="(rib or protrusion) prox/distance<10 (screw or auger)"`
  - 열기: https://worldwide.espacenet.com/patent/search?q=ta%3D%22%28rib%20or%20protrusion%29%20prox/distance%3C10%20%28screw%20or%20auger%29%22

## PATENTSCOPE
- **Q1** F1*F3 넓은 검색
  - 식: `EN_AB:((screw OR auger) AND (juicer OR juice extractor))`
  - 열기: https://patentscope.wipo.int/search/en/result.jsf?query=EN_AB%3A%28%28screw%20OR%20auger%29%20AND%20%28juicer%20OR%20juice%20extractor%29%29
- **Q2** F1*F2*F3 핵심 조합
  - 식: `EN_AB:((screw OR auger) AND (rib OR protrusion) AND (juicer OR juice extractor))`
  - 열기: https://patentscope.wipo.int/search/en/result.jsf?query=EN_AB%3A%28%28screw%20OR%20auger%29%20AND%20%28rib%20OR%20protrusion%29%20AND%20%28juicer%20OR%20juice%20extractor%29%29
- **Q3** F2*F1 근접 + 분류 한정
  - 식: `EN_CL:((rib OR protrusion) NEAR10 (screw OR auger))`
  - 열기: https://patentscope.wipo.int/search/en/result.jsf?query=EN_CL%3A%28%28rib%20OR%20protrusion%29%20NEAR10%20%28screw%20OR%20auger%29%29

## KR 확대된 선출원·선출원 검토용 (cutoff 없이)
- `TL=[(스크루+스크류)*(착즙+주스+녹즙)]`
- `TL=[(스크루+스크류)*(리브+돌기)*(착즙+주스+녹즙)]`
- `CL=[(리브+돌기)^10(스크루+스크류)]`

> 문법·URL·내보내기 한도는 바뀔 수 있습니다. 첫 사용 때 각 DB에서 실제 실행을 확인하세요.
