<!--
Sync Impact Report:
- Version change: [UNVERSIONED] → 1.0.0
- Initial constitution creation
- Principles derived from Project_Description.md
- Templates requiring updates:
  ✅ constitution.md (created)
  ⚠ plan-template.md (pending review)
  ⚠ spec-template.md (pending review)
  ⚠ tasks-template.md (pending review)
-->

# Obsidian MCP Extended Constitution

## Core Principles

### I. Performance-First Architecture
The project MUST maintain or improve upon the base `obsidian-mcp` performance characteristics:
- Direct filesystem access with SQLite indexing
- 90% less memory usage compared to API-based alternatives
- 60x faster searches than API-based solutions
- Instant startup with persistent indexing
- No blocking operations on Obsidian application

**Rationale**: The primary value proposition is combining performance with features. Any feature that degrades performance below the base implementation must be rejected or redesigned.

### II. Zero External Dependencies
The server MUST operate independently without requiring:
- Obsidian application to be running
- Obsidian plugins or extensions
- Network connectivity for local operations
- External services or APIs for core functionality

**Rationale**: Independence ensures reliability, offline capability, and simplifies deployment for users who want a lightweight solution.

### III. Filesystem-Native Operations
All features MUST be implemented using direct filesystem operations:
- Read/write operations on `.md` files
- SQLite for indexing and caching
- Standard file system APIs (no proprietary formats)
- Respect Obsidian's file structure conventions

**Rationale**: Filesystem-native operations ensure compatibility, debuggability, and maintain performance advantages. Users can inspect and modify vault contents with any tool.

### IV. Feature Parity with API-Based Solutions
The project MUST implement all major features available in API-based MCP servers:
- Backlink analysis and broken link detection
- Comprehensive tag management (frontmatter + inline)
- Smart content insertion at specific locations
- Detailed note and vault statistics
- Any additional features that enhance user workflows

**Rationale**: Users should not have to choose between performance and features. The goal is to demonstrate that filesystem-based implementation can match or exceed API-based capabilities.

### V. Backward Compatibility
The project MUST maintain compatibility with the base `obsidian-mcp` implementation:
- All existing tools remain functional
- Existing configurations continue to work
- No breaking changes to tool interfaces without major version bump
- Migration path provided for any structural changes

**Rationale**: Users should be able to adopt this extended version without disrupting existing workflows or configurations.

## Implementation Standards

### Code Quality
- All Python code MUST follow PEP 8 style guidelines
- Type hints REQUIRED for all function signatures
- Docstrings REQUIRED for all public functions and classes
- Error handling MUST be explicit and informative
- No silent failures or swallowed exceptions

### Testing Requirements
- Unit tests REQUIRED for all utility functions
- Integration tests REQUIRED for all MCP tools
- Test coverage MUST be maintained above 80%
- Edge cases (empty vaults, malformed files) MUST be tested
- Performance regression tests for critical paths

### Documentation Standards
- README.md MUST include setup, configuration, and usage examples
- Each new tool MUST be documented with examples
- API changes MUST be documented in a CHANGELOG
- Troubleshooting section MUST address common issues
- Comparison table with alternatives MUST be maintained

## Development Workflow

### Feature Development Process
1. Specification: Define feature requirements and acceptance criteria
2. Design: Document implementation approach respecting core principles
3. Test Design: Write tests that validate the specification
4. Implementation: Build the feature to pass the tests
5. Documentation: Update README and relevant docs
6. Validation: Verify no performance regression

### Code Review Requirements
- All changes MUST pass automated tests
- Performance benchmarks MUST be verified for critical paths
- Documentation updates MUST accompany feature additions
- Breaking changes REQUIRE explicit approval and migration guide
- Security considerations MUST be addressed for file operations

### Deployment Standards
- `uv` package manager is the primary installation method
- Installation MUST work on Linux, macOS, and Windows
- Configuration via environment variables preferred
- MCP server registration examples MUST be provided
- Version compatibility with Claude Code MUST be verified

## Governance

### Amendment Process
- Constitutional amendments REQUIRE documented rationale
- Breaking changes to principles REQUIRE major version increment
- Community feedback SHOULD be considered for significant changes
- All amendments MUST update dependent templates and documentation

### Compliance
- All pull requests MUST verify constitutional compliance
- Performance regressions MUST be justified or rejected
- New dependencies MUST be justified (favor stdlib where possible)
- Security vulnerabilities MUST be addressed immediately

### Version Management
This constitution follows semantic versioning:
- MAJOR: Principle removal or backward-incompatible governance changes
- MINOR: New principles or materially expanded guidance
- PATCH: Clarifications, wording improvements, non-semantic fixes

**Version**: 1.0.0 | **Ratified**: 2025-10-22 | **Last Amended**: 2025-10-22
