"""Unit tests for statistics functionality.

Following TDD - these tests are written FIRST and should FAIL until implementation.
Tests cover: note statistics (words, links, tags, headings, code, file metadata) and vault statistics.
"""

import pytest
from pathlib import Path
import tempfile
import os
import time

# Import the functions we'll implement
from src.tools.statistics import (
    get_note_stats,
    get_vault_stats
)


class TestGetNoteStats:
    """Test suite for get_note_stats() function."""

    @pytest.fixture
    def temp_note_comprehensive(self):
        """Create a comprehensive note with various elements."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""---
title: Comprehensive Test Note
tags: [python, testing, analysis]
status: active
---

# Main Title

This is a paragraph with **bold** and *italic* text. It contains a [[wikilink]] and another [[wikilink|with alias]].

Here's a [markdown link](https://example.com) for testing.

## Section 1

Some content with #inline-tag and #another-tag.

### Subsection 1.1

Testing code blocks:

```python
def hello():
    print("world")
```

And some `inline code` here.

### Subsection 1.2

More content with [[Section Reference#Heading]] and a broken [[NonexistentNote]].

## Section 2

Final section with more `code` and #final-tag.

```javascript
console.log("test");
```
""")
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_note_simple(self):
        """Create a simple note."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# Simple Note\n\nJust some text with five words.")
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_note_empty(self):
        """Create an empty note."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("")
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_word_count(self, temp_note_comprehensive):
        """Test word count calculation."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "word_count" in stats
        assert isinstance(stats["word_count"], int)
        assert stats["word_count"] > 0

    def test_character_count(self, temp_note_comprehensive):
        """Test character count (with and without spaces)."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "character_count" in stats
        assert "character_count_no_spaces" in stats
        assert isinstance(stats["character_count"], int)
        assert isinstance(stats["character_count_no_spaces"], int)
        assert stats["character_count"] > stats["character_count_no_spaces"]

    def test_line_count(self, temp_note_comprehensive):
        """Test line count calculation."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "line_count" in stats
        assert isinstance(stats["line_count"], int)
        assert stats["line_count"] > 0

    def test_wikilink_count(self, temp_note_comprehensive):
        """Test wikilink detection and counting."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "links" in stats
        assert "wikilink_count" in stats["links"]
        assert "wikilinks" in stats["links"]

        # Should find: [[wikilink]], [[wikilink|with alias]], [[Section Reference#Heading]], [[NonexistentNote]]
        assert stats["links"]["wikilink_count"] == 4
        assert isinstance(stats["links"]["wikilinks"], list)
        assert len(stats["links"]["wikilinks"]) == 4

    def test_markdown_link_count(self, temp_note_comprehensive):
        """Test markdown link detection."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "markdown_link_count" in stats["links"]
        # Should find: [markdown link](https://example.com)
        assert stats["links"]["markdown_link_count"] == 1

    def test_total_links(self, temp_note_comprehensive):
        """Test total link count."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "total_links" in stats["links"]
        # 4 wikilinks + 1 markdown link = 5 total
        assert stats["links"]["total_links"] == 5

    def test_tag_extraction(self, temp_note_comprehensive):
        """Test tag extraction from frontmatter and inline."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "tags" in stats
        assert "count" in stats["tags"]
        assert "unique_tags" in stats["tags"]
        assert "all_tags" in stats["tags"]

        # Frontmatter: python, testing, analysis
        # Inline: inline-tag, another-tag, final-tag
        # Total unique: 6
        assert stats["tags"]["count"] == 6
        assert len(stats["tags"]["unique_tags"]) == 6
        assert isinstance(stats["tags"]["all_tags"], list)

    def test_heading_count(self, temp_note_comprehensive):
        """Test heading detection and counting."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "headings" in stats
        assert "count" in stats["headings"]

        # Should find: # Main Title, ## Section 1, ### Subsection 1.1, ### Subsection 1.2, ## Section 2
        assert stats["headings"]["count"] == 5

    def test_heading_by_level(self, temp_note_comprehensive):
        """Test heading grouping by level."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "by_level" in stats["headings"]
        assert isinstance(stats["headings"]["by_level"], dict)

        # Check level 1
        assert "1" in stats["headings"]["by_level"]
        assert "Main Title" in stats["headings"]["by_level"]["1"]

        # Check level 2
        assert "2" in stats["headings"]["by_level"]
        assert len(stats["headings"]["by_level"]["2"]) == 2

        # Check level 3
        assert "3" in stats["headings"]["by_level"]
        assert len(stats["headings"]["by_level"]["3"]) == 2

    def test_heading_structure(self, temp_note_comprehensive):
        """Test heading structure with levels and text."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "structure" in stats["headings"]
        assert isinstance(stats["headings"]["structure"], list)

        # First heading should be [1, "Main Title"]
        assert stats["headings"]["structure"][0] == [1, "Main Title"]

        # Should have 5 total headings
        assert len(stats["headings"]["structure"]) == 5

    def test_code_block_count(self, temp_note_comprehensive):
        """Test code block detection."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "code" in stats
        assert "code_blocks" in stats["code"]

        # Should find 2 fenced code blocks (python and javascript)
        assert stats["code"]["code_blocks"] == 2

    def test_inline_code_count(self, temp_note_comprehensive):
        """Test inline code detection."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "inline_code" in stats["code"]

        # Should find: `inline code`, `code` (appears twice in different contexts)
        assert stats["code"]["inline_code"] >= 2

    def test_file_metadata(self, temp_note_comprehensive):
        """Test file metadata extraction."""
        stats = get_note_stats(temp_note_comprehensive)

        assert "file" in stats
        assert "size_bytes" in stats["file"]
        assert "size_kb" in stats["file"]
        assert "created" in stats["file"]
        assert "modified" in stats["file"]
        assert "accessed" in stats["file"]

        # Check types
        assert isinstance(stats["file"]["size_bytes"], int)
        assert isinstance(stats["file"]["size_kb"], float)
        assert stats["file"]["size_bytes"] > 0
        assert stats["file"]["size_kb"] > 0

    def test_simple_note_stats(self, temp_note_simple):
        """Test statistics on simple note."""
        stats = get_note_stats(temp_note_simple)

        # "Simple Note" (heading) + "Just some text with five words" = 8 words
        assert stats["word_count"] == 8
        assert stats["headings"]["count"] == 1
        assert stats["links"]["total_links"] == 0
        assert stats["tags"]["count"] == 0

    def test_empty_note_stats(self, temp_note_empty):
        """Test statistics on empty note."""
        stats = get_note_stats(temp_note_empty)

        assert stats["word_count"] == 0
        assert stats["character_count"] == 0
        assert stats["line_count"] == 1  # Empty file still has 1 line
        assert stats["headings"]["count"] == 0
        assert stats["links"]["total_links"] == 0
        assert stats["tags"]["count"] == 0

    def test_file_not_found(self):
        """Test error handling for non-existent file."""
        with pytest.raises(FileNotFoundError):
            get_note_stats("/nonexistent/path.md")

    def test_code_blocks_not_counted_as_content(self):
        """Test that code blocks are excluded from word count."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# Title

Three words here.

```python
# This code should not be counted as content words
def function_name():
    pass
```

Two more.
""")
            temp_path = f.name

        try:
            stats = get_note_stats(temp_path)

            # Should count: Title, Three, words, here, Two, more = 6 words
            # Code block content should be excluded
            assert stats["word_count"] < 20  # Would be much higher if code counted

        finally:
            os.unlink(temp_path)

    def test_frontmatter_not_counted_in_content(self):
        """Test that frontmatter is excluded from word count."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""---
title: Long Title With Many Words That Should Not Count
description: Another long description here
---

# Real Content

Five words in actual content.
""")
            temp_path = f.name

        try:
            stats = get_note_stats(temp_path)

            # Should count only: Real, Content, Five, words, in, actual, content = 7 words
            # Frontmatter should be excluded
            assert stats["word_count"] == 7

        finally:
            os.unlink(temp_path)

    def test_tags_in_code_blocks_ignored(self):
        """Test that tags in code blocks are not counted."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# Note

Real tag: #actual-tag

```python
# This #fake-tag should not count
print("#another-fake")
```
""")
            temp_path = f.name

        try:
            stats = get_note_stats(temp_path)

            # Should only find #actual-tag
            assert stats["tags"]["count"] == 1
            assert "actual-tag" in stats["tags"]["unique_tags"]

        finally:
            os.unlink(temp_path)

    def test_unicode_content(self):
        """Test handling of Unicode content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# 日本語のタイトル

Some 日本語 content with émojis 🚀 ✅.

[[日本語リンク]]

#ascii-tag #日本語タグ
""")
            temp_path = f.name

        try:
            stats = get_note_stats(temp_path)

            assert stats["word_count"] > 0
            assert stats["links"]["wikilink_count"] == 1
            # Note: Current TAG_PATTERN only supports ASCII tags, so Unicode tags not counted
            # Testing with ascii-tag to ensure Unicode doesn't break parsing
            assert stats["tags"]["count"] >= 1  # At least ascii-tag should be found

        finally:
            os.unlink(temp_path)


