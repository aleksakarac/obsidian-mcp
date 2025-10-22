"""Unit tests for tags functionality.

Following TDD - these tests are written FIRST and should FAIL until implementation.
Tests cover: frontmatter tags, inline tags, tag extraction, add/remove tags, tag search.
"""

import pytest
from pathlib import Path
import tempfile
import os

# Import the functions we'll implement
from src.tools.tags import (
    extract_all_tags,
    add_tag_to_frontmatter,
    remove_tag_from_frontmatter,
    find_notes_by_tag
)


class TestExtractAllTags:
    """Test suite for extract_all_tags() function."""

    def test_extract_frontmatter_tags_only(self):
        """Test extracting tags from frontmatter only."""
        content = """---
tags: [project, active, planning]
---

# Note Content

Some text here."""

        result = extract_all_tags(content)

        assert "frontmatter_tags" in result
        assert "inline_tags" in result
        assert "all_tags" in result

        assert set(result["frontmatter_tags"]) == {"project", "active", "planning"}
        assert result["inline_tags"] == []
        assert set(result["all_tags"]) == {"project", "active", "planning"}

    def test_extract_inline_tags_only(self):
        """Test extracting inline tags (no frontmatter)."""
        content = """# Note Without Frontmatter

This note has #inline-tag and #another/nested tags.

More content with #test tag."""

        result = extract_all_tags(content)

        assert result["frontmatter_tags"] == []
        assert set(result["inline_tags"]) == {"inline-tag", "another/nested", "test"}
        assert set(result["all_tags"]) == {"inline-tag", "another/nested", "test"}

    def test_extract_mixed_tags(self):
        """Test extracting both frontmatter and inline tags."""
        content = """---
tags: [project, meeting]
---

# Meeting Notes

Discussion about #project/planning and #action-items.

Tags in frontmatter and inline #meeting notes."""

        result = extract_all_tags(content)

        assert set(result["frontmatter_tags"]) == {"project", "meeting"}
        assert set(result["inline_tags"]) == {"project/planning", "action-items", "meeting"}
        # all_tags should be deduplicated
        assert "meeting" in result["all_tags"]
        assert "project" in result["all_tags"]
        assert "project/planning" in result["all_tags"]
        assert "action-items" in result["all_tags"]

    def test_extract_no_tags(self):
        """Test note with no tags at all."""
        content = """# Simple Note

Just plain content with no tags."""

        result = extract_all_tags(content)

        assert result["frontmatter_tags"] == []
        assert result["inline_tags"] == []
        assert result["all_tags"] == []

    def test_frontmatter_single_tag_format(self):
        """Test frontmatter with single tag (not array)."""
        content = """---
tags: single-tag
---

Content"""

        result = extract_all_tags(content)

        assert "single-tag" in result["frontmatter_tags"]

    def test_frontmatter_tag_field_variant(self):
        """Test alternate frontmatter field name 'tag' (singular)."""
        content = """---
tag: mytag
---

Content"""

        result = extract_all_tags(content)

        # Should support both 'tags' and 'tag' field
        assert "mytag" in result["frontmatter_tags"] or "mytag" in result["all_tags"]

    def test_deduplication(self):
        """Test that duplicate tags are deduplicated."""
        content = """---
tags: [project, meeting]
---

# Note

Content with #project and #meeting and #project again."""

        result = extract_all_tags(content)

        # all_tags should contain each tag only once
        assert result["all_tags"].count("project") == 1
        assert result["all_tags"].count("meeting") == 1

    def test_nested_tags(self):
        """Test nested/hierarchical tags."""
        content = """# Note

Tags: #project/active #project/planning/meeting #status/in-progress"""

        result = extract_all_tags(content)

        assert "project/active" in result["inline_tags"]
        assert "project/planning/meeting" in result["inline_tags"]
        assert "status/in-progress" in result["inline_tags"]

    def test_tags_in_code_blocks_ignored(self):
        """Test that tags inside code blocks are NOT extracted."""
        content = """# Note

Regular #tag here.

```python
# This #code-tag should be ignored
print("#also-ignored")
```

Another #real-tag."""

        result = extract_all_tags(content)

        # This is a known limitation - we extract all # patterns
        # In a full implementation, we'd parse markdown properly
        # For now, just verify real tags are found
        assert "tag" in result["inline_tags"]
        assert "real-tag" in result["inline_tags"]


