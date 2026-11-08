# AGENTS.md — 이 폴더에서 에이전트가 항상 지킬 것

이 폴더는 핸드북 25편 '로컬 LLM 추론 장비 구축·운영' 키트입니다.

## 안전 먼저
- 전력: 고출력 GPU는 일반 110V 회로를 넘기기 쉽다. `power_budget.py`로 계산하고, 실제 배선은 전기 기술자와 확인.
- 전력 제한(nvidia-smi -pl)을 반드시 적용. 콘센트 1구에 몰아쓰기 금지.
- 보안: iommu=off·ACS off는 격리를 약화하므로 외부와 분리된 전용 추론 머신에서만.

## 항상
- 한국어, 초보자도 따라 하기 쉽게 단계별로.
- VRAM 최우선. 사기 전에 `vram_fit.py`로 스필오버 여부 계산.
- 모델 제품·버전명은 자주 바뀌니 '역할'로 설명하고 현재 최적을 확인.

## 도구(표준 라이브러리)
- `tools/power_budget.py` — 전력 예산·회로 안전(OK/WARN/DANGER).
- `tools/vram_fit.py` — VRAM 적합성·스필오버(OK/WARN/SPILL).
- 시험: `python tools/test_power_budget.py`, `python tools/test_vram_fit.py`.
