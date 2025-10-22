"""Canvas file manipulation tools (filesystem-native).

This module provides tools for working with Obsidian Canvas files (.canvas),
which use the JSON Canvas v1.0 specification. Canvas files are JSON documents
containing nodes (text, files, links, groups) and edges (connections between nodes).

JSON Canvas Spec: https://jsoncanvas.org/spec/1.0/

All operations are filesystem-native and work offline.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Use simple dict structures for Canvas since specific node type models may not be defined


# ============================================================================
# Canvas Parsing
# ============================================================================

def parse_canvas_file(file_path: str) -> Dict[str, Any]:
    """Parse a Canvas file into structured data.

    Args:
        file_path: Absolute path to .canvas file

    Returns:
        Dict with nodes, edges, and metadata

    Raises:
        FileNotFoundError: If canvas file doesn't exist
        ValueError: If JSON is invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Canvas file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return {
        "file_path": file_path,
        "nodes": data.get("nodes", []),
        "edges": data.get("edges", []),
        "node_count": len(data.get("nodes", [])),
        "edge_count": len(data.get("edges", [])),
    }


def save_canvas_file(canvas: Dict[str, Any]) -> None:
    """Save a canvas dict to file.

    Args:
        canvas: Canvas dict to save

    Raises:
        ValueError: If file_path not set
    """
    if not canvas.get("file_path"):
        raise ValueError("Canvas file_path must be set")

    # Convert to JSON Canvas format
    data = {
        "nodes": canvas["nodes"],
        "edges": canvas["edges"],
    }

    with open(canvas["file_path"], 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


# ============================================================================
# Node Operations
# ============================================================================

def add_text_node(canvas: Dict[str, Any], text: str, x: int, y: int, width: int = 250, height: int = 60) -> str:
    """Add a text node to canvas."""
    import uuid
    node_id = str(uuid.uuid4())
    canvas["nodes"].append({"id": node_id, "type": "text", "text": text, "x": x, "y": y, "width": width, "height": height})
    return node_id

def add_file_node(canvas: Dict[str, Any], file: str, x: int, y: int, width: int = 400, height: int = 400) -> str:
    """Add a file node to canvas."""
    import uuid
    node_id = str(uuid.uuid4())
    canvas["nodes"].append({"id": node_id, "type": "file", "file": file, "x": x, "y": y, "width": width, "height": height})
    return node_id

def add_edge(canvas: Dict[str, Any], from_node: str, to_node: str, label: Optional[str] = None) -> str:
    """Add an edge between two nodes."""
    import uuid
    edge_id = str(uuid.uuid4())
    edge = {"id": edge_id, "fromNode": from_node, "toNode": to_node}
    if label:
        edge["label"] = label
    canvas["edges"].append(edge)
    return edge_id

def remove_node(canvas: Dict[str, Any], node_id: str) -> bool:
    """Remove a node and its connected edges."""
    initial_count = len(canvas["nodes"])
    canvas["nodes"] = [n for n in canvas["nodes"] if n.get("id") != node_id]
    if len(canvas["nodes"]) == initial_count:
        return False
    canvas["edges"] = [e for e in canvas["edges"] if e.get("fromNode") != node_id and e.get("toNode") != node_id]
    return True

def get_node_connections(canvas: Dict[str, Any], node_id: str) -> Dict[str, List[str]]:
    """Get all connections for a node."""
    incoming = [e.get("fromNode") for e in canvas["edges"] if e.get("toNode") == node_id]
    outgoing = [e.get("toNode") for e in canvas["edges"] if e.get("fromNode") == node_id]
    return {"incoming": incoming, "outgoing": outgoing}


# ============================================================================
# MCP Tool Functions
# ============================================================================

async def parse_canvas_fs_tool(
    file_path: str,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Parse a Canvas file (filesystem-native, offline).

    Args:
        file_path: Path to .canvas file (relative to vault)
        vault_path: Path to vault root (optional)

    Returns:
        Canvas structure with nodes and edges

    Raises:
        ValueError: If file doesn't exist or is invalid
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    # Resolve absolute path
    if not os.path.isabs(file_path):
        file_path = os.path.join(vault, file_path)

    try:
        canvas = parse_canvas_file(file_path)
        return canvas
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        raise ValueError(str(e))


async def add_canvas_node_fs_tool(
    file_path: str,
    node_type: str,
    content: str,
    x: int,
    y: int,
    width: int = 250,
    height: int = 60,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a node to a Canvas file (filesystem-native, offline).

    Args:
        file_path: Path to .canvas file (relative to vault)
        node_type: Node type ("text", "file", or "link")
        content: Node content (text, file path, or URL)
        x: X position
        y: Y position
        width: Node width
        height: Node height
        vault_path: Path to vault root (optional)

    Returns:
        Success status and node ID

    Raises:
        ValueError: If file doesn't exist or invalid node type
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    # Resolve absolute path
    if not os.path.isabs(file_path):
        file_path = os.path.join(vault, file_path)

    try:
        canvas = parse_canvas_file(file_path)

        # Add node based on type
        if node_type == "text":
            node_id = add_text_node(canvas, content, x, y, width, height)
        elif node_type == "file":
            node_id = add_file_node(canvas, content, x, y, width, height)
        else:
            raise ValueError(f"Unsupported node type: {node_type}")

        # Save canvas
        save_canvas_file(canvas)

        return {
            "success": True,
            "file_path": file_path,
            "node_id": node_id,
            "node_type": node_type,
        }
    except (FileNotFoundError, ValueError) as e:
        raise ValueError(str(e))


async def add_canvas_edge_fs_tool(
    file_path: str,
    from_node: str,
    to_node: str,
    label: Optional[str] = None,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Add an edge between nodes (filesystem-native, offline).

    Args:
        file_path: Path to .canvas file (relative to vault)
        from_node: Source node ID
        to_node: Target node ID
        label: Optional edge label
        vault_path: Path to vault root (optional)

    Returns:
        Success status and edge ID

    Raises:
        ValueError: If file or nodes don't exist
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    # Resolve absolute path
    if not os.path.isabs(file_path):
        file_path = os.path.join(vault, file_path)

    try:
        canvas = parse_canvas_file(file_path)

        # Verify nodes exist
        node_ids = {n.get("id") for n in canvas["nodes"]}
        if from_node not in node_ids:
            raise ValueError(f"Source node not found: {from_node}")
        if to_node not in node_ids:
            raise ValueError(f"Target node not found: {to_node}")

        # Add edge
        edge_id = add_edge(canvas, from_node, to_node, label)

        # Save canvas
        save_canvas_file(canvas)

        return {
            "success": True,
            "file_path": file_path,
            "edge_id": edge_id,
            "from_node": from_node,
            "to_node": to_node,
        }
    except (FileNotFoundError, ValueError) as e:
        raise ValueError(str(e))


async def remove_canvas_node_fs_tool(
    file_path: str,
    node_id: str,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Remove a node from Canvas (filesystem-native, offline).

    Args:
        file_path: Path to .canvas file (relative to vault)
        node_id: Node ID to remove
        vault_path: Path to vault root (optional)

    Returns:
        Success status

    Raises:
        ValueError: If file or node doesn't exist
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    # Resolve absolute path
    if not os.path.isabs(file_path):
        file_path = os.path.join(vault, file_path)

    try:
        canvas = parse_canvas_file(file_path)

        # Remove node
        removed = remove_node(canvas, node_id)

        if not removed:
            raise ValueError(f"Node not found: {node_id}")

        # Save canvas
        save_canvas_file(canvas)

        return {
            "success": True,
            "file_path": file_path,
            "node_id": node_id,
        }
    except (FileNotFoundError, ValueError) as e:
        raise ValueError(str(e))


async def get_canvas_node_connections_fs_tool(
    file_path: str,
    node_id: str,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Get connections for a canvas node (filesystem-native, offline).

    Args:
        file_path: Path to .canvas file (relative to vault)
        node_id: Node ID to query
        vault_path: Path to vault root (optional)

    Returns:
        Incoming and outgoing connections

    Raises:
        ValueError: If file or node doesn't exist
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

    # Resolve absolute path
    if not os.path.isabs(file_path):
        file_path = os.path.join(vault, file_path)

    try:
        canvas = parse_canvas_file(file_path)

        # Verify node exists
        node_ids = {n.get("id") for n in canvas["nodes"]}
        if node_id not in node_ids:
            raise ValueError(f"Node not found: {node_id}")

        # Get connections
        connections = get_node_connections(canvas, node_id)

        return {
            "file_path": file_path,
            "node_id": node_id,
            "incoming_count": len(connections["incoming"]),
            "outgoing_count": len(connections["outgoing"]),
            **connections,
        }
    except (FileNotFoundError, ValueError) as e:
        raise ValueError(str(e))
