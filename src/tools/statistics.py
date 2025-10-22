"""Filesystem-native statistics and analytics tools.

This module provides direct filesystem access for analyzing notes and vaults,
following the Performance-First and Filesystem-Native constitutional principles.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import frontmatter


# Compiled regex patterns for performance
WIKILINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')
MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
TAG_PATTERN = re.compile(r'(?:^|\s)#([a-zA-Z0-9_/-]+)')
HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
CODE_BLOCK_PATTERN = re.compile(r'```[\s\S]*?```', re.MULTILINE)
INLINE_CODE_PATTERN = re.compile(r'`([^`]+)`')


def get_note_stats(filepath: str) -> Dict[str, Any]:
    """
    Get comprehensive statistics about a single note.

    Analyzes the note for words, characters, lines, links (wikilinks and markdown),
    tags (frontmatter and inline), headings, code blocks, and file metadata.

    Args:
        filepath: Path to the markdown file

    Returns:
        Dictionary with comprehensive note statistics:
            - word_count: Total words (excluding frontmatter and code blocks)
            - character_count: Total characters including spaces
            - character_count_no_spaces: Total characters excluding spaces
            - line_count: Total lines in file
            - links: Dict with wikilink_count, wikilinks list, markdown_link_count, total_links
            - tags: Dict with count, unique_tags list, all_tags list
            - headings: Dict with count, by_level dict, structure list
            - code: Dict with code_blocks count, inline_code count
            - file: Dict with size_bytes, size_kb, created, modified, accessed timestamps

    Raises:
        FileNotFoundError: If the file doesn't exist

    Examples:
        >>> stats = get_note_stats("Projects/Analysis.md")
        >>> print(f"Words: {stats['word_count']}, Links: {stats['links']['total_links']}")
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    # Read file content
    with open(filepath, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # Parse frontmatter
    post = frontmatter.loads(full_content)
    content = post.content  # Content without frontmatter

    # Count lines
    line_count = len(full_content.split('\n'))

    # Character counts
    character_count = len(full_content)
    character_count_no_spaces = len(full_content.replace(' ', '').replace('\t', ''))

    # Remove code blocks for word counting
    content_without_code = CODE_BLOCK_PATTERN.sub('', content)

    # Word count (excluding frontmatter and code blocks)
    words = re.findall(r'\b\w+\b', content_without_code)
    word_count = len(words)

    # Extract wikilinks
    wikilinks = []
    for match in WIKILINK_PATTERN.finditer(content):
        link_text = match.group(1)
        # Extract just the note name (before | or #)
        if '|' in link_text:
            note_name = link_text.split('|')[0]
        elif '#' in link_text:
            note_name = link_text.split('#')[0]
        else:
            note_name = link_text
        wikilinks.append(note_name.strip())

    wikilink_count = len(wikilinks)

    # Extract markdown links
    markdown_links = MARKDOWN_LINK_PATTERN.findall(content)
    markdown_link_count = len(markdown_links)

    total_links = wikilink_count + markdown_link_count

    # Extract tags from frontmatter
    frontmatter_tags = []
    if 'tags' in post.metadata:
        tags_value = post.metadata['tags']
        if isinstance(tags_value, list):
            frontmatter_tags.extend([str(t) for t in tags_value])
        elif isinstance(tags_value, str):
            frontmatter_tags.append(tags_value)
    if 'tag' in post.metadata:
        tag_value = post.metadata['tag']
        if isinstance(tag_value, list):
            frontmatter_tags.extend([str(t) for t in tag_value])
        elif isinstance(tag_value, str):
            frontmatter_tags.append(tag_value)

    # Extract inline tags (excluding code blocks)
    inline_tags = []
    for match in TAG_PATTERN.finditer(content_without_code):
        tag = match.group(1)
        inline_tags.append(tag)

    # Combine and deduplicate tags
    all_tags = []
    seen = set()
    for tag in frontmatter_tags + inline_tags:
        if tag not in seen:
            seen.add(tag)
            all_tags.append(tag)

    # Extract headings
    headings_by_level = {}
    headings_structure = []

    for match in HEADING_PATTERN.finditer(content):
        level = len(match.group(1))  # Number of # characters
        heading_text = match.group(2).strip()

        # Add to by_level dict
        if str(level) not in headings_by_level:
            headings_by_level[str(level)] = []
        headings_by_level[str(level)].append(heading_text)

        # Add to structure list
        headings_structure.append([level, heading_text])

    heading_count = len(headings_structure)

    # Count code blocks
    code_blocks = len(CODE_BLOCK_PATTERN.findall(content))

    # Count inline code (excluding code blocks)
    inline_code_matches = INLINE_CODE_PATTERN.findall(content_without_code)
    inline_code_count = len(inline_code_matches)

    # File metadata
    file_path = Path(filepath)
    stat = file_path.stat()

    file_stats = {
        "size_bytes": stat.st_size,
        "size_kb": round(stat.st_size / 1024, 2),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "accessed": datetime.fromtimestamp(stat.st_atime).isoformat()
    }

    return {
        "word_count": word_count,
        "character_count": character_count,
        "character_count_no_spaces": character_count_no_spaces,
        "line_count": line_count,
        "links": {
            "wikilink_count": wikilink_count,
            "wikilinks": wikilinks,
            "markdown_link_count": markdown_link_count,
            "total_links": total_links
        },
        "tags": {
            "count": len(all_tags),
            "unique_tags": all_tags,
            "all_tags": all_tags  # Same as unique_tags for single note
        },
        "headings": {
            "count": heading_count,
            "by_level": headings_by_level,
            "structure": headings_structure
        },
        "code": {
            "code_blocks": code_blocks,
            "inline_code": inline_code_count
        },
        "file": file_stats
    }


def get_vault_stats(vault_path: str) -> Dict[str, Any]:
    """
    Get aggregate statistics for the entire vault.

    Walks through the vault directory, analyzes all markdown files (excluding .obsidian),
    and aggregates statistics. Uses generator-based iteration for memory efficiency.

    Args:
        vault_path: Path to vault root directory

    Returns:
        Dictionary with vault-wide statistics:
            - total_notes: Total number of markdown files
            - total_words: Sum of words across all notes
            - total_links: Sum of all links (wikilinks + markdown)
            - unique_tags: Count of unique tags across vault
            - all_tags: Sorted list of all unique tags
            - avg_words_per_note: Average words per note

    Raises:
        FileNotFoundError: If the vault path doesn't exist

    Examples:
        >>> stats = get_vault_stats("/path/to/vault")
        >>> print(f"Total notes: {stats['total_notes']}, Avg words: {stats['avg_words_per_note']:.1f}")
    """
    if not os.path.exists(vault_path):
        raise FileNotFoundError(f"Vault not found: {vault_path}")

    total_notes = 0
    total_words = 0
    total_links = 0
    all_tags_set = set()

    # Walk through vault directory
    for root, dirs, files in os.walk(vault_path):
        # Skip .obsidian directory
        if '.obsidian' in root:
            continue

        # Filter to only .md files
        md_files = [f for f in files if f.endswith('.md')]

        for filename in md_files:
            filepath = os.path.join(root, filename)

            try:
                # Get stats for this note
                note_stats = get_note_stats(filepath)

                # Aggregate stats
                total_notes += 1
                total_words += note_stats['word_count']
                total_links += note_stats['links']['total_links']

                # Collect tags
                for tag in note_stats['tags']['unique_tags']:
                    all_tags_set.add(tag)

            except Exception:
                # Skip files that can't be processed
                continue

    # Calculate average words per note
    avg_words = total_words / total_notes if total_notes > 0 else 0.0

    # Convert tags set to sorted list
    all_tags_list = sorted(list(all_tags_set))

    return {
        "total_notes": total_notes,
        "total_words": total_words,
        "total_links": total_links,
        "unique_tags": len(all_tags_list),
        "all_tags": all_tags_list,
        "avg_words_per_note": round(avg_words, 2)
    }
