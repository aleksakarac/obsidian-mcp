"""Enhanced link tracking and relationship mapping tools (filesystem-native).

This module provides advanced link analysis beyond basic backlinks/outgoing links:
- Link graph generation (discovers connections between notes)
- Orphaned notes detection (no inlinks or outlinks)
- Hub notes identification (high outlink count)
- Link type breakdown (wikilinks, markdown links, embeds)
- Link health analysis (broken links, circular references)

All operations are filesystem-native for maximum performance and offline capability.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from ..utils.patterns import (
    WIKILINK_PATTERN,
    MARKDOWN_LINK,
    EMBED_PATTERN,
)


# ============================================================================
# Core Link Extraction Functions
# ============================================================================

def extract_all_links(content: str, source_file: str) -> Dict[str, List[str]]:
    """Extract all link types from content.

    Args:
        content: File content to parse
        source_file: Source file path for context

    Returns:
        Dictionary with keys: wikilinks, markdown_links, embeds, all_links
    """
    # Extract wikilinks (including aliases)
    wikilinks = []
    for match in WIKILINK_PATTERN.finditer(content):
        target = match.group(1)
        # Strip anchor/heading references
        if '#' in target:
            target = target.split('#')[0]
        if '|' in target:
            target = target.split('|')[0]
        target = target.strip()
        if target:
            wikilinks.append(target)

    # Extract markdown links
    markdown_links = []
    for match in MARKDOWN_LINK.finditer(content):
        url = match.group(2)
        # Only include relative markdown links (not http/https)
        if not url.startswith(('http://', 'https://')):
            # Remove .md extension if present
            if url.endswith('.md'):
                url = url[:-3]
            # Strip anchor references
            if '#' in url:
                url = url.split('#')[0]
            url = url.strip()
            if url:
                markdown_links.append(url)

    # Extract embeds (![[file]])
    embeds = []
    for match in EMBED_PATTERN.finditer(content):
        target = match.group(1)
        # Strip anchor references
        if '#' in target:
            target = target.split('#')[0]
        if '|' in target:
            target = target.split('|')[0]
        target = target.strip()
        if target:
            embeds.append(target)

    # Combine all (deduplicated)
    all_links = list(set(wikilinks + markdown_links + embeds))

    return {
        "wikilinks": wikilinks,
        "markdown_links": markdown_links,
        "embeds": embeds,
        "all_links": all_links,
    }


def find_note_by_name(vault_path: str, note_name: str) -> Optional[str]:
    """Find a note file by name (supports both with and without .md).

    Args:
        vault_path: Root vault directory
        note_name: Note name to find (with or without .md)

    Returns:
        Relative path to note from vault root, or None if not found
    """
    vault_path = Path(vault_path)

    # Try exact match first
    candidates = [
        note_name if note_name.endswith('.md') else f"{note_name}.md",
        note_name[:-3] if note_name.endswith('.md') else note_name,
    ]

    for md_file in vault_path.rglob('*.md'):
        # Skip .obsidian directory
        if '.obsidian' in md_file.parts:
            continue

        relative_path = str(md_file.relative_to(vault_path))
        file_name = md_file.stem

        # Check if filename matches any candidate
        for candidate in candidates:
            if file_name == candidate or file_name == candidate.replace('.md', ''):
                return relative_path
            # Also check full relative path
            if relative_path == candidate or relative_path.replace('.md', '') == candidate.replace('.md', ''):
                return relative_path

    return None


# ============================================================================
# Link Graph Generation
# ============================================================================

def build_link_graph(vault_path: str) -> Dict[str, Dict[str, any]]:
    """Build complete link graph for vault.

    Args:
        vault_path: Root vault directory

    Returns:
        Graph dict: {file_path: {outlinks: [...], inlinks: [...], link_types: {...}}}
    """
    vault_path = Path(vault_path)
    graph = defaultdict(lambda: {
        "outlinks": [],
        "inlinks": [],
        "link_types": {"wikilinks": 0, "markdown_links": 0, "embeds": 0},
    })

    # First pass: collect all files
    all_notes = {}
    for md_file in vault_path.rglob('*.md'):
        if '.obsidian' in md_file.parts:
            continue
        relative_path = str(md_file.relative_to(vault_path))
        note_name = md_file.stem
        all_notes[note_name] = relative_path
        all_notes[relative_path] = relative_path

    # Second pass: extract links
    for md_file in vault_path.rglob('*.md'):
        if '.obsidian' in md_file.parts:
            continue

        relative_path = str(md_file.relative_to(vault_path))

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue

        links = extract_all_links(content, relative_path)

        # Track link types
        graph[relative_path]["link_types"]["wikilinks"] = len(links["wikilinks"])
        graph[relative_path]["link_types"]["markdown_links"] = len(links["markdown_links"])
        graph[relative_path]["link_types"]["embeds"] = len(links["embeds"])

        # Resolve links to actual files
        for link in links["all_links"]:
            # Try to find target file
            target_path = all_notes.get(link) or all_notes.get(link.replace('.md', ''))

            if target_path:
                # Add outlink from source
                if target_path not in graph[relative_path]["outlinks"]:
                    graph[relative_path]["outlinks"].append(target_path)

                # Add inlink to target
                if relative_path not in graph[target_path]["inlinks"]:
                    graph[target_path]["inlinks"].append(relative_path)

    return dict(graph)


# ============================================================================
# Link Analysis Functions
# ============================================================================

def find_orphaned_notes(vault_path: str) -> List[Dict[str, any]]:
    """Find notes with no inlinks or outlinks (orphaned/isolated).

    Args:
        vault_path: Root vault directory

    Returns:
        List of orphaned note details
    """
    graph = build_link_graph(vault_path)

    orphaned = []
    for file_path, data in graph.items():
        if len(data["inlinks"]) == 0 and len(data["outlinks"]) == 0:
            orphaned.append({
                "file_path": file_path,
                "inlink_count": 0,
                "outlink_count": 0,
            })

    return orphaned


def find_hub_notes(vault_path: str, min_outlinks: int = 5) -> List[Dict[str, any]]:
    """Find notes with high outlink counts (hub notes).

    Args:
        vault_path: Root vault directory
        min_outlinks: Minimum outlink count to be considered a hub

    Returns:
        List of hub note details sorted by outlink count (descending)
    """
    graph = build_link_graph(vault_path)

    hubs = []
    for file_path, data in graph.items():
        outlink_count = len(data["outlinks"])
        if outlink_count >= min_outlinks:
            hubs.append({
                "file_path": file_path,
                "outlink_count": outlink_count,
                "inlink_count": len(data["inlinks"]),
                "outlinks": data["outlinks"],
            })

    # Sort by outlink count descending
    hubs.sort(key=lambda x: x["outlink_count"], reverse=True)

    return hubs


def analyze_link_health(vault_path: str) -> Dict[str, any]:
    """Analyze overall link health across vault.

    Args:
        vault_path: Root vault directory

    Returns:
        Health metrics including broken links, orphaned notes, link density
    """
    vault_path = Path(vault_path)
    graph = build_link_graph(vault_path)

    # Count notes
    total_notes = len(graph)

    # Count links
    total_outlinks = sum(len(data["outlinks"]) for data in graph.values())
    total_inlinks = sum(len(data["inlinks"]) for data in graph.values())

    # Find orphaned notes
    orphaned_count = sum(1 for data in graph.values()
                        if len(data["inlinks"]) == 0 and len(data["outlinks"]) == 0)

    # Find notes with no inlinks (potential orphans)
    no_inlinks_count = sum(1 for data in graph.values() if len(data["inlinks"]) == 0)

    # Find notes with no outlinks
    no_outlinks_count = sum(1 for data in graph.values() if len(data["outlinks"]) == 0)

    # Calculate link density (average links per note)
    avg_outlinks = total_outlinks / total_notes if total_notes > 0 else 0
    avg_inlinks = total_inlinks / total_notes if total_notes > 0 else 0

    # Find broken links
    broken_links = []
    all_notes = set(graph.keys())

    for source_path in vault_path.rglob('*.md'):
        if '.obsidian' in source_path.parts:
            continue

        relative_source = str(source_path.relative_to(vault_path))

        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue

        links = extract_all_links(content, relative_source)

        for link in links["all_links"]:
            # Check if link target exists
            target_path = find_note_by_name(str(vault_path), link)
            if not target_path or target_path not in all_notes:
                broken_links.append({
                    "source_file": relative_source,
                    "target": link,
                })

    return {
        "total_notes": total_notes,
        "total_links": total_outlinks,
        "orphaned_notes": orphaned_count,
        "notes_with_no_inlinks": no_inlinks_count,
        "notes_with_no_outlinks": no_outlinks_count,
        "broken_links_count": len(broken_links),
        "average_outlinks_per_note": round(avg_outlinks, 2),
        "average_inlinks_per_note": round(avg_inlinks, 2),
        "link_density_score": round((total_outlinks / total_notes) if total_notes > 0 else 0, 2),
    }


def get_note_connections(vault_path: str, note_name: str, depth: int = 1) -> Dict[str, any]:
    """Get all connections for a note up to specified depth.

    Args:
        vault_path: Root vault directory
        note_name: Note name to analyze (with or without .md)
        depth: Connection depth (1 = direct, 2 = second-degree, etc.)

    Returns:
        Connection graph with inlinks, outlinks, and multi-level connections
    """
    graph = build_link_graph(vault_path)

    # Find the note
    note_path = find_note_by_name(vault_path, note_name)
    if not note_path:
        raise ValueError(f"Note not found: {note_name}")

    if note_path not in graph:
        return {
            "note": note_path,
            "direct_inlinks": [],
            "direct_outlinks": [],
            "connections": {},
        }

    data = graph[note_path]

    # Build multi-level connections
    connections = {}
    visited = set()

    def explore_connections(current_path: str, current_depth: int):
        """Recursively explore connections."""
        if current_depth > depth or current_path in visited:
            return

        visited.add(current_path)

        if current_path not in graph:
            return

        current_data = graph[current_path]

        connections[current_path] = {
            "depth": current_depth,
            "inlinks": current_data["inlinks"],
            "outlinks": current_data["outlinks"],
        }

        # Recurse on outlinks
        for outlink in current_data["outlinks"]:
            explore_connections(outlink, current_depth + 1)

    # Start exploration from target note
    for outlink in data["outlinks"]:
        explore_connections(outlink, 1)

    return {
        "note": note_path,
        "direct_inlinks": data["inlinks"],
        "direct_outlinks": data["outlinks"],
        "direct_inlink_count": len(data["inlinks"]),
        "direct_outlink_count": len(data["outlinks"]),
        "connection_depth": depth,
        "total_connections_explored": len(connections),
        "connections": connections,
    }


# ============================================================================
# MCP Tool Functions
# ============================================================================

async def get_link_graph_fs_tool(vault_path: Optional[str] = None) -> Dict[str, any]:
    """Get complete link graph for vault (filesystem-native).

    Args:
        vault_path: Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)

    Returns:
        Complete link graph with all note connections
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    if not os.path.exists(vault):
        raise ValueError(f"Vault not found: {vault}")

    graph = build_link_graph(vault)

    return {
        "vault_path": vault,
        "total_notes": len(graph),
        "graph": graph,
    }


