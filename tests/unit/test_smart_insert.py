"""Unit tests for smart insertion functionality.

Following TDD - these tests are written FIRST and should FAIL until implementation.
Tests cover: insert after heading, insert after block, frontmatter updates, append to note.
"""

import pytest
from pathlib import Path
import tempfile
import os

# Import the functions we'll implement
from src.tools.smart_insert import (
    insert_after_heading,
    insert_after_block,
    update_frontmatter_field,
    append_to_note
)


class TestInsertAfterHeading:
    """Test suite for insert_after_heading() function."""

    @pytest.fixture
    def temp_note_with_headings(self):
        """Create a temporary note with multiple headings."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# Main Title

Some intro content.

## Tasks

- [ ] Existing task 1
- [ ] Existing task 2

## Notes

Some notes here.

### Subsection

Nested content.

## References

Links and references.
""")
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_insert_after_h2_heading(self, temp_note_with_headings):
        """Test inserting content after a level 2 heading."""
        result = insert_after_heading(
            temp_note_with_headings,
            "Tasks",
            "\n- [ ] New task from test"
        )

        assert result["success"] is True
        assert "Tasks" in result["message"]

        # Verify content was inserted
        with open(temp_note_with_headings, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "- [ ] New task from test" in content
        # Verify it's after Tasks heading
        assert content.index("## Tasks") < content.index("- [ ] New task from test")

    def test_insert_after_h1_heading(self, temp_note_with_headings):
        """Test inserting content after level 1 heading."""
        result = insert_after_heading(
            temp_note_with_headings,
            "Main Title",
            "\n**Important notice**\n"
        )

        assert result["success"] is True

        with open(temp_note_with_headings, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "**Important notice**" in content
        assert content.index("# Main Title") < content.index("**Important notice**")

    def test_insert_after_h3_heading(self, temp_note_with_headings):
        """Test inserting after nested heading."""
        result = insert_after_heading(
            temp_note_with_headings,
            "Subsection",
            "\nAdditional subsection content"
        )

        assert result["success"] is True

        with open(temp_note_with_headings, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "Additional subsection content" in content

    def test_heading_not_found(self, temp_note_with_headings):
        """Test inserting after non-existent heading."""
        result = insert_after_heading(
            temp_note_with_headings,
            "Nonexistent Heading",
            "\nSome content"
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower() or "error" in result

    def test_case_sensitive_heading_match(self, temp_note_with_headings):
        """Test that heading matching is case-sensitive."""
        result = insert_after_heading(
            temp_note_with_headings,
            "tasks",  # lowercase
            "\n- [ ] New task"
        )

        # Should fail because "Tasks" != "tasks"
        assert result["success"] is False

    def test_insert_preserves_existing_content(self, temp_note_with_headings):
        """Test that insertion doesn't destroy existing content."""
        # Read original content
        with open(temp_note_with_headings, 'r', encoding='utf-8') as f:
            original = f.read()

        result = insert_after_heading(
            temp_note_with_headings,
            "Notes",
            "\nNew note content"
        )

        assert result["success"] is True

        # Read modified content
        with open(temp_note_with_headings, 'r', encoding='utf-8') as f:
            modified = f.read()

        # Original content should still be there
        assert "Some notes here." in modified
        assert "## References" in modified
        assert "Links and references." in modified

    def test_insert_after_heading_with_immediate_content(self):
        """Test insertion when heading has content on next line."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""## Heading
Immediate content on next line.

More content.
""")
            temp_path = f.name

        try:
            result = insert_after_heading(temp_path, "Heading", "\nInserted line")

            assert result["success"] is True

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Should insert after heading line, before existing content
            assert "## Heading\nInserted line" in content or "## Heading\n\nInserted line" in content

        finally:
            os.unlink(temp_path)

    def test_insert_multiline_content(self, temp_note_with_headings):
        """Test inserting multi-line content block."""
        multiline = "\n- Item 1\n- Item 2\n- Item 3\n"

        result = insert_after_heading(temp_note_with_headings, "Tasks", multiline)

        assert result["success"] is True

        with open(temp_note_with_headings, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "- Item 1" in content
        assert "- Item 2" in content
        assert "- Item 3" in content

    def test_file_not_found(self):
        """Test inserting into non-existent file."""
        with pytest.raises(FileNotFoundError):
            insert_after_heading("/nonexistent/path.md", "Heading", "Content")

    def test_heading_with_special_characters(self):
        """Test heading with special characters in name."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""## TODO: Action Items (2025)

- Task 1
""")
            temp_path = f.name

        try:
            result = insert_after_heading(
                temp_path,
                "TODO: Action Items (2025)",
                "\n- Task 2"
            )

            assert result["success"] is True

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "- Task 2" in content

        finally:
            os.unlink(temp_path)

    def test_duplicate_headings_matches_first(self):
        """Test that with duplicate headings, first occurrence is used."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""## Section

First section content.

## Section

Second section content.
""")
            temp_path = f.name

        try:
            result = insert_after_heading(temp_path, "Section", "\nInserted")

            assert result["success"] is True

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Should insert after first occurrence
            lines = content.split('\n')
            first_section_idx = lines.index("## Section")
            inserted_idx = next(i for i, line in enumerate(lines) if "Inserted" in line)

            assert inserted_idx > first_section_idx
            # Should be before second Section heading
            second_section_idx = lines.index("## Section", first_section_idx + 1)
            assert inserted_idx < second_section_idx

        finally:
            os.unlink(temp_path)


class TestInsertAfterBlock:
    """Test suite for insert_after_block() function."""

    @pytest.fixture
    def temp_note_with_blocks(self):
        """Create a temporary note with block references."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# Note with Blocks

This is the main content paragraph. ^intro

## Section 1

Some content here with block reference. ^section1-block

Another paragraph without block.

## Section 2

Final paragraph. ^conclusion
""")
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_insert_after_block_with_caret(self, temp_note_with_blocks):
        """Test inserting after block using ^block-id format."""
        result = insert_after_block(
            temp_note_with_blocks,
            "^intro",
            "\n\nAdditional intro content."
        )

        assert result["success"] is True
        assert "intro" in result["message"]

        with open(temp_note_with_blocks, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "Additional intro content." in content
        assert content.index("^intro") < content.index("Additional intro content.")

    def test_insert_after_block_without_caret(self, temp_note_with_blocks):
        """Test inserting after block without ^ prefix."""
        result = insert_after_block(
            temp_note_with_blocks,
            "section1-block",
            "\n\nInserted after section1."
        )

        assert result["success"] is True

        with open(temp_note_with_blocks, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "Inserted after section1." in content

    def test_block_not_found(self, temp_note_with_blocks):
        """Test inserting after non-existent block."""
        result = insert_after_block(
            temp_note_with_blocks,
            "nonexistent-block",
            "\nContent"
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower() or "error" in result

    def test_insert_preserves_block_reference(self, temp_note_with_blocks):
        """Test that insertion preserves the block reference marker."""
        result = insert_after_block(temp_note_with_blocks, "conclusion", "\n\nFinal thoughts.")

        assert result["success"] is True

        with open(temp_note_with_blocks, 'r', encoding='utf-8') as f:
            content = f.read()

        # Block reference should still be present
        assert "^conclusion" in content
        assert "Final thoughts." in content

    def test_insert_multiline_after_block(self, temp_note_with_blocks):
        """Test inserting multi-line content after block."""
        multiline = "\n\n**Follow-up**:\n- Point 1\n- Point 2"

        result = insert_after_block(temp_note_with_blocks, "intro", multiline)

        assert result["success"] is True

        with open(temp_note_with_blocks, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "**Follow-up**:" in content
        assert "- Point 1" in content
        assert "- Point 2" in content

    def test_file_not_found_block(self):
        """Test inserting into non-existent file."""
        with pytest.raises(FileNotFoundError):
            insert_after_block("/nonexistent/path.md", "block-id", "Content")

    def test_block_at_end_of_file(self):
        """Test inserting after block that's at the end of file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("Last line. ^end-block")
            temp_path = f.name

        try:
            result = insert_after_block(temp_path, "end-block", "\n\nAppended content.")

            assert result["success"] is True

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "Appended content." in content

        finally:
            os.unlink(temp_path)


class TestUpdateFrontmatterField:
    """Test suite for update_frontmatter_field() function."""

    @pytest.fixture
    def temp_note_with_frontmatter(self):
        """Create note with existing frontmatter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""---
title: Test Note
tags: [existing, tags]
status: draft
---

# Content

Note content here.
""")
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_update_existing_field(self, temp_note_with_frontmatter):
        """Test updating an existing frontmatter field."""
        result = update_frontmatter_field(
            temp_note_with_frontmatter,
            "status",
            "published"
        )

        assert result["success"] is True

        with open(temp_note_with_frontmatter, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "status: published" in content or "status:" in content
        assert "draft" not in content.split("---")[1]  # Not in frontmatter

    def test_add_new_field(self, temp_note_with_frontmatter):
        """Test adding a new field to existing frontmatter."""
        result = update_frontmatter_field(
            temp_note_with_frontmatter,
            "author",
            "Test Author"
        )

        assert result["success"] is True

        with open(temp_note_with_frontmatter, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "author:" in content
        assert "Test Author" in content

    def test_create_frontmatter_if_missing(self):
        """Test creating frontmatter when note has none."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# Note\n\nNo frontmatter.")
            temp_path = f.name

        try:
            result = update_frontmatter_field(temp_path, "created", "2025-01-22")

            assert result["success"] is True

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Should have frontmatter now
            assert content.startswith("---\n")
            assert "created:" in content
            assert "2025-01-22" in content

        finally:
            os.unlink(temp_path)

    def test_update_preserves_other_fields(self, temp_note_with_frontmatter):
        """Test that updating one field preserves others."""
        result = update_frontmatter_field(temp_note_with_frontmatter, "status", "updated")

        assert result["success"] is True

        with open(temp_note_with_frontmatter, 'r', encoding='utf-8') as f:
            content = f.read()

        # Other fields should still exist
        assert "title: Test Note" in content or "title:" in content
        assert "tags:" in content

    def test_update_with_list_value(self, temp_note_with_frontmatter):
        """Test updating field with list/array value."""
        result = update_frontmatter_field(
            temp_note_with_frontmatter,
            "categories",
            ["tech", "notes", "reference"]
        )

        assert result["success"] is True

        with open(temp_note_with_frontmatter, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "categories:" in content
        # Should contain list items
        assert "tech" in content

    def test_update_with_numeric_value(self, temp_note_with_frontmatter):
        """Test updating with numeric value."""
        result = update_frontmatter_field(temp_note_with_frontmatter, "version", 2)

        assert result["success"] is True

        with open(temp_note_with_frontmatter, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "version: 2" in content or "version:" in content

    def test_update_with_boolean_value(self, temp_note_with_frontmatter):
        """Test updating with boolean value."""
        result = update_frontmatter_field(temp_note_with_frontmatter, "published", True)

        assert result["success"] is True

        with open(temp_note_with_frontmatter, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "published: true" in content or "published:" in content

    def test_file_not_found_frontmatter(self):
        """Test updating frontmatter in non-existent file."""
        with pytest.raises(FileNotFoundError):
            update_frontmatter_field("/nonexistent/path.md", "field", "value")

    def test_preserves_content_after_frontmatter(self, temp_note_with_frontmatter):
        """Test that content after frontmatter is preserved."""
        result = update_frontmatter_field(temp_note_with_frontmatter, "new_field", "value")

        assert result["success"] is True

        with open(temp_note_with_frontmatter, 'r', encoding='utf-8') as f:
            content = f.read()

        # Content should be preserved
        assert "# Content" in content
        assert "Note content here." in content


class TestAppendToNote:
    """Test suite for append_to_note() function."""

    @pytest.fixture
    def temp_note(self):
        """Create a temporary note."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# Test Note

Existing content.

## Section

More content.
""")
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_append_single_line(self, temp_note):
        """Test appending a single line to note."""
        result = append_to_note(temp_note, "\nAppended line.")

        assert result["success"] is True

        with open(temp_note, 'r', encoding='utf-8') as f:
            content = f.read()

        assert content.endswith("\nAppended line.") or content.endswith("Appended line.")

    def test_append_multiline(self, temp_note):
        """Test appending multiple lines."""
        multiline = "\n## New Section\n\nNew content.\n"

        result = append_to_note(temp_note, multiline)

        assert result["success"] is True

        with open(temp_note, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "## New Section" in content
        assert "New content." in content

    def test_append_preserves_existing(self, temp_note):
        """Test that appending preserves existing content."""
        # Read original
        with open(temp_note, 'r', encoding='utf-8') as f:
            original = f.read()

        result = append_to_note(temp_note, "\n---\nFooter")

        assert result["success"] is True

        with open(temp_note, 'r', encoding='utf-8') as f:
            content = f.read()

        # Original should be intact
        assert "# Test Note" in content
        assert "Existing content." in content
        assert "## Section" in content
        # New content at end
        assert "Footer" in content

    def test_append_to_empty_file(self):
        """Test appending to empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("")
            temp_path = f.name

        try:
            result = append_to_note(temp_path, "First content")

            assert result["success"] is True

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "First content" in content

        finally:
            os.unlink(temp_path)

    def test_append_with_newlines(self, temp_note):
        """Test appending content with proper newline handling."""
        result = append_to_note(temp_note, "\n\n---\n\n**End of document**\n")

        assert result["success"] is True

        with open(temp_note, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "---" in content
        assert "**End of document**" in content

    def test_file_not_found_append(self):
        """Test appending to non-existent file."""
        with pytest.raises(FileNotFoundError):
            append_to_note("/nonexistent/path.md", "Content")

    def test_append_markdown_formatting(self, temp_note):
        """Test appending content with markdown formatting."""
        markdown = """

## Appendix

- List item 1
- List item 2

> Quote block

```python
code_block()
```
"""

        result = append_to_note(temp_note, markdown)

        assert result["success"] is True

        with open(temp_note, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "## Appendix" in content
        assert "- List item 1" in content
        assert "> Quote block" in content
        assert "```python" in content

    def test_append_unicode_content(self, temp_note):
        """Test appending Unicode content."""
        unicode_content = "\n\n日本語のコンテンツ\nEmoji: 🚀 ✅"

        result = append_to_note(temp_note, unicode_content)

        assert result["success"] is True

        with open(temp_note, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "日本語のコンテンツ" in content
        assert "🚀" in content
