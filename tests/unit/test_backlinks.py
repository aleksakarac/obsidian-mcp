"""Unit tests for backlinks functionality.

Following TDD - these tests are written FIRST and should FAIL until implementation.
Tests cover: simple wikilinks, aliased wikilinks, section links, broken links, edge cases.
"""

import pytest
from pathlib import Path
import tempfile
import os

# Import the functions we'll implement
from src.tools.backlinks import find_backlinks, find_broken_links


class TestFindBacklinks:
    """Test suite for find_backlinks() function."""

    @pytest.fixture
    def sample_vault(self):
        """Create a temporary vault with test notes for backlinks testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)

            # Create note1.md - has links TO note2 and note3
            (vault_path / "note1.md").write_text(
                "This links to [[note2]] and [[note3|Note Three]].\n"
                "Also links to [[note2#section]]."
            )

            # Create note2.md - has link TO note1 (creates bidirectional link)
            (vault_path / "note2.md").write_text(
                "# Note 2\n\n"
                "This references [[note1]].\n"
                "## Section\n"
                "Some content."
            )

            # Create note3.md - has link TO note1
            (vault_path / "note3.md").write_text(
                "Links back to [[note1]]."
            )

            # Create isolated.md - no links to/from other notes
            (vault_path / "isolated.md").write_text(
                "This note has no wikilinks."
            )

            # Create subfolder with nested note
            subfolder = vault_path / "subfolder"
            subfolder.mkdir()
            (subfolder / "nested.md").write_text(
                "From nested folder, linking to [[note1]]."
            )

            # Create .obsidian folder (should be ignored)
            obsidian_dir = vault_path / ".obsidian"
            obsidian_dir.mkdir()
            (obsidian_dir / "config.md").write_text(
                "Config linking to [[note1]] - should be IGNORED."
            )

            yield str(vault_path)

    def test_find_simple_backlinks(self, sample_vault):
        """Test finding simple wikilinks [[note]] format."""
        result = find_backlinks(sample_vault, "note1")

        # note2.md and note3.md link to note1, plus subfolder/nested.md
        # .obsidian/config.md should be IGNORED
        assert len(result) == 3

        note_paths = [r["source_path"] for r in result]
        assert "note2.md" in note_paths
        assert "note3.md" in note_paths
        assert "subfolder/nested.md" in note_paths
        assert ".obsidian/config.md" not in note_paths

    def test_find_backlinks_with_alias(self, sample_vault):
        """Test finding aliased wikilinks [[note|alias]] format."""
        result = find_backlinks(sample_vault, "note3")

        # note1.md links to note3 using alias [[note3|Note Three]]
        assert len(result) == 1
        assert result[0]["source_path"] == "note1.md"

        # Verify the link text is captured
        assert "note3" in result[0]["link_target"]

    def test_find_backlinks_with_section_reference(self, sample_vault):
        """Test that section links [[note#section]] are found."""
        result = find_backlinks(sample_vault, "note2")

        # note1.md has both [[note2]] and [[note2#section]]
        # Should find note1 as a backlink (may find multiple matches in same file)
        assert len(result) >= 1
        assert result[0]["source_path"] == "note1.md"

    def test_no_backlinks(self, sample_vault):
        """Test note with no backlinks returns empty list."""
        result = find_backlinks(sample_vault, "isolated")

        assert result == []
        assert isinstance(result, list)

    def test_nonexistent_note(self, sample_vault):
        """Test querying backlinks for a note that doesn't exist."""
        result = find_backlinks(sample_vault, "nonexistent-note")

        # Should return empty list, not error
        assert result == []

    def test_obsidian_directory_ignored(self, sample_vault):
        """Test that .obsidian directory is completely ignored."""
        result = find_backlinks(sample_vault, "note1")

        # Verify no results come from .obsidian directory
        for backlink in result:
            assert not backlink["source_path"].startswith(".obsidian")

    def test_case_sensitivity(self, sample_vault):
        """Test that note names are case-sensitive (Obsidian default)."""
        # Create note with different casing
        vault_path = Path(sample_vault)
        (vault_path / "CamelCase.md").write_text("Links to [[note1]].")

        result_lower = find_backlinks(sample_vault, "note1")
        result_camel = find_backlinks(sample_vault, "Note1")  # Different case

        # note1 (lowercase) should have backlinks
        assert len(result_lower) > 0

        # Note1 (capitalized) should have no backlinks
        assert len(result_camel) == 0

    def test_backlinks_contain_required_fields(self, sample_vault):
        """Test that backlink results contain all required fields."""
        result = find_backlinks(sample_vault, "note1")

        assert len(result) > 0

        for backlink in result:
            # Verify schema matches contract specification
            assert "source_path" in backlink
            assert "link_target" in backlink
            assert "line_number" in backlink or "context" in backlink

            # source_path should be relative to vault root
            assert isinstance(backlink["source_path"], str)
            assert not backlink["source_path"].startswith("/")


class TestFindBrokenLinks:
    """Test suite for find_broken_links() function."""

    @pytest.fixture
    def vault_with_broken_links(self):
        """Create a vault with intentionally broken wikilinks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)

            # Create valid_note.md
            (vault_path / "valid_note.md").write_text("# Valid Note\n\nContent here.")

            # Create note with broken links
            (vault_path / "has_broken_links.md").write_text(
                "Links to [[valid_note]] (good).\n"
                "Links to [[nonexistent1]] (broken).\n"
                "Links to [[nonexistent2|Broken Alias]] (broken).\n"
                "Links to [[valid_note#section]] (good - section links ok if note exists)."
            )

            # Create note with only broken links
            (vault_path / "all_broken.md").write_text(
                "[[missing1]] and [[missing2]]."
            )

            # Create note with no links
            (vault_path / "no_links.md").write_text(
                "No wikilinks here."
            )

            yield str(vault_path)

    def test_find_broken_links(self, vault_with_broken_links):
        """Test detection of broken wikilinks."""
        result = find_broken_links(vault_with_broken_links)

        # Should find broken links: nonexistent1, nonexistent2, missing1, missing2
        assert len(result) >= 4

        # Extract just the broken link targets
        broken_targets = [r["link_target"] for r in result]

        assert "nonexistent1" in broken_targets
        assert "nonexistent2" in broken_targets
        assert "missing1" in broken_targets
        assert "missing2" in broken_targets

        # Valid links should NOT appear
        assert "valid_note" not in broken_targets

    def test_no_broken_links(self, sample_vault):
        """Test vault with all valid links returns empty list."""
        # Create a clean vault with only valid links
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)

            (vault_path / "a.md").write_text("Links to [[b]].")
            (vault_path / "b.md").write_text("Links to [[a]].")

            result = find_broken_links(str(vault_path))

            assert result == []

    def test_broken_links_with_aliases(self, vault_with_broken_links):
        """Test that broken links with aliases are detected."""
        result = find_broken_links(vault_with_broken_links)

        # nonexistent2 is linked as [[nonexistent2|Broken Alias]]
        broken_targets = [r["link_target"] for r in result]
        assert "nonexistent2" in broken_targets

    def test_section_links_not_broken_if_note_exists(self, vault_with_broken_links):
        """Test that [[note#section]] is valid if note exists (even if section doesn't)."""
        result = find_broken_links(vault_with_broken_links)

        # [[valid_note#section]] should NOT be broken (note exists)
        broken_targets = [r["link_target"] for r in result]

        # Only check the note name portion, ignore section
        for target in broken_targets:
            base_note = target.split("#")[0]
            assert base_note != "valid_note"

    def test_broken_links_contain_required_fields(self, vault_with_broken_links):
        """Test that broken link results contain all required fields."""
        result = find_broken_links(vault_with_broken_links)

        assert len(result) > 0

        for broken_link in result:
            # Verify schema matches contract specification
            assert "source_path" in broken_link
            assert "link_target" in broken_link
            assert "line_number" in broken_link or "context" in broken_link

    def test_empty_vault(self):
        """Test broken links detection on empty vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = find_broken_links(tmpdir)
            assert result == []

    @pytest.fixture
    def sample_vault(self):
        """Reuse sample vault fixture for cross-test compatibility."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)
            (vault_path / "test.md").write_text("Test content")
            yield str(vault_path)
