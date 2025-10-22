"""API availability checking and graceful degradation utilities.

This module provides utilities for checking if the Obsidian Local REST API
is available and raising helpful error messages when API-based tools are
called without the API running.
"""

from fastmcp.exceptions import McpError
from .obsidian_api_client import ObsidianAPIClient


# Singleton API client instance
_api_client: ObsidianAPIClient = None


def get_api_client() -> ObsidianAPIClient:
    """Get or create singleton API client instance.

    Returns:
        Singleton ObsidianAPIClient instance

    Note:
        Uses singleton pattern to reuse HTTP client configuration
        across multiple tool calls in the same session.
    """
    global _api_client
    if _api_client is None:
        _api_client = ObsidianAPIClient()
    return _api_client


async def require_api_available():
    """Check if API is available and raise helpful error if not.

    Raises:
        McpError: If API is not reachable with instructions for user

    Note:
        This is the standard pre-check for all API-based tools (_api_tool suffix).
        It provides clear, actionable error messages to help users understand
        why the tool failed and how to fix it.
    """
    client = get_api_client()
    if not await client.is_available():
        raise McpError(
            error_code="API_UNAVAILABLE",
            message=(
                "This tool requires Obsidian to be running with the Local REST API plugin enabled.\n\n"
                "To use this feature:\n"
                "1. Ensure Obsidian is running\n"
                "2. Install the 'Local REST API' plugin from Community Plugins\n"
                "3. Enable the plugin in Settings > Community Plugins\n"
                "4. Configure the API key in plugin settings\n"
                "5. Set environment variables:\n"
                "   - OBSIDIAN_API_URL (default: http://localhost:27124)\n"
                "   - OBSIDIAN_REST_API_KEY (from plugin settings)\n\n"
                "Note: Many features work without the API using filesystem-native tools."
            )
        )


async def check_api_available() -> bool:
    """Check if API is available without raising an error.

    Returns:
        True if API is reachable, False otherwise

    Note:
        Use this for conditional logic where you want to try API-based
        approach first and fall back to filesystem-native approach.
    """
    client = get_api_client()
    return await client.is_available()
