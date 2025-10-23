"""Error handling utilities for MCP server."""

import httpx
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


def handle_api_error(e: Exception) -> McpError:
    """Convert API errors to user-friendly McpError.

    Args:
        e: Exception from API call

    Returns:
        McpError with helpful message

    Example:
        >>> try:
        ...     await api.create_note(...)
        ... except Exception as e:
        ...     raise handle_api_error(e)
    """
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 401:
            return create_error(
                "This tool requires Obsidian to be running with the Local REST API plugin enabled.\n\n"
                "To use this feature:\n"
                "1. Ensure Obsidian is running\n"
                "2. Install the 'Local REST API' plugin from Community Plugins\n"
                "3. Enable the plugin in Settings > Community Plugins\n"
                "4. Configure the API key in plugin settings\n"
                "5. Set environment variables:\n"
                "   - OBSIDIAN_API_URL (default: http://localhost:27124)\n"
                "   - OBSIDIAN_REST_API_KEY (from plugin settings)",
                code=401
            )
        return create_error(
            f"API request failed ({e.response.status_code}): {str(e)}",
            code=e.response.status_code
        )

    if isinstance(e, (httpx.ConnectError, httpx.TimeoutException, ConnectionError)):
        return create_error(
            "Cannot connect to Obsidian Local REST API.\n\n"
            "Please ensure:\n"
            "1. Obsidian is running\n"
            "2. Local REST API plugin is enabled\n"
            "3. API URL is correct (check OBSIDIAN_API_URL environment variable)",
            code=503
        )

    # Generic error
    return create_error(str(e))
