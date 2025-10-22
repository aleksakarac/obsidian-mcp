"""Filesystem-native tools for Dataview inline field extraction and manipulation.

This module provides tools for working with Dataview inline fields without requiring
Obsidian to be running. Supports all three Dataview syntax variants:
- Full-line: field:: value
- Bracket: [field:: value]
- Paren: (field:: value) - hidden key

All operations work directly on markdown files.
"""

import os
import re
from pathlib import Path
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Literal, Union
from pydantic import Field

from ..models.obsidian import DataviewField
from ..utils.patterns import (
    DATAVIEW_FULL_LINE,
    DATAVIEW_BRACKET,
    DATAVIEW_PAREN,
    DATE_ISO8601,
    LIST_QUOTED,
    WIKILINK_PATTERN,
)


def canonicalize_key(key: str) -> str:
    """Convert field key to canonical form.

    Canonical form: lowercase, spaces → hyphens, strip formatting
    Examples:
        "Project Status" → "project-status"
        "_Priority_" → "priority"
        "**Due Date**" → "due-date"

    Args:
        key: Original field key

    Returns:
        Canonicalized key string
    """
    # Remove markdown formatting
    cleaned = key.strip("_*~")
    # Convert to lowercase and replace spaces with hyphens
    canonical = cleaned.lower().replace(" ", "-")
    # Remove any non-alphanumeric chars except hyphens
    canonical = re.sub(r"[^a-z0-9-]", "", canonical)
    return canonical


def detect_value_type(value: str) -> Literal["string", "number", "boolean", "date", "link", "list"]:
    """Detect the type of a Dataview field value.

    Args:
        value: Value string to analyze

    Returns:
        Detected type: string, number, boolean, date, link, or list
    """
    value_stripped = value.strip()

    # Boolean check
    if value_stripped.lower() in ("true", "false"):
        return "boolean"

    # Number check (int or float)
    try:
        float(value_stripped)
        return "number"
    except ValueError:
        pass

    # Date check (ISO8601)
    if DATE_ISO8601.match(value_stripped):
        return "date"

    # Wikilink check
    if WIKILINK_PATTERN.match(value_stripped):
        return "link"

    # List check (comma-separated, may have quoted items)
    if "," in value_stripped:
        return "list"

    # Default to string
    return "string"


def parse_value(value: str, value_type: str) -> Any:
    """Parse value string based on detected type.

    Args:
        value: Value string
        value_type: Detected type

    Returns:
        Parsed value (appropriate Python type)
    """
    value_stripped = value.strip()

    if value_type == "boolean":
        return value_stripped.lower() == "true"

    elif value_type == "number":
        try:
            # Try int first
            if "." not in value_stripped:
                return int(value_stripped)
            return float(value_stripped)
        except ValueError:
            return value_stripped

    elif value_type == "date":
        try:
            # Parse ISO8601 date
            if "T" in value_stripped:
                return datetime.fromisoformat(value_stripped.replace("Z", "+00:00"))
            return datetime.strptime(value_stripped, "%Y-%m-%d").date()
        except ValueError:
            return value_stripped

    elif value_type == "link":
        # Extract link target
        match = WIKILINK_PATTERN.match(value_stripped)
        if match:
            return match.group(1)  # Return target without brackets
        return value_stripped

    elif value_type == "list":
        # Parse comma-separated list
        # Handle quoted items: "item1", "item2" or simple: item1, item2
        items = []
        for quoted_match in LIST_QUOTED.finditer(value_stripped):
            items.append(quoted_match.group(1))

        # If no quoted items found, split by comma
        if not items:
            items = [item.strip() for item in value_stripped.split(",")]

        return items

    # Default: return as string
    return value_stripped


def extract_dataview_fields(content: str, source_file: str) -> List[DataviewField]:
    """Extract all Dataview inline fields from content.

    Supports all three syntax variants:
    - Full-line: field:: value
    - Bracket: [field:: value]
    - Paren: (field:: value)

    Args:
        content: Markdown content
        source_file: Path to source file

    Returns:
        List of DataviewField objects
    """
    fields = []

    # Skip code blocks
    code_block_pattern = re.compile(r"```.*?```", re.DOTALL)
    code_blocks = [(m.start(), m.end()) for m in code_block_pattern.finditer(content)]

    def in_code_block(pos: int) -> bool:
        """Check if position is inside a code block."""
        return any(start <= pos < end for start, end in code_blocks)

    # Extract full-line fields (field:: value)
    for match in DATAVIEW_FULL_LINE.finditer(content):
        if in_code_block(match.start()):
            continue

        key = match.group(1).strip()
        value_str = match.group(2).strip()
        canonical_key = canonicalize_key(key)
        value_type = detect_value_type(value_str)
        value = parse_value(value_str, value_type)

        # Calculate line number
        line_number = content[:match.start()].count("\n") + 1

        fields.append(
            DataviewField(
                key=key,
                value=value,
                canonical_key=canonical_key,
                line_number=line_number,
                syntax_type="full-line",
                source_file=source_file,
                value_type=value_type,
            )
        )

    # Extract bracket fields ([field:: value])
    for match in DATAVIEW_BRACKET.finditer(content):
        if in_code_block(match.start()):
            continue

        key = match.group(1).strip()
        value_str = match.group(2).strip()
        canonical_key = canonicalize_key(key)
        value_type = detect_value_type(value_str)
        value = parse_value(value_str, value_type)

        line_number = content[:match.start()].count("\n") + 1

        fields.append(
            DataviewField(
                key=key,
                value=value,
                canonical_key=canonical_key,
                line_number=line_number,
                syntax_type="bracket",
                source_file=source_file,
                value_type=value_type,
            )
        )

    # Extract paren fields ((field:: value))
    for match in DATAVIEW_PAREN.finditer(content):
        if in_code_block(match.start()):
            continue

        key = match.group(1).strip()
        value_str = match.group(2).strip()
        canonical_key = canonicalize_key(key)
        value_type = detect_value_type(value_str)
        value = parse_value(value_str, value_type)

        line_number = content[:match.start()].count("\n") + 1

        fields.append(
            DataviewField(
                key=key,
                value=value,
                canonical_key=canonical_key,
                line_number=line_number,
                syntax_type="paren",
                source_file=source_file,
                value_type=value_type,
            )
        )

    return fields


