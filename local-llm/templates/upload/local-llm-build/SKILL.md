---
name: local-llm-build
description: 로컬 LLM 추론 장비를 처음부터 안전하게 계획·구축·운영하도록 돕는다. VRAM 최우선 부품 선정, 전력·회로 안전, PCIe P2P 스위치, BIOS/커널 튜닝, Docker/vLLM 서빙, 검증·문제해결. 고전력·고가 하드웨어라 안전 환기를 우선한다.
---

# 로컬 LLM 추론 장비 구축·운영

클라우드 API 대신 내 하드웨어에서 LLM을 직접 서빙하려는 사람을 돕는다. 핵심 철학: **예산을 VRAM에 집중**한다.
전기·고가 하드웨어를 다루므로 안전을 먼저 환기한다.

## 0. 안전 먼저 (항상)
- 전력: 고출력 GPU 여러 장은 일반 110V 회로를 넘기기 쉽다. 사기 전에 `power_budget.py`로 계산하고,
  실제 배선·전용 회로·접지는 자격 있는 전기 기술자와 확인한다. 전력 제한(nvidia-smi -pl)을 적용한다.
- 보안: iommu=off·ACS 비활성화는 격리를 약화한다. 외부와 분리된 전용 추론 머신에서만 쓰고, 일반 PC엔 적용하지 않는다.
- 비용: 최상위($40k+) 구성은 소수에게만 의미가 있다. 대부분은 입문($2k, RTX 3090 2장)부터 시작한다.

## 1. VRAM 최우선 계획
- 병목은 VRAM 용량·대역폭이다. 모델이 VRAM을 넘어 시스템 RAM으로 넘치면(Spillover) 속도가 급락한다.
- 최신 메인보드·DDR5에 돈을 쓰기보다, 중고 EPYC+DDR4 ECC로 호스트를 아끼고 VRAM GPU에 집중한다.
- 사기 전에 `vram_fit.py`로 모델이 들어가는지 계산한다(가중치 = params × bits/8).

## 2. GPU 간 고속 통신 (P2P)
- 여러 GPU로 한 모델을 나눠 추론(텐서 병렬)하면 GPU끼리 쉴 새 없이 통신한다.
- NVLink·PCIe5 대신 독립 PCIe Gen4 스위치로 CPU를 거치지 않는 P2P 통신을 만든다(c-payne 등).

## 3. BIOS·커널 튜닝 (P2P가 막히지 않게)
- BIOS: PCIe Link Width x16, Speed Gen4 고정, ASPM Disabled, Re-Size BAR Enabled, SR-IOV Disabled.
- 커널: GRUB `iommu=off amd_iommu=off`(없으면 NCCL이 멈춤), ACS를 런타임에 비활성화(setpci + systemd).
- 전력: systemd로 지속성 모드·전력 제한을 부팅 시 적용.

## 4. 서빙 (Docker + vLLM)
- ZFS 미러로 가중치를 보관하고, 가중치는 컨테이너에 읽기 전용(:ro)으로 마운트한다.
- vLLM OpenAI 호환 서버를 띄우고 텐서 병렬 크기를 GPU 수에 맞춘다.

## 5. 검증·문제해결
- `nvidia-smi topo -m`가 GPU 간 PIX(스위치 P2P)로 나오는지 확인(PHB/NODE면 ACS 문제).
- 벤치마크로 P2P 대역폭·지연을 측정한다. NCCL 멈춤 → iommu, 속도 저하 → ACS·케이블·ASPM 점검.

## 참조
- `references/checklist.md` — 안전·BIOS/커널·검증 체크리스트
- `references/platforms.md` — 로컬 서버를 Claude·ChatGPT·Gemini·Copilot·Antigravity에서 쓰기, 로컬 vs 클라우드
