# 로컬 LLM 장비 체크리스트

## 안전(가장 먼저)
- [ ] 전력: `power_budget.py`로 벽 소비 전력이 회로 연속 허용치(차단기 80%) 이하인지 확인
- [ ] 전력 제한: `nvidia-smi -pm 1` + `nvidia-smi -pl <W>` 를 부팅 시 systemd로 적용
- [ ] 배선·전용 회로·접지: 자격 있는 전기 기술자와 확인(특히 220V 공사)
- [ ] 콘센트 1구에 고출력 기기 몰아쓰기 금지, 발열·환기 확보
- [ ] 보안: iommu=off·ACS off는 외부와 분리된 전용 추론 머신에서만

## 부품 계획(VRAM 우선)
- [ ] `vram_fit.py`로 목표 모델이 VRAM에 들어가는지(스필오버 없는지) 확인
- [ ] 호스트는 중고 EPYC+DDR4 ECC로 아끼고, 예산을 VRAM GPU에 집중
- [ ] 입문은 RTX 3090 2장(48GB)부터. 최상위 구성은 전력·비용·소음까지 고려

## BIOS (예: ASRock ROMED8-2T)
- [ ] PCIe Link Width: x16 (x8/x8 분할 해제)
- [ ] PCIe Link Speed: Gen4 고정(Auto 금지)
- [ ] ASPM: Disabled / Re-Size BAR: Enabled / SR-IOV: Disabled

## 커널·드라이버
- [ ] GRUB `iommu=off amd_iommu=off` → `update-grub` → 재부팅(없으면 NCCL Hang)
- [ ] ACS 런타임 비활성화(setpci) + systemd 자동 실행
- [ ] `options nvidia_uvm uvm_disable_hmm=1`

## 검증
- [ ] `nvidia-smi topo -m` 에서 GPU 간 PIX(스위치 P2P) 표시(PHB/NODE면 ACS 재점검)
- [ ] P2P 대역폭·지연 벤치마크로 정상 범위 확인
- [ ] 증상별: NCCL 멈춤→iommu / 속도 저하→ACS·케이블·ASPM / 차단기 다운→전력 제한

## 운영
- [ ] 가중치는 ZFS 미러 보관, 컨테이너에 읽기 전용(:ro) 마운트
- [ ] vLLM 텐서 병렬 크기 = GPU 수, 모델 길이·양자화는 VRAM에 맞춰
