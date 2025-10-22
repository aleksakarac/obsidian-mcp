"""Unit tests for enhanced link tracking tools."""

import pytest
from pathlib import Path

from src.tools.links import (
    extract_all_links,
    find_note_by_name,
    build_link_graph,
    find_orphaned_notes,
    find_hub_notes,
    analyze_link_health,
    get_note_connections,
    get_link_graph_fs_tool,
    find_orphaned_notes_fs_tool,
    find_hub_notes_fs_tool,
    analyze_link_health_fs_tool,
    get_note_connections_fs_tool,
)


class TestExtractAllLinks:
    """Tests for extract_all_links function."""

    def test_extract_wikilinks(self):
        """Test extracting wikilinks."""
        content = "See [[Note 1]] and [[Note 2|Alias]]."
        links = extract_all_links(content, "test.md")

        assert "Note 1" in links["wikilinks"]
        assert "Note 2" in links["wikilinks"]
        assert len(links["wikilinks"]) == 2

    def test_extract_markdown_links(self):
        """Test extracting markdown links."""
        content = "See [link](note.md) and [another](../path/note2.md)."
        links = extract_all_links(content, "test.md")

        assert "note" in links["markdown_links"]
        assert "../path/note2" in links["markdown_links"]

    def test_extract_embeds(self):
        """Test extracting embed links."""
        content = "![[Image.png]] and ![[Note#heading]]"
        links = extract_all_links(content, "test.md")

        assert "Image.png" in links["embeds"]
        assert "Note" in links["embeds"]

    def test_extract_all_link_types(self):
        """Test extracting all link types together."""
        content = """
[[Wikilink]] and [markdown](note.md) and ![[embed]]
"""
        links = extract_all_links(content, "test.md")

        assert "Wikilink" in links["all_links"]
        assert "note" in links["all_links"]
        assert "embed" in links["all_links"]

    def test_ignore_external_urls(self):
        """Test that external URLs are ignored."""
        content = "[external](https://example.com) and [[internal]]"
        links = extract_all_links(content, "test.md")

        assert "https://example.com" not in links["all_links"]
        assert "internal" in links["all_links"]


class TestFindNoteByName:
    """Tests for find_note_by_name function."""

    def test_find_note_exact_match(self, temp_vault):
        """Test finding note with exact name."""
        # Create test note
        (temp_vault / "Test Note.md").write_text("content", encoding="utf-8")

        result = find_note_by_name(str(temp_vault), "Test Note")
        assert result == "Test Note.md"

    def test_find_note_with_md_extension(self, temp_vault):
        """Test finding note when .md is provided."""
        (temp_vault / "Note.md").write_text("content", encoding="utf-8")

        result = find_note_by_name(str(temp_vault), "Note.md")
        assert result == "Note.md"

    def test_find_note_in_subfolder(self, temp_vault):
        """Test finding note in subfolder."""
        (temp_vault / "folder").mkdir()
        (temp_vault / "folder" / "Note.md").write_text("content", encoding="utf-8")

        result = find_note_by_name(str(temp_vault), "Note")
        assert result == str(Path("folder") / "Note.md")

    def test_note_not_found(self, temp_vault):
        """Test when note doesn't exist."""
        result = find_note_by_name(str(temp_vault), "NonExistent")
        assert result is None


class TestBuildLinkGraph:
    """Tests for build_link_graph function."""

    def test_build_simple_graph(self, temp_vault):
        """Test building graph with simple links."""
        (temp_vault / "A.md").write_text("[[B]]", encoding="utf-8")
        (temp_vault / "B.md").write_text("[[C]]", encoding="utf-8")
        (temp_vault / "C.md").write_text("", encoding="utf-8")

        graph = build_link_graph(str(temp_vault))

        assert "B.md" in graph["A.md"]["outlinks"]
        assert "A.md" in graph["B.md"]["inlinks"]
        assert "C.md" in graph["B.md"]["outlinks"]

    def test_track_link_types(self, temp_vault):
        """Test that link types are tracked."""
        content = "[[wikilink]] and [markdown](note.md) and ![[embed]]"
        (temp_vault / "test.md").write_text(content, encoding="utf-8")
        (temp_vault / "wikilink.md").write_text("", encoding="utf-8")
        (temp_vault / "note.md").write_text("", encoding="utf-8")
        (temp_vault / "embed.md").write_text("", encoding="utf-8")

        graph = build_link_graph(str(temp_vault))

        assert graph["test.md"]["link_types"]["wikilinks"] == 1
        assert graph["test.md"]["link_types"]["markdown_links"] == 1
        assert graph["test.md"]["link_types"]["embeds"] == 1

    def test_bidirectional_links(self, temp_vault):
        """Test bidirectional link tracking."""
        (temp_vault / "A.md").write_text("[[B]]", encoding="utf-8")
        (temp_vault / "B.md").write_text("[[A]]", encoding="utf-8")

        graph = build_link_graph(str(temp_vault))

        assert "B.md" in graph["A.md"]["outlinks"]
        assert "A.md" in graph["A.md"]["inlinks"]
        assert "A.md" in graph["B.md"]["outlinks"]
        assert "B.md" in graph["B.md"]["inlinks"]