def format_dataview_field(
    key: str,
    value: Any,
    syntax_type: Literal["full-line", "bracket", "paren"] = "full-line",
) -> str:
    """Format a Dataview field into its string representation.

    Args:
        key: Field key
        value: Field value
        syntax_type: Syntax variant to use

    Returns:
        Formatted field string
    """
    # Format value
    if isinstance(value, bool):
        value_str = "true" if value else "false"
    elif isinstance(value, (date, datetime)):
        value_str = value.isoformat()
    elif isinstance(value, list):
        # Format as quoted list
        value_str = ", ".join(f'"{item}"' for item in value)
    else:
        value_str = str(value)

    # Format based on syntax type
    if syntax_type == "bracket":
        return f"[{key}:: {value_str}]"
    elif syntax_type == "paren":
        return f"({key}:: {value_str})"
    else:  # full-line
        return f"{key}:: {value_str}"


def scan_vault_for_fields(vault_path: str, key_filter: Optional[str] = None) -> List[DataviewField]:
    """Scan entire vault for Dataview fields.

    Args:
        vault_path: Path to Obsidian vault
        key_filter: Optional canonical key to filter by

    Returns:
        List of all matching fields found in vault
    """
    fields = []
    vault_dir = Path(vault_path)

    for md_file in vault_dir.rglob("*.md"):
        # Skip hidden files and folders
        if any(part.startswith(".") for part in md_file.parts):
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
            relative_path = str(md_file.relative_to(vault_dir))

            file_fields = extract_dataview_fields(content, relative_path)

            # Apply filter if specified
            if key_filter:
                file_fields = [f for f in file_fields if f.canonical_key == key_filter]

            fields.extend(file_fields)

        except Exception:
            # Skip files that can't be read
            continue

    return fields


def add_field_to_file(
    vault_path: str,
    file_path: str,
    key: str,
    value: Any,
    syntax_type: Literal["full-line", "bracket", "paren"] = "full-line",
    insert_at: Literal["start", "end", "after_frontmatter"] = "after_frontmatter",
) -> bool:
    """Add a Dataview field to a file.

    Args:
        vault_path: Path to vault
        file_path: Relative path to file
        key: Field key
        value: Field value
        syntax_type: Syntax variant
        insert_at: Where to insert the field

    Returns:
        True if successful, False otherwise
    """
    full_path = Path(vault_path) / file_path

    try:
        if not full_path.exists():
            # Create file if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            field_line = format_dataview_field(key, value, syntax_type)
            full_path.write_text(field_line + "\n", encoding="utf-8")
            return True

        content = full_path.read_text(encoding="utf-8")

        # Format field
        field_line = format_dataview_field(key, value, syntax_type)

        # Determine insertion point
        if insert_at == "start":
            new_content = field_line + "\n" + content

        elif insert_at == "end":
            new_content = content.rstrip() + "\n" + field_line + "\n"

        elif insert_at == "after_frontmatter":
            # Check for frontmatter
            frontmatter_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
            match = frontmatter_pattern.match(content)

            if match:
                # Insert after frontmatter
                fm_end = match.end()
                new_content = content[:fm_end] + field_line + "\n" + content[fm_end:]
            else:
                # No frontmatter, insert at start
                new_content = field_line + "\n" + content

        else:
            new_content = content + "\n" + field_line + "\n"

        full_path.write_text(new_content, encoding="utf-8")
        return True

    except Exception:
        return False


