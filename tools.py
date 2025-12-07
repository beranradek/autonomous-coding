"""
Tools Configuration
===================

Shared configuration for MCP tools and servers used by AI coding agents.
This module provides reusable tool definitions that can be used by different
client implementations (Claude SDK, Copilot CLI, etc.).
"""

import os

# Context7 MCP tools for library documentation
CONTEXT7_TOOLS = [
    "mcp__context7__resolve-library-id",
    "mcp__context7__get-library-docs",
]

# BrowserMCP tools for browser automation
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
    "mcp__browsermcp__browser_tab",
    "mcp__browsermcp__browser_scroll",
    "mcp__browsermcp__browser_get_console_logs",
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

# Postgres MCP tools for database operations
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

# Serena MCP tools for code analysis
SERENA_TOOLS = [
    "mcp__serena__find_file",
    "mcp__serena__think_about_collected_information",
    "mcp__serena__search_for_pattern",
    "mcp__serena__find_symbol",
    "mcp__serena__get_symbols_overview",
    "mcp__serena__replace_symbol_body",
    "mcp__serena__insert_before_symbol",
    "mcp__serena__insert_after_symbol",
    "mcp__serena__list_dir",
    "mcp__serena__find_referencing_symbols",
]

# Built-in tools available in Claude SDK
BUILTIN_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash",
]

# MCP server configurations
# Note: For Claude SDK, these are passed programmatically
# For Copilot CLI, these should be configured in ~/.copilot/mcp-config.json
MCP_SERVERS = {
    "context7": {
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp@latest"]
    },
    # Puppeteer with custom screenshot settings (currently disabled due to large screenshots)
    # "puppeteer": {
    #     "command": "npx",
    #     "args": ["puppeteer-mcp-server"],
    #     "env": {
    #         "SCREENSHOT_QUALITY": os.getenv("SCREENSHOT_QUALITY", "60"),
    #         "SCREENSHOT_DEFAULT_WIDTH": os.getenv("SCREENSHOT_DEFAULT_WIDTH", "800"),
    #         "SCREENSHOT_DEFAULT_HEIGHT": os.getenv("SCREENSHOT_DEFAULT_HEIGHT", "600"),
    #         "SCREENSHOT_MAX_WIDTH": os.getenv("SCREENSHOT_MAX_WIDTH", "1280"),
    #         "SCREENSHOT_MAX_HEIGHT": os.getenv("SCREENSHOT_MAX_HEIGHT", "800")
    #     }
    # },
    # Browser MCP enhanced by D. Strejc (HTTP server)
    "browsermcp": {
        "type": "http",
        "url": os.getenv("MCP_BROWSER_URL", "http://127.0.0.1:3000/mcp")
    },
    # Postgres MCP for database operations
    "postgres": {
        "command": "uv",
        "args": ["run", "postgres-mcp", "--access-mode=unrestricted"],
        "env": {
            "DATABASE_URI": os.getenv("MCP_DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/artbeams")
        }
    },
}
