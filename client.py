"""
Claude SDK Client Configuration
===============================

Functions for creating and configuring the Claude Agent SDK client.
"""

import json
import os
from pathlib import Path

from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient
from claude_code_sdk.types import HookMatcher

from security import bash_security_hook
from subscription import api_key

CONTEXT7_TOOLS = [
    "mcp__context7__resolve-library-id",
    "mcp__context7__get-library-docs",
]

BROWSERMCP_TOOLS = [
    "mcp__browsermcp__browser_navigate",
    "mcp__browsermcp__browser_go_back",
    "mcp__browsermcp__browser_go_forward",
    "mcp__browsermcp__browser_click",
    "mcp__browsermcp__browser_fill_form",
    "mcp__browsermcp__browser_type",
    "mcp__browsermcp__browser_execute_js",
    "mcp__browsermcp__browser_snapshot",
    "mcp__browsermcp__browser_screenshot",
    "mcp__browsermcp__browser_extract_html",
    "mcp__browsermcp__browser_select_option",
    "mcp__browsermcp__browser_press_key",
    "mcp__browsermcp__dom.click",
    "mcp__browsermcp__dom.type",
    "mcp__browsermcp__dom.hover",
    "mcp__browsermcp__dom.select",
    "mcp__browsermcp__snapshot.accessibility",
    "mcp__browsermcp__tabs.list",
    "mcp__browsermcp__tabs.select",
    "mcp__browsermcp__tabs.news",
    "mcp__browsermcp__tabs.close",
    "mcp__browsermcp__console.get",
    "mcp__browsermcp__screenshot.capture",
    "mcp__browsermcp__js.execute",
]

# Puppeteer MCP tools for browser automation
PUPPETEER_TOOLS = [
    "mcp__puppeteer__puppeteer_navigate",
    "mcp__puppeteer__puppeteer_screenshot",
    "mcp__puppeteer__puppeteer_click",
    "mcp__puppeteer__puppeteer_fill",
    "mcp__puppeteer__puppeteer_select",
    "mcp__puppeteer__puppeteer_hover",
    "mcp__puppeteer__puppeteer_evaluate",
    "mcp__puppeteer__puppeteer_connect_active_tab",
    "mcp__puppeteer__puppeteer_mouse_move",
    "mcp__puppeteer__puppeteer_mouse_click",
    "mcp__puppeteer__puppeteer_mouse_down",
    "mcp__puppeteer__puppeteer_mouse_up",
    "mcp__puppeteer__puppeteer_mouse_wheel",
    "mcp__puppeteer__puppeteer_mouse_drag",
    "mcp__puppeteer__puppeteer_get_cookies",
    "mcp__puppeteer__puppeteer_set_cookies",
    "mcp__puppeteer__puppeteer_delete_cookies",
]

POSTGRES_TOOLS = [
    "mcp__postgres__list_schemas",
    "mcp__postgres__list_objects",
    "mcp__postgres__get_object_details",
    "mcp__postgres__execute_sql",
    "mcp__postgres__explain_query",
    "mcp__postgres__get_top_queries",
    "mcp__postgres__analyze_workload_indexes",
    "mcp__postgres__analyze_query_indexes",
    "mcp__postgres__analyze_db_health",
]

# Serena MCP tools
SERENA_TOOLS = [
    "mcp__serena__find_file",
    "mcp__serena__think_about_collected_information",
    "mcp__serena__search_for_pattern",
    "mcp__serena__find_symbol",
    "mcp__serena__get_symbols_overview",
    "mcp__serena__replace_symbol_body",
    "mcp__serena__insert_before_symbol",
    "mcp__serena__list_dir",
    "mcp__serena__find_referencing_symbols",
]

# Built-in tools
BUILTIN_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash",
]


def create_client(project_dir: Path, model: str) -> ClaudeSDKClient:
    """
    Create a Claude Agent SDK client with multi-layered security.

    Args:
        project_dir: Directory for the project
        model: Claude model to use

    Returns:
        Configured ClaudeSDKClient

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
    print("   - MCP servers: see client.py")
    print()

    return ClaudeSDKClient(
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
            mcp_servers={
                "context7": {"command": "npx", "args": ["-y", "@upstash/context7-mcp@latest"]},
                # "puppeteer": {"command": "npx", "args": ["puppeteer-mcp-server"], "env": {"SCREENSHOT_QUALITY": "60","SCREENSHOT_DEFAULT_WIDTH": "800","SCREENSHOT_DEFAULT_HEIGHT": "600","SCREENSHOT_MAX_WIDTH": "1280","SCREENSHOT_MAX_HEIGHT": "800"}},
                # Browser MCP enhanced by D. Strejc:
                "browsermcp": {"type": "http", "url": "http://127.0.0.1:3000/mcp"},
                "postgres": {"command": "uv","args": ["run","postgres-mcp","--access-mode=unrestricted"],"env": {"DATABASE_URI": "postgresql://postgres:postgres@localhost:5432/artbeams"}},
            },
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
