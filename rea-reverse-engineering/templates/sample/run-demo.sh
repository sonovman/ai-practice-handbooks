#!/usr/bin/env bash
# 자작 바이너리 역공학 시범. REA/Ghidra가 자동화하는 '근거 수집'을 표준 binutils로 손수 보이는 예.
set -e
cd "$(dirname "$0")"
gcc -O1 -o panning panning.c            # 1) 내가 만든 소스를 컴파일 (이 바이너리를 '소스 없이' 분석한다고 가정)
echo "== 1. 실행 결과(정답지)"; ./panning
echo; echo "== 2. 함수 목록 (nm) — compute_pan 심볼 위치"
nm panning | grep -i compute_pan || true
echo; echo "== 3. 어셈블리/상수 (objdump) — compute_pan 디스어셈블"
objdump -d --no-show-raw-insn -M att panning | awk '/<compute_pan>:/{p=1} p{print} /ret/{if(p)exit}'
echo; echo "== 4. 읽기전용 데이터의 double 상수 (objdump -s .rodata)"
objdump -s -j .rodata panning | head -8
