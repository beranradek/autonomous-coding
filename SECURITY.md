# Security Configuration Guide

## Environment Variables Setup

This project uses environment variables to manage sensitive credentials and configuration. **Never commit the `.env` file to version control.**

### Initial Setup

1. **Copy the example file:**
   ```bash
   cp .env-example .env
   ```

2. **Edit `.env` and fill in your actual values:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Verify `.env` is in `.gitignore`:**
   ```bash
   grep "^\.env$" .gitignore
   ```

## Required Environment Variables

### AI Provider Authentication

**For Claude SDK** (choose one):
```bash
# Option 1: OAuth token (recommended - uses your paid subscription)
CLAUDE_CODE_OAUTH_TOKEN=your-oauth-token-here

# Option 2: API key (costs money per request)
ANTHROPIC_API_KEY=your-api-key-here
```

**For GitHub Copilot CLI:**
```bash
GITHUB_TOKEN=your-github-token-here
```

### MCP Server Configuration

**PostgreSQL Database:**
```bash
# Format: postgresql://username:password@host:port/database
MCP_DATABASE_URI=postgresql://your_user:your_password@localhost:5432/your_database
```

**Browser MCP Server:**
```bash
MCP_BROWSER_URL=http://127.0.0.1:3000/mcp
```

## Security Best Practices

### ✅ DO:
- Keep `.env` file in `.gitignore`
- Use `.env-example` to document required variables (without actual values)
- Use strong, unique passwords for database connections
- Rotate credentials regularly
- Use OAuth tokens instead of API keys when possible
- Set restrictive file permissions: `chmod 600 .env`

### ❌ DON'T:
- Commit `.env` to version control
- Share `.env` file via email, chat, or screenshots
- Use default passwords in production
- Hardcode credentials in source code
- Use the same credentials across multiple environments

## Default Values

The application provides sensible defaults for development:

| Variable | Default Value | Security Risk |
|----------|---------------|---------------|
| `MCP_DATABASE_URI` | `postgresql://postgres:postgres@localhost:5432/artbeams` | ⚠️ **HIGH** - Default credentials |
| `MCP_BROWSER_URL` | `http://127.0.0.1:3000/mcp` | ✅ Low - Localhost only |

**⚠️ WARNING**: The default database credentials (`postgres:postgres`) are **NOT SECURE** for production use. Always set `MCP_DATABASE_URI` in your `.env` file with proper credentials.

## Checking for Exposed Secrets

Before committing code, verify no secrets are exposed:

```bash
# Check if .env is tracked by git (should return nothing)
git ls-files | grep "^\.env$"

# Search for potential hardcoded secrets
grep -r "postgresql://" --include="*.py" --exclude-dir=".venv"
grep -r "API_KEY\|TOKEN\|PASSWORD" --include="*.py" --exclude-dir=".venv"
```

## Production Deployment

For production environments:

1. **Never use default credentials**
2. **Use environment-specific `.env` files** (`.env.production`, `.env.staging`)
3. **Consider using secret management services** (AWS Secrets Manager, HashiCorp Vault, etc.)
4. **Audit access to credentials** regularly
5. **Enable database connection encryption** (SSL/TLS)

## Troubleshooting

**Environment variables not loading:**
```bash
# Verify .env file exists
ls -la .env

# Check file contents (be careful not to expose in logs)
cat .env | grep -v "^#" | grep -v "^$"

# Verify python-dotenv is installed
uv pip list | grep python-dotenv
```

**Database connection fails:**
- Verify `MCP_DATABASE_URI` format is correct
- Check database is running: `pg_isready -h localhost -p 5432`
- Verify credentials are correct
- Check firewall/network access

## Security Audit Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] No hardcoded credentials in source code
- [ ] Database uses non-default credentials
- [ ] `.env` file has restrictive permissions (600)
- [ ] Credentials are documented in `.env-example` (without actual values)
- [ ] Team members know not to commit `.env`
- [ ] Production uses separate credentials from development
