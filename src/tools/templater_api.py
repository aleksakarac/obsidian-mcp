"""Templater plugin template rendering tools via Obsidian API.

This module provides tools for rendering Templater templates that require the
Templater plugin and Obsidian to be running. Templater extends template capabilities
beyond basic variable substitution with JavaScript execution, dynamic dates, and
plugin integration.

Templater Syntax:
- <% tp.date.now() %> - Dynamic dates
- <% tp.file.title %> - File properties
- <% tp.web.random_picture() %> - External integrations
- <% ... %> - Any JavaScript expression

All tools require Obsidian with Templater plugin running and API access.
"""

import os
from typing import Dict, List, Optional, Any

from ..utils.api_availability import require_api_available, get_api_client
from fastmcp.exceptions import McpError


# ============================================================================
# Templater Template Rendering
# ============================================================================

async def render_templater_template(
    template_file: str,
    target_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Render a Templater template.

    Args:
        template_file: Path to template file (relative to vault)
        target_file: Optional target file path for context (affects tp.file.*)

    Returns:
        Rendered template content

    Raises:
        McpError: If API is unavailable or rendering fails
    """
    await require_api_available()

    client = get_api_client()

    try:
        # Execute Templater command to render template
        result = await client.execute_command(
            "templater-obsidian:replace-in-file-templater",
            {
                "template": template_file,
                "target": target_file or template_file,
            }
        )
        return result
    except Exception as e:
        raise McpError(f"Templater rendering failed: {str(e)}")


async def create_note_from_template(
    template_file: str,
    target_file: str,
    open_file: bool = False,
) -> Dict[str, Any]:
    """Create a new note from a Templater template.

    Args:
        template_file: Path to template file
        target_file: Path for new note
        open_file: Whether to open the file after creation

    Returns:
        Creation result with rendered content

    Raises:
        McpError: If API is unavailable or creation fails
    """
    await require_api_available()

    client = get_api_client()

    try:
        result = await client.execute_command(
            "templater-obsidian:create-new-note-from-template",
            {
                "template": template_file,
                "filename": target_file,
                "open": open_file,
            }
        )
        return result
    except Exception as e:
        raise McpError(f"Note creation from template failed: {str(e)}")


# ============================================================================
# MCP Tool Functions
# ============================================================================

async def render_templater_template_api_tool(
    template_file: str,
    target_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Render a Templater template (requires Obsidian + Templater plugin).

    Args:
        template_file: Path to template file (relative to vault)
        target_file: Optional target file path for context

    Returns:
        Rendered template content with all Templater syntax processed

    Raises:
        McpError: If API unavailable or rendering fails
    """
    result = await render_templater_template(template_file, target_file)

    return {
        "template_file": template_file,
        "target_file": target_file,
        "success": True,
        "rendered_content": result,
    }


async def create_note_from_template_api_tool(
    template_file: str,
    target_file: str,
    open_file: bool = False,
) -> Dict[str, Any]:
    """Create a new note from a Templater template (requires Obsidian + Templater).

    Args:
        template_file: Path to template file
        target_file: Path for new note
        open_file: Whether to open the file after creation

    Returns:
        Creation result with file path and rendered content

    Raises:
        McpError: If API unavailable or creation fails
    """
    result = await create_note_from_template(
        template_file=template_file,
        target_file=target_file,
        open_file=open_file,
    )

    return {
        "template_file": template_file,
        "target_file": target_file,
        "open_file": open_file,
        "success": True,
        "result": result,
    }


async def insert_templater_template_api_tool(
    template_file: str,
    active_file: bool = True,
) -> Dict[str, Any]:
    """Insert a Templater template at cursor position (requires Obsidian + Templater).

    Args:
        template_file: Path to template file
        active_file: Whether to insert into currently active file

    Returns:
        Insertion result

    Raises:
        McpError: If API unavailable or insertion fails
    """
    await require_api_available()

    client = get_api_client()

    try:
        result = await client.execute_command(
            "templater-obsidian:insert-templater",
            {
                "template": template_file,
                "active": active_file,
            }
        )

        return {
            "template_file": template_file,
            "active_file": active_file,
            "success": True,
            "result": result,
        }
    except Exception as e:
        raise McpError(f"Template insertion failed: {str(e)}")