class TestFindOrphanedNotes:
    """Tests for find_orphaned_notes function."""

    def test_find_orphaned_notes(self, temp_vault):
        """Test finding truly orphaned notes."""
        (temp_vault / "A.md").write_text("[[B]]", encoding="utf-8")
        (temp_vault / "B.md").write_text("", encoding="utf-8")
        (temp_vault / "orphan.md").write_text("No links", encoding="utf-8")

        orphaned = find_orphaned_notes(str(temp_vault))

        # Only orphan.md should be orphaned
        orphaned_paths = [o["file_path"] for o in orphaned]
        assert "orphan.md" in orphaned_paths
        assert "A.md" not in orphaned_paths
        assert "B.md" not in orphaned_paths  # B has inlink from A

    def test_no_orphaned_notes(self, temp_vault):
        """Test when all notes are connected."""
        (temp_vault / "A.md").write_text("[[B]]", encoding="utf-8")
        (temp_vault / "B.md").write_text("[[A]]", encoding="utf-8")

        orphaned = find_orphaned_notes(str(temp_vault))
        assert len(orphaned) == 0


class TestFindHubNotes:
    """Tests for find_hub_notes function."""

    def test_find_hub_notes(self, temp_vault):
        """Test finding notes with high outlink counts."""
        # Create hub note with many outlinks
        hub_content = "[[A]] [[B]] [[C]] [[D]] [[E]] [[F]]"
        (temp_vault / "hub.md").write_text(hub_content, encoding="utf-8")

        # Create target notes
        for name in ["A", "B", "C", "D", "E", "F"]:
            (temp_vault / f"{name}.md").write_text("", encoding="utf-8")

        # Create non-hub note
        (temp_vault / "normal.md").write_text("[[A]]", encoding="utf-8")

        hubs = find_hub_notes(str(temp_vault), min_outlinks=5)

        assert len(hubs) == 1
        assert hubs[0]["file_path"] == "hub.md"
        assert hubs[0]["outlink_count"] >= 5

    def test_sort_hubs_by_outlink_count(self, temp_vault):
        """Test that hubs are sorted by outlink count."""
        (temp_vault / "hub1.md").write_text("[[A]] [[B]] [[C]] [[D]] [[E]]", encoding="utf-8")
        (temp_vault / "hub2.md").write_text("[[A]] [[B]] [[C]] [[D]] [[E]] [[F]] [[G]]", encoding="utf-8")

        for name in ["A", "B", "C", "D", "E", "F", "G"]:
            (temp_vault / f"{name}.md").write_text("", encoding="utf-8")

        hubs = find_hub_notes(str(temp_vault), min_outlinks=5)

        assert len(hubs) == 2
        assert hubs[0]["outlink_count"] > hubs[1]["outlink_count"]


class TestAnalyzeLinkHealth:
    """Tests for analyze_link_health function."""

    def test_analyze_link_health(self, temp_vault):
        """Test link health analysis."""
        (temp_vault / "A.md").write_text("[[B]] [[C]]", encoding="utf-8")
        (temp_vault / "B.md").write_text("[[C]]", encoding="utf-8")
        (temp_vault / "C.md").write_text("", encoding="utf-8")
        (temp_vault / "orphan.md").write_text("No links", encoding="utf-8")

        health = analyze_link_health(str(temp_vault))

        assert health["total_notes"] == 4
        assert health["total_links"] == 3  # A->B, A->C, B->C
        assert health["orphaned_notes"] == 1  # orphan.md
        assert health["average_outlinks_per_note"] > 0

    def test_detect_broken_links(self, temp_vault):
        """Test broken link detection."""
        (temp_vault / "A.md").write_text("[[NonExistent]] [[B]]", encoding="utf-8")
        (temp_vault / "B.md").write_text("", encoding="utf-8")

        health = analyze_link_health(str(temp_vault))

        assert health["broken_links_count"] >= 1


