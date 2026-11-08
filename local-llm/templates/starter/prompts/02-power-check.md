# 전력·회로 안전 점검

내 구성은 GPU (수)장, 호스트 약 (W)이고, 콘센트는 (전압 V/암페어 A)야.
- `python tools/power_budget.py --gpus N --gpu-watts W --host-watts H --volts V --amps A` 로 계산해 줘.
- 연속 허용치를 넘으면 GPU 전력 제한값(nvidia-smi -pl)이나 전용 회로 방안을 제시해.
- 실제 배선·차단기·접지는 전기 기술자와 확인해야 한다는 점을 반드시 알려 줘.
