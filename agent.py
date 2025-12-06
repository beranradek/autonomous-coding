"""
Agent Session Logic
===================

Core agent interaction functions for running autonomous coding sessions.
"""

import asyncio
from pathlib import Path
from typing import Optional

from claude_code_sdk import ClaudeSDKClient

from client import create_client
from progress import print_session_header, print_progress_summary
from prompts import (
    get_initializer_prompt,
    get_coding_prompt,
    get_enhancement_initializer_prompt,
    copy_spec_to_project,
    copy_or_verify_spec,
)


# Configuration
AUTO_CONTINUE_DELAY_SECONDS = 3


async def run_agent_session(
    client: ClaudeSDKClient,
    message: str,
    project_dir: Path,
    previous_error: Optional[str] = None,
) -> tuple[str, str]:
    """
    Run a single agent session using Claude Agent SDK.

    Args:
        client: Claude SDK client
        message: The prompt to send
        project_dir: Project directory path
        previous_error: Optional error message from previous session to inform the agent

    Returns:
        (status, response_text) where status is:
        - "continue" if agent should continue working
        - "error" if an error occurred
        - "large_response_error" if a response exceeded buffer limits
    """
    print("Sending prompt to Claude Agent SDK...\n")

    # If there was a previous error, prepend it to the message so the agent knows
    if previous_error:
        error_context = f"""
IMPORTANT: The previous session encountered an error. You must adapt your approach to avoid repeating this error.

Previous Error:
{previous_error}

Action Required:
- DO NOT repeat the exact same action that caused this error
- If the error was from a screenshot being too large, use different screenshot settings (smaller dimensions, lower quality) or skip screenshots
- If the error was from a tool response being too large, use different tool parameters to get smaller responses
- Acknowledge this error and explain your adapted approach before proceeding

Continue with your task, taking this error into account:

"""
        message = error_context + message

    try:
        # Send the query
        await client.query(message)

        # Collect response text and show tool use
        response_text = ""
        last_tool_name = None  # Track the last tool that was called

        try:
            async for msg in client.receive_response():
                msg_type = type(msg).__name__

                # Handle AssistantMessage (text and tool use)
                if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        block_type = type(block).__name__

                        if block_type == "TextBlock" and hasattr(block, "text"):
                            response_text += block.text
                            print(block.text, end="", flush=True)
                        elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                            last_tool_name = block.name  # Track tool name
                            print(f"\n[Tool: {block.name}]", flush=True)
                            if hasattr(block, "input"):
                                input_str = str(block.input)
                                if len(input_str) > 200:
                                    print(f"   Input: {input_str[:200]}...", flush=True)
                                else:
                                    print(f"   Input: {input_str}", flush=True)

                # Handle UserMessage (tool results)
                elif msg_type == "UserMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        block_type = type(block).__name__

                        if block_type == "ToolResultBlock":
                            result_content = getattr(block, "content", "")
                            is_error = getattr(block, "is_error", False)

                            # Check if command was blocked by security hook
                            if "blocked" in str(result_content).lower():
                                print(f"   [BLOCKED] {result_content}", flush=True)
                            elif is_error:
                                # Show errors (truncated)
                                error_str = str(result_content)[:500]
                                print(f"   [Error] {error_str}", flush=True)
                            else:
                                # Tool succeeded - just show brief confirmation
                                print("   [Done]", flush=True)

        except Exception as stream_error:
            # Handle errors that occur during message streaming
            error_msg = str(stream_error)

            # Check if this is a buffer overflow error from the SDK
            if "JSON message exceeded maximum buffer size" in error_msg or "Failed to decode JSON" in error_msg:
                print(f"\n⚠️  Large Response Error: Tool response exceeded 1MB buffer size")
                tool_info = f" (from tool: {last_tool_name})" if last_tool_name else ""
                detailed_error = (
                    f"Tool response exceeded 1MB buffer size{tool_info}. "
                    "This typically happens with screenshots that are too large. "
                    "To avoid this error: (1) skip taking screenshots and focus on functional testing, "
                    "or (2) if screenshots are essential, the page content may be too large to capture."
                )
                return "large_response_error", detailed_error

            # Re-raise other streaming errors
            raise

        print("\n" + "-" * 70 + "\n")
        return "continue", response_text

    except Exception as e:
        error_msg = str(e)

        # Handle other errors
        print(f"Error during agent session: {e}")
        return "error", error_msg


