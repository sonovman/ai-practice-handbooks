# 자작 바이너리 compute_pan 을 근거(.rodata 상수 + 디스어셈블)만으로 파이썬에 복원한 결과.
def compute_pan(x: int) -> float:
    pan = (x - 320.0) * 0.003125          # subsd 320.0, mulsd 0.003125
    return max(-1.0, min(1.0, pan))        # comisd 로 -1.0 / 1.0 클램프

if __name__ == "__main__":
    for x in (0, 160, 320, 480, 639):
        print(f"x={x:3d} -> pan={compute_pan(x):+.4f}")
