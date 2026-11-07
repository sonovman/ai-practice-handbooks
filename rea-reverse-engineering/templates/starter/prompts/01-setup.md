# REA 설치와 Claude Code 연결

전제: Node.js 22.19+ 또는 24.11+ (Windows는 설치 시 PATH 포함). 터미널에서 `node --version` 확인.

```
npx rea-agents setup
```
1. 에이전트 목록에서 **Claude Code** 선택(여러 개 선택 가능: Codex, Gemini CLI, Antigravity, GitHub Copilot CLI 등).
2. REA가 MCP 서버와 역공학 스킬 지침을 등록하겠다고 하면, 바뀌는 내용을 확인하고 승인.
3. 네이티브 바이너리(.exe/.dll/ELF/Mach-O)를 분석하려면 디컴파일러가 필요합니다:
   - **Ghidra**(무료·오픈소스, NSA 공개) 또는 **Hopper**(설정 중 승인하면 자동 설치 안내), 또는 보유한 **IDA Pro**.
   - JS/Electron·웹·HAR 분석은 디컴파일러 없이도 됩니다.
4. 연결 점검: `npx rea-agents doctor`  (문제 시 안내가 나옵니다)
5. Claude Code를 재시작해 MCP를 적용. `/mcp` 또는 도구 목록에서 REA가 보이는지 확인.

주의: 모든 분석은 내 컴퓨터(로컬)에서 실행되고, 대상 파일은 외부로 올라가지 않습니다.
동적 분석·브라우저 관찰은 기본 꺼짐이며, 켤 때마다 승인을 거칩니다.
