# Feature Specification: Extended Obsidian MCP Server

**Feature Branch**: `001-obsidian-mcp-extended`
**Created**: 2025-10-22
**Status**: Draft
**Input**: User description: "Extended Obsidian MCP server with backlinks, tag management, smart insertion, and statistics features while maintaining filesystem-based performance"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover Note Connections via Backlinks (Priority: P1)

As an Obsidian user working with Claude Code, I want to find all notes that link to a specific note so I can understand the context and relationships within my knowledge base without opening Obsidian.

**Why this priority**: Backlink discovery is fundamental to understanding note relationships in a networked note-taking system. This is the most frequently used feature in knowledge management workflows and provides immediate value for users building interconnected knowledge bases.

**Independent Test**: Can be fully tested by querying backlinks for a known note and verifying all linking notes are returned. Delivers value independently by enabling users to understand note relationships through Claude Code.

**Acceptance Scenarios**:

1. **Given** a vault with multiple notes containing wikilinks, **When** I request backlinks for a specific note, **Then** I receive a list of all notes that link to it with their file paths
2. **Given** a note with no backlinks, **When** I request backlinks for it, **Then** I receive an empty list with appropriate messaging
3. **Given** notes with wikilink aliases (e.g., `[[note|alias]]`), **When** I request backlinks, **Then** aliased links are correctly identified and included
4. **Given** a request for broken links in the vault, **When** the system scans all notes, **Then** I receive a list of all wikilinks pointing to non-existent notes

---

### User Story 2 - Manage Tags Across Vault (Priority: P1)

As an Obsidian user, I want to add, remove, and search for tags (both frontmatter and inline) across my vault so I can organize and categorize my notes programmatically through Claude Code.

**Why this priority**: Tag management is critical for organization and retrieval. This enables users to maintain taxonomies and find related content, which is essential for knowledge management workflows. Equal priority to backlinks as both are core organizational features.

**Independent Test**: Can be fully tested by adding/removing tags to notes and searching for notes by tag. Delivers value independently by enabling programmatic tag-based organization.

**Acceptance Scenarios**:

1. **Given** a note with frontmatter tags, **When** I extract all tags, **Then** I receive both frontmatter and inline tags separately and combined
2. **Given** a note path and a tag name, **When** I add the tag to frontmatter, **Then** the tag is added to the frontmatter tags list without duplicates
3. **Given** a note with a specific tag, **When** I remove the tag, **Then** the tag is removed from frontmatter and the file is updated
4. **Given** a tag name, **When** I search for notes by tag, **Then** I receive all notes containing that tag in either frontmatter or inline format
5. **Given** notes with nested tags (e.g., `#project/active`), **When** I search by partial tag, **Then** appropriate matching behavior occurs

---

### User Story 3 - Insert Content Intelligently (Priority: P2)

As an Obsidian user working with Claude Code, I want to insert content at specific locations (after headings, after blocks, in frontmatter) so I can update notes programmatically without manual editing.

**Why this priority**: Smart insertion enables automation and reduces manual work, but users can still accomplish their goals with manual editing. It's a productivity enhancer rather than core functionality, hence P2.

**Independent Test**: Can be fully tested by inserting content at various locations and verifying placement. Delivers value independently by enabling automated note updates.

**Acceptance Scenarios**:

1. **Given** a note with a specific heading, **When** I insert content after that heading, **Then** the content appears immediately after the heading before any other content
2. **Given** a note with block references, **When** I insert content after a specific block ID, **Then** the content appears on the next line after the block
3. **Given** a note, **When** I insert or update a frontmatter field, **Then** the frontmatter is created or updated without affecting note content
4. **Given** a note, **When** I append content, **Then** the content is added at the end with appropriate spacing
5. **Given** a note without the specified heading, **When** I attempt to insert after that heading, **Then** I receive a clear error message indicating the heading was not found

---

### User Story 4 - Analyze Note and Vault Statistics (Priority: P3)

