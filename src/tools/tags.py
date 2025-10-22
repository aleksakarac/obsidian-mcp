"""Filesystem-native tag management tools.

This module provides direct filesystem access for tag extraction, manipulation,
and search operations, following the Performance-First and Filesystem-Native
constitutional principles.
"""

import os
import frontmatter
from typing import List, Dict
from pathlib import Path

from ..utils.patterns import TAG_PATTERN
from ..utils.validators import is_markdown_file


def extract_all_tags(content: str) -> Dict[str, List[str]]:
    """
    Extract all tags (frontmatter and inline) from markdown content.

    Args:
        content: Markdown content string

    Returns:
        Dictionary with:
            - frontmatter_tags: Tags from YAML frontmatter
            - inline_tags: Tags from #hashtag syntax in content
            - all_tags: Deduplicated union of both

    Examples:
        >>> content = '''---
        ... tags: [project, meeting]
        ... ---
        ... # Note
        ... Discussion about #project/planning and #action-items.'''
        >>> result = extract_all_tags(content)
        >>> 'project' in result['all_tags']
        True
    """
    frontmatter_tags = []
    inline_tags = []

    # Parse frontmatter using python-frontmatter
    try:
        post = frontmatter.loads(content)
        metadata = post.metadata

        # Extract from 'tags' field (list or string)
        if 'tags' in metadata:
            tags_value = metadata['tags']
            if isinstance(tags_value, list):
                frontmatter_tags.extend([str(t) for t in tags_value])
            elif isinstance(tags_value, str):
                frontmatter_tags.append(tags_value)

        # Also check 'tag' field (singular)
        if 'tag' in metadata:
            tag_value = metadata['tag']
            if isinstance(tag_value, list):
                frontmatter_tags.extend([str(t) for t in tag_value])
            elif isinstance(tag_value, str):
                frontmatter_tags.append(tag_value)

    except Exception:
        # If frontmatter parsing fails, continue with empty frontmatter tags
        pass

    # Extract inline tags using TAG_PATTERN
    for match in TAG_PATTERN.finditer(content):
        tag = match.group(1)  # Capture group without the #
        inline_tags.append(tag)

    # Deduplicate all_tags while preserving order
    seen = set()
    all_tags = []
    for tag in frontmatter_tags + inline_tags:
        if tag not in seen:
            seen.add(tag)
            all_tags.append(tag)

    return {
        "frontmatter_tags": frontmatter_tags,
        "inline_tags": inline_tags,
        "all_tags": all_tags
    }


def add_tag_to_frontmatter(filepath: str, tag: str) -> Dict[str, any]:
    """
    Add a tag to a note's frontmatter.

    If the note has no frontmatter, creates it. If the tag already exists,
    returns success with appropriate message.

    Args:
        filepath: Path to the markdown file
        tag: Tag to add (without # symbol)

    Returns:
        Dictionary with:
            - success: Boolean indicating if operation succeeded
            - message: Descriptive message

    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse frontmatter
    post = frontmatter.loads(content)

    # Get existing tags
    if 'tags' in post.metadata:
        tags_value = post.metadata['tags']
        if isinstance(tags_value, list):
            existing_tags = tags_value
        else:
            existing_tags = [tags_value]
    else:
        existing_tags = []

    # Check if tag already exists
    if tag in existing_tags:
        return {
            "success": True,
            "message": f"Tag '{tag}' already exists in frontmatter"
        }

    # Add the new tag
    existing_tags.append(tag)
    post.metadata['tags'] = existing_tags

    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(post))

    return {
        "success": True,
        "message": f"Added tag '{tag}' to frontmatter"
    }


def remove_tag_from_frontmatter(filepath: str, tag: str) -> Dict[str, any]:
    """
    Remove a tag from a note's frontmatter.

    Args:
        filepath: Path to the markdown file
        tag: Tag to remove (without # symbol)

    Returns:
        Dictionary with:
            - success: Boolean indicating if operation succeeded
            - message: Descriptive message

    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse frontmatter
    post = frontmatter.loads(content)

    # Get existing tags
    if 'tags' not in post.metadata:
        return {
            "success": True,
            "message": f"No tags found in frontmatter"
        }

    tags_value = post.metadata['tags']
    if isinstance(tags_value, list):
        existing_tags = tags_value
    else:
        existing_tags = [tags_value]

    # Check if tag exists
    if tag not in existing_tags:
        return {
            "success": True,
            "message": f"Tag '{tag}' not found in frontmatter"
        }

    # Remove the tag
    existing_tags.remove(tag)

    # Update or remove tags field
    if existing_tags:
        post.metadata['tags'] = existing_tags
    else:
        # If no tags left, keep empty list
        post.metadata['tags'] = []

    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(post))

    return {
        "success": True,
        "message": f"Removed tag '{tag}' from frontmatter"
    }


def find_notes_by_tag(vault_path: str, tag: str) -> List[Dict[str, any]]:
    """
    Find all notes containing a specific tag (frontmatter or inline).

    Args:
        vault_path: Absolute path to the vault root directory
        tag: Tag to search for (with or without # symbol)

    Returns:
        List of dictionaries, each containing:
            - file: Relative path from vault root
            - absolute_path: Full filesystem path
            - tag_locations: Dict with 'frontmatter' and 'inline' booleans

    Examples:
        >>> find_notes_by_tag("/path/to/vault", "project")
        [
            {
                "file": "notes/active.md",
                "absolute_path": "/path/to/vault/notes/active.md",
                "tag_locations": {"frontmatter": True, "inline": False}
            }
        ]
    """
    # Normalize tag (remove # if present)
    search_tag = tag.lstrip('#')

    results = []

    # Traverse vault directory
    for root, dirs, files in os.walk(vault_path):
        # Skip .obsidian directory
        dirs[:] = [d for d in dirs if d != ".obsidian"]

        for filename in files:
            # Only process markdown files
            if not is_markdown_file(filename):
                continue

            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, vault_path)

            # Read file and extract tags
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tags_info = extract_all_tags(content)

                # Check if tag is present
                found_in_frontmatter = search_tag in tags_info["frontmatter_tags"]
                found_in_inline = search_tag in tags_info["inline_tags"]

                if found_in_frontmatter or found_in_inline:
                    results.append({
                        "file": relative_path,
                        "absolute_path": file_path,
                        "tag_locations": {
                            "frontmatter": found_in_frontmatter,
                            "inline": found_in_inline
                        }
                    })

            except (FileNotFoundError, PermissionError, UnicodeDecodeError):
                # Skip files that can't be read
                continue

    return results
