"""HTTP client for Obsidian Local REST API with graceful degradation.

This module provides a dedicated client for the hybrid plugin control system,
separate from the existing ObsidianAPI class in obsidian_api.py.

The existing ObsidianAPI handles vault-level operations (notes, search, vault structure).
This ObsidianAPIClient handles plugin-specific operations (Dataview queries, commands, etc.).
"""

import httpx
import os
from typing import Optional, Dict, Any, List


class ObsidianAPIClient:
    """HTTP client for Obsidian Local REST API plugin-specific operations.

    This client is designed for the hybrid architecture where filesystem-native
    tools have priority, and API-based tools provide enhanced functionality when
    Obsidian is running.
    """

    def __init__(self):
        """Initialize the API client with configuration from environment."""
        self.base_url = os.getenv("OBSIDIAN_API_URL", "http://localhost:27124")
        self.api_key = os.getenv("OBSIDIAN_REST_API_KEY")
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        self.timeout = 30.0

    async def is_available(self) -> bool:
        """Check if Obsidian Local REST API is reachable.

        Returns:
            True if API responds successfully, False otherwise

        Note:
            This method does NOT raise exceptions. It's used for graceful degradation
            checking, so connection failures return False rather than propagating.
        """
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    f"{self.base_url}/",
                    headers=self.headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            # Catch all exceptions (connection refused, timeout, etc.)
            return False

    async def execute_command(self, command_id: str) -> Dict[str, Any]:
        """Execute an Obsidian command by ID.

        Args:
            command_id: Command identifier (e.g., "editor:toggle-bold")

        Returns:
            Response data from the API

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self.base_url}/commands/{command_id}/",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def search_simple(self, query: str, context_length: int = 100) -> List[Dict[str, Any]]:
        """Execute simple text search via API.

        Args:
            query: Search query string
            context_length: Number of characters of context to return

        Returns:
            List of search results with context

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self.base_url}/search/simple/",
                headers=self.headers,
                json={"query": query, "contextLength": context_length},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def execute_dataview_query(self, query: str) -> Dict[str, Any]:
        """Execute Dataview Query Language (DQL) query.

        Args:
            query: DQL query (e.g., "LIST FROM #project")

        Returns:
            Query results in structured format

        Raises:
            httpx.HTTPStatusError: If the request fails

        Note:
            Requires Dataview plugin to be installed and active in Obsidian.
        """
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self.base_url}/search/",
                headers={
                    **self.headers,
                    "Content-Type": "application/vnd.olrapi.dataview.dql+txt"
                },
                data=query,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def execute_templater(self, template_path: str, target_path: str,
                                variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute Templater template rendering.

        Args:
            template_path: Path to template file in vault
            target_path: Path where rendered template should be created
            variables: Optional template variables

        Returns:
            Response data from the API

        Raises:
            httpx.HTTPStatusError: If the request fails

        Note:
            Requires Templater plugin to be installed and active in Obsidian.
            Templater must have "Trigger Templater on new file creation" enabled.
        """
        payload = {
            "templatePath": template_path,
            "targetPath": target_path
        }
        if variables:
            payload["variables"] = variables

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self.base_url}/templater/execute/",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def list_commands(self) -> List[Dict[str, Any]]:
        """List all available Obsidian commands.

        Returns:
            List of command objects with id, name, and other metadata

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{self.base_url}/commands/",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def get_active_file(self) -> Optional[Dict[str, Any]]:
        """Get the currently active file in Obsidian.

        Returns:
            File information or None if no file is active

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{self.base_url}/active/",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def open_file(self, file_path: str, new_leaf: bool = False) -> Dict[str, Any]:
        """Open a file in Obsidian.

        Args:
            file_path: Path to file in vault
            new_leaf: Whether to open in a new pane

        Returns:
            Response data from the API

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self.base_url}/open/{file_path}",
                headers=self.headers,
                params={"newLeaf": str(new_leaf).lower()},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def get_file(self, file_path: str) -> Dict[str, Any]:
        """Get file content via API.

        Args:
            file_path: Path to file in vault (relative)

        Returns:
            File content and metadata

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{self.base_url}/vault/{file_path}",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def put_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Create or update file content via API.

        Args:
            file_path: Path to file in vault (relative)
            content: File content to write

        Returns:
            Response data from the API

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.put(
                f"{self.base_url}/vault/{file_path}",
                headers={**self.headers, "Content-Type": "text/markdown"},
                content=content,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
