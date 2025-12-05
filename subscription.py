"""
API key to use for autonomous coding
====================================
"""

import os

# Regular API key would consume a lot of money
# api_key = os.environ.get("ANTHROPIC_API_KEY")
# if not api_key:
#     raise ValueError(
#         "ANTHROPIC_API_KEY environment variable not set.\n"
#         "Get your API key from: https://console.anthropic.com/"
#     )

# Let's use OAuth token generated for Pro/Max subscription
api_key = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
if not api_key:
    print("Error: CLAUDE_CODE_OAUTH_TOKEN environment variable not set")
    print("\nGet your API key from running `claude setup-token` after installing the Claude Code CLI.")
    print("\nThen set it:")
    print("\n  export CLAUDE_CODE_OAUTH_TOKEN=...")
