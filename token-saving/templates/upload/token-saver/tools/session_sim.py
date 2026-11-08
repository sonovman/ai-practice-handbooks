#!/usr/bin/env python3
"""세션 누적 비용 시뮬레이터 (핸드북 27). 표준 라이브러리만 사용.

클로드 코드는 매 턴 '지금까지의 전체'를 다시 보냅니다. 그래서 세션이 길수록 비용이 급증합니다.
이 도구는 N턴 세션의 누적 비용을 (1) 캐시 없음 (2) 캐시 사용 (3) 캐시+중간 /clear 로 비교해,
왜 급증하는지와 /clear·캐시의 효과를 숫자로 보여 줍니다.

  python tools/session_sim.py --turns 40 --turn-input 1500 --turn-output 1500 \
      --start-context 12000 --in-price 3 --out-price 15 --clear-every 10

모델(근사): 매 턴 '그동안 쌓인 앞부분(prefix)'을 다시 입력으로 보낸다.
  - 캐시 없음: prefix 전체를 입력 단가로.
  - 캐시 사용: prefix 는 캐시 읽기 단가(입력×0.1)로, 새 입력만 입력 단가로.
  - /clear: --clear-every K 턴마다 prefix 를 시작값으로 리셋.
각 턴 뒤 prefix 에 (새 입력 + 출력) 이 누적된다.

주의: 실제 비용은 모델 내부 처리·사고 토큰·도구 호출에 따라 달라집니다. 이 값은 '구조적 경향'을 보는 근사입니다.
"""
import argparse
import sys


def per_tok(p):
    return p / 1_000_000.0


def simulate(turns, t_in, t_out, start_ctx, p_in, p_out, p_cr, cache, clear_every):
    ctx = start_ctx
    total = 0.0
    for t in range(1, turns + 1):
        prefix = ctx
        if cache:
            in_cost = prefix * per_tok(p_cr) + t_in * per_tok(p_in)
        else:
            in_cost = (prefix + t_in) * per_tok(p_in)
        out_cost = t_out * per_tok(p_out)
        total += in_cost + out_cost
        ctx += t_in + t_out
        if clear_every and t % clear_every == 0:
            ctx = start_ctx
    return total


def main(argv=None):
    ap = argparse.ArgumentParser(description="세션 누적 비용 시뮬레이터")
    ap.add_argument("--turns", type=int, default=40)
    ap.add_argument("--turn-input", type=float, default=1500, help="턴당 새 입력 토큰")
    ap.add_argument("--turn-output", type=float, default=1500, help="턴당 출력 토큰(사고 포함)")
    ap.add_argument("--start-context", type=float, default=12000, help="세션 시작 고정분(시스템+CLAUDE.md+도구정의 등)")
    ap.add_argument("--in-price", type=float, required=True)
    ap.add_argument("--out-price", type=float)
    ap.add_argument("--cache-read-price", type=float)
    ap.add_argument("--clear-every", type=int, default=10, help="N턴마다 /clear(0=안 함)")
    ap.add_argument("--currency", default="$")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    p_out = a.out_price if a.out_price is not None else a.in_price * 5
    p_cr = a.cache_read_price if a.cache_read_price is not None else a.in_price * 0.1

    base = dict(turns=a.turns, t_in=a.turn_input, t_out=a.turn_output, start_ctx=a.start_context,
                p_in=a.in_price, p_out=p_out, p_cr=p_cr)
    s1 = simulate(cache=False, clear_every=0, **base)
    s2 = simulate(cache=True, clear_every=0, **base)
    s3 = simulate(cache=True, clear_every=a.clear_every, **base)
    cur = a.currency

    if a.json:
        import json
        sys.stdout.write(json.dumps({"no_cache": round(s1, 4), "cache": round(s2, 4),
                                     "cache_clear": round(s3, 4), "clear_every": a.clear_every},
                                    ensure_ascii=False, indent=1) + "\n")
        return 0

    def pct(x):
        return "{:.0f}%".format(x / s1 * 100) if s1 else "-"
    out = ["# 세션 누적 비용 ({}턴, 턴당 입력 {:.0f}/출력 {:.0f})".format(a.turns, a.turn_input, a.turn_output), "",
           "| 시나리오 | 누적 비용 | 대비 |", "|---|---:|---:|",
           "| 캐시 없음, /clear 없음 | {}{:,.3f} | 100% |".format(cur, s1),
           "| 캐시 사용, /clear 없음 | {}{:,.3f} | {} |".format(cur, s2, pct(s2)),
           "| 캐시 + {}턴마다 /clear | {}{:,.3f} | {} |".format(a.clear_every, cur, s3, pct(s3)), "",
           "> 매 턴 '그동안의 전체'를 다시 보내므로 길수록 급증합니다. 캐시는 앞부분을 싸게,",
           "> /clear 는 쌓인 앞부분을 리셋해 재전송량 자체를 줄입니다. 단가는 현재 공식값으로 확인하세요."]
    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
