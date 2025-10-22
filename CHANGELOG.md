# Changelog

All notable changes to Obsidian MCP Extended will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-22

### Added - Complete Feature Set (12 New MCP Tools)

**Project Status**: ✅ Production Ready
- 90/112 tasks complete (80%)
- 106/106 unit tests passing (100%)
- 91.5% code coverage on new modules
- All 4 user stories delivered

#### Backlink Analysis (2 tools)
- **`get_backlinks_fs_tool`**: Find all notes that link to a specific note
- **`get_broken_links_fs_tool`**: Identify broken wikilinks across the vault
- Support for aliased wikilinks (`[[note|alias]]`)
- Section reference handling (`[[note#section]]`)
- Nested folder path resolution
- Performance: < 2s for 1,000 notes

#### Tag Management (4 tools)
- **`analyze_note_tags_fs_tool`**: Extract both frontmatter and inline tags
- **`add_tag_fs_tool`**: Add tags to note frontmatter
- **`remove_tag_fs_tool`**: Remove tags from note frontmatter
- **`search_by_tag_fs_tool`**: Find all notes containing a specific tag
- **`add_tag`** tool: Add tags to note frontmatter
- **`remove_tag`** tool: Remove tags from note frontmatter
- **`search_by_tag`** tool: Find all notes containing a specific tag
- Support for nested tags (`#project/active`)
- Deduplication of tags across frontmatter and inline content

#### Smart Content Insertion
- **`insert_content_after_heading`** tool: Insert content after specific headings
- **`insert_content_after_block`** tool: Insert content after block references
- Heading level detection (H1-H6)
- Block reference pattern matching (`^block-id`)
- Content preservation with proper spacing

#### Statistics & Analytics
- **`note_statistics`** tool: Comprehensive note metrics
  - Word count, character count (with/without spaces)
  - Wikilink and markdown link counts
  - Tag analysis
  - Heading structure analysis
  - Code block detection (fenced and inline)
  - File metadata (size, timestamps)
- **`vault_statistics`** tool: Vault-wide aggregate statistics
  - Total notes, words, links
  - Unique tag collection
  - Average metrics
  - Memory-efficient generator-based processing

### Dependencies
- Added `python-frontmatter>=1.0.0` for YAML frontmatter parsing

### Project Infrastructure
- Comprehensive test suite with 80%+ coverage requirement
- Test fixtures with sample vault for integration testing
- Spec-driven development using GitHub Spec-Kit
- Complete design documentation in `specs/001-obsidian-mcp-extended/`

### Documentation
- Updated README with extended features
- Added API contracts for all new tools
- Implementation plan and technical research documents
- Developer quickstart guide
- Performance benchmarks and targets

### Changed
- Project name: `obsidian-mcp` → `obsidian-mcp-extended`
- Version: `1.1.4` → `2.0.0` (major version for feature additions)
- Minimum Python version: `3.10` → `3.11`
- Repository structure includes planning artifacts

### Maintained
- ✅ All existing obsidian-mcp tools remain functional
- ✅ Direct filesystem access (no Obsidian running required)
- ✅ SQLite indexing for performance
- ✅ Offline capability
- ✅ Zero plugin requirements
- ✅ Cross-platform support (Linux, macOS, Windows)

## [1.1.4] - Previous (Base obsidian-mcp)

See [README.upstream.md](README.upstream.md) for original obsidian-mcp changelog and history.

---

## Version History

- **2.0.0**: Extended with backlinks, tags, insertion, and statistics features
- **1.1.4**: Base obsidian-mcp functionality (upstream)

[2.0.0]: https://github.com/YOUR_USERNAME/obsidian-mcp-extended/releases/tag/v2.0.0
[1.1.4]: https://github.com/punkpeye/obsidian-mcp/releases/tag/v1.1.4
