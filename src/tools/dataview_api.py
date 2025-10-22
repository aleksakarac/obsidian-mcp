"""Dataview Query Language (DQL) execution tools via Obsidian API.

This module provides tools for executing Dataview queries that require the
Dataview plugin and Obsidian to be running. These complement the filesystem-native
Dataview field tools with full DQL query capabilities.

DQL Queries supported:
- LIST: Simple lists of pages
- TABLE: Tabular data views
- TASK: Task queries (different from Tasks plugin)
- CALENDAR: Date-based views

All tools require Obsidian with Dataview plugin running and API access.
"""

import os
from typing import Dict, List, Optional, Any

from ..utils.api_availability import require_api_available, get_api_client
from fastmcp.exceptions import McpError
from ..utils.error_utils import create_error


# ============================================================================
# DQL Query Execution
# ============================================================================

async def execute_dataview_query(query: str) -> Dict[str, Any]:
    """Execute a Dataview Query Language (DQL) query.

    Args:
        query: DQL query string (e.g., "LIST FROM #project")

    Returns:
        Query results in structured format

    Raises:
        McpError: If API is unavailable or query fails
    """
    await require_api_available()

    client = get_api_client()

    try:
        result = await client.execute_dataview_query(query)
        return result
    except Exception as e:
        raise create_error(f"Dataview query failed: {str(e)}")


# ============================================================================
# Query Helper Functions
# ============================================================================

def validate_dql_query(query: str) -> bool:
    """Validate basic DQL query syntax.

    Args:
        query: DQL query string

    Returns:
        True if query appears valid, False otherwise

    Note:
        This is basic validation - the Dataview plugin performs full validation.
    """
    query = query.strip()

    # Must start with a query type
    valid_types = ["LIST", "TABLE", "TASK", "CALENDAR"]
    starts_with_type = any(query.upper().startswith(t) for t in valid_types)

    if not starts_with_type:
        return False

    # Basic sanity checks
    if len(query) < 4:  # Minimum: "LIST"
        return False

    return True


def build_dql_list_query(
    from_clause: Optional[str] = None,
    where_clause: Optional[str] = None,
    sort_clause: Optional[str] = None,
    limit: Optional[int] = None,
) -> str:
    """Build a DQL LIST query from components.

    Args:
        from_clause: FROM clause (e.g., "#project", '"folder"')
        where_clause: WHERE clause (e.g., "status = 'active'")
        sort_clause: SORT clause (e.g., "file.name ASC")
        limit: LIMIT value

    Returns:
        Complete DQL query string

    Examples:
        >>> build_dql_list_query(from_clause="#project", where_clause="status = 'active'")
        'LIST FROM #project WHERE status = 'active''
    """
    parts = ["LIST"]

    if from_clause:
        parts.append(f"FROM {from_clause}")

    if where_clause:
        parts.append(f"WHERE {where_clause}")

    if sort_clause:
        parts.append(f"SORT {sort_clause}")

    if limit:
        parts.append(f"LIMIT {limit}")

    return " ".join(parts)


def build_dql_table_query(
    fields: List[str],
    from_clause: Optional[str] = None,
    where_clause: Optional[str] = None,
    sort_clause: Optional[str] = None,
    limit: Optional[int] = None,
) -> str:
    """Build a DQL TABLE query from components.

    Args:
        fields: List of fields to display (e.g., ["file.name", "status", "due"])
        from_clause: FROM clause
        where_clause: WHERE clause
        sort_clause: SORT clause
        limit: LIMIT value

    Returns:
        Complete DQL query string

    Examples:
        >>> build_dql_table_query(["file.name", "status"], from_clause="#project")
        'TABLE file.name, status FROM #project'
    """
    if not fields:
        raise ValueError("TABLE query requires at least one field")

    fields_str = ", ".join(fields)
    parts = [f"TABLE {fields_str}"]

    if from_clause:
        parts.append(f"FROM {from_clause}")

    if where_clause:
        parts.append(f"WHERE {where_clause}")

    if sort_clause:
        parts.append(f"SORT {sort_clause}")

    if limit:
        parts.append(f"LIMIT {limit}")

    return " ".join(parts)


# ============================================================================
# MCP Tool Functions
# ============================================================================

async def execute_dataview_query_api_tool(query: str) -> Dict[str, Any]:
    """Execute a Dataview Query Language (DQL) query (requires Obsidian + Dataview plugin).

    Args:
        query: DQL query string

    Returns:
        Query results in structured format from Dataview plugin

    Raises:
        McpError: If API unavailable or query fails
    """
    # Validate query
    if not validate_dql_query(query):
        raise ValueError(f"Invalid DQL query syntax: {query}")

    result = await execute_dataview_query(query)

    return {
        "query": query,
        "success": True,
        "results": result,
    }


async def list_from_tag_api_tool(
    tag: str,
    where_clause: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute a DQL LIST query for notes with a specific tag (requires Obsidian + Dataview).

    Args:
        tag: Tag to query (with or without # prefix)
        where_clause: Optional WHERE filter
        sort_by: Optional SORT clause
        limit: Optional result limit

    Returns:
        List of matching notes
    """
    # Ensure tag has # prefix
    if not tag.startswith('#'):
        tag = f"#{tag}"

    query = build_dql_list_query(
        from_clause=tag,
        where_clause=where_clause,
        sort_clause=sort_by,
        limit=limit,
    )

    result = await execute_dataview_query(query)

    return {
        "tag": tag,
        "query": query,
        "results": result,
    }


async def list_from_folder_api_tool(
    folder: str,
    where_clause: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute a DQL LIST query for notes in a folder (requires Obsidian + Dataview).

    Args:
        folder: Folder path to query
        where_clause: Optional WHERE filter
        sort_by: Optional SORT clause
        limit: Optional result limit

    Returns:
        List of matching notes
    """
    # Quote folder path
    folder_clause = f'"{folder}"'

    query = build_dql_list_query(
        from_clause=folder_clause,
        where_clause=where_clause,
        sort_clause=sort_by,
        limit=limit,
    )

    result = await execute_dataview_query(query)

    return {
        "folder": folder,
        "query": query,
        "results": result,
    }


async def table_query_api_tool(
    fields: List[str],
    from_clause: Optional[str] = None,
    where_clause: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute a DQL TABLE query (requires Obsidian + Dataview plugin).

    Args:
        fields: List of fields to display
        from_clause: FROM clause (e.g., "#project", '"folder"')
        where_clause: Optional WHERE filter
        sort_by: Optional SORT clause
        limit: Optional result limit

    Returns:
        Table results with specified fields
    """
    query = build_dql_table_query(
        fields=fields,
        from_clause=from_clause,
        where_clause=where_clause,
        sort_clause=sort_by,
        limit=limit,
    )

    result = await execute_dataview_query(query)

    return {
        "fields": fields,
        "query": query,
        "results": result,
    }
