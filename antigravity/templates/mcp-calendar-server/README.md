# mcp-calendar-server — Antigravity 실습용 MCP 서버

날짜를 받아 그날 일정을 돌려주는 도구 2개(`get_calendar_events`, `list_event_dates`)를 제공합니다.
데이터는 같은 폴더의 `events.json`(예시)입니다. 실제 캘린더에 붙이려면 `loadEvents()`만 바꾸면 됩니다.

## 준비
- Node.js 18 이상

## 실행·시험
```
npm install
npm test           # 도구 목록·호출·잘못된 입력 거절 확인 (결과 예: test-output.txt)
npm run inspect    # (선택) MCP Inspector로 브라우저에서 직접 시험
```

## Antigravity에 연결
`~/.gemini/config/mcp_config.json`(전역) 또는 작업 폴더의 `.agents/mcp_config.json`에:
```json
{
  "mcpServers": {
    "calendar": { "command": "node", "args": ["/절대/경로/mcp-calendar-server/index.js"] }
  }
}
```
Windows: `"C:\\Users\\me\\mcp-calendar-server\\index.js"`. 저장 후 앱의 MCP Servers 목록에서 재시작합니다.
