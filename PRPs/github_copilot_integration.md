Abstract ClaudeSDKClient returned by create_client in client.py under an interface that will have the same methods as ClaudeSDKClient (query, receive_response, etc.) to use it in agent.py and autocode.py, and to allow another client integrations - like GitHub Copilot CLI integration. Use this abstraction in mentioned higher level files (like in run_agent_session). Rename client.py to claude_sdk_client.py (and update the code that references it).

Extract arrays with concrete MCP tools and block with:
mcp_servers={
                "context7": {"command": "npx", "args": ["-y", "@upstash/context7-mcp@latest"]},
                # "puppeteer": {"command": "npx", "args": ["puppeteer-mcp-server"], "env": {"SCREENSHOT_QUALITY": "60","SCREENSHOT_DEFAULT_WIDTH": "800","SCREENSHOT_DEFAULT_HEIGHT": "600","SCREENSHOT_MAX_WIDTH": "1280","SCREENSHOT_MAX_HEIGHT": "800"}},
                # Browser MCP enhanced by D. Strejc:
                "browsermcp": {"type": "http", "url": "http://127.0.0.1:3000/mcp"},
                "postgres": {"command": "uv","args": ["run","postgres-mcp","--access-mode=unrestricted"],"env": {"DATABASE_URI": "postgresql://postgres:postgres@localhost:5432/artbeams"}},
            }
from client.py to tools.py file to be reusable in different clients.

I have now copilot cli installed.

Read https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli and https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli

Implement copilot_client.py file that will use copilot cli so it can be integrated (under the interface described before into my application) as another coding agent/provider.

This is generic example of code that could allow copilot integration into my Python application:

