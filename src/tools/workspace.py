"""Workspace management tools via Obsidian API.

This module provides tools for managing the Obsidian workspace including:
- Active file management
- Pane/split management
- Navigation between notes
- Workspace layout control

All tools require Obsidian running with Local REST API plugin.
"""

import os
from typing import Dict, List, Optional, Any

from ..utils.api_availability import require_api_available, get_api_client
from fastmcp.exceptions import McpError
from ..utils.error_utils import create_error


# ============================================================================
# Active File Management
# ============================================================================

async def get_active_file() -> Dict[str, Any]:
    """Get currently active file.

    Returns:
        Active file information

    Raises:
        McpError: If API unavailable or no active file
    """
    await require_api_available()

    client = get_api_client()

    try:
        result = await client.execute_command("app:get-active-file")
        return result
    except Exception as e:
        raise create_error(f"Failed to get active file: {str(e)}")


async def open_file(file_path: str, new_leaf: bool = False) -> Dict[str, Any]:
    """Open a file in Obsidian.

    Args:
        file_path: Path to file (relative to vault)
        new_leaf: Whether to open in new pane

    Returns:
        Operation result

    Raises:
        McpError: If API unavailable or file doesn't exist
    """
    await require_api_available()

    client = get_api_client()

    try:
        result = await client.execute_command(
            "app:open-file",
            {
                "file": file_path,
                "newLeaf": new_leaf,
            }
        )
        return result
    except Exception as e:
        raise create_error(f"Failed to open file: {str(e)}")


# ============================================================================
# MCP Tool Functions
# ============================================================================

async def get_active_file_api_tool() -> Dict[str, Any]:
    """Get currently active file (requires Obsidian running).

    Returns:
        Active file path, name, and metadata

    Raises:
        McpError: If API unavailable or no active file
    """
    result = await get_active_file()

    return {
        "success": True,
        "active_file": result,
    }


async def open_file_api_tool(
    file_path: str,
    new_pane: bool = False,
) -> Dict[str, Any]:
    """Open a file in Obsidian (requires Obsidian running).

    Args:
        file_path: Path to file (relative to vault)
        new_pane: Whether to open in new pane/split

    Returns:
        Operation result

    Raises:
        McpError: If API unavailable or file doesn't exist
    """
    result = await open_file(file_path, new_pane)

    return {
        "success": True,
        "file_path": file_path,
        "new_pane": new_pane,
        "result": result,
    }


async def close_active_file_api_tool() -> Dict[str, Any]:
    """Close currently active file (requires Obsidian running).

    Returns:
        Operation result

    Raises:
        McpError: If API unavailable
    """
    await require_api_available()

    client = get_api_client()

    try:
        result = await client.execute_command("app:close-active-file")

        return {
            "success": True,
            "result": result,
        }
    except Exception as e:
        raise create_error(f"Failed to close active file: {str(e)}")


async def navigate_back_api_tool() -> Dict[str, Any]:
    """Navigate back in history (requires Obsidian running).

    Returns:
        Operation result

    Raises:
        McpError: If API unavailable
    """
    await require_api_available()

    client = get_api_client()

    try:
        result = await client.execute_command("app:go-back")

        return {
            "success": True,
            "result": result,
        }
    except Exception as e:
        raise create_error(f"Failed to navigate back: {str(e)}")


async def navigate_forward_api_tool() -> Dict[str, Any]:
    """Navigate forward in history (requires Obsidian running).

    Returns:
        Operation result

    Raises:
        McpError: If API unavailable
    """
    await require_api_available()

    client = get_api_client()

    try:
        result = await client.execute_command("app:go-forward")

        return {
            "success": True,
            "result": result,
        }
    except Exception as e:
        raise create_error(f"Failed to navigate forward: {str(e)}")


async def toggle_edit_mode_api_tool() -> Dict[str, Any]:
    """Toggle between edit/preview mode (requires Obsidian running).

    Returns:
        Operation result

    Raises:
        McpError: If API unavailable
    """
    await require_api_available()

    client = get_api_client()

    try:
        result = await client.execute_command("markdown:toggle-preview")

        return {
            "success": True,
            "result": result,
        }
    except Exception as e:
        raise create_error(f"Failed to toggle edit mode: {str(e)}")
