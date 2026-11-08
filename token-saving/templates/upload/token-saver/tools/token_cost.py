#!/usr/bin/env python3
"""토큰 비용 계산기 (핸드북 27). 표준 라이브러리만 사용.

한 번의 요청에서 입력·출력·캐시 토큰이 각각 얼마의 비용이 되는지 계산합니다.
'출력 토큰은 입력보다 비싸다', '캐시로 읽으면 싸다'를 숫자로 눈에 보이게 하는 도구입니다.

  python tools/token_cost.py --in 50000 --out 3000 --in-price 3 --out-price 15
  python tools/token_cost.py --in 2000 --cache-read 48000 --out 3000 --in-price 3 --out-price 15 --cache-read-price 0.3

단가(--*-price)는 '100만 토큰당' 금액입니다(통화는 그대로 환산). 기본 비율만 넣으면 추정합니다:
  - 출력 단가 미지정 시: 입력 단가 × 5 (출력이 보통 더 비쌈)
  - 캐시 읽기 미지정 시: 입력 단가 × 0.1 (캐시는 보통 1/10)
  - 캐시 쓰기 미지정 시: 입력 단가 × 1.25

주의: 실제 단가·비율은 모델과 시점에 따라 다릅니다. 반드시 현재 모델의 공식 단가를 넣어 확인하세요.
      '사고 토큰(thinking)'도 출력 토큰으로 계산되니, 출력에 포함해 보면 체감이 됩니다.
"""
import argparse
import sys


def per_tok(price_per_million):
    return price_per_million / 1_000_000.0


def compute(n_in, n_out, n_cw, n_cr, p_in, p_out, p_cw, p_cr):
    rows = [
        ("입력(비캐시)", n_in, n_in * per_tok(p_in)),
        ("캐시 쓰기", n_cw, n_cw * per_tok(p_cw)),
        ("캐시 읽기", n_cr, n_cr * per_tok(p_cr)),
        ("출력(+사고)", n_out, n_out * per_tok(p_out)),
    ]
    total = sum(c for _, _, c in rows)
    return rows, total


def main(argv=None):
    ap = argparse.ArgumentParser(description="토큰 비용 계산기")
    ap.add_argument("--in", dest="n_in", type=float, default=0, help="비캐시 입력 토큰")
    ap.add_argument("--out", dest="n_out", type=float, default=0, help="출력 토큰(사고 포함)")
    ap.add_argument("--cache-write", dest="n_cw", type=float, default=0)
    ap.add_argument("--cache-read", dest="n_cr", type=float, default=0)
    ap.add_argument("--in-price", type=float, required=True, help="입력 100만 토큰당 단가")
    ap.add_argument("--out-price", type=float, help="출력 단가(미지정 시 입력×5)")
    ap.add_argument("--cache-write-price", type=float, help="캐시 쓰기 단가(미지정 시 입력×1.25)")
    ap.add_argument("--cache-read-price", type=float, help="캐시 읽기 단가(미지정 시 입력×0.1)")
    ap.add_argument("--currency", default="$")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    p_out = a.out_price if a.out_price is not None else a.in_price * 5
    p_cw = a.cache_write_price if a.cache_write_price is not None else a.in_price * 1.25
    p_cr = a.cache_read_price if a.cache_read_price is not None else a.in_price * 0.1

    rows, total = compute(a.n_in, a.n_out, a.n_cw, a.n_cr, a.in_price, p_out, p_cw, p_cr)
    cur = a.currency
    if a.json:
        import json
        sys.stdout.write(json.dumps({"rows": [{"kind": k, "tokens": t, "cost": round(c, 6)} for k, t, c in rows],
                                     "total": round(total, 6)}, ensure_ascii=False, indent=1) + "\n")
        return 0
    out = ["# 토큰 비용", "",
           "| 항목 | 토큰 | 비용 | 비중 |", "|---|---:|---:|---:|"]
    for k, t, c in rows:
        if t:
            pct = (c / total * 100) if total else 0
            out.append("| {} | {:,.0f} | {}{:,.4f} | {:.0f}% |".format(k, t, cur, c, pct))
    out += ["| **합계** | | **{}{:,.4f}** | |".format(cur, total), "",
            "> 단가·비율은 모델·시점마다 다릅니다. 현재 공식 단가로 확인하세요.",
            "> 출력(사고 포함)이 흔히 비용의 큰 몫입니다. 캐시 읽기는 비캐시 입력보다 훨씬 쌉니다."]
    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
