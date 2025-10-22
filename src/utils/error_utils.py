"""Error handling utilities for MCP server."""

from fastmcp.exceptions import McpError
from mcp.types import ErrorData


def create_error(message: str, code: int = -1) -> McpError:
    """Helper to create McpError with proper ErrorData structure.

    Args:
        message: Error message
        code: Error code (default: -1 for generic error)

    Returns:
        Properly constructed McpError

    Example:
        >>> raise create_error("File not found")
        >>> raise create_error("API unavailable", code=503)
    """
    return McpError(ErrorData(code=code, message=message))
