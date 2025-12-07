"""
Claude SDK Client Implementation
=================================

Claude Agent SDK client wrapper implementing the BaseClient interface.
"""

import json
from pathlib import Path
from typing import AsyncGenerator, Any

from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient
from claude_code_sdk.types import HookMatcher

from base_client import BaseClient
from security import bash_security_hook
from subscription import api_key
from tools import (
    BUILTIN_TOOLS,
    CONTEXT7_TOOLS,
    BROWSERMCP_TOOLS,
    PUPPETEER_TOOLS,
    POSTGRES_TOOLS,
    SERENA_TOOLS,
    MCP_SERVERS,
)


class ClaudeClientWrapper(BaseClient):
    """
    Wrapper for ClaudeSDKClient implementing the BaseClient interface.
    
    This allows the Claude SDK client to be used interchangeably with
    other AI client implementations through a common interface.
    """
    
    def __init__(self, sdk_client: ClaudeSDKClient):
        """
        Initialize the wrapper.
        
        Args:
            sdk_client: Configured ClaudeSDKClient instance
        """
        self._client = sdk_client
    
    async def query(self, message: str) -> None:
        """Send a query to the Claude SDK client."""
        await self._client.query(message)
    
    async def receive_response(self) -> AsyncGenerator[Any, None]:
        """Stream responses from the Claude SDK client."""
        async for msg in self._client.receive_response():
            yield msg
    
    async def __aenter__(self):
        """Enter async context manager."""
        await self._client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self._client.__aexit__(exc_type, exc_val, exc_tb)


def create_client(project_dir: Path, model: str) -> ClaudeClientWrapper:
    """
    Create a Claude Agent SDK client with multi-layered security.

    Args:
        project_dir: Directory for the project
        model: Claude model to use

    Returns:
        ClaudeClientWrapper implementing BaseClient interface

    Security layers (defense in depth):
    1. Sandbox - OS-level bash command isolation prevents filesystem escape
    2. Permissions - File operations restricted to project_dir only
    3. Security hooks - Bash commands validated against an allowlist
       (see security.py for ALLOWED_COMMANDS)
    """

    # Check for API key
    if not api_key:
        raise ValueError("API key not set.")

    # Create comprehensive security settings
    # Note: Using relative paths ("./**") restricts access to project directory
    # since cwd is set to project_dir
    security_settings = {
        "sandbox": {"enabled": True, "autoAllowBashIfSandboxed": True},
        "permissions": {
            "defaultMode": "acceptEdits",  # Auto-approve edits within allowed directories
            "allow": [
                # Allow all file operations within the project directory
                "Read(./**)",
                "Write(./**)",
                "Edit(./**)",
                "Glob(./**)",
                "Grep(./**)",
                # Bash permission granted here, but actual commands are validated
                # by the bash_security_hook (see security.py for allowed commands)
                "Bash(*)",
                "WebFetch(*)",
                "WebSearch",
                *CONTEXT7_TOOLS,
                *BROWSERMCP_TOOLS,
                # Allow Puppeteer MCP tools for browser automation
                # *PUPPETEER_TOOLS,
                *POSTGRES_TOOLS,
                # *SERENA_TOOLS,
            ],
        },
    }

    # Ensure project directory exists before creating settings file
    project_dir.mkdir(parents=True, exist_ok=True)

    # Write settings to a file in the project directory
    settings_file = project_dir / ".claude_settings.json"
    with open(settings_file, "w") as f:
        json.dump(security_settings, f, indent=2)

    print(f"Created security settings at {settings_file}")
    print("   - Sandbox enabled (OS-level bash isolation)")
    print(f"   - Filesystem restricted to: {project_dir.resolve()}")
    print("   - Bash commands restricted to allowlist (see security.py)")
    print("   - MCP servers: see tools.py")
    print()

    sdk_client = ClaudeSDKClient(
        options=ClaudeCodeOptions(
            model=model,
            system_prompt="You are an expert full-stack developer building a production-quality web application.",
            allowed_tools=[
                *BUILTIN_TOOLS,
                *CONTEXT7_TOOLS,
                *BROWSERMCP_TOOLS,
                # *PUPPETEER_TOOLS, # Problems with every time large screenshots
                *POSTGRES_TOOLS,
                # *SERENA_TOOLS,
            ],
            # Using enhanced https://github.com/sultannaufal/puppeteer-mcp-server with mouse tools that also allows configuration of screenshot quality
            mcp_servers=MCP_SERVERS,
            hooks={
                "PreToolUse": [
                    HookMatcher(matcher="Bash", hooks=[bash_security_hook]),
                ],
            },
            max_turns=1000,
            cwd=str(project_dir.resolve()),
            settings=str(settings_file.resolve()),  # Use absolute path
        )
    )
    
    return ClaudeClientWrapper(sdk_client)
