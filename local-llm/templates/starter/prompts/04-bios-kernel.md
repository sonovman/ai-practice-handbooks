# BIOS·커널 튜닝 점검

내 메인보드/GPU 구성에서 GPU P2P가 막히지 않도록 설정을 점검해 줘.
- BIOS: PCIe Link Width x16, Speed Gen4 고정, ASPM Disabled, Re-Size BAR Enabled, SR-IOV Disabled 가 맞는지.
- 커널: GRUB iommu=off amd_iommu=off, ACS 런타임 비활성화(setpci+systemd), nvidia_uvm 옵션.
- 각 항목이 '무엇을 막기 위한 것인지' 한 줄로 설명하고, 적용 후 재부팅·검증 순서를 알려 줘.
- 보안 영향(iommu/ACS off)도 함께 환기해 줘.
