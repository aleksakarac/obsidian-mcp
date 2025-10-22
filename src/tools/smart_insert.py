"""Filesystem-native smart content insertion tools.

This module provides direct filesystem access for inserting content at specific
locations in markdown files, following the Performance-First and Filesystem-Native
constitutional principles.
"""

import os
import re
import frontmatter
from typing import Dict, Any


def insert_after_heading(filepath: str, heading: str, content: str) -> Dict[str, Any]:
    """
    Insert content immediately after a specific heading in a note.

    This function finds the specified heading and inserts the content on the line
    immediately following it. Heading matching is case-sensitive. If multiple
    headings with the same text exist, content is inserted after the first occurrence.

    Args:
        filepath: Path to the markdown file
        heading: Heading text to search for (without # symbols)
        content: Content to insert after the heading

    Returns:
        Dictionary with:
            - success: Boolean indicating if operation succeeded
            - message: Descriptive message
            - error: Error message if success is False

    Raises:
        FileNotFoundError: If the file doesn't exist

    Examples:
        >>> insert_after_heading("note.md", "Tasks", "\n- [ ] New task")
        {"success": True, "message": "Inserted content after heading 'Tasks'"}

        >>> insert_after_heading("note.md", "Nonexistent", "content")
        {"success": False, "error": "Heading 'Nonexistent' not found in note"}
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the heading - match any level (# to ######)
    heading_pattern = re.compile(r'^(#{1,6})\s+' + re.escape(heading) + r'\s*$')

    insert_index = None
    for i, line in enumerate(lines):
        if heading_pattern.match(line):
            insert_index = i + 1  # Insert after the heading line
            break

    if insert_index is None:
        return {
            "success": False,
            "error": f"Heading '{heading}' not found in note"
        }

    # Insert the content
    lines.insert(insert_index, content)

    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return {
        "success": True,
        "message": f"Inserted content after heading '{heading}'"
    }


def insert_after_block(filepath: str, block_id: str, content: str) -> Dict[str, Any]:
    """
    Insert content immediately after a block reference.

    This function finds the specified block reference (^block-id) and inserts
    content after the line containing it. The block_id can be provided with or
    without the ^ prefix.

    Args:
        filepath: Path to the markdown file
        block_id: Block reference ID (with or without ^ prefix)
        content: Content to insert after the block

    Returns:
        Dictionary with:
            - success: Boolean indicating if operation succeeded
            - message: Descriptive message
            - error: Error message if success is False

    Raises:
        FileNotFoundError: If the file doesn't exist

    Examples:
        >>> insert_after_block("note.md", "intro", "\nFollow-up content")
        {"success": True, "message": "Inserted content after block '^intro'"}

        >>> insert_after_block("note.md", "^summary", "\n## Analysis")
        {"success": True, "message": "Inserted content after block '^summary'"}
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    # Normalize block_id (ensure it starts with ^)
    if not block_id.startswith('^'):
        block_id = '^' + block_id

    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the block reference
    # Block references appear at end of line: "Some text ^block-id"
    block_pattern = re.compile(r'\s+' + re.escape(block_id) + r'\s*$')

    insert_index = None
    for i, line in enumerate(lines):
        if block_pattern.search(line):
            insert_index = i + 1  # Insert after the line with block reference
            break

    if insert_index is None:
        return {
            "success": False,
            "error": f"Block '{block_id}' not found in note"
        }

    # Insert the content
    lines.insert(insert_index, content)

    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return {
        "success": True,
        "message": f"Inserted content after block '{block_id}'"
    }


def update_frontmatter_field(filepath: str, field: str, value: Any) -> Dict[str, Any]:
    """
    Update or add a field in the note's YAML frontmatter.

    If the note has no frontmatter, it will be created. If the field already exists,
    its value will be updated. Otherwise, the field will be added to the frontmatter.

    Args:
        filepath: Path to the markdown file
        field: Field name to update/add
        value: Value to set (can be string, number, boolean, list, etc.)

    Returns:
        Dictionary with:
            - success: Boolean indicating if operation succeeded
            - message: Descriptive message

    Raises:
        FileNotFoundError: If the file doesn't exist

    Examples:
        >>> update_frontmatter_field("note.md", "status", "published")
        {"success": True, "message": "Updated frontmatter field 'status'"}

        >>> update_frontmatter_field("note.md", "tags", ["python", "code"])
        {"success": True, "message": "Updated frontmatter field 'tags'"}
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse frontmatter using python-frontmatter
    post = frontmatter.loads(content)

    # Update or add the field
    post.metadata[field] = value

    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(post))

    return {
        "success": True,
        "message": f"Updated frontmatter field '{field}'"
    }


def append_to_note(filepath: str, content: str) -> Dict[str, Any]:
    """
    Append content to the end of a note.

    This function adds content at the very end of the file. It's useful for
    adding appendices, logs, or any content that should come after all existing
    content.

    Args:
        filepath: Path to the markdown file
        content: Content to append

    Returns:
        Dictionary with:
            - success: Boolean indicating if operation succeeded
            - message: Descriptive message

    Raises:
        FileNotFoundError: If the file doesn't exist

    Examples:
        >>> append_to_note("note.md", "\n## Appendix\n\nAdditional notes.")
        {"success": True, "message": "Appended content to note"}
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    # Append to file
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(content)

    return {
        "success": True,
        "message": "Appended content to note"
    }