class TestGetNoteConnections:
    """Tests for get_note_connections function."""

    def test_get_direct_connections(self, temp_vault):
        """Test getting direct (depth=1) connections."""
        (temp_vault / "A.md").write_text("[[B]] [[C]]", encoding="utf-8")
        (temp_vault / "B.md").write_text("[[D]]", encoding="utf-8")
        (temp_vault / "C.md").write_text("", encoding="utf-8")
        (temp_vault / "D.md").write_text("", encoding="utf-8")

        connections = get_note_connections(str(temp_vault), "A", depth=1)

        assert connections["note"] == "A.md"
        assert connections["direct_outlink_count"] == 2
        assert "B.md" in connections["direct_outlinks"]
        assert "C.md" in connections["direct_outlinks"]

    def test_get_second_degree_connections(self, temp_vault):
        """Test getting second-degree (depth=2) connections."""
        (temp_vault / "A.md").write_text("[[B]]", encoding="utf-8")
        (temp_vault / "B.md").write_text("[[C]]", encoding="utf-8")
        (temp_vault / "C.md").write_text("[[D]]", encoding="utf-8")
        (temp_vault / "D.md").write_text("", encoding="utf-8")

        connections = get_note_connections(str(temp_vault), "A", depth=2)

        # Should find B (depth 1) and C (depth 2)
        assert "B.md" in connections["connections"]
        assert "C.md" in connections["connections"]
        assert connections["connections"]["B.md"]["depth"] == 1
        assert connections["connections"]["C.md"]["depth"] == 2

    def test_note_not_found_raises_error(self, temp_vault):
        """Test that missing note raises error."""
        with pytest.raises(ValueError, match="Note not found"):
            get_note_connections(str(temp_vault), "NonExistent", depth=1)


class TestToolFunctions:
    """Integration tests for MCP tool functions."""

    @pytest.mark.asyncio
    async def test_get_link_graph_fs_tool(self, temp_vault):
        """Test get_link_graph_fs_tool."""
        (temp_vault / "A.md").write_text("[[B]]", encoding="utf-8")
        (temp_vault / "B.md").write_text("", encoding="utf-8")

        result = await get_link_graph_fs_tool(vault_path=str(temp_vault))

        assert result["total_notes"] == 2
        assert "A.md" in result["graph"]
        assert "B.md" in result["graph"]["A.md"]["outlinks"]

    @pytest.mark.asyncio
    async def test_find_orphaned_notes_fs_tool(self, temp_vault):
        """Test find_orphaned_notes_fs_tool."""
        (temp_vault / "A.md").write_text("[[B]]", encoding="utf-8")
        (temp_vault / "B.md").write_text("", encoding="utf-8")
        (temp_vault / "orphan.md").write_text("No links", encoding="utf-8")

        result = await find_orphaned_notes_fs_tool(vault_path=str(temp_vault))

        assert result["orphaned_count"] == 1
        assert any(o["file_path"] == "orphan.md" for o in result["orphaned_notes"])

    @pytest.mark.asyncio
    async def test_find_hub_notes_fs_tool(self, temp_vault):
        """Test find_hub_notes_fs_tool."""
        (temp_vault / "hub.md").write_text("[[A]] [[B]] [[C]] [[D]] [[E]]", encoding="utf-8")
        for name in ["A", "B", "C", "D", "E"]:
            (temp_vault / f"{name}.md").write_text("", encoding="utf-8")

        result = await find_hub_notes_fs_tool(min_outlinks=5, vault_path=str(temp_vault))

        assert result["hub_count"] == 1
        assert result["hubs"][0]["file_path"] == "hub.md"

    @pytest.mark.asyncio
    async def test_analyze_link_health_fs_tool(self, temp_vault):
        """Test analyze_link_health_fs_tool."""
        (temp_vault / "A.md").write_text("[[B]]", encoding="utf-8")
        (temp_vault / "B.md").write_text("", encoding="utf-8")

        result = await analyze_link_health_fs_tool(vault_path=str(temp_vault))

        assert result["total_notes"] == 2
        assert result["total_links"] == 1
        assert "link_density_score" in result

    @pytest.mark.asyncio
    async def test_get_note_connections_fs_tool(self, temp_vault):
        """Test get_note_connections_fs_tool."""
        (temp_vault / "A.md").write_text("[[B]]", encoding="utf-8")
        (temp_vault / "B.md").write_text("[[C]]", encoding="utf-8")
        (temp_vault / "C.md").write_text("", encoding="utf-8")

        result = await get_note_connections_fs_tool(
            note_name="A",
            depth=2,
            vault_path=str(temp_vault)
        )

        assert result["note"] == "A.md"
        assert result["connection_depth"] == 2
        assert "B.md" in result["connections"]