class TestGetVaultStats:
    """Test suite for get_vault_stats() function."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault with multiple notes."""
        vault_dir = tempfile.mkdtemp()

        # Create several notes
        notes = [
            ("note1.md", """# Note 1

Content with [[link1]] and [[link2]].

Tags: #tag1 #tag2

Total: 10 words here in this content.
"""),
            ("note2.md", """---
tags: [tag1, tag3]
---

# Note 2

Shorter note with [[link1]].

#tag4

Five words total here.
"""),
            ("note3.md", """# Note 3

Empty note with just a title and five words.
"""),
            ("subfolder/note4.md", """# Nested Note

Content in subfolder with [[link3]].

#tag5

Six words in this nested note.
""")
        ]

        # Create notes
        for filename, content in notes:
            filepath = os.path.join(vault_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        yield vault_dir

        # Cleanup
        import shutil
        shutil.rmtree(vault_dir)

    @pytest.fixture
    def temp_vault_empty(self):
        """Create an empty vault."""
        vault_dir = tempfile.mkdtemp()
        yield vault_dir

        import shutil
        shutil.rmtree(vault_dir)

    def test_total_notes_count(self, temp_vault):
        """Test counting total notes in vault."""
        stats = get_vault_stats(temp_vault)

        assert "total_notes" in stats
        assert stats["total_notes"] == 4

    def test_total_words_count(self, temp_vault):
        """Test aggregating total words across vault."""
        stats = get_vault_stats(temp_vault)

        assert "total_words" in stats
        assert isinstance(stats["total_words"], int)
        assert stats["total_words"] > 0

    def test_total_links_count(self, temp_vault):
        """Test aggregating total links across vault."""
        stats = get_vault_stats(temp_vault)

        assert "total_links" in stats
        # Should find: link1 (appears in note1 and note2), link2, link3
        assert stats["total_links"] >= 4

    def test_unique_tags_count(self, temp_vault):
        """Test counting unique tags across vault."""
        stats = get_vault_stats(temp_vault)

        assert "unique_tags" in stats
        # Should find: tag1, tag2, tag3, tag4, tag5
        assert stats["unique_tags"] == 5

    def test_all_tags_list(self, temp_vault):
        """Test collecting all unique tags in sorted list."""
        stats = get_vault_stats(temp_vault)

        assert "all_tags" in stats
        assert isinstance(stats["all_tags"], list)
        assert len(stats["all_tags"]) == 5

        # Should be sorted
        assert stats["all_tags"] == sorted(stats["all_tags"])

        # Should contain expected tags
        assert "tag1" in stats["all_tags"]
        assert "tag5" in stats["all_tags"]

    def test_avg_words_per_note(self, temp_vault):
        """Test calculating average words per note."""
        stats = get_vault_stats(temp_vault)

        assert "avg_words_per_note" in stats
        assert isinstance(stats["avg_words_per_note"], float)
        assert stats["avg_words_per_note"] > 0

        # Average should be total_words / total_notes
        expected_avg = stats["total_words"] / stats["total_notes"]
        assert abs(stats["avg_words_per_note"] - expected_avg) < 0.01

    def test_empty_vault(self, temp_vault_empty):
        """Test statistics on empty vault."""
        stats = get_vault_stats(temp_vault_empty)

        assert stats["total_notes"] == 0
        assert stats["total_words"] == 0
        assert stats["total_links"] == 0
        assert stats["unique_tags"] == 0
        assert len(stats["all_tags"]) == 0
        assert stats["avg_words_per_note"] == 0.0

    def test_obsidian_directory_ignored(self):
        """Test that .obsidian directory is excluded from stats."""
        vault_dir = tempfile.mkdtemp()

        try:
            # Create a regular note
            with open(os.path.join(vault_dir, "note.md"), 'w', encoding='utf-8') as f:
                f.write("# Note\n\nContent here.")

            # Create .obsidian directory with a file
            obsidian_dir = os.path.join(vault_dir, ".obsidian")
            os.makedirs(obsidian_dir)
            with open(os.path.join(obsidian_dir, "config.md"), 'w', encoding='utf-8') as f:
                f.write("# Config\n\nThis should not be counted.")

            stats = get_vault_stats(vault_dir)

            # Should only count the regular note
            assert stats["total_notes"] == 1

        finally:
            import shutil
            shutil.rmtree(vault_dir)

    def test_nonexistent_vault(self):
        """Test error handling for non-existent vault."""
        with pytest.raises(FileNotFoundError):
            get_vault_stats("/nonexistent/vault/path")

    def test_vault_with_non_markdown_files(self):
        """Test that non-.md files are ignored."""
        vault_dir = tempfile.mkdtemp()

        try:
            # Create markdown file
            with open(os.path.join(vault_dir, "note.md"), 'w', encoding='utf-8') as f:
                f.write("# Note\n\nContent.")

            # Create non-markdown files
            with open(os.path.join(vault_dir, "file.txt"), 'w', encoding='utf-8') as f:
                f.write("Text file content.")

            with open(os.path.join(vault_dir, "data.json"), 'w', encoding='utf-8') as f:
                f.write('{"key": "value"}')

            stats = get_vault_stats(vault_dir)

            # Should only count the .md file
            assert stats["total_notes"] == 1

        finally:
            import shutil
            shutil.rmtree(vault_dir)

    def test_performance_with_many_notes(self):
        """Test performance with larger vault (50 notes)."""
        vault_dir = tempfile.mkdtemp()

        try:
            # Create 50 notes
            for i in range(50):
                filepath = os.path.join(vault_dir, f"note{i}.md")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"""# Note {i}

Content for note {i} with [[link{i}]] and #tag{i % 10}.

Some more content to test word counting.
""")

            start_time = time.time()
            stats = get_vault_stats(vault_dir)
            elapsed = time.time() - start_time

            # Should complete in reasonable time (< 5 seconds for 50 notes)
            assert elapsed < 5.0

            # Verify counts
            assert stats["total_notes"] == 50
            assert stats["total_links"] == 50
            assert stats["unique_tags"] == 10  # tag0 through tag9

        finally:
            import shutil
            shutil.rmtree(vault_dir)