async def find_orphaned_notes_fs_tool(vault_path: Optional[str] = None) -> Dict[str, any]:
    """Find orphaned notes with no connections (filesystem-native).

    Args:
        vault_path: Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)

    Returns:
        List of orphaned notes
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    if not os.path.exists(vault):
        raise ValueError(f"Vault not found: {vault}")

    orphaned = find_orphaned_notes(vault)

    return {
        "vault_path": vault,
        "orphaned_count": len(orphaned),
        "orphaned_notes": orphaned,
    }


async def find_hub_notes_fs_tool(
    min_outlinks: int = 5,
    vault_path: Optional[str] = None
) -> Dict[str, any]:
    """Find hub notes with high outlink counts (filesystem-native).

    Args:
        min_outlinks: Minimum outlink count to be considered a hub (default: 5)
        vault_path: Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)

    Returns:
        List of hub notes sorted by outlink count
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    if not os.path.exists(vault):
        raise ValueError(f"Vault not found: {vault}")

    hubs = find_hub_notes(vault, min_outlinks)

    return {
        "vault_path": vault,
        "min_outlinks": min_outlinks,
        "hub_count": len(hubs),
        "hubs": hubs,
    }


async def analyze_link_health_fs_tool(vault_path: Optional[str] = None) -> Dict[str, any]:
    """Analyze vault-wide link health metrics (filesystem-native).

    Args:
        vault_path: Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)

    Returns:
        Health metrics including link density, broken links, orphaned notes
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    if not os.path.exists(vault):
        raise ValueError(f"Vault not found: {vault}")

    health = analyze_link_health(vault)

    return {
        "vault_path": vault,
        **health,
    }


async def get_note_connections_fs_tool(
    note_name: str,
    depth: int = 1,
    vault_path: Optional[str] = None
) -> Dict[str, any]:
    """Get connection graph for a specific note (filesystem-native).

    Args:
        note_name: Note name to analyze (with or without .md)
        depth: Connection depth to explore (1 = direct, 2 = second-degree, etc.)
        vault_path: Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)

    Returns:
        Connection graph with multi-level links
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    if not os.path.exists(vault):
        raise ValueError(f"Vault not found: {vault}")

    connections = get_note_connections(vault, note_name, depth)

    return connections
