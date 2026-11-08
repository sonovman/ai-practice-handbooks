#!/usr/bin/env bash
# PreCompact 훅: /compact(수동·자동) 직전에 실행. 압축으로 잃기 쉬운 상태를 파일로 남긴다.
date "+compact at %F %T" >> .claude/compact.log
exit 0