def remove_field_from_file(
    vault_path: str,
    file_path: str,
    key: str,
    line_number: Optional[int] = None,
) -> bool:
    """Remove a Dataview field from a file.

    Args:
        vault_path: Path to vault
        file_path: Relative path to file
        key: Canonical key of field to remove
        line_number: Optional specific line number (if multiple fields with same key)

    Returns:
        True if successful, False otherwise
    """
    full_path = Path(vault_path) / file_path

    try:
        content = full_path.read_text(encoding="utf-8")
        fields = extract_dataview_fields(content, file_path)

        # Find matching fields
        canonical_key = canonicalize_key(key)
        matching_fields = [f for f in fields if f.canonical_key == canonical_key]

        if not matching_fields:
            return False

        # If line_number specified, remove only that one
        if line_number:
            matching_fields = [f for f in matching_fields if f.line_number == line_number]
            if not matching_fields:
                return False

        # Remove fields from content (work backwards to preserve line numbers)
        lines = content.splitlines(keepends=True)

        for field in sorted(matching_fields, key=lambda f: f.line_number, reverse=True):
            if field.line_number <= len(lines):
                line_idx = field.line_number - 1
                line = lines[line_idx]

                # For bracket/paren syntax, remove just the field (inline)
                if field.syntax_type in ("bracket", "paren"):
                    pattern = format_dataview_field(field.key, ".*?", field.syntax_type)
                    pattern_regex = re.escape(pattern).replace(r"\.\*\?", ".*?")
                    lines[line_idx] = re.sub(pattern_regex, "", line)

                    # If line becomes empty, remove it
                    if not lines[line_idx].strip():
                        del lines[line_idx]
                else:
                    # For full-line syntax, remove entire line
                    del lines[line_idx]

        full_path.write_text("".join(lines), encoding="utf-8")
        return True

    except Exception:
        return False


# ============================================================================
# MCP TOOL FUNCTIONS
# ============================================================================

async def extract_dataview_fields_fs_tool(
    file_path: str,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract all Dataview inline fields from a note (filesystem-native).

    Args:
        file_path: Relative path to file
        vault_path: Path to vault (defaults to env var)

    Returns:
        Dictionary with fields list and count
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    full_path = Path(vault) / file_path

    if not full_path.exists():
        raise ValueError(f"File not found: {file_path}")

    content = full_path.read_text(encoding="utf-8")
    fields = extract_dataview_fields(content, file_path)

    return {
        "file_path": file_path,
        "field_count": len(fields),
        "fields": [
            {
                "key": f.key,
                "canonical_key": f.canonical_key,
                "value": f.value,
                "value_type": f.value_type,
                "syntax_type": f.syntax_type,
                "line_number": f.line_number,
            }
            for f in fields
        ],
    }


async def search_by_dataview_field_fs_tool(
    key: str,
    value: Optional[Any] = None,
    value_type: Optional[Literal["string", "number", "boolean", "date", "link", "list"]] = None,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Find notes containing a specific Dataview field (filesystem-native).

    Args:
        key: Field key to search for (will be canonicalized)
        value: Optional value to match (exact match)
        value_type: Optional value type filter
        vault_path: Path to vault (defaults to env var)

    Returns:
        Dictionary with matching fields grouped by file
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    canonical_key = canonicalize_key(key)
    all_fields = scan_vault_for_fields(vault, key_filter=canonical_key)

    # Apply value filter if specified
    if value is not None:
        all_fields = [f for f in all_fields if f.value == value]

    # Apply value_type filter if specified
    if value_type:
        all_fields = [f for f in all_fields if f.value_type == value_type]

    # Group by file
    by_file = {}
    for field in all_fields:
        if field.source_file not in by_file:
            by_file[field.source_file] = []
        by_file[field.source_file].append(
            {
                "key": field.key,
                "canonical_key": field.canonical_key,
                "value": field.value,
                "value_type": field.value_type,
                "syntax_type": field.syntax_type,
                "line_number": field.line_number,
            }
        )

    return {
        "search_key": key,
        "canonical_key": canonical_key,
        "total_matches": len(all_fields),
        "files_with_matches": len(by_file),
        "matches_by_file": by_file,
    }


async def add_dataview_field_fs_tool(
    file_path: str,
    key: str,
    value: Any,
    syntax_type: Literal["full-line", "bracket", "paren"] = "full-line",
    insert_at: Literal["start", "end", "after_frontmatter"] = "after_frontmatter",
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a Dataview inline field to a note (filesystem-native).

    Args:
        file_path: Relative path to file
        key: Field key
        value: Field value
        syntax_type: Syntax variant (full-line, bracket, paren)
        insert_at: Where to insert
        vault_path: Path to vault (defaults to env var)

    Returns:
        Dictionary with success status and formatted field
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    formatted_field = format_dataview_field(key, value, syntax_type)

    success = add_field_to_file(vault, file_path, key, value, syntax_type, insert_at)

    return {
        "success": success,
        "file_path": file_path,
        "formatted_field": formatted_field,
        "canonical_key": canonicalize_key(key),
    }


async def remove_dataview_field_fs_tool(
    file_path: str,
    key: str,
    line_number: Optional[int] = None,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Remove a Dataview inline field from a note (filesystem-native).

    Args:
        file_path: Relative path to file
        key: Field key to remove
        line_number: Optional specific line (if multiple fields with same key)
        vault_path: Path to vault (defaults to env var)

    Returns:
        Dictionary with success status
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    success = remove_field_from_file(vault, file_path, key, line_number)

    return {
        "success": success,
        "file_path": file_path,
        "removed_key": key,
        "canonical_key": canonicalize_key(key),
    }
