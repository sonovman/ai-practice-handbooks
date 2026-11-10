---
trigger: model_decision
description: 사용자가 특허 사건을 시작하거나, 청구항 분해·해석·Claim Chart·회피설계 중 둘 이상을 이어서 하거나, 사건 진행 상황·다음 단계를 물을 때 적용.
---

# 통합 오케스트레이터(모델 판단 시 적용)

1. claim-suite 스킬을 먼저 불러 목적·관할을 확인한다.
2. 사건 폴더가 없으면 `cases/example`을 복사해 만든다.
3. `python tools/suite_status.py <사건폴더>`로 단계를 확인하고, 다음 할 일에 적힌 스킬을 부른다.
4. 각 단계 끝에 `--run`으로 점검하고, 관문을 통과하지 못하면 되돌아간다(references/routing.md).
5. 관문 G1·G5와 각 단계 결과는 사람에게 보여 주고 확인받은 뒤 진행한다.
