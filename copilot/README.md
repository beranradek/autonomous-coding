# GitHub Copilot CLI Configuration

This directory contains configuration files and documentation for using GitHub Copilot CLI with the autonomous coding agent.

## MCP Server Configuration

GitHub Copilot CLI MCP servers are automatically configured at the **project level** for this autonomous coding agent.

### Automatic Configuration

When you run the agent with `--cli copilot`, it automatically:

1. Creates a `.copilot/` directory in your project
2. Generates `mcp-config.json` with the same MCP servers as Claude SDK
3. Sets `XDG_CONFIG_HOME` to use the project-level configuration

This means **each project has its own MCP configuration**, and you don't need to manually configure anything in `~/.copilot/`.

### Customizing MCP Configuration

To customize MCP servers for a specific project:

1. Edit `<project_dir>/.copilot/mcp-config.json`
2. Modify server settings (database URIs, ports, etc.)
3. The changes will be used automatically on the next run

## Trusted Directories

The autonomous coding agent **automatically trusts the project directory** using the `--add-dir` flag when running Copilot CLI.

This means:
- ✅ No manual trust confirmation needed
- ✅ Copilot can immediately work with files in the project directory
- ✅ Fully autonomous operation from the first run

The project directory is added as a trusted directory with each Copilot CLI invocation, so you never need to manually configure this.

## Autonomous Operation

The autonomous coding agent uses the `--allow-all-tools` flag when running Copilot CLI. This means:

- **No manual confirmations required**: Copilot can execute any tool without asking
- **Full file access**: Copilot can read, modify, and execute files in the project directory
- **Shell command execution**: Copilot can run any shell command

> **Security Note**: This is similar to the Claude SDK sandbox mode. The agent has full access within the project directory but is isolated from the rest of your system.

## Available MCP Servers

The auto-generated configuration includes the same MCP servers as Claude SDK (defined in `tools.py`):

- **context7**: Library documentation lookup
- **browsermcp**: Browser automation (requires HTTP server running on port 3000)
- **postgres**: Database operations (requires PostgreSQL connection)

To see the exact configuration, check `<project_dir>/.copilot/mcp-config.json` after the first run.

## Environment Variables

Copilot CLI needs access to GitHub authentication. Ensure you have:

```bash
# GitHub token for Copilot access
export GITHUB_TOKEN="your-github-token"

# Or use GitHub CLI authentication
gh auth login
```

The autonomous agent automatically passes all system environment variables to the Copilot CLI subprocess.
