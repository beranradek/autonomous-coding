"""
GitHub Copilot CLI Client Implementation
=========================================

Client implementation for GitHub Copilot CLI that implements the BaseClient interface.
This allows Copilot CLI to be used as an alternative AI provider in the autonomous coding agent.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

from base_client import BaseClient


# ----------------------------
# Events
# ----------------------------

@dataclass
class CopilotEvent:
    """Event emitted by the Copilot CLI output parser."""
    type: str  # "raw", "text", "tool_call", "json", "done", "error"
    text: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)


# ----------------------------
# Output parser
# ----------------------------

class OutputParser:
    """
    Parser for Copilot CLI output.
    
    Attempts to extract structured information from the CLI output including:
    - JSON responses
    - Code fences (```language blocks)
    - Shell commands (lines starting with $)
    - File operations (Create/Update/Delete patterns)
    """
    
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
        """
        Feed a chunk of output to the parser.
        
        Args:
            chunk: Text chunk from Copilot CLI output
            
        Returns:
            List of parsed events
        """
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

        # Heuristics for tool-calls
        lines = chunk.splitlines()
        for ln in lines:
            fence = self._re_code_fence.match(ln.strip())
            if fence:
                if not self._in_fence:
                    self._in_fence = True
                    self._fence_lang = fence.group("lang") or None
                    self._fence_buf = []
                else:
                    # End of fence
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
        """Attempt to extract JSON from a chunk of text."""
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
    """
    Runner for non-interactive Copilot CLI execution.
    
    Executes Copilot CLI with a single prompt and streams the output.
    """
    
    def __init__(self, copilot_cmd: str = "copilot", workdir: Optional[str] = None, copilot_config_dir: Optional[str] = None, env=None):
        """
        Initialize the Copilot runner.
        
        Args:
            copilot_cmd: Command to run Copilot CLI (default: "copilot")
            workdir: Working directory for the process
            copilot_config_dir: Directory for Copilot configuration (sets XDG_CONFIG_HOME)
            env: Environment variables to pass to the process
        """
        self.copilot_cmd = copilot_cmd
        self.workdir = workdir or os.getcwd()
        # Set up environment with XDG_CONFIG_HOME for project-level config
        self.env = {**os.environ, **(env or {})}
        if copilot_config_dir:
            self.env["XDG_CONFIG_HOME"] = copilot_config_dir
        self._parser = OutputParser()

    async def ask_stream(self, prompt: str) -> AsyncGenerator[CopilotEvent, None]:
        """
        Run copilot with a prompt and stream parsed events.
        
        Args:
            prompt: The prompt to send to Copilot CLI
            
        Yields:
            CopilotEvent objects parsed from the output
        """
        proc = await asyncio.create_subprocess_exec(
            self.copilot_cmd,
            "-p",
            prompt,
            "--allow-all-tools",  # Allow autonomous operation without confirmations
            "--add-dir", self.workdir,  # Automatically trust the project directory
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


# ----------------------------
# Client wrapper implementing BaseClient
# ----------------------------

class CopilotClient(BaseClient):
    """
    Copilot CLI client implementing the BaseClient interface.
    
    This allows Copilot CLI to be used interchangeably with other
    AI client implementations through a common interface.
    """
    
    def __init__(self, project_dir: Path, copilot_config_dir: Optional[Path] = None):
        """
        Initialize the Copilot client.
        
        Args:
            project_dir: Project directory for the Copilot CLI to work in
            copilot_config_dir: Directory for Copilot configuration (optional, for project-level config)
        """
        self.project_dir = project_dir
        self.copilot_config_dir = copilot_config_dir
        self.runner = CopilotRunner(
            workdir=str(project_dir.resolve()),
            copilot_config_dir=str(copilot_config_dir.resolve()) if copilot_config_dir else None
        )
        self._current_prompt: Optional[str] = None
    
    async def query(self, message: str) -> None:
        """
        Store the query for execution when receive_response() is called.
        
        Args:
            message: The prompt to send to Copilot CLI
        """
        self._current_prompt = message
    
    async def receive_response(self) -> AsyncGenerator[CopilotEvent, None]:
        """
        Execute Copilot CLI with the stored prompt and stream responses.
        
        Yields:
            CopilotEvent objects from the Copilot CLI output
        """
        if self._current_prompt is None:
            raise RuntimeError("No query set. Call query() before receive_response()")
        
        async for event in self.runner.ask_stream(self._current_prompt):
            yield event
    
    async def __aenter__(self):
        """Enter async context manager."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        # No cleanup needed for Copilot CLI (subprocess handles its own cleanup)
        pass


def create_copilot_client(project_dir: Path) -> CopilotClient:
    """
    Create a Copilot CLI client.
    
    Args:
        project_dir: Directory for the project
        
    Returns:
        CopilotClient implementing BaseClient interface
    """
    # Ensure project directory exists
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create project-level .copilot directory for configuration
    copilot_config_dir = project_dir / ".copilot"
    copilot_config_dir.mkdir(exist_ok=True)
    
    # Copy example MCP config if it doesn't exist
    mcp_config_file = copilot_config_dir / "mcp-config.json"
    if not mcp_config_file.exists():
        # Create a basic MCP config from tools.py
        from tools import MCP_SERVERS
        
        # Convert MCP_SERVERS to Copilot CLI format
        copilot_mcp_config = {"mcpServers": {}}
        for server_name, server_config in MCP_SERVERS.items():
            if server_config.get("type") == "http":
                copilot_mcp_config["mcpServers"][server_name] = {
                    "type": "http",
                    "url": server_config["url"]
                }
            else:
                copilot_mcp_config["mcpServers"][server_name] = {
                    "command": server_config["command"],
                    "args": server_config["args"]
                }
                if "env" in server_config:
                    copilot_mcp_config["mcpServers"][server_name]["env"] = server_config["env"]
        
        with open(mcp_config_file, "w") as f:
            json.dump(copilot_mcp_config, f, indent=2)
        
        print(f"Created MCP config at {mcp_config_file}")
    
    print(f"Using GitHub Copilot CLI")
    print(f"   - Working directory: {project_dir.resolve()}")
    print(f"   - Autonomous mode: --allow-all-tools enabled")
    print(f"   - Auto-trusted directory: --add-dir {project_dir.resolve()}")
    print(f"   - MCP config: {mcp_config_file}")
    print()
    
    return CopilotClient(project_dir, copilot_config_dir)
