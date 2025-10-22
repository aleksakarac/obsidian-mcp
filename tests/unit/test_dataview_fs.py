"""Unit tests for Dataview filesystem-native tools."""

import pytest
from datetime import date, datetime
from pathlib import Path

from src.tools.dataview_fs import (
    canonicalize_key,
    detect_value_type,
    parse_value,
    extract_dataview_fields,
    format_dataview_field,
    scan_vault_for_fields,
    add_field_to_file,
    remove_field_from_file,
    extract_dataview_fields_fs_tool,
    search_by_dataview_field_fs_tool,
    add_dataview_field_fs_tool,
    remove_dataview_field_fs_tool,
)
from src.models.obsidian import DataviewField


class TestCanonicalizeKey:
    """Tests for canonicalize_key function."""

    def test_simple_lowercase(self):
        """Test simple lowercase conversion."""
        assert canonicalize_key("status") == "status"
        assert canonicalize_key("Status") == "status"
        assert canonicalize_key("STATUS") == "status"

    def test_spaces_to_hyphens(self):
        """Test space to hyphen conversion."""
        assert canonicalize_key("Project Status") == "project-status"
        assert canonicalize_key("Due Date") == "due-date"
        assert canonicalize_key("Multiple   Spaces") == "multiple---spaces"

    def test_strip_formatting(self):
        """Test markdown formatting removal."""
        assert canonicalize_key("_Priority_") == "priority"
        assert canonicalize_key("**Important**") == "important"
        assert canonicalize_key("~~Deprecated~~") == "deprecated"
        assert canonicalize_key("_**Mixed**_") == "mixed"

    def test_remove_special_chars(self):
        """Test special character removal."""
        assert canonicalize_key("key@with#special$chars") == "keywithspecialchars"
        assert canonicalize_key("key-with-hyphens") == "key-with-hyphens"

    def test_complex_cases(self):
        """Test complex real-world cases."""
        assert canonicalize_key("**Project Status**") == "project-status"
        assert canonicalize_key("_Due Date_") == "due-date"
        assert canonicalize_key("Task #1") == "task-1"


class TestDetectValueType:
    """Tests for detect_value_type function."""

    def test_detect_boolean(self):
        """Test boolean detection."""
        assert detect_value_type("true") == "boolean"
        assert detect_value_type("false") == "boolean"
        assert detect_value_type("True") == "boolean"
        assert detect_value_type("FALSE") == "boolean"

    def test_detect_number(self):
        """Test number detection."""
        assert detect_value_type("42") == "number"
        assert detect_value_type("3.14") == "number"
        assert detect_value_type("-100") == "number"
        assert detect_value_type("0.001") == "number"

    def test_detect_date(self):
        """Test date detection (ISO8601)."""
        assert detect_value_type("2025-10-22") == "date"
        assert detect_value_type("2025-10-22T15:30:00") == "date"
        assert detect_value_type("2025-10-22T15:30:00Z") == "date"
        assert detect_value_type("2025-10-22T15:30:00+02:00") == "date"

    def test_detect_link(self):
        """Test wikilink detection."""
        assert detect_value_type("[[Note Name]]") == "link"
        assert detect_value_type("[[Note|Alias]]") == "link"
        assert detect_value_type("[[Note#Section]]") == "link"

    def test_detect_list(self):
        """Test list detection."""
        assert detect_value_type("item1, item2, item3") == "list"
        assert detect_value_type('"quoted1", "quoted2"') == "list"

    def test_detect_string(self):
        """Test string as default."""
        assert detect_value_type("Some text") == "string"
        assert detect_value_type("Not a number") == "string"
        assert detect_value_type("2025-13-45") == "string"  # Invalid date


