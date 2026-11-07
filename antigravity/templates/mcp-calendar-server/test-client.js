// test-client.js — Antigravity에 연결하기 전에 서버가 도구 목록·호출에 제대로 답하는지 확인
// 실행: npm test
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));   // Node 18에서도 동작

const client = new Client({ name: "check", version: "1.0.0" });
await client.connect(new StdioClientTransport({ command: "node", args: ["index.js"], cwd: here }));

const { tools } = await client.listTools();
console.log("tools/list →", tools.map((t) => t.name).join(", "));

const r = await client.callTool({ name: "get_calendar_events", arguments: { date: "2026-11-09" } });
console.log("tools/call get_calendar_events(2026-11-09) →\n" + r.content[0].text);

const bad = await client.callTool({ name: "get_calendar_events", arguments: { date: "11월 9일" } });
console.log("잘못된 날짜 형식 →", bad.isError ? "오류로 거절됨(정상)" : "통과됨(확인 필요)");

await client.close();