```
from __future__ import annotations
import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, Optional, Union


# ----------------------------
# Events
# ----------------------------

@dataclass
class CopilotEvent:
    type: str                 # "raw", "text", "tool_call", "json", "done", "error"
    text: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)


# ----------------------------
# Output parser
# ----------------------------

class OutputParser:
    _re_shell_line = re.compile(r"^\s*\$\s+(?P<cmd>.+)$")
    _re_code_fence = re.compile(r"^```(?P<lang>\w+)?\s*$")
    _re_file_op = re.compile(
        r"(?P<op>Create|Create\s+file|Update|Edit|Modify|Delete)\s+(?:file\s+)?(?P<path>[^\s]+)",
        re.IGNORECASE,
    )

    def __init__(self):
        self._in_fence = False
        self._fence_lang: Optional[str] = None
        self._fence_buf: list[str] = []

    def feed(self, chunk: str) -> list[CopilotEvent]:
        events: list[CopilotEvent] = []
        if not chunk:
            return events

        events.append(CopilotEvent(type="raw", text=chunk))

        # JSON auto-detection
        maybe = self._extract_json(chunk)
        if maybe is not None:
            events.append(
                CopilotEvent(
                    type="json",
                    text=json.dumps(maybe, ensure_ascii=False),
                    meta={"parsed": maybe},
                )
            )
            for tc in maybe.get("tool_calls", []):
                events.append(
                    CopilotEvent(
                        type="tool_call",
                        text=str(tc),
                        meta={"name": tc.get("name"), "args": tc.get("args", {})},
                    )
                )
            final = maybe.get("final") or maybe.get("final_text") or ""
            if final:
                events.append(CopilotEvent(type="text", text=final))
            return events

        # Heuristiky na tool-calls
        lines = chunk.splitlines()
        for ln in lines:
            fence = self._re_code_fence.match(ln.strip())
            if fence:
                if not self._in_fence:
                    self._in_fence = True
                    self._fence_lang = fence.group("lang") or None
                    self._fence_buf = []
                else:
                    # ukončení
                    code = "\n".join(self._fence_buf)
                    events.append(
                        CopilotEvent(
                            type="text",
                            text=code,
                            meta={"kind": "code", "lang": self._fence_lang},
                        )
                    )
                    # shell → tool_call
                    if (
                        self._fence_lang in ("sh", "bash", "shell")
                        or code.strip().startswith("$ ")
                    ):
                        cmd = code.strip().lstrip("$ ").strip()
                        events.append(
                            CopilotEvent(
                                type="tool_call",
                                text=cmd,
                                meta={"name": "shell", "args": {"cmd": cmd}},
                            )
                        )
                    self._in_fence = False
                    self._fence_lang = None
                    self._fence_buf = []
                continue

            if self._in_fence:
                self._fence_buf.append(ln)
                continue

            m_shell = self._re_shell_line.match(ln)
            if m_shell:
                cmd = m_shell.group("cmd").strip()
                events.append(
                    CopilotEvent(
                        type="tool_call",
                        text=cmd,
                        meta={"name": "shell", "args": {"cmd": cmd}},
                    )
                )
                continue

            m_file = self._re_file_op.search(ln)
            if m_file:
                events.append(
                    CopilotEvent(
                        type="tool_call",
                        text=f"{m_file.group('op')} {m_file.group('path')}",
                        meta={
                            "name": "file_op",
                            "args": {"op": m_file.group("op"), "path": m_file.group("path")},
                        },
                    )
                )
                continue

        events.append(CopilotEvent(type="text", text=chunk))
        return events

    def _extract_json(self, chunk: str) -> Optional[Dict[str, Any]]:
        start = chunk.find("{")
        end = chunk.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = chunk[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            return None


# ----------------------------
# NON-INTERACTIVE Copilot runner
# ----------------------------

class CopilotRunner:
    def __init__(self, copilot_cmd: str = "copilot", workdir: Optional[str] = None, env=None):
        self.copilot_cmd = copilot_cmd
        self.workdir = workdir or os.getcwd()
        self.env = {**os.environ, **(env or {})}
        self._parser = OutputParser()

    async def ask_stream(self, prompt: str) -> AsyncGenerator[CopilotEvent, None]:
        """
        Spustí copilot -p "<prompt>" jako jednorázový neinteraktivní proces
        a streamuje výstup přes parser.
        """
        proc = await asyncio.create_subprocess_exec(
            self.copilot_cmd,
            "-p",
            prompt,
            cwd=self.workdir,
            env=self.env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        assert proc.stdout is not None

        while True:
            data = await proc.stdout.read(4096)
            if not data:
                break
            chunk = data.decode(errors="replace")
            for ev in self._parser.feed(chunk):
                yield ev

        rc = await proc.wait()
        yield CopilotEvent(type="done", meta={"returncode": rc})
```

How to use it:

```
import asyncio

async def main():
    runner = CopilotRunner()

    prompt = """
    Napiš JSON:
    {
      "final": "...",
      "tool_calls": [...]
    }
    """

    async for ev in runner.ask_stream(prompt):
        if ev.type == "text":
            print("AGENT:", ev.text)
        elif ev.type == "tool_call":
            print("TOOL:", ev.meta)
        elif ev.type == "json":
            print("JSON:", ev.meta["parsed"])
        elif ev.type == "done":
            print("DONE", ev.meta)

asyncio.run(main())
```

But it must be adapted to the project needs.
Try your best so the output from copilot cli process is parsed correctly
and is detailed/responsive and useful for end user reading/following output of autonomous coding process (sessions), including tool calls and final responses of the agent.

Pass in the system environment variables to the Copilot subprocess so it
can read needed variables like GITHUB_TOKEN, COPILOT_API_KEY etc.

Add mandatory --cli [claude|copilot] option to my main autocode.py program (with error message printed if not given). Update README.md with this option.

Read copilot cli documentation about permissions and also MCP server
and try the best to integrate allowed MCP servers and their tools and
all commands to copilot cli execution process. If it is not possible in the code, document neccessary configuration file needed for permissions and MCP server configurations and place these files within copilot subfolder of this project and document their usage in README.md.
Do not be much restrictive in permissions for tool usage. Our agent MUST be able to run autonomously without manual confirmations. Probably, --allow-all-tools is the best option.

Obviously, copilot cli will be needed to run with copilot --prompt

Implement it all and try to run:

`uv sync`
`uv run autocode.py --cli copilot`

within this project folder (/generations/my_project), test it, investigate errors that kill it after while it runs.
Do the fixes if needed and run it again to check it works finally.
