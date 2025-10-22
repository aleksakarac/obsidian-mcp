"""Filesystem-native backlinks discovery tools.

This module provides direct filesystem access for backlink discovery,
following the Performance-First and Filesystem-Native constitutional principles.

Unlike the API-based link_management.py, this module directly reads files from disk
for maximum performance and reliability (no Obsidian running required).
"""

import os
from typing import List, Dict, Optional
from pathlib import Path

from ..utils.patterns import WIKILINK_PATTERN
from ..utils.validators import resolve_vault_path, is_markdown_file


def find_backlinks(vault_path: str, note_name: str) -> List[Dict[str, str]]:
    """
    Find all notes that contain wikilinks pointing to the target note.

    This function performs a filesystem traversal to find backlinks without
    requiring Obsidian to be running (filesystem-native approach).

    Args:
        vault_path: Absolute path to the vault root directory
        note_name: Name of the target note (with or without .md extension)

    Returns:
        List of dictionaries, each containing:
            - source_path: Relative path to the note containing the backlink
            - link_target: The wikilink target text (what was matched)
            - line_number: Line number where the link was found
            - context: Surrounding text for context

    Examples:
        >>> find_backlinks("/home/user/vault", "note1")
        [
            {
                "source_path": "note2.md",
                "link_target": "note1",
                "line_number": 5,
                "context": "This links to [[note1]] for reference."
            }
        ]
    """
    # Normalize note name: remove .md if present
    target_note = note_name.rstrip(".md")

    # Prepare result list
    backlinks = []

    # Traverse vault directory
    for root, dirs, files in os.walk(vault_path):
        # Skip .obsidian directory (constitutional requirement: ignore metadata)
        dirs[:] = [d for d in dirs if d != ".obsidian"]

        for filename in files:
            # Only process markdown files
            if not is_markdown_file(filename):
                continue

            file_path = os.path.join(root, filename)

            # Get relative path from vault root
            relative_path = os.path.relpath(file_path, vault_path)

            # Skip the target note itself
            if filename.rstrip(".md") == target_note:
                continue

            # Read file and search for wikilinks
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, start=1):
                    # Find all wikilinks in this line
                    for match in WIKILINK_PATTERN.finditer(line):
                        # Extract target and optional alias
                        full_match = match.group(1)  # e.g., "note1" or "note1#heading"
                        alias = match.group(2) if match.lastindex >= 2 else None

                        # Extract base note name (before # if section link)
                        base_note = full_match.split("#")[0].strip()

                        # Check if this wikilink targets our note
                        if base_note == target_note:
                            backlinks.append({
                                "source_path": relative_path,
                                "link_target": full_match,
                                "line_number": line_num,
                                "context": line.strip()
                            })

            except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
                # Skip files that can't be read (constitutional: error handling)
                continue

    return backlinks


def find_broken_links(vault_path: str) -> List[Dict[str, str]]:
    """
    Find all wikilinks that point to non-existent notes in the vault.

    Performs filesystem traversal to identify broken links without requiring
    Obsidian to be running.

    Args:
        vault_path: Absolute path to the vault root directory

    Returns:
        List of dictionaries, each containing:
            - source_path: Relative path to the note containing the broken link
            - link_target: The broken wikilink target
            - line_number: Line number where the broken link was found
            - context: Surrounding text for context

    Examples:
        >>> find_broken_links("/home/user/vault")
        [
            {
                "source_path": "note1.md",
                "link_target": "nonexistent",
                "line_number": 10,
                "context": "Links to [[nonexistent]] which doesn't exist."
            }
        ]
    """
    # First, build a set of all note names that exist in the vault
    existing_notes = set()

    for root, dirs, files in os.walk(vault_path):
        # Skip .obsidian directory
        dirs[:] = [d for d in dirs if d != ".obsidian"]

        for filename in files:
            if is_markdown_file(filename):
                # Store note name without extension
                # Handle both .md and .markdown extensions
                if filename.endswith(".md"):
                    note_name = filename[:-3]
                elif filename.endswith(".markdown"):
                    note_name = filename[:-9]
                else:
                    note_name = filename
                existing_notes.add(note_name)

    # Now traverse again to find broken links
    broken_links = []

    for root, dirs, files in os.walk(vault_path):
        # Skip .obsidian directory
        dirs[:] = [d for d in dirs if d != ".obsidian"]

        for filename in files:
            if not is_markdown_file(filename):
                continue

            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, vault_path)

            # Read file and search for wikilinks
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, start=1):
                    # Find all wikilinks in this line
                    for match in WIKILINK_PATTERN.finditer(line):
                        # Extract target (before # if section link)
                        full_match = match.group(1)
                        base_note = full_match.split("#")[0].strip()

                        # Check if target note exists
                        if base_note not in existing_notes:
                            broken_links.append({
                                "source_path": relative_path,
                                "link_target": base_note,
                                "line_number": line_num,
                                "context": line.strip()
                            })

            except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
                # Skip files that can't be read
                continue

    return broken_links