As an Obsidian user, I want to view comprehensive statistics about my notes and vault (word counts, link counts, tag usage, file metadata) so I can understand my knowledge base growth and usage patterns.

**Why this priority**: Statistics provide insights but aren't essential for day-to-day workflows. Users can work effectively without this feature, making it a nice-to-have enhancement for power users.

**Independent Test**: Can be fully tested by requesting statistics for a note or vault and verifying metrics. Delivers value independently by providing analytical insights.

**Acceptance Scenarios**:

1. **Given** a specific note, **When** I request note statistics, **Then** I receive word count, character count, line count, link counts, tag counts, heading structure, code block counts, and file metadata
2. **Given** a vault, **When** I request vault statistics, **Then** I receive total notes, total words, total links, unique tags, and average words per note
3. **Given** a note with headings at different levels, **When** I request statistics, **Then** headings are grouped by level and structure is preserved
4. **Given** a note with both wikilinks and markdown links, **When** I request statistics, **Then** both types are counted separately and in total

---

### Edge Cases

- What happens when a note has both frontmatter and inline tags with the same name (avoid duplicates in "all_tags")?
- How does the system handle malformed frontmatter (missing closing `---`, invalid YAML)?
- What happens when inserting content would create invalid markdown structure?
- How does the system handle very large vaults (10,000+ notes) without performance degradation?
- What happens when file permissions prevent reading or writing a note?
- How does the system handle symbolic links or nested `.obsidian` directories?
- What happens when a note is modified externally while being processed?
- How does the system handle Unicode characters in note names, links, and content?
- What happens when circular wikilinks exist (Note A → Note B → Note A)?
- How does the system handle wikilinks with section references (e.g., `[[note#section]]`)?

## Requirements *(mandatory)*

### Functional Requirements

#### Backlink Analysis

- **FR-001**: System MUST scan all markdown files in the vault to find wikilinks matching the target note name
- **FR-002**: System MUST support both simple wikilinks (`[[note]]`) and aliased wikilinks (`[[note|alias]]`)
- **FR-003**: System MUST handle nested folder structures and relative wikilink paths
- **FR-004**: System MUST skip the `.obsidian` directory during vault scanning
- **FR-005**: System MUST identify broken wikilinks by comparing link targets against existing note names
- **FR-006**: System MUST return file paths, absolute paths, and link details for each backlink found

#### Tag Management

- **FR-007**: System MUST extract tags from both YAML frontmatter and inline markdown content
- **FR-008**: System MUST handle frontmatter tags as both single strings and arrays
- **FR-009**: System MUST parse inline tags using the pattern `#tag` and support nested tags (`#parent/child`)
- **FR-010**: System MUST add tags to frontmatter without creating duplicates
- **FR-011**: System MUST remove tags from frontmatter and clean up empty tag arrays
- **FR-012**: System MUST search for tags across all notes in the vault
- **FR-013**: System MUST indicate whether tags appear in frontmatter, inline, or both

#### Smart Content Insertion

