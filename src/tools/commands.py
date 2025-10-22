"""Obsidian command execution tools via API.

This module provides tools for executing Obsidian commands programmatically.
Commands include both built-in Obsidian commands and commands registered by
community plugins.

All tools require Obsidian running with Local REST API plugin.
"""

import os
from typing import Dict, List, Optional, Any

from ..utils.api_availability import require_api_available, get_api_client
from fastmcp.exceptions import McpError
from ..utils.error_utils import create_error


# ============================================================================
# Command Execution
# ============================================================================

async def execute_command(
    command_id: str,
    args: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute an Obsidian command.

    Args:
        command_id: Command ID (e.g., "editor:toggle-bold")
        args: Optional command arguments

    Returns:
        Command execution result

    Raises:
        McpError: If API unavailable or command fails
    """
    await require_api_available()

    client = get_api_client()

    try:
        result = await client.execute_command(command_id, args)
        return result
    except Exception as e:
        raise create_error(f"Command execution failed: {str(e)}")


async def list_available_commands() -> List[Dict[str, Any]]:
    """List all available commands.

    Returns:
        List of command definitions

    Raises:
        McpError: If API unavailable
    """
    await require_api_available()

    client = get_api_client()

    try:
        result = await client.execute_command("app:list-commands")
        return result
    except Exception as e:
        raise create_error(f"Failed to list commands: {str(e)}")


# ============================================================================
# MCP Tool Functions
# ============================================================================

async def execute_command_api_tool(
    command_id: str,
    args: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute an Obsidian command (requires Obsidian running).

    Args:
        command_id: Command ID (e.g., "editor:toggle-bold", "file-explorer:reveal-active-file")
        args: Optional command arguments

    Returns:
        Command execution result

    Raises:
        McpError: If API unavailable or command fails

    Common commands:
    - editor:toggle-bold - Toggle bold formatting
    - editor:toggle-italic - Toggle italic formatting
    - editor:toggle-code - Toggle inline code
    - editor:toggle-blockquote - Toggle blockquote
    - editor:insert-link - Insert link
    - file-explorer:reveal-active-file - Reveal in file explorer
    - app:reload - Reload Obsidian
    - workspace:split-vertical - Split pane vertically
    - workspace:split-horizontal - Split pane horizontally
    """
    result = await execute_command(command_id, args)

    return {
        "success": True,
        "command_id": command_id,
        "args": args,
        "result": result,
    }


async def list_commands_api_tool() -> Dict[str, Any]:
    """List all available Obsidian commands (requires Obsidian running).

    Returns:
        List of all commands with IDs and names

    Raises:
        McpError: If API unavailable
    """
    commands = await list_available_commands()

    return {
        "success": True,
        "command_count": len(commands),
        "commands": commands,
    }


async def search_commands_api_tool(query: str) -> Dict[str, Any]:
    """Search for commands by name or ID (requires Obsidian running).

    Args:
        query: Search query (case-insensitive)

    Returns:
        Matching commands

    Raises:
        McpError: If API unavailable
    """
    all_commands = await list_available_commands()

    # Filter commands
    query_lower = query.lower()
    matching = [
        cmd for cmd in all_commands
        if query_lower in cmd.get("id", "").lower()
        or query_lower in cmd.get("name", "").lower()
    ]

    return {
        "success": True,
        "query": query,
        "match_count": len(matching),
        "matches": matching,
    }
