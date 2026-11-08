#!/usr/bin/env python3
"""VRAM 적합성·스필오버 점검 (핸드북 25). 표준 라이브러리만 사용.

모델이 GPU VRAM에 들어가는지, 아니면 시스템 RAM으로 '넘쳐(Spillover)' 실사용이 불가능해지는지 미리 계산합니다.
로컬 LLM 추론의 절대 병목은 VRAM이라는 원고의 철학을, 사기 전에 숫자로 확인하기 위한 도구입니다.

  python tools/vram_fit.py --params 27 --bits 8 --vram 48
  python tools/vram_fit.py --params 594 --bits 4 --vram 384 --kv-gb 40
  python tools/vram_fit.py --params 27 --bits 16 --vram 24                 # 스필오버 확인

판정은 '가중치 + 여유 (+ 지정한 KV)' 기준입니다. 이 부분이 가장 믿을 만합니다.
  가중치(GB) = params(10억) × bits / 8
  합계       = 가중치 + 여유(가중치의 일정 비율 + --extra-gb) + --kv-gb

판정  OK     합계가 VRAM의 85% 이하
      WARN   85~100% — 빠듯함(컨텍스트·동시요청 늘리면 넘칠 수 있음)
      SPILL  100% 초과 — 시스템 RAM으로 넘침, 에이전트 작업엔 사실상 사용 불가

KV 캐시는 모델 구조(GQA/MLA)·KV 양자화에 따라 크게 달라져 정확히 예측하기 어렵습니다. 그래서 판정에는
  --kv-gb(직접 지정, 엔진 로그에서 확인)만 넣고, --layers/--hidden/--context를 주면 '다중헤드 기준 최악 상한'을
  참고용으로만 보여 줍니다(실제 모델은 보통 이보다 훨씬 작습니다).

주의: 실제 점유는 추론 엔진(vLLM 등)·양자화·동시 요청 수에 따라 달라집니다. 이 값은 '대략 맞는지' 가늠용입니다.
"""
import argparse
import sys

OVERHEAD_FRAC = 0.08   # 활성화·단편화 등 기본 여유(가중치의 비율)


def weight_gb(params_b, bits):
    return params_b * bits / 8.0


def kv_upper_gb(layers, hidden, context, kv_bytes):
    """다중헤드 기준 KV '최악 상한'. GQA/MLA·KV 양자화 미반영 → 실제는 보통 훨씬 작음. 참고용."""
    if not (layers and hidden and context):
        return 0.0
    return 2.0 * layers * hidden * context * kv_bytes / 1e9


def compute(params_b, bits, vram_gb, kv_gb, extra_gb):
    w = weight_gb(params_b, bits)
    overhead = w * OVERHEAD_FRAC + extra_gb
    total = w + overhead + kv_gb
    pct = total / vram_gb * 100 if vram_gb > 0 else float("inf")
    if total > vram_gb:
        status = "SPILL"
    elif pct > 85:
        status = "WARN"
    else:
        status = "OK"
    return {"weight": round(w, 1), "overhead": round(overhead, 1), "kv_gb": round(kv_gb, 1),
            "total": round(total, 1), "vram": vram_gb, "pct": round(pct), "status": status}


def to_markdown(r, params_b, bits, kv_upper):
    mark = {"OK": "여유 있음", "WARN": "빠듯함", "SPILL": "VRAM 초과(RAM으로 넘침)"}
    L = ["# VRAM 적합성 점검", "",
         "- 모델: {}B · {}-bit".format(params_b, bits),
         "- 가중치: {} GB".format(r["weight"]),
         "- 여유(활성화 등): {} GB".format(r["overhead"])]
    if r["kv_gb"]:
        L.append("- KV 캐시(지정): {} GB".format(r["kv_gb"]))
    L += ["- 합계: **{} GB** / VRAM {} GB (점유 {}%)".format(r["total"], r["vram"], r["pct"]),
          "- 판정: **{}**".format(mark[r["status"]]), ""]
    if kv_upper:
        L += ["> 참고: 다중헤드 기준 KV 최악 상한 ≈ {} GB (GQA/MLA·KV 양자화 미반영 — 실제 모델은 보통 훨씬 작습니다).".format(round(kv_upper)),
              "> 정확한 KV는 엔진 로그로 확인해 --kv-gb 로 넣으세요.", ""]
    if r["status"] == "SPILL":
        L += ["## 권고", "- 비트를 낮추거나(예: 16→8→4), VRAM을 늘리거나, 컨텍스트·동시요청을 줄이세요.",
              "- 시스템 RAM으로 넘치면 대역폭 차이로 에이전트 작업 속도가 급락합니다.", ""]
    elif r["status"] == "WARN":
        L += ["## 권고", "- 동시 요청·컨텍스트를 늘릴 여지가 적습니다. 여유를 두려면 비트↓ 또는 VRAM↑.", ""]
    L += ["> 실제 점유는 엔진·양자화·동시 요청에 따라 달라집니다. 이 값은 가늠용 근사입니다."]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="VRAM 적합성·스필오버 점검")
    ap.add_argument("--params", type=float, required=True, help="모델 파라미터 수(단위: 10억, 예: 27, 594)")
    ap.add_argument("--bits", type=float, default=16, help="가중치 비트(16/8/4 등)")
    ap.add_argument("--vram", type=float, required=True, help="사용 가능한 총 VRAM(GB)")
    ap.add_argument("--kv-gb", type=float, default=0, help="KV 캐시(GB) — 엔진 로그에서 확인한 값. 판정에 포함")
    ap.add_argument("--extra-gb", type=float, default=0, help="추가 오버헤드(GB)")
    ap.add_argument("--layers", type=float, default=0, help="(참고용) 레이어 수")
    ap.add_argument("--hidden", type=float, default=0, help="(참고용) 히든 차원")
    ap.add_argument("--context", type=float, default=0, help="(참고용) 컨텍스트 길이(토큰)")
    ap.add_argument("--kv-bytes", type=float, default=2, help="(참고용) KV 원소당 바이트")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.params <= 0 or a.vram <= 0 or a.bits <= 0:
        sys.exit("--params, --bits, --vram 는 양수")
    r = compute(a.params, a.bits, a.vram, a.kv_gb, a.extra_gb)
    kv_upper = kv_upper_gb(a.layers, a.hidden, a.context, a.kv_bytes)
    if a.json:
        import json
        out = dict(r); out["kv_upper_est"] = round(kv_upper, 1)
        sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    else:
        sys.stdout.write(to_markdown(r, a.params, a.bits, kv_upper))
    return {"OK": 0, "WARN": 1, "SPILL": 2}[r["status"]]


if __name__ == "__main__":
    sys.exit(main())