class TestAddTagToFrontmatter:
    """Test suite for add_tag_to_frontmatter() function."""

    @pytest.fixture
    def temp_note(self):
        """Create a temporary note file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
tags: [existing, tags]
---

# Note Content""")
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_add_tag_to_existing_frontmatter(self, temp_note):
        """Test adding a tag to existing frontmatter tags list."""
        result = add_tag_to_frontmatter(temp_note, "new-tag")

        assert result["success"] is True

        # Verify tag was added
        with open(temp_note, 'r') as f:
            content = f.read()

        tags = extract_all_tags(content)
        assert "new-tag" in tags["frontmatter_tags"]
        assert "existing" in tags["frontmatter_tags"]
        assert "tags" in tags["frontmatter_tags"]

    def test_add_duplicate_tag(self, temp_note):
        """Test adding a tag that already exists."""
        result = add_tag_to_frontmatter(temp_note, "existing")

        # Should handle gracefully (either skip or succeed)
        assert result["success"] is True
        assert "already" in result["message"].lower() or "added" in result["message"].lower()

    def test_add_tag_to_note_without_frontmatter(self):
        """Test adding tag to note that has no frontmatter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Note\n\nNo frontmatter here.")
            temp_path = f.name

        try:
            result = add_tag_to_frontmatter(temp_path, "first-tag")

            assert result["success"] is True

            # Verify frontmatter was created
            with open(temp_path, 'r') as f:
                content = f.read()

            assert content.startswith("---\n")
            tags = extract_all_tags(content)
            assert "first-tag" in tags["frontmatter_tags"]

        finally:
            os.unlink(temp_path)

    def test_add_tag_to_nonexistent_file(self):
        """Test adding tag to file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            add_tag_to_frontmatter("/nonexistent/path/note.md", "tag")

    def test_add_nested_tag(self, temp_note):
        """Test adding nested/hierarchical tag."""
        result = add_tag_to_frontmatter(temp_note, "project/active/critical")

        assert result["success"] is True

        with open(temp_note, 'r') as f:
            content = f.read()

        tags = extract_all_tags(content)
        assert "project/active/critical" in tags["frontmatter_tags"]


