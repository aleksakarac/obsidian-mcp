# Clean Installation Guide

This guide will completely remove all existing installations and reinstall the MCP server fresh from GitHub.

---

## Step 1: Remove All Existing Installations

### 1.1 Backup Current Config
```bash
# Backup Claude Code config
cp ~/.config/claude/claude_desktop_config.json ~/.config/claude/claude_desktop_config.json.backup-$(date +%Y%m%d)
```

### 1.2 Remove MCP Server from Claude Config
```bash
# Clear the MCP server config (we'll add it back later)
cat > ~/.config/claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {}
}
EOF
```

### 1.3 Uninstall Global obsidian-mcp Tool
```bash
# Remove globally installed tool
uv tool uninstall obsidian-mcp-extended 2>/dev/null || true
uv tool uninstall obsidian-mcp 2>/dev/null || true

# Verify it's gone
which obsidian-mcp  # Should return nothing
```

### 1.4 Clean Project Directory (Optional)
```bash
cd /home/aleksa/Documents/Projects/CustomObsidianMcp

# Remove virtual environment and build artifacts
rm -rf .venv/
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
rm -rf __pycache__/
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```

---

## Step 2: Fresh Installation from GitHub

### 2.1 Pull Latest Changes
```bash
cd /home/aleksa/Documents/Projects/CustomObsidianMcp
git pull origin main
```

### 2.2 Install Using uv (Recommended Method)
```bash
# Create fresh virtual environment
uv venv

# Install the package
uv pip install -e .

# Verify installation
uv run obsidian-mcp --help
```

**Expected output:**
```
Usage: obsidian-mcp [OPTIONS]
...
```

---

## Step 3: Configure Claude Code

### 3.1 Get Your Obsidian API Key

1. Open Obsidian
2. Go to: **Settings → Community Plugins → Local REST API**
3. Copy the **API Key** (or generate a new one)
4. Note the **Port** (should be 27124)
5. **Important**: Check if HTTPS is enabled:
   - If "Enable HTTPS" is ON → Use `https://127.0.0.1:27124`
   - If "Enable HTTPS" is OFF → Use `http://localhost:27124`

### 3.2 Update Claude Config

**Create the correct config:**

```bash
cat > ~/.config/claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "obsidian": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/aleksa/Documents/Projects/CustomObsidianMcp",
        "run",
        "obsidian-mcp"
      ],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/home/aleksa/Obsidian/",
        "OBSIDIAN_REST_API_KEY": "PASTE_YOUR_API_KEY_HERE",
        "OBSIDIAN_API_URL": "https://127.0.0.1:27124"
      }
    }
  }
}
EOF
```

**Then edit the file to add your actual API key:**

```bash
# Edit the config file
nano ~/.config/claude/claude_desktop_config.json

# Replace "PASTE_YOUR_API_KEY_HERE" with your actual API key from Obsidian
# Save and exit (Ctrl+X, Y, Enter)
```

---

## Step 4: Verify Installation

### 4.1 Test MCP Server Directly
```bash
cd /home/aleksa/Documents/Projects/CustomObsidianMcp

# Test with environment variables
OBSIDIAN_VAULT_PATH="/home/aleksa/Obsidian/" \
OBSIDIAN_API_URL="https://127.0.0.1:27124" \
OBSIDIAN_REST_API_KEY="YOUR_KEY_HERE" \
uv run python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.utils.obsidian_api_client import ObsidianAPIClient

async def test():
    client = ObsidianAPIClient()
    print(f'✓ API URL: {client.base_url}')
    print(f'✓ API Key present: {bool(client.api_key)}')
    is_available = await client.is_available()
    print(f'✓ API Available: {is_available}')

asyncio.run(test())
"
```

**Expected output:**
```
✓ API URL: https://127.0.0.1:27124
✓ API Key present: True
✓ API Available: True
```