class TestParseValue:
    """Tests for parse_value function."""

    def test_parse_boolean(self):
        """Test boolean parsing."""
        assert parse_value("true", "boolean") is True
        assert parse_value("false", "boolean") is False
        assert parse_value("True", "boolean") is True

    def test_parse_number(self):
        """Test number parsing."""
        assert parse_value("42", "number") == 42
        assert parse_value("3.14", "number") == 3.14
        assert parse_value("-100", "number") == -100

    def test_parse_date(self):
        """Test date parsing."""
        result = parse_value("2025-10-22", "date")
        assert isinstance(result, date)
        assert result == date(2025, 10, 22)

        result_dt = parse_value("2025-10-22T15:30:00", "date")
        assert isinstance(result_dt, datetime)

    def test_parse_link(self):
        """Test wikilink parsing."""
        assert parse_value("[[Note Name]]", "link") == "Note Name"
        assert parse_value("[[Note|Alias]]", "link") == "Note"

    def test_parse_list(self):
        """Test list parsing."""
        result = parse_value('"item1", "item2", "item3"', "list")
        assert result == ["item1", "item2", "item3"]

        result_simple = parse_value("a, b, c", "list")
        assert result_simple == ["a", "b", "c"]

    def test_parse_string(self):
        """Test string parsing (default)."""
        assert parse_value("Some text", "string") == "Some text"


class TestExtractDataviewFields:
    """Tests for extract_dataview_fields function."""

    def test_extract_full_line_syntax(self):
        """Test extraction of full-line syntax fields."""
        content = """# Test Note

status:: active
priority:: high
completion:: 75
"""
        fields = extract_dataview_fields(content, "test.md")

        assert len(fields) == 3
        assert fields[0].key == "status"
        assert fields[0].value == "active"
        assert fields[0].syntax_type == "full-line"
        assert fields[0].line_number == 3

    def test_extract_bracket_syntax(self):
        """Test extraction of bracket syntax fields."""
        content = "This is a note with [status:: active] inline field."
        fields = extract_dataview_fields(content, "test.md")

        assert len(fields) == 1
        assert fields[0].key == "status"
        assert fields[0].value == "active"
        assert fields[0].syntax_type == "bracket"

    def test_extract_paren_syntax(self):
        """Test extraction of paren syntax fields (hidden key)."""
        content = "This note has (priority:: high) hidden metadata."
        fields = extract_dataview_fields(content, "test.md")

        assert len(fields) == 1
        assert fields[0].key == "priority"
        assert fields[0].value == "high"
        assert fields[0].syntax_type == "paren"

    def test_extract_all_syntax_variants(self):
        """Test extraction of mixed syntax variants."""
        content = """# Project

status:: in-progress
This is [priority:: high] with hidden (completion:: 50).
due:: 2025-10-30
"""
        fields = extract_dataview_fields(content, "test.md")

        assert len(fields) == 4
        syntax_types = {f.syntax_type for f in fields}
        assert syntax_types == {"full-line", "bracket", "paren"}

    def test_skip_code_blocks(self):
        """Test that code blocks are skipped."""
        content = """# Test

status:: active

```python
# This should be ignored
priority:: high
```

actual:: value
"""
        fields = extract_dataview_fields(content, "test.md")

        assert len(fields) == 2
        keys = [f.key for f in fields]
        assert "priority" not in keys
        assert "status" in keys
        assert "actual" in keys

    def test_value_type_detection(self):
        """Test automatic value type detection."""
        content = """
boolean_field:: true
number_field:: 42
date_field:: 2025-10-22
link_field:: [[Note]]
list_field:: "a", "b", "c"
string_field:: Just text
"""
        fields = extract_dataview_fields(content, "test.md")

        field_types = {f.key: f.value_type for f in fields}
        assert field_types["boolean_field"] == "boolean"
        assert field_types["number_field"] == "number"
        assert field_types["date_field"] == "date"
        assert field_types["link_field"] == "link"
        assert field_types["list_field"] == "list"
        assert field_types["string_field"] == "string"

    def test_canonical_key_generation(self):
        """Test canonical key auto-generation."""
        content = """
**Project Status**:: active
_Due Date_:: 2025-10-30
"""
        fields = extract_dataview_fields(content, "test.md")

        assert fields[0].canonical_key == "project-status"
        assert fields[1].canonical_key == "due-date"