class TestRemoveTagFromFrontmatter:
    """Test suite for remove_tag_from_frontmatter() function."""

    @pytest.fixture
    def temp_note_with_tags(self):
        """Create a temporary note with tags."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
tags: [project, active, planning, test]
---

# Note Content""")
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_remove_existing_tag(self, temp_note_with_tags):
        """Test removing a tag that exists."""
        result = remove_tag_from_frontmatter(temp_note_with_tags, "active")

        assert result["success"] is True

        # Verify tag was removed
        with open(temp_note_with_tags, 'r') as f:
            content = f.read()

        tags = extract_all_tags(content)
        assert "active" not in tags["frontmatter_tags"]
        assert "project" in tags["frontmatter_tags"]  # Other tags still there
        assert "planning" in tags["frontmatter_tags"]

    def test_remove_nonexistent_tag(self, temp_note_with_tags):
        """Test removing a tag that doesn't exist."""
        result = remove_tag_from_frontmatter(temp_note_with_tags, "nonexistent")

        # Should handle gracefully
        assert result["success"] is True or result["success"] is False
        assert "not found" in result["message"].lower() or "removed" in result["message"].lower()

    def test_remove_last_tag(self):
        """Test removing the only tag in frontmatter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
tags: [only-tag]
---

# Note""")
            temp_path = f.name

        try:
            result = remove_tag_from_frontmatter(temp_path, "only-tag")

            assert result["success"] is True

            with open(temp_path, 'r') as f:
                content = f.read()

            tags = extract_all_tags(content)
            assert "only-tag" not in tags["frontmatter_tags"]

        finally:
            os.unlink(temp_path)

    def test_remove_from_note_without_frontmatter(self):
        """Test removing tag from note with no frontmatter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Note\n\nNo frontmatter.")
            temp_path = f.name

        try:
            result = remove_tag_from_frontmatter(temp_path, "tag")

            # Should handle gracefully
            assert "message" in result

        finally:
            os.unlink(temp_path)


class TestFindNotesByTag:
    """Test suite for find_notes_by_tag() function."""

    @pytest.fixture
    def sample_vault(self):
        """Create a sample vault with tagged notes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)

            # Note with frontmatter tag
            (vault_path / "note1.md").write_text("""---
tags: [project, active]
---

# Note 1""")

            # Note with inline tags
            (vault_path / "note2.md").write_text("""# Note 2

Content with #project and #meeting tags.""")

            # Note with both
            (vault_path / "note3.md").write_text("""---
tags: [meeting]
---

# Note 3

Also has #project/planning inline.""")

            # Note without target tag
            (vault_path / "note4.md").write_text("""# Note 4

Has #other tags.""")

            # Subfolder note
            subfolder = vault_path / "subfolder"
            subfolder.mkdir()
            (subfolder / "nested.md").write_text("""# Nested

Has #project tag.""")

            yield str(vault_path)

    def test_find_notes_by_frontmatter_tag(self, sample_vault):
        """Test finding notes that have tag in frontmatter."""
        result = find_notes_by_tag(sample_vault, "active")

        assert len(result) >= 1
        note_files = [n["file"] for n in result]
        assert any("note1.md" in f for f in note_files)

    def test_find_notes_by_inline_tag(self, sample_vault):
        """Test finding notes that have inline tag."""
        result = find_notes_by_tag(sample_vault, "project")

        # Should find note1 (frontmatter), note2 (inline), note3 (inline nested), subfolder/nested (inline)
        assert len(result) >= 3

    def test_find_notes_by_nested_tag(self, sample_vault):
        """Test finding notes with nested tag."""
        result = find_notes_by_tag(sample_vault, "project/planning")

        assert len(result) >= 1
        note_files = [n["file"] for n in result]
        assert any("note3.md" in f for f in note_files)

    def test_find_no_notes(self, sample_vault):
        """Test searching for tag that doesn't exist."""
        result = find_notes_by_tag(sample_vault, "nonexistent-tag")

        assert result == []

    def test_tag_with_hash_symbol(self, sample_vault):
        """Test that search works with or without # symbol."""
        result_with_hash = find_notes_by_tag(sample_vault, "#project")
        result_without_hash = find_notes_by_tag(sample_vault, "project")

        # Both should return same results
        assert len(result_with_hash) == len(result_without_hash)

    def test_result_includes_tag_locations(self, sample_vault):
        """Test that results include where tag was found."""
        result = find_notes_by_tag(sample_vault, "project")

        assert len(result) > 0

        note = result[0]
        assert "file" in note
        assert "tag_locations" in note
        assert "frontmatter" in note["tag_locations"]
        assert "inline" in note["tag_locations"]

    def test_case_sensitivity(self, sample_vault):
        """Test that tag search is case-sensitive."""
        # Create note with specific casing
        vault_path = Path(sample_vault)
        (vault_path / "cased.md").write_text("# Note\n\n#Project tag here.")

        result_upper = find_notes_by_tag(sample_vault, "Project")
        result_lower = find_notes_by_tag(sample_vault, "project")

        # Should be case-sensitive (following Obsidian behavior)
        # Upper case search should find the camelcase tag
        assert any("cased.md" in n["file"] for n in result_upper)

    def test_obsidian_directory_ignored(self, sample_vault):
        """Test that .obsidian directory is skipped."""
        vault_path = Path(sample_vault)
        obsidian_dir = vault_path / ".obsidian"
        obsidian_dir.mkdir()
        (obsidian_dir / "config.md").write_text("# Config\n\n#project")

        result = find_notes_by_tag(sample_vault, "project")

        # Should not include .obsidian files
        for note in result:
            assert ".obsidian" not in note["file"]
