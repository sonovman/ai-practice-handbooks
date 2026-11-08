#!/usr/bin/env python3
"""전력 예산·회로 안전 점검 (핸드북 25). 표준 라이브러리만 사용.

고성능 GPU 여러 장을 집·사무실의 일반 회로에 물리기 전에, 소비 전력이 회로 한계를 넘는지 미리 계산합니다.
전기는 되돌릴 수 없는 사고(과열·화재·차단기 다운)로 이어지므로, '사전 계산'이 핵심입니다.

  python tools/power_budget.py --gpus 4 --gpu-watts 350 --host-watts 280
  python tools/power_budget.py --gpus 4 --gpu-watts 600 --volts 120 --amps 15   # 기본값(미제한) 위험 확인
  python tools/power_budget.py --gpus 2 --gpu-watts 350 --host-watts 200 --volts 220 --amps 16

판정  OK     연속 부하가 회로의 연속 허용치(차단기의 80%) 이하
      WARN   연속 허용치 초과(80~100%) — 전력 제한·회로 분리 필요
      DANGER 차단기 정격 초과 — 그대로 켜지 말 것

연속 부하 규칙: 3시간 넘게 이어지는 부하는 차단기 정격의 80%까지만 쓰는 것이 안전 기준(NEC 등)입니다.
  예) 120V×15A=1800W 정격 → 연속 허용 1440W. 220V×16A=3520W → 연속 허용 2816W.

주의: 이 도구는 '계획 점검' 보조입니다. 실제 배선·차단기·전용 회로·접지는 반드시 자격 있는 전기 기술자와
      확인하세요. 벽 콘센트 1구에서 여러 고출력 기기를 함께 쓰지 마세요. PSU 효율로 인해 '벽에서 끌어가는'
      전력은 부품 합계보다 큽니다(이 도구가 반영).
"""
import argparse
import sys

CONTINUOUS_FACTOR = 0.80  # 연속 부하 허용 비율(차단기 정격 대비)


def compute(gpus, gpu_watts, host_watts, psu_eff, volts, amps):
    dc_load = gpus * gpu_watts + host_watts          # 부품이 쓰는 전력(DC 측)
    wall = dc_load / psu_eff                          # 벽에서 끌어가는 전력(PSU 손실 반영)
    breaker = volts * amps                            # 차단기 정격 용량
    continuous = breaker * CONTINUOUS_FACTOR          # 연속 부하 허용치
    if wall > breaker:
        status = "DANGER"
    elif wall > continuous:
        status = "WARN"
    else:
        status = "OK"
    return {
        "gpus": gpus, "gpu_watts": gpu_watts, "host_watts": host_watts,
        "dc_load": round(dc_load), "wall": round(wall),
        "breaker": round(breaker), "continuous": round(continuous),
        "headroom": round(continuous - wall), "status": status,
        "pct": round(wall / breaker * 100),
    }


def advise(r):
    tips = []
    if r["status"] != "OK":
        # 제한으로 연속 허용치 안에 들어오려면 GPU당 몇 W?
        room_dc = r["continuous"] * 0.9 - r["host_watts"]  # psu_eff 0.9 가정 역산
        if r["gpus"] > 0 and room_dc > 0:
            per = int(room_dc / r["gpus"])
            if per < r["gpu_watts"]:
                tips.append("GPU당 약 {}W로 제한하면 연속 허용치 안에 들어옵니다(nvidia-smi -pl {}).".format(per, per))
        tips.append("또는 GPU를 별도 전용 회로로 나누거나, 더 높은 정격(예: 220V) 전용 회로를 전기 기술자와 구성하세요.")
    return tips


def to_markdown(r):
    mark = {"OK": "안전 범위", "WARN": "연속 허용 초과", "DANGER": "정격 초과(위험)"}
    L = ["# 전력 예산 점검", "",
         "- 구성: GPU {}장 × {}W + 호스트 {}W".format(r["gpus"], r["gpu_watts"], r["host_watts"]),
         "- 부품 합계(DC): {}W / 벽에서 끌어가는 전력: **{}W**".format(r["dc_load"], r["wall"]),
         "- 회로: 정격 {}W · 연속 허용(80%) {}W".format(r["breaker"], r["continuous"]),
         "- 여유: {}W (회로 대비 {}%)".format(r["headroom"], r["pct"]),
         "- 판정: **{}**".format(mark[r["status"]]), ""]
    tips = advise(r)
    if tips:
        L.append("## 권고")
        L += ["- " + t for t in tips]
        L.append("")
    L += ["> 실제 배선·차단기·전용 회로·접지는 반드시 자격 있는 전기 기술자와 확인하세요.",
          "> 고출력 기기를 벽 콘센트 1구에 몰아 쓰지 마세요."]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="전력 예산·회로 안전 점검")
    ap.add_argument("--gpus", type=int, default=4)
    ap.add_argument("--gpu-watts", type=float, default=350, help="GPU 1장당 소비 전력(제한값 권장)")
    ap.add_argument("--host-watts", type=float, default=280, help="CPU·메인보드·SSD·팬 등 나머지")
    ap.add_argument("--psu-eff", type=float, default=0.90, help="PSU 효율(기본 0.90)")
    ap.add_argument("--volts", type=float, default=120)
    ap.add_argument("--amps", type=float, default=15)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not (0 < a.psu_eff <= 1):
        sys.exit("--psu-eff 는 0~1 사이")
    r = compute(a.gpus, a.gpu_watts, a.host_watts, a.psu_eff, a.volts, a.amps)
    if a.json:
        import json
        sys.stdout.write(json.dumps(r, ensure_ascii=False, indent=1) + "\n")
    else:
        sys.stdout.write(to_markdown(r))
    return {"OK": 0, "WARN": 1, "DANGER": 2}[r["status"]]


if __name__ == "__main__":
    sys.exit(main())
