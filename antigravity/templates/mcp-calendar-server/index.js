// index.js — Antigravity 실습용 MCP 서버 (일정 조회)
// 실행: node index.js   (Antigravity가 stdio로 실행하므로 직접 켜 둘 필요는 없습니다)
// 데이터: 같은 폴더의 events.json (실제 캘린더 대신 쓰는 예시 데이터)
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const server = new McpServer({ name: "calendar-server", version: "1.0.0" });

async function loadEvents() {
  return JSON.parse(await readFile(join(here, "events.json"), "utf8"));
}

// 도구 1: 특정 날짜의 일정 — 입력 스키마(zod)를 한 번만 적으면 목록·검증에 함께 쓰입니다
server.registerTool(
  "get_calendar_events",
  {
    title: "날짜별 일정 조회",
    description: "YYYY-MM-DD 날짜를 받아 그날의 일정(시각·제목·장소)을 돌려줍니다. '내일 일정', '11월 9일 회의'처럼 일정을 물을 때 사용하세요.",
    inputSchema: { date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe("조회할 날짜, YYYY-MM-DD") },
  },
  async ({ date }) => {
    const events = (await loadEvents())[date] ?? [];
    return {
      content: [{ type: "text", text: JSON.stringify({ date, count: events.length, events }, null, 2) }],
    };
  }
);

// 도구 2: 일정이 있는 날짜 목록 — 에이전트가 범위를 모를 때 먼저 확인
server.registerTool(
  "list_event_dates",
  {
    title: "일정이 있는 날짜",
    description: "일정이 등록된 날짜 목록을 돌려줍니다.",
    inputSchema: {},
  },
  async () => ({
    content: [{ type: "text", text: JSON.stringify(Object.keys(await loadEvents()).sort()) }],
  })
);

// 주의: stdio 서버는 표준 출력이 통신 통로입니다. 디버그 메시지는 console.error로만 쓰세요.
await server.connect(new StdioServerTransport());
console.error("calendar-server 준비 완료 (stdio)");
