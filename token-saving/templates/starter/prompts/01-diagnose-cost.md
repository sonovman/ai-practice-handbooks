# 비용 진단 요청

지금 세션에서 토큰이 어디서 많이 나가는지 진단해 줘.
- /context 로 무엇이 창을 차지하는지, /usage 로 최근 소모를 확인하고 요약.
- 안 쓰는 MCP·플러그인, 무거운 로그, 큰 파일을 골라 정리안을 제시.
(보조: `python tools/session_sim.py --turns 40 --in-price <입력단가> --out-price <출력단가>`)
