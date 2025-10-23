# Test: Are Environment Variables Visible?

**Purpose:** Determine if Claude CLI can see the environment variables from ~/.bashrc

---

## Quick Test

**In your Claude CLI session, ask it:**

```
What are the values of these environment variables:
- OBSIDIAN_VAULT_PATH
- OBSIDIAN_API_URL
- OBSIDIAN_REST_API_KEY (first 8 characters only)
```

---

## Expected Results

### ✅ If Environment Variables ARE Loaded:
```
OBSIDIAN_VAULT_PATH: /home/aleksa/Obsidian/
OBSIDIAN_API_URL: https://127.0.0.1:27124
OBSIDIAN_REST_API_KEY: e16ee5b5...
```

**Then the issue is with how the MCP server accesses them.**

### ❌ If Environment Variables Are NOT Loaded:
```
OBSIDIAN_VAULT_PATH: (empty or not set)
OBSIDIAN_API_URL: (empty or not set)
OBSIDIAN_REST_API_KEY: (empty or not set)
```

**Then you need to:**
1. Close Claude CLI completely (exit)
2. Close your terminal
3. Open a BRAND NEW terminal
4. Run: `echo $OBSIDIAN_REST_API_KEY` to verify
5. Start Claude CLI: `claude`

---

## Alternative: Manual Export Before Starting Claude

If closing/reopening terminals doesn't work, try this:

```bash
# In your terminal (NOT in Claude CLI), run:
export OBSIDIAN_VAULT_PATH="/home/aleksa/Obsidian/"
export OBSIDIAN_API_URL="https://127.0.0.1:27124"
export OBSIDIAN_REST_API_KEY="e16ee5b59a739c4f1800b1ddcf6084ed72601170bd2eeedb8b060898dbf7c980"

# Verify:
echo $OBSIDIAN_REST_API_KEY

# Then start Claude CLI:
claude
```

---

## Nuclear Option: Config File with Absolute Path to Script

If environment variables still don't work, create this startup script:

**File:** `/home/aleksa/start-claude-with-obsidian.sh`
```bash
#!/bin/bash
export OBSIDIAN_VAULT_PATH="/home/aleksa/Obsidian/"
export OBSIDIAN_API_URL="https://127.0.0.1:27124"
export OBSIDIAN_REST_API_KEY="e16ee5b59a739c4f1800b1ddcf6084ed72601170bd2eeedb8b060898dbf7c980"
exec claude "$@"
```

Make it executable:
```bash
chmod +x /home/aleksa/start-claude-with-obsidian.sh
```

Then always start Claude CLI with:
```bash
/home/aleksa/start-claude-with-obsidian.sh
```

---

## Debug: Check What MCP Server Sees

If you want to see what environment variables the MCP server actually receives, ask Claude CLI:

```
Use the Bash tool to run this command:
uv run python -c "import os; print('OBSIDIAN_REST_API_KEY:', os.getenv('OBSIDIAN_REST_API_KEY', 'NOT SET'))"
```

This will show if the MCP server subprocess has access to the environment variable.

---

**Current Status:** Environment variables are in ~/.bashrc but may not be loaded in your current session.

**Next Step:** Verify if Claude CLI can see them with the quick test above.