class TestFormatDataviewField:
    """Tests for format_dataview_field function."""

    def test_format_full_line(self):
        """Test full-line format."""
        result = format_dataview_field("status", "active", "full-line")
        assert result == "status:: active"

    def test_format_bracket(self):
        """Test bracket format."""
        result = format_dataview_field("priority", "high", "bracket")
        assert result == "[priority:: high]"

    def test_format_paren(self):
        """Test paren format."""
        result = format_dataview_field("completion", 75, "paren")
        assert result == "(completion:: 75)"

    def test_format_boolean(self):
        """Test boolean formatting."""
        result = format_dataview_field("active", True, "full-line")
        assert result == "active:: true"

    def test_format_date(self):
        """Test date formatting."""
        result = format_dataview_field("due", date(2025, 10, 30), "full-line")
        assert result == "due:: 2025-10-30"

    def test_format_list(self):
        """Test list formatting."""
        result = format_dataview_field("tags", ["urgent", "work"], "full-line")
        assert result == 'tags:: "urgent", "work"'


class TestToolFunctions:
    """Integration tests for MCP tool functions."""

    @pytest.mark.asyncio
    async def test_extract_dataview_fields_fs_tool(self, temp_vault):
        """Test extract_dataview_fields_fs_tool."""
        file_path = "test.md"
        (temp_vault / file_path).write_text(
            """# Test

status:: active
priority:: high
[progress:: 50]
""",
            encoding="utf-8",
        )

        result = await extract_dataview_fields_fs_tool(
            file_path=file_path, vault_path=str(temp_vault)
        )

        assert result["field_count"] == 3
        assert len(result["fields"]) == 3

        # Verify field details
        status_field = next(f for f in result["fields"] if f["key"] == "status")
        assert status_field["value"] == "active"
        assert status_field["syntax_type"] == "full-line"
        assert status_field["canonical_key"] == "status"

    @pytest.mark.asyncio
    async def test_search_by_dataview_field_fs_tool(self, temp_vault):
        """Test search_by_dataview_field_fs_tool."""
        # Create multiple files with fields
        (temp_vault / "note1.md").write_text("status:: active\n", encoding="utf-8")
        (temp_vault / "note2.md").write_text("status:: completed\n", encoding="utf-8")
        (temp_vault / "note3.md").write_text("status:: active\n", encoding="utf-8")

        # Search by key only
        result = await search_by_dataview_field_fs_tool(
            key="status", vault_path=str(temp_vault)
        )

        assert result["total_matches"] == 3
        assert result["files_with_matches"] == 3
        assert result["canonical_key"] == "status"

        # Search by key and value
        result_filtered = await search_by_dataview_field_fs_tool(
            key="status", value="active", vault_path=str(temp_vault)
        )

        assert result_filtered["total_matches"] == 2
        assert result_filtered["files_with_matches"] == 2

    @pytest.mark.asyncio
    async def test_add_dataview_field_fs_tool(self, temp_vault):
        """Test add_dataview_field_fs_tool."""
        file_path = "new_note.md"

        result = await add_dataview_field_fs_tool(
            file_path=file_path,
            key="status",
            value="active",
            syntax_type="full-line",
            vault_path=str(temp_vault),
        )

        assert result["success"] is True
        assert result["formatted_field"] == "status:: active"
        assert result["canonical_key"] == "status"

        # Verify file was created
        content = (temp_vault / file_path).read_text(encoding="utf-8")
        assert "status:: active" in content

    @pytest.mark.asyncio
    async def test_add_field_with_frontmatter(self, temp_vault):
        """Test adding field after frontmatter."""
        file_path = "with_frontmatter.md"
        (temp_vault / file_path).write_text(
            """---
title: Test
---

# Content
""",
            encoding="utf-8",
        )

        result = await add_dataview_field_fs_tool(
            file_path=file_path,
            key="status",
            value="active",
            insert_at="after_frontmatter",
            vault_path=str(temp_vault),
        )

        assert result["success"] is True

        content = (temp_vault / file_path).read_text(encoding="utf-8")
        lines = content.split("\n")

        # Find status field
        status_line_idx = next(i for i, line in enumerate(lines) if "status::" in line)

        # Should be after frontmatter (line 3, after ---)
        assert status_line_idx == 3

    @pytest.mark.asyncio
    async def test_remove_dataview_field_fs_tool(self, temp_vault):
        """Test remove_dataview_field_fs_tool."""
        file_path = "test.md"
        (temp_vault / file_path).write_text(
            """status:: active
priority:: high
completion:: 75
""",
            encoding="utf-8",
        )

        # Remove one field
        result = await remove_dataview_field_fs_tool(
            file_path=file_path, key="priority", vault_path=str(temp_vault)
        )

        assert result["success"] is True
        assert result["removed_key"] == "priority"

        # Verify removal
        content = (temp_vault / file_path).read_text(encoding="utf-8")
        assert "priority" not in content
        assert "status:: active" in content
        assert "completion:: 75" in content

    @pytest.mark.asyncio
    async def test_remove_inline_field(self, temp_vault):
        """Test removing inline bracket field."""
        file_path = "inline.md"
        (temp_vault / file_path).write_text(
            "This is text with [status:: active] inline field.\n", encoding="utf-8"
        )

        result = await remove_dataview_field_fs_tool(
            file_path=file_path, key="status", vault_path=str(temp_vault)
        )

        assert result["success"] is True

        content = (temp_vault / file_path).read_text(encoding="utf-8")
        assert "status" not in content
        assert "This is text with  inline field" in content

    @pytest.mark.asyncio
    async def test_add_multiple_syntax_types(self, temp_vault):
        """Test adding fields with different syntax types."""
        file_path = "multi.md"

        # Add full-line
        await add_dataview_field_fs_tool(
            file_path=file_path,
            key="status",
            value="active",
            syntax_type="full-line",
            insert_at="end",
            vault_path=str(temp_vault),
        )

        # Add bracket
        await add_dataview_field_fs_tool(
            file_path=file_path,
            key="priority",
            value="high",
            syntax_type="bracket",
            insert_at="end",
            vault_path=str(temp_vault),
        )

        # Add paren
        await add_dataview_field_fs_tool(
            file_path=file_path,
            key="completion",
            value=50,
            syntax_type="paren",
            insert_at="end",
            vault_path=str(temp_vault),
        )

        content = (temp_vault / file_path).read_text(encoding="utf-8")
        assert "status:: active" in content
        assert "[priority:: high]" in content
        assert "(completion:: 50)" in content


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_extract_empty_content(self):
        """Test extraction from empty content."""
        fields = extract_dataview_fields("", "empty.md")
        assert len(fields) == 0

    def test_extract_no_fields(self):
        """Test extraction from content without fields."""
        content = "# Just a heading\n\nSome text without fields."
        fields = extract_dataview_fields(content, "test.md")
        assert len(fields) == 0

    def test_canonicalize_empty_key(self):
        """Test canonicalizing empty key."""
        assert canonicalize_key("") == ""
        assert canonicalize_key("   ") == ""

    @pytest.mark.asyncio
    async def test_extract_from_nonexistent_file(self, temp_vault):
        """Test extracting from non-existent file."""
        with pytest.raises(ValueError, match="File not found"):
            await extract_dataview_fields_fs_tool(
                file_path="nonexistent.md", vault_path=str(temp_vault)
            )

    @pytest.mark.asyncio
    async def test_search_in_empty_vault(self, temp_vault):
        """Test searching in empty vault."""
        result = await search_by_dataview_field_fs_tool(
            key="status", vault_path=str(temp_vault)
        )

        assert result["total_matches"] == 0
        assert result["files_with_matches"] == 0

    def test_format_with_special_characters(self):
        """Test formatting values with special characters."""
        result = format_dataview_field("key", "value: with: colons", "full-line")
        assert result == "key:: value: with: colons"

        result_bracket = format_dataview_field("key", "value [brackets]", "bracket")
        assert result_bracket == "[key:: value [brackets]]"