- **FR-014**: System MUST insert content after markdown headings at any level (# to ######)
- **FR-015**: System MUST insert content after block references identified by `^block-id`
- **FR-016**: System MUST create or update frontmatter fields using the python-frontmatter library
- **FR-017**: System MUST append content to the end of notes with proper spacing
- **FR-018**: System MUST provide clear error messages when target locations (headings, blocks) are not found
- **FR-019**: System MUST preserve existing formatting and line endings during insertions

#### Statistics

- **FR-020**: System MUST calculate word count, character count (with and without spaces), and line count
- **FR-021**: System MUST count wikilinks and markdown links separately
- **FR-022**: System MUST extract and count unique tags
- **FR-023**: System MUST analyze heading structure by level
- **FR-024**: System MUST count code blocks (fenced) and inline code occurrences
- **FR-025**: System MUST retrieve file metadata (size, creation date, modification date, access date)
- **FR-026**: System MUST aggregate vault-wide statistics across all notes

#### Performance & Compatibility

- **FR-027**: System MUST maintain direct filesystem access without requiring Obsidian to be running
- **FR-028**: System MUST use UTF-8 encoding for all file operations
- **FR-029**: System MUST handle file I/O errors gracefully with informative error messages
- **FR-030**: System MUST be compatible with the existing obsidian-mcp tool interface patterns

### Key Entities

- **Note**: A markdown file (`.md`) in the vault with optional YAML frontmatter and markdown content
  - Attributes: file path, absolute path, content, frontmatter metadata, modification timestamp
  - Relationships: Links to other notes via wikilinks, has tags, contains headings and blocks

- **Wikilink**: A reference to another note using Obsidian's `[[note]]` or `[[note|alias]]` syntax
  - Attributes: target note name, display alias (optional), section reference (optional)
  - Relationships: Originates from one note, points to another note (or broken if target doesn't exist)

- **Tag**: A categorization marker in frontmatter (YAML array/string) or inline content (`#tag`)
  - Attributes: tag name, location (frontmatter/inline), nesting level (e.g., `parent/child`)
  - Relationships: Associated with one or more notes

- **Block**: A markdown content block with a unique identifier (`^block-id`)
  - Attributes: block ID, content, line position
  - Relationships: Exists within a note, can be referenced by other notes

- **Heading**: A markdown section header (`#` to `######`)
  - Attributes: level (1-6), text content, line position
  - Relationships: Organizes content within a note, can have child headings

- **Vault**: The root directory containing all Obsidian notes
  - Attributes: vault path, total note count, aggregate statistics
  - Relationships: Contains all notes, has a `.obsidian` metadata directory (excluded from processing)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can discover all backlinks for a note in under 2 seconds for vaults with up to 1,000 notes
- **SC-002**: Broken link detection completes in under 10 seconds for vaults with up to 1,000 notes
- **SC-003**: Tag search returns results in under 3 seconds for vaults with up to 1,000 notes
- **SC-004**: Content insertion operations complete instantly (under 500ms) for notes up to 10,000 words
- **SC-005**: Statistics generation for a single note completes in under 1 second
- **SC-006**: Vault-wide statistics calculation completes in under 30 seconds for vaults with up to 1,000 notes
- **SC-007**: Memory usage remains under 100MB during normal operations on vaults with up to 1,000 notes
- **SC-008**: All features work correctly with Unicode characters, special characters, and non-ASCII file names
- **SC-009**: 100% of valid wikilinks (both simple and aliased) are correctly identified in backlink analysis
- **SC-010**: Zero data loss or corruption occurs during tag management and content insertion operations
- **SC-011**: Users can successfully use all features without requiring Obsidian to be running
- **SC-012**: The extended server maintains backward compatibility with all existing obsidian-mcp tools

### Assumptions

- Vault size: Specifications assume vaults with up to 1,000 notes for performance targets. Larger vaults may require optimization or pagination.
- File format: All notes are valid UTF-8 encoded markdown files with `.md` extension
- Frontmatter format: YAML frontmatter follows standard Obsidian conventions (opening and closing `---` delimiters)
- Wikilink format: Uses Obsidian's standard wikilink syntax without custom link resolution rules
- File system: Standard POSIX-compliant filesystem with read/write permissions for the vault directory
- Concurrent access: No external processes are modifying files during MCP operations (single-user assumption)
- Python environment: Python 3.11+ with `uv` package manager available
- Dependencies: Only `python-frontmatter` library added beyond base obsidian-mcp dependencies

### Out of Scope

- Real-time file watching or automatic index updates when vault changes externally
- Obsidian plugin installation or API-based communication with Obsidian
- Graph visualization or visual rendering of backlink networks
- Template system or note creation from templates
- Dataview-like query language or complex filtering
- Export to formats other than markdown
- Sync conflict detection or resolution
- Encrypted vault support
- Mobile-specific optimizations or mobile app integration
