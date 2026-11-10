# 05 진보성 단계(S6)

obviousness 스킬로 진보성 판단 재료를 만들어 줘. 결론은 아직 내지 마.
1. 기준일과 통상의 기술자 수준(근거 포함)을 확정.
2. inbox/의 선행문헌마다 원장의 모든 한정을 ●◐○로 대비(위치·원문 인용). 해석은 work/03_construction.json 그대로.
3. A/B/C/X 분류 → 상위 B와의 차이점마다 기준일 당시 기술상식·주지관용기술을 조사(교과서·핸드북·표준·서로 다른 출원인의 여러 문헌). 원문을 확인하지 못한 자료는 disputed.
4. 결합안 C1, C2…: 차이점마다 출처·would 이유와 근거 위치·성공 기대·저해·유사 분야. 2차적 고려사항과 효과.
5. work/06_obviousness.json 저장 → `python tools/suite_status.py <사건폴더> --run` → G6 오류 0이면 case.json의 obviousness_combo로 진보성 차트가 만들어진다.
