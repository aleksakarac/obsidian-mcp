# Implementation Plan: Extended Obsidian MCP Server

**Branch**: `001-obsidian-mcp-extended` | **Date**: 2025-10-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-obsidian-mcp-extended/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Extend the existing `obsidian-mcp` Python MCP server with four advanced feature modules (backlinks, tag management, smart insertion, statistics) while maintaining its core performance advantages: direct filesystem access, SQLite indexing, 90% less memory usage, and 60x faster searches compared to API-based alternatives. The implementation will add new tool modules in `src/tools/` and register them in `src/server.py`, requiring only the `python-frontmatter` library as an additional dependency.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
  - Existing: `mcp>=0.1.0` (MCP SDK), existing obsidian-mcp dependencies
  - New: `python-frontmatter>=1.0.0` (YAML frontmatter parsing)
**Storage**: Direct filesystem access (`.md` files) + SQLite for indexing (existing `.obsidian/mcp-search-index.db`)
**Testing**: pytest (unit tests), MCP Inspector (integration tests), manual testing with Claude Code
**Target Platform**: Linux, macOS, Windows (cross-platform via Python)
**Project Type**: Single Python package (extending existing obsidian-mcp structure)
**Performance Goals**:
  - Backlinks: <2s for 1,000 note vaults
  - Tag search: <3s for 1,000 note vaults
  - Content insertion: <500ms for 10,000 word notes
  - Vault statistics: <30s for 1,000 note vaults
**Constraints**:
  - Memory: <100MB for 1,000 note vaults
  - Zero Obsidian dependency (no application running required)
  - Offline capable (no network required)
  - Filesystem-native operations only
**Scale/Scope**:
  - Target vault size: up to 1,000 notes (baseline), scalable to 10,000+ notes
  - 4 new feature modules with 12 new MCP tools
  - 30 functional requirements across backlinks, tags, insertion, statistics

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Performance-First Architecture ✅
- **Status**: COMPLIANT
- Direct filesystem access maintained (no API layer)
- SQLite indexing preserved from base implementation
- All performance targets defined and measured
- No blocking operations on Obsidian

### Principle II: Zero External Dependencies ✅
- **Status**: COMPLIANT
- No Obsidian application required
- No plugins needed
- Works fully offline
- Only adds `python-frontmatter` (YAML parsing library, minimal footprint)

### Principle III: Filesystem-Native Operations ✅
- **Status**: COMPLIANT
- All features use direct file I/O
- SQLite only for optional caching/indexing
- Standard `.md` file format
- Respects Obsidian conventions

### Principle IV: Feature Parity with API-Based Solutions ✅
- **Status**: COMPLIANT
- Implements all major features: backlinks, tags, insertion, statistics
- Matches or exceeds API-based capabilities
- No feature gaps

### Principle V: Backward Compatibility ✅
- **Status**: COMPLIANT
- Extends existing `obsidian-mcp` structure
- All existing tools remain unchanged
- Additive changes only (new modules, new tools)
- No breaking changes to interfaces

### Implementation Standards ✅
- **Code Quality**: PEP 8, type hints, docstrings required
- **Testing**: 80%+ coverage, unit + integration tests
- **Documentation**: README, tool examples, CHANGELOG required

### Development Workflow ✅
- **Process**: Spec → Design → Tests → Implementation → Docs → Validation
- **Review**: Automated tests, performance benchmarks required
- **Deployment**: `uv` package manager, cross-platform support

**GATE RESULT**: ✅ PASSED - All constitutional principles satisfied, no violations

## Project Structure

### Documentation (this feature)

```text
specs/001-obsidian-mcp-extended/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0: Technical decisions & patterns
├── data-model.md        # Phase 1: Entity definitions & relationships
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/           # Phase 1: MCP tool interface definitions
│   ├── backlinks.md     # Backlink tools: get_backlinks, get_broken_links
│   ├── tags.md          # Tag tools: analyze_note_tags, add_tag, remove_tag, search_by_tag
│   ├── insertion.md     # Insertion tools: insert_content_after_heading, insert_content_after_block
│   └── statistics.md    # Statistics tools: note_statistics, vault_statistics
├── checklists/          # Quality validation checklists
│   └── requirements.md  # Specification quality checklist (completed)
└── tasks.md             # Phase 2: Implementation tasks (/speckit.tasks - NOT YET CREATED)
```

### Source Code (repository root)

**Note**: This project extends an existing repository (`obsidian-mcp`). We are forking and adding new modules to the existing structure.

```text
obsidian-mcp-extended/  (forked repository root)
├── src/
│   ├── server.py                  # MODIFY: Register 12 new MCP tools
│   ├── tools/
│   │   ├── note_management.py     # EXISTING: Keep unchanged
│   │   ├── search_discovery.py    # EXISTING: Keep unchanged
│   │   ├── organization.py        # EXISTING: Keep unchanged
│   │   ├── backlinks.py           # NEW: Backlink analysis functions
│   │   ├── tags.py                # NEW: Tag management functions
│   │   ├── smart_insert.py        # NEW: Content insertion functions
│   │   └── statistics.py          # NEW: Note & vault statistics
│   ├── models/
│   │   └── obsidian.py            # EXISTING: May extend for new entities
│   ├── utils/
│   │   ├── validators.py          # EXISTING: May add tag/link validators
│   │   └── validation.py          # EXISTING: Keep unchanged
│   └── constants.py               # EXISTING: May add new constants
│
├── tests/
│   ├── unit/
│   │   ├── test_backlinks.py      # NEW: Unit tests for backlink functions
│   │   ├── test_tags.py           # NEW: Unit tests for tag functions
│   │   ├── test_smart_insert.py   # NEW: Unit tests for insertion functions
│   │   └── test_statistics.py     # NEW: Unit tests for statistics functions
│   ├── integration/
│   │   ├── test_backlinks_integration.py  # NEW: MCP tool integration tests
│   │   ├── test_tags_integration.py       # NEW: MCP tool integration tests
│   │   ├── test_insertion_integration.py  # NEW: MCP tool integration tests
│   │   └── test_statistics_integration.py # NEW: MCP tool integration tests
│   └── fixtures/
│       └── sample_vault/          # NEW: Test vault with sample notes
│
├── pyproject.toml                 # MODIFY: Add python-frontmatter dependency
├── README.md                      # MODIFY: Update with new features
├── CHANGELOG.md                   # NEW: Document changes from base
└── .obsidian/                     # EXISTING: SQLite index location
    └── mcp-search-index.db
```

**Structure Decision**: Single Python package (Option 1) extending the existing `obsidian-mcp` repository structure. We maintain the modular architecture with new tool modules in `src/tools/`, comprehensive tests in `tests/`, and registration in `src/server.py`. This approach preserves backward compatibility while cleanly segregating new functionality.

## Complexity Tracking

**No violations** - All implementation decisions align with constitutional principles. No complexity justifications needed.
