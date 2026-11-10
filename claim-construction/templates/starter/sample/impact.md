# 해석 반영 영향 보고 — 가상특허 A (교육용 예시)

| 원장 ID | 용어 | 상태 | 해석 | 확인할 점 |
|---|---|---|---|---|
| [1pre] | A juice extractor | 반영 | 전제부 — 한정 아님(본문이 완결된 구조를 모두 적고, 전제부는 용도·명칭만 표시) |  |
| [1c.2] | a gap ... decreases toward a lower end of the drum | 반영 | 같은 축 높이에서 잰 날개–내벽 간격이 드럼의 배출측 끝(사용 상태의 아래쪽)으로 갈수록 줄어듦(감소율 무관, 단조 감소) |  |
| [1d] | ribs | 재검토 | 내벽에서 0.3mm 이상 돌출되어 길게 뻗은 부재(명칭 불문) | 해석이 요구하는 조건의 근거가 대응 사실에 없음: 돌출 높이 0.3mm 이상 |
| [1d] | at an inclination of 5 to 15 degrees relative to a rotation axis | 반영 | 내벽에 투영한 회전축 선을 기준으로 잰 리브 길이 방향의 각도가 5°~15° |  |
| [1e] | means for rotating the screw at a speed of 40 to 60 rpm | 반영 | §112(f): 기능=스크루를 40~60rpm으로 회전 / 구조=BLDC 모터 M1 + 감속기어 G1(1:30) 및 그 균등물 |  |
| [1f] | configured to select either a juice mode or a smoothie mode | 반영 | 사용자 입력에 따라 두 모드 중 하나만 활성으로 두도록 설계·프로그램된 제어부(두 모드 동시 수행 제외) |  |

재검토 1건 — 30편 `chart_lint.py`를 다시 돌리고, 표시된 행의 사실을 보강하거나 결론(충족/불충족)을 바꾸세요.