### 4.2 Test API Directly with curl
```bash
# Replace YOUR_KEY_HERE with your actual API key
curl -k -H "Authorization: Bearer YOUR_KEY_HERE" https://127.0.0.1:27124/vault/
```

**Expected output:**
```json
{
  "files": [
    "folder1/",
    "folder2/",
    ...
  ]
}
```

---

## Step 5: Restart Claude CLI and Test

### 5.1 Restart Claude CLI
```bash
# Exit current session (Ctrl+D or type 'exit')
# Start new session
claude
```

### 5.2 Verify MCP Server is Loaded
In Claude CLI, type: `/mcp`

**Expected output:**
```
Obsidian MCP Server
Status: ✔ connected
Command: uv
Args: --directory /home/aleksa/Documents/Projects/CustomObsidianMcp run obsidian-mcp
Tools: 63 tools
```

### 5.3 Test Filesystem Tool (Should Always Work)
```
Ask Claude: "Use the vault_statistics_fs_tool to analyze my Obsidian vault"
```

**Expected result:** Vault statistics returned successfully

### 5.4 Test API Tool (Requires Obsidian Running)
```
Ask Claude: "Use the create_note_tool to create a note called 'Installation Test.md' with content '# Test\n\nInstallation successful!'"
```

**Expected result:** Note created successfully

---

## Troubleshooting

### Issue: `uv: command not found`
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart shell
source ~/.bashrc
```

### Issue: API tools still fail with 401
**Check:**
1. Is Obsidian running? `pgrep -f obsidian`
2. Is Local REST API plugin enabled?
3. Is the API key correct? (regenerate in plugin settings)
4. Does curl work? (see Step 4.2)
5. Is the URL correct? (http vs https)

**Debug:**
```bash
# Check if API is listening
ss -tlnp | grep 27124

# Test API with verbose output
curl -v -k -H "Authorization: Bearer YOUR_KEY_HERE" https://127.0.0.1:27124/vault/
```

### Issue: Environment variables not reaching MCP server

If the config's `env` section doesn't work, use the wrapper script approach:

```bash
# Create wrapper script
cat > /home/aleksa/Documents/Projects/CustomObsidianMcp/run-with-env.sh << 'EOF'
#!/bin/bash
export OBSIDIAN_VAULT_PATH="/home/aleksa/Obsidian/"
export OBSIDIAN_API_URL="https://127.0.0.1:27124"
export OBSIDIAN_REST_API_KEY="YOUR_KEY_HERE"
cd /home/aleksa/Documents/Projects/CustomObsidianMcp
exec uv run obsidian-mcp "$@"
EOF

chmod +x /home/aleksa/Documents/Projects/CustomObsidianMcp/run-with-env.sh

# Update config to use wrapper:
cat > ~/.config/claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "obsidian": {
      "command": "/home/aleksa/Documents/Projects/CustomObsidianMcp/run-with-env.sh",
      "args": []
    }
  }
}
EOF
```

### Issue: MCP server not connecting

**Check logs:**
```bash
# Claude CLI debug mode
claude --debug

# Check system logs
journalctl --user -n 100 | grep -i claude
```

---

## Success Criteria

After following this guide, you should have:

- ✅ Clean installation from GitHub
- ✅ Proper configuration in `~/.config/claude/claude_desktop_config.json`
- ✅ MCP server connecting in Claude CLI
- ✅ Filesystem tools working (33 tools)
- ✅ API tools working when Obsidian is running (12 tools)
- ✅ Clear error messages when things go wrong

---

## Quick Command Summary

```bash
# Complete clean installation (copy/paste this whole block)
cd /home/aleksa/Documents/Projects/CustomObsidianMcp
git pull origin main
rm -rf .venv/ build/ dist/ *.egg-info/
uv venv
uv pip install -e .
uv run obsidian-mcp --help

# Then configure ~/.config/claude/claude_desktop_config.json
# Then restart Claude CLI
```

---

**Ready to start? Begin with Step 1!**
