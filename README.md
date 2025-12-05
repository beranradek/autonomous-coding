# Harness for long-running autonomous AI coding

A minimal harness demonstrating long-running autonomous coding with the Claude Agent SDK. This demo implements a two-agent pattern (initializer + coding agent) that can:
- Build complete applications from scratch (greenfield mode)
- Add features to existing projects (enhancement mode)
- Work across multiple long-running sessions

## Prerequisites

**Required:** Install the latest versions of both Claude Code and the Claude Agent SDK:

```bash
# Install Claude Code CLI (latest version required)
npm install -g @anthropic-ai/claude-code

# Install Python dependencies
python -m venv .venv
source .venv/bin/activate # or for Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Verify your installations:
```bash
claude --version  # Should be latest version
pip show claude-code-sdk  # Check SDK is installed
```

**API Key:** Set your Anthropic API key (but this can cost lot of money for long runs, rather set CLAUDE_CODE_OAUTH_TOKEN leveraging your regular paid subscription - see instructions in subscription.py):
```bash
# export ANTHROPIC_API_KEY='your-api-key-here'
export CLAUDE_CODE_OAUTH_TOKEN='your-api-key-here'
```

**Prepare your application specification in prompts/app_spec.txt:**
- See `GENERATING_APP_SPEC.md` for detailed guidance
- Use `prompts/app_spec_generator_prompt.md` with an AI assistant to generate specifications
- Or copy and modify `prompts/app_spec_example.txt`

## Quick Start

### For New Projects (Greenfield Mode)

```bash
# Auto-detected - creates new project from scratch
python autonomous_agent.py --project-dir ./my_new_project

# Or explicitly specify greenfield mode
python autonomous_agent.py --project-dir ./my_new_project --mode greenfield
```

### For Existing Projects (Enhancement Mode)

```bash
# Auto-detected if .git directory exists
# You can point to any existing project with an absolute path that can be outside of this repo
python autonomous_agent.py --project-dir ./my_existing_project

# Or explicitly specify enhancement mode
python autonomous_agent.py --project-dir ./my_existing_project --mode enhancement
```

### Testing with Limited Iterations

```bash
python autonomous_agent.py --project-dir ./my_project --max-iterations 3
```

## Important Timing Expectations

> **Warning: This demo takes a long time to run!**

- **First session (initialization):** The agent generates a `feature_list.json` with 200 test cases. This takes several minutes and may appear to hang - this is normal. The agent is writing out all the features.

- **Subsequent sessions:** Each coding iteration can take **5-15 minutes** depending on complexity.

- **Full app:** Building all 200 features typically requires **many hours** of total runtime across multiple sessions.

**Tip:** The 200 features parameter in the prompts is designed for comprehensive coverage. If you want faster demos, you can modify `prompts/initializer_prompt.md` to reduce the feature count (e.g., 20-50 features for a quicker demo).

## How It Works

### Two-Agent Pattern with Dual Modes

The harness supports two modes of operation:

#### Greenfield Mode (New Projects)

1. **Greenfield Initializer Agent (Session 1):**
   - Reads `app_spec.txt`
   - Creates `feature_list.json` with 200 test cases
   - Sets up project structure from scratch
   - Initializes git repository
   - Creates `init.sh` for environment setup

2. **Coding Agent (Sessions 2+):**
   - Picks up where the previous session left off
   - Implements features one by one
   - Marks them as passing in `feature_list.json`

#### Enhancement Mode (Existing Projects)

1. **Enhancement Initializer Agent (Session 1):**
   - Analyzes existing codebase structure
   - Reads `app_spec.txt` (defines NEW features to add)
   - Creates `feature_list.json` with test cases for NEW features only
   - Creates/updates `init.sh` if needed
   - Creates `agent_progress.txt` with codebase analysis
   - Does NOT reinitialize git (preserves existing repository)

2. **Coding Agent (Sessions 2+):**
   - Same as greenfield mode
   - Adds new features to existing codebase
   - Respects existing architecture and patterns

### Session Management

- Each session runs with a fresh context window
- Progress is persisted via `feature_list.json` and git commits
- The agent auto-continues between sessions (3 second delay)
- Press `Ctrl+C` to pause; run the same command to resume

## Security Model

This demo uses a defense-in-depth security approach (see `security.py` and `client.py`):

1. **OS-level Sandbox:** Bash commands run in an isolated environment
2. **Filesystem Restrictions:** File operations restricted to the project directory only
3. **Bash Allowlist:** Only specific commands are permitted:
   - File inspection: `ls`, `cat`, `head`, `tail`, `wc`, `grep`
   - Node.js: `npm`, `node`
   - Version control: `git`
   - Process management: `ps`, `lsof`, `sleep`, `pkill` (dev processes only)

Commands not in the allowlist are blocked by the security hook.

## Project Structure

```
autonomous-coding/
├── autonomous_agent.py       # Main entry point
├── agent.py                  # Agent session logic
├── client.py                 # Claude SDK client configuration
├── security.py               # Bash command allowlist and validation
├── progress.py               # Progress tracking utilities
├── prompts.py                # Prompt loading utilities
├── prompts/
│   ├── app_spec.txt                    # Application specification (greenfield)
│   ├── initializer_prompt.md           # Greenfield first session prompt
│   ├── enhancement_initializer_prompt.md # Enhancement first session prompt
│   └── coding_prompt.md                # Continuation session prompt
└── requirements.txt          # Python dependencies
```

## Generated Project Structure

After running, your project directory will contain:

```
my_project/
├── feature_list.json         # Test cases (source of truth)
├── app_spec.txt              # Copied specification
├── init.sh                   # Environment setup script
├── agent_progress.txt        # Session progress notes
├── .claude_settings.json     # Security settings
└── [application files]       # Generated application code
```

## Running the Generated Application

After the agent completes (or pauses), you can run the generated application:

```bash
cd generations/my_project

