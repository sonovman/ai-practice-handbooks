# 원본 실행 결과(정답지)와 복원 함수를 대조. REA의 '검증' 단계를 손으로 한 예.
from reconstructed import compute_pan
expected = {0:-1.0000, 160:-0.5000, 320:0.0000, 480:0.5000, 639:0.9969}
ok = True
for x, want in expected.items():
    got = round(compute_pan(x), 4)
    mark = "일치" if abs(got-want) < 1e-4 else "불일치"
    if mark == "불일치": ok = False
    print(f"x={x:3d}  복원 {got:+.4f}  원본 {want:+.4f}  {mark}")
print("\n전체:", "통과" if ok else "실패")
