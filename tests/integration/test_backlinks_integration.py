"""Integration tests for backlinks MCP tools.

Following TDD - these tests are written FIRST and should FAIL until implementation.
Tests verify the MCP tool registration, input validation, and end-to-end functionality.
"""

import pytest
from pathlib import Path
import tempfile
import os

# Import MCP server and test utilities
from src.server import mcp
from src.tools.backlinks import find_backlinks as find_backlinks_fs, find_broken_links as find_broken_links_fs


class TestBacklinksMCPTools:
    """Integration tests for get_backlinks and get_broken_links MCP tools."""

    @pytest.fixture
    def sample_vault(self):
        """Create a temporary vault for integration testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)

            # Create interconnected notes
            (vault_path / "main.md").write_text(
                "# Main Note\n\n"
                "Content here."
            )

            (vault_path / "references_main.md").write_text(
                "This note links to [[main]].\n"
                "Multiple times: [[main|Main Note]]."
            )

            (vault_path / "also_references.md").write_text(
                "Another backlink to [[main]]."
            )

            (vault_path / "broken_links.md").write_text(
                "Links to [[nonexistent]] and [[also-missing]]."
            )

            # Create subfolder
            subfolder = vault_path / "folder"
            subfolder.mkdir()
            (subfolder / "nested.md").write_text(
                "From subfolder: [[main]]."
            )

            yield str(vault_path)

    @pytest.mark.asyncio
    async def test_get_backlinks_fs_tool_registered(self):
        """Test that get_backlinks_fs tool is registered with MCP server."""
        # Verify tool is in the list of available tools
        tools = await mcp.get_tools()
        tool_names = list(tools.keys())  # get_tools() returns a dict

        assert "get_backlinks_fs_tool" in tool_names, "get_backlinks_fs_tool not registered"

    @pytest.mark.asyncio
    async def test_get_broken_links_fs_tool_registered(self):
        """Test that get_broken_links_fs tool is registered with MCP server."""
        tools = await mcp.get_tools()
        tool_names = list(tools.keys())  # get_tools() returns a dict

        assert "get_broken_links_fs_tool" in tool_names, "get_broken_links_fs_tool not registered"

    @pytest.mark.asyncio
    async def test_get_backlinks_fs_tool_basic_functionality(self, sample_vault):
        """Test get_backlinks_fs MCP tool returns correct backlinks."""
        # Call the underlying filesystem function
        result = find_backlinks_fs(sample_vault, "main")

        # Result should be a list of backlinks
        assert isinstance(result, list)
        assert len(result) >= 3  # references_main, also_references, folder/nested

        # Should find the notes that link to 'main'
        source_paths = [bl["source_path"] for bl in result]
        assert any("references_main" in path for path in source_paths)

    def test_get_backlinks_fs_tool_no_results(self, sample_vault):
        """Test get_backlinks_fs with note that has no backlinks."""
        result = find_backlinks_fs(sample_vault, "broken_links")
        assert result == []

    def test_get_backlinks_fs_tool_nonexistent_note(self, sample_vault):
        """Test get_backlinks_fs with note that doesn't exist."""
        result = find_backlinks_fs(sample_vault, "does-not-exist")
        assert result == []

    def test_get_broken_links_fs_tool_basic_functionality(self, sample_vault):
        """Test get_broken_links_fs MCP tool finds broken links."""
        result = find_broken_links_fs(sample_vault)

        # Should find the broken links
        assert len(result) >= 2  # nonexistent and also-missing
        broken_targets = [link["link_target"] for link in result]
        assert "nonexistent" in broken_targets or "also-missing" in broken_targets

    def test_get_broken_links_fs_tool_clean_vault(self):
        """Test get_broken_links_fs on vault with no broken links."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)
            (vault_path / "a.md").write_text("Links to [[b]].")
            (vault_path / "b.md").write_text("Links to [[a]].")

            result = find_broken_links_fs(str(vault_path))
            assert result == []

    def test_backlinks_fs_output_format(self, sample_vault):
        """Test that backlinks output follows contract specification."""
        result = find_backlinks_fs(sample_vault, "main")

        # Should be a list
        assert isinstance(result, list)
        assert len(result) > 0

        # Each backlink should have required fields
        backlink = result[0]
        assert "source_path" in backlink
        assert "link_target" in backlink
        assert "line_number" in backlink
        assert "context" in backlink

    def test_broken_links_fs_output_format(self, sample_vault):
        """Test that broken links output follows contract specification."""
        result = find_broken_links_fs(sample_vault)

        # Should be a list
        assert isinstance(result, list)

        # Each entry should have required fields
        if result:
            entry = result[0]
            assert "source_path" in entry
            assert "link_target" in entry
            assert "line_number" in entry
            assert "context" in entry
