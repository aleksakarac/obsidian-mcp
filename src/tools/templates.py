"""Filesystem-native template expansion tools.

This module provides basic template variable substitution without requiring
Obsidian to be running. Supports simple variable replacement for common use cases.

Template Syntax:
- {{variable_name}} - Simple variable substitution
- {{date}} - Current date (YYYY-MM-DD)
- {{time}} - Current time (HH:MM:SS)
- {{datetime}} - Current datetime (YYYY-MM-DD HH:MM:SS)
- {{title}} - Note title (from filename)

All operations are filesystem-native for maximum performance and offline capability.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any


# ============================================================================
# Template Variable Expansion
# ============================================================================

def expand_template_variables(
    template_content: str,
    variables: Optional[Dict[str, str]] = None,
    filename: Optional[str] = None,
) -> str:
    """Expand template variables in content.

    Args:
        template_content: Template content with {{variable}} placeholders
        variables: Dictionary of variable name -> value mappings
        filename: Optional filename for {{title}} variable

    Returns:
        Content with all variables expanded

    Examples:
        >>> expand_template_variables("Hello {{name}}!", {"name": "World"})
        'Hello World!'
    """
    variables = variables or {}

    # Add built-in variables
    now = datetime.now()
    built_in = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "year": now.strftime("%Y"),
        "month": now.strftime("%m"),
        "day": now.strftime("%d"),
    }

    # Add title from filename if provided
    if filename:
        title = Path(filename).stem
        built_in["title"] = title

    # Merge variables (user variables override built-ins)
    all_variables = {**built_in, **variables}

    # Replace all {{variable}} patterns
    def replace_var(match):
        var_name = match.group(1).strip()
        return all_variables.get(var_name, match.group(0))

    content = re.sub(r'\{\{([^}]+)\}\}', replace_var, template_content)

    return content


def read_template(template_path: str) -> str:
    """Read template file content.

    Args:
        template_path: Absolute path to template file

    Returns:
        Template content

    Raises:
        FileNotFoundError: If template doesn't exist
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_from_template(
    template_path: str,
    target_path: str,
    variables: Optional[Dict[str, str]] = None,
) -> None:
    """Create a file from a template.

    Args:
        template_path: Path to template file
        target_path: Path for new file
        variables: Variables to expand

    Raises:
        FileNotFoundError: If template doesn't exist
        FileExistsError: If target already exists
    """
    if os.path.exists(target_path):
        raise FileExistsError(f"Target file already exists: {target_path}")

    template_content = read_template(template_path)

    # Expand variables
    filename = os.path.basename(target_path)
    expanded = expand_template_variables(template_content, variables, filename)

    # Create parent directories if needed
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    # Write to target
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(expanded)


# ============================================================================
# MCP Tool Functions
# ============================================================================

async def expand_template_fs_tool(
    template_path: str,
    variables: Optional[Dict[str, str]] = None,
    filename: Optional[str] = None,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Expand template variables (filesystem-native, offline).

    Args:
        template_path: Path to template file (relative to vault)
        variables: Dictionary of variable name -> value
        filename: Optional filename for {{title}} variable
        vault_path: Path to vault root (optional)

    Returns:
        Expanded template content

    Raises:
        ValueError: If template not found
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    # Resolve absolute path
    if not os.path.isabs(template_path):
        template_path = os.path.join(vault, template_path)

    try:
        template_content = read_template(template_path)
        expanded = expand_template_variables(template_content, variables, filename)

        return {
            "template_path": template_path,
            "expanded_content": expanded,
            "variables_used": list((variables or {}).keys()),
        }
    except FileNotFoundError as e:
        raise ValueError(str(e))


async def create_note_from_template_fs_tool(
    template_path: str,
    target_path: str,
    variables: Optional[Dict[str, str]] = None,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a note from a template (filesystem-native, offline).

    Args:
        template_path: Path to template file (relative to vault)
        target_path: Path for new note (relative to vault)
        variables: Dictionary of variable name -> value
        vault_path: Path to vault root (optional)

    Returns:
        Creation result with file path and expanded content

    Raises:
        ValueError: If template not found or target exists
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    # Resolve absolute paths
    if not os.path.isabs(template_path):
        template_path = os.path.join(vault, template_path)

    if not os.path.isabs(target_path):
        target_path = os.path.join(vault, target_path)

    try:
        write_from_template(template_path, target_path, variables)

        # Read back the created file
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "success": True,
            "template_path": template_path,
            "target_path": target_path,
            "created_content": content,
            "variables_used": list((variables or {}).keys()),
        }
    except (FileNotFoundError, FileExistsError) as e:
        raise ValueError(str(e))


async def list_templates_fs_tool(
    template_folder: str = "Templates",
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """List all available templates (filesystem-native, offline).

    Args:
        template_folder: Folder containing templates (relative to vault)
        vault_path: Path to vault root (optional)

    Returns:
        List of template files with metadata

    Raises:
        ValueError: If template folder doesn't exist
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    # Resolve absolute path
    if not os.path.isabs(template_folder):
        template_folder = os.path.join(vault, template_folder)

    if not os.path.exists(template_folder):
        raise ValueError(f"Template folder not found: {template_folder}")

    templates = []
    for root, dirs, files in os.walk(template_folder):
        for filename in files:
            if filename.endswith('.md'):
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, vault)

                # Get file stats
                stats = os.stat(full_path)

                # Read first line for description
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                except Exception:
                    first_line = ""

                templates.append({
                    "name": filename,
                    "path": relative_path,
                    "size_bytes": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "first_line": first_line,
                })

    return {
        "template_folder": template_folder,
        "template_count": len(templates),
        "templates": templates,
    }
