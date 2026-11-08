---
trigger: model_decision
description: 사용자가 로컬 LLM 추론 장비를 계획·구축·운영하거나, VRAM·전력·PCIe P2P·BIOS/커널 튜닝·vLLM 서빙을 물을 때 적용.
---

# 로컬 LLM 장비 작업 흐름(모델 판단 시 적용)

1. 안전 먼저 — 전력(`power_budget.py`)과 회로 한계부터. 전력 제한·전용 회로·전기 기술자 확인.
2. VRAM 우선 — 목표 모델이 들어가는지 `vram_fit.py`로 확인. 넘치면 비트↓·VRAM↑·컨텍스트↓.
3. P2P — 여러 GPU면 PCIe Gen4 스위치로 CPU 우회 통신.
4. BIOS/커널 — x16·Gen4 고정, ASPM off, ReBAR on, iommu=off, ACS 비활성화.
5. 서빙 — ZFS 미러 + vLLM(가중치 :ro, 텐서 병렬=GPU 수).
6. 검증 — nvidia-smi topo -m(PIX 확인), 대역폭·지연 벤치, 증상별 문제해결.

주의: 고전력·고가·보안 트레이드오프. 모델명·버전은 자주 바뀌니 '역할'로.