# Run the setup script created by the agent
./init.sh

# Or manually (typical for Node.js apps):
npm install
npm run dev
```

The application will typically be available at `http://localhost:3000` or similar (check the agent's output or `init.sh` for the exact URL).

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir` | Directory for the project | `./autonomous_demo_project` |
| `--max-iterations` | Max agent iterations | Unlimited |
| `--model` | Claude model to use | `claude-sonnet-4-5-20250929` |
| `--mode` | Mode: `auto`, `greenfield`, or `enhancement` | `auto` (auto-detect) |

### Mode Selection

- **`auto`** (default): Automatically detects mode based on project state
  - If `.git` exists but no `feature_list.json` → Enhancement mode
  - If neither exists → Greenfield mode
  - If `feature_list.json` exists → Continue mode
- **`greenfield`**: Force creation of new project from scratch
- **`enhancement`**: Force enhancement mode for existing projects

## Enhancement Mode Workflow

Here's a complete example of adding features to an existing project:

### Step 1: Prepare Your Project

```bash
# If you have an existing project
cd /path/to/your/existing/project

# Ensure it has a git repository
git status  # Should show it's a git repo

# Create an app_spec.txt describing NEW features
cat > app_spec.txt << 'EOF'
# New Features for My Existing App

## Feature: Dark Mode Toggle
Add a dark mode theme toggle that persists user preference...

## Feature: Export to PDF
Add ability to export reports as PDF files...

[Describe all new features you want to add]
EOF
```

### Step 2: Run the Enhancement Agent

```bash
# From the autonomous-coding directory
python autonomous_agent.py --project-dir /path/to/your/existing/project --mode enhancement
```

### Step 3: What Happens

1. **Session 1 (Enhancement Initializer):**
   - Agent analyzes your existing codebase
   - Creates `feature_list.json` with tests for NEW features only
   - Creates `agent_progress.txt` with codebase analysis
   - May start implementing first features

2. **Session 2+ (Coding Agent):**
   - Continues adding features from `feature_list.json`
   - Respects your existing architecture
   - Commits progress regularly

### Step 4: Monitor Progress

The agent will:
- Leave your existing code intact
- Add new features incrementally
- Update `feature_list.json` as features pass
- Can be paused with `Ctrl+C` and resumed anytime

### Important Notes for Enhancement Mode

- **Existing files are preserved** unless they need modification for new features
- **Git history is preserved** - agent adds commits, doesn't reinitialize
- **Architecture is respected** - agent analyzes and follows your patterns
- **init.sh is updated** if needed for new dependencies
- **Specify feature count** in your app_spec.txt (e.g., "create 50 features" or "create 20 features")

## Customization

### Changing the Application (Greenfield Mode)

Edit `prompts/app_spec.txt` to specify a different application to build from scratch.

### Adding Features to Existing Project (Enhancement Mode)

1. Copy your existing project to a directory (or use an existing one)
2. Create `app_spec.txt` in your project directory describing the NEW features to add
3. Run: `python autonomous_agent.py --project-dir ./your_project --mode enhancement`

**Important:** In enhancement mode, `app_spec.txt` should describe ONLY the new features you want to add, not the entire application.

### Adjusting Feature Count

- **Greenfield:** Edit `prompts/initializer_prompt.md` and change the "200 features" requirement
- **Enhancement:** Edit `prompts/enhancement_initializer_prompt.md` or specify the desired count in your `app_spec.txt`

For faster demos, use a smaller number (e.g., 20-50 features).

### Modifying Allowed Commands

Edit `security.py` to add or remove commands from `ALLOWED_COMMANDS`.

## Troubleshooting

**"Appears to hang on first run"**
This is normal. The initializer agent is generating 200 detailed test cases, which takes significant time. Watch for `[Tool: ...]` output to confirm the agent is working.

**"Command blocked by security hook"**
The agent tried to run a command not in the allowlist. This is the security system working as intended. If needed, add the command to `ALLOWED_COMMANDS` in `security.py`.

**"MCP error -32603: Failed to launch the browser process"**
No usable sandbox! If you are running on Ubuntu 23.10+ or another Linux distro that has disabled unprivileged user namespaces with AppArmor, see https://chromium.googlesource.com/chromium/src/+/main/docs/security/apparmor-userns-restrictions.md. Otherwise see https://chromium.googlesource.com/chromium/src/+/main/docs/linux/suid_sandbox_development.md for more information.

If you have Google Chrome installed, easiest and safest way is to
use setuid sandbox helper (the old version of the sandbox) available at /opt/google/chrome/chrome-sandbox. You can tell developer builds to use it by putting the following in your ~/.bashrc:

`export CHROME_DEVEL_SANDBOX=/opt/google/chrome/chrome-sandbox`