async def run_autonomous_agent(
    project_dir: Path,
    model: str,
    max_iterations: Optional[int] = None,
    mode: str = "auto",
) -> None:
    """
    Run the autonomous agent loop.

    Args:
        project_dir: Directory for the project
        model: Claude model to use
        max_iterations: Maximum number of iterations (None for unlimited)
        mode: Mode selection - "auto", "greenfield", or "enhancement"
    """
    print("\n" + "=" * 70)
    print("  AUTONOMOUS CODING AGENT")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print(f"Model: {model}")
    if max_iterations:
        print(f"Max iterations: {max_iterations}")
    else:
        print("Max iterations: Unlimited (will run until completion)")
    print()

    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=True)

    # Check what exists in the project
    tests_file = project_dir / "feature_list.json"
    progress_file = project_dir / "agent_progress.txt"
    spec_file = project_dir / "app_spec.txt"
    git_dir = project_dir / ".git"

    has_git = git_dir.exists()
    has_features = tests_file.exists()
    has_progress = progress_file.exists()

    # Determine run mode
    if mode == "auto":
        # Auto-detect based on what exists
        if not has_features and not has_progress:
            # No harness files exist
            if has_git:
                run_mode = "enhancement_init"
                print("Existing project detected (has .git) - will use enhancement initializer")
            else:
                run_mode = "greenfield_init"
                print("Fresh start - will use greenfield initializer")
        else:
            # Harness files exist - continue mode
            run_mode = "continue"
            print("Continuing existing autonomous session")
            print_progress_summary(project_dir)
    elif mode == "greenfield":
        run_mode = "greenfield_init"
        print("Greenfield mode - will create new project from scratch")
    elif mode == "enhancement":
        run_mode = "enhancement_init"
        print("Enhancement mode - will add features to existing project")
    else:
        raise ValueError(f"Invalid mode: {mode}")

    # Handle spec file based on mode
    if run_mode == "greenfield_init":
        print()
        print("=" * 70)
        print("  NOTE: First session can take 10-20+ minutes!")
        print("  The agent is generating detailed test cases.")
        print("  This may appear to hang - it's working. Watch for [Tool: ...] output.")
        print("=" * 70)
        print()
        copy_spec_to_project(project_dir)
    elif run_mode == "enhancement_init":
        print()
        print("=" * 70)
        print("  NOTE: Enhancement initialization may take 10-20+ minutes!")
        print("  The agent is analyzing your codebase and generating test cases.")
        print("  This may appear to hang - it's working. Watch for [Tool: ...] output.")
        print("=" * 70)
        print()
        copy_or_verify_spec(project_dir)

    # Main loop
    iteration = 0
    last_error = None  # Track errors to pass to next session

    while True:
        iteration += 1

        # Check max iterations
        if max_iterations and iteration > max_iterations:
            print(f"\nReached max iterations ({max_iterations})")
            print("To continue, run the script again without --max-iterations")
            break

        # Print session header
        is_initializer = run_mode in ["greenfield_init", "enhancement_init"]
        print_session_header(iteration, is_initializer)

        # Create client (fresh context)
        client = create_client(project_dir, model)

        # Choose prompt based on run mode
        if run_mode == "greenfield_init":
            prompt = get_initializer_prompt()
            run_mode = "continue"  # Switch to continue mode after first session
        elif run_mode == "enhancement_init":
            prompt = get_enhancement_initializer_prompt()
            run_mode = "continue"  # Switch to continue mode after first session
        else:
            prompt = get_coding_prompt()

        # Run session with async context manager, passing any error from previous session
        async with client:
            status, response = await run_agent_session(client, prompt, project_dir, previous_error=last_error)

        # Handle status
        if status == "continue":
            last_error = None  # Clear error on success
            print(f"\nAgent will auto-continue in {AUTO_CONTINUE_DELAY_SECONDS}s...")
            print_progress_summary(project_dir)
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        elif status == "large_response_error":
            print("\n⚠️  Continuing with error context...")
            print("The agent will be informed about the error and adapt its approach...\n")
            last_error = response  # Save error details to pass to next session
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        elif status == "error":
            print("\nSession encountered an error")
            print("The agent will be informed and retry with adapted approach...")
            last_error = response  # Save error details to pass to next session
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        # Small delay between sessions
        if max_iterations is None or iteration < max_iterations:
            print("\nPreparing next session...\n")
            await asyncio.sleep(1)

    # Final summary
    print("\n" + "=" * 70)
    print("  SESSION COMPLETE")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print_progress_summary(project_dir)

    # Print instructions for running the generated application
    print("\n" + "-" * 70)
    print("  TO RUN THE GENERATED APPLICATION:")
    print("-" * 70)
    print(f"\n  cd {project_dir.resolve()}")
    print("  ./init.sh           # Check and then run the setup script")
    print("-" * 70)

    print("\nDone!")
