#!/bin/bash
# Wrapper script to run obsidian-mcp with environment variables
# This ensures the MCP server always has access to Obsidian API credentials

export OBSIDIAN_VAULT_PATH="/home/aleksa/Obsidian/"
export OBSIDIAN_API_URL="https://127.0.0.1:27124"
export OBSIDIAN_REST_API_KEY="2fb876ddc80233ce88d6ec9366b8fb4eb224a399cdcd4b0c27b6ce10335e26c6"

# Run the MCP server with uv
cd /home/aleksa/Documents/Projects/CustomObsidianMcp
exec uv run obsidian-mcp "$@"
