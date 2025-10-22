# Implementation Plan: Hybrid Plugin Control System

**Branch**: `002-hybrid-plugin-control` | **Date**: 2025-10-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-hybrid-plugin-control/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature extends the Obsidian MCP server with hybrid control capabilities for popular Obsidian plugins (Tasks, Dataview, Templater, Kanban, Canvas, Excalidraw) while maintaining the filesystem-native performance advantages. The implementation uses a two-tier approach: **filesystem-native operations** (priority) for all operations that can be performed via direct file manipulation (task metadata parsing, Dataview inline fields, Kanban boards, canvas JSON files, link tracking), and **API-based operations** (when Obsidian must be running) for features requiring Obsidian's runtime environment (Dataview query execution, Templater JavaScript execution, workspace control, command execution). This hybrid architecture enables complete Obsidian control while preserving the 90% memory reduction and 60x performance advantages of filesystem-based operations for core workflows.

## Technical Context

**Language/Version**: Python 3.11+ (existing project requirement)
**Primary Dependencies**:
- Existing: `fastmcp>=0.5.8`, `httpx>=0.25.0`, `python-dotenv>=1.0.0`, `pydantic>=2.0.0`, `python-frontmatter>=1.0.0`
- New: None (uses stdlib for regex parsing, JSON handling, and HTTP client via existing `httpx`)
**Storage**: Filesystem-native (.md markdown files, .canvas JSON files) + SQLite indexing (future optimization, not required for MVP)
**Testing**: pytest>=7.0.0, pytest-asyncio>=0.21.0, pytest-mock>=3.10.0 (existing)
**Target Platform**: Linux, macOS, Windows (cross-platform via Python stdlib)
**Project Type**: Single project (MCP server extension)
**Performance Goals**:
- Task search: <3s for 1,000 notes
- Dataview field extraction: <100ms per note
- Kanban operations: <500ms per operation
- Canvas creation: <1s for 50 nodes
- API calls: <3s with 30s timeout
**Constraints**:
- Must maintain <100MB memory for 1,000 note vaults (filesystem-native operations)
- Must work offline for all filesystem-native tools
- Must gracefully degrade when Obsidian API unavailable
- Zero new external dependencies (use stdlib + existing deps)
**Scale/Scope**:
- Support vaults up to 1,000 notes (primary target), scalable to 10,000 notes
- 40+ new MCP tools (~25 filesystem-native, ~15 API-based)
- 12 new key entities (Task, Dataview Field, Kanban structures, Canvas nodes, etc.)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Performance-First Architecture ✅ PASS

**Compliance**: This feature maintains and extends the performance-first architecture:
- Filesystem-native operations (Tasks, Dataview fields, Kanban, Canvas creation, enhanced links) use direct file I/O with no Obsidian dependency
- API-based operations (Dataview queries, Templater, workspace control) only activate when Obsidian is running
- No blocking operations: async API calls with timeouts
- Memory-efficient: regex parsing, streaming file reads, no in-memory vault caching
- Performance targets documented in spec (SC-001 through SC-015)

**Justification**: The hybrid approach enhances the base implementation by adding features while preserving the filesystem-native performance for all operations that don't absolutely require Obsidian's runtime.

### II. Zero External Dependencies ✅ PASS (with architectural decision)

**Compliance**:
- Filesystem-native tools: 100% independent, no Obsidian required
- API-based tools: **Optional** dependency on Obsidian Local REST API plugin
- No new Python dependencies added (uses stdlib regex, json, datetime)
- Offline capability maintained for all filesystem operations

**Architectural Decision**: API-based tools are clearly marked with `_api_tool` suffix and provide informative errors when Obsidian is not running. Users choose their usage model:
- **Offline-only**: Use filesystem-native tools (Tasks, Dataview fields, Kanban, Canvas, links)
- **Hybrid**: Use filesystem tools + API tools when Obsidian is running for advanced features

This does not violate the principle because the server still "operates independently" for all core functionality. API features are opt-in enhancements, not core requirements.

### III. Filesystem-Native Operations ✅ PASS

**Compliance**: All new operations use filesystem-native approaches where possible:
- Tasks plugin metadata: regex parsing of markdown emoji syntax
- Dataview inline fields: regex extraction from note content
- Kanban boards: markdown structure parsing and manipulation
- Canvas files: JSON file creation and parsing
- Enhanced link tracking: regex detection of all link syntaxes
- Templates: text file reading with variable substitution

Only when filesystem operations are insufficient (executing JavaScript, querying Obsidian's internal index, controlling UI) do we use the optional API path.

### IV. Feature Parity with API-Based Solutions ✅ PASS

**Compliance**: This feature achieves feature parity and exceeds API-based solutions:
- Matches capabilities: Task management, Dataview queries, Canvas manipulation
- Exceeds in performance: Filesystem operations are faster than API calls
- Exceeds in offline capability: API-based servers cannot work offline
- Provides unique hybrid value: Users get best of both approaches

### V. Backward Compatibility ✅ PASS

**Compliance**:
- All existing tools from feature 001 remain functional (FR-054)
- Tool naming convention prevents conflicts (`_fs_tool` vs `_api_tool`)
- Environment variables extended (OBSIDIAN_API_URL, OBSIDIAN_REST_API_KEY), not replaced
- No breaking changes to existing tool interfaces
- Existing OBSIDIAN_VAULT_PATH usage unchanged

**Migration**: Users can adopt new tools incrementally. No forced migration required.

### Constitution Compliance Summary

**Result**: ✅ ALL GATES PASSED

All five constitutional principles are respected. The hybrid architecture is a thoughtful extension that preserves core values while enabling advanced features through optional API integration.

## Project Structure

### Documentation (this feature)

```text
specs/002-hybrid-plugin-control/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── tasks-fs.md          # Tasks plugin filesystem tools
│   ├── dataview-fs.md       # Dataview inline field tools
│   ├── dataview-api.md      # Dataview query execution tools
│   ├── kanban-fs.md         # Kanban board tools
│   ├── links-fs.md          # Enhanced link tracking tools
│   ├── templates-fs.md      # Basic template tools
│   ├── templates-api.md     # Templater execution tools
│   ├── canvas-fs.md         # Canvas file manipulation tools
│   ├── canvas-api.md        # Canvas UI tools
│   ├── workspace-api.md     # Workspace control tools
│   ├── commands-api.md      # Command execution tools
│   └── graph-fs.md          # Graph analysis tools
├── checklists/
│   └── requirements.md  # Spec quality checklist (completed)
├── spec.md              # Feature specification (completed)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
CustomObsidianMcp/
├── src/
│   ├── server.py                    # EXTEND: Register new MCP tools
│   ├── models/
│   │   └── obsidian.py              # EXTEND: Add Task, DataviewField, KanbanBoard, CanvasNode entities
│   ├── tools/
│   │   ├── backlinks.py             # EXISTING: Enhanced with embed/block/section tracking
│   │   ├── tags.py                  # EXISTING: Enhanced with Dataview field support
│   │   ├── smart_insert.py          # EXISTING: Used as reference for content manipulation
│   │   ├── statistics.py            # EXISTING: Enhanced with Dataview fields, task counts
│   │   ├── note_management.py       # EXISTING: Reference for CRUD patterns
│   │   ├── search_discovery.py      # EXISTING: Reference for vault scanning
│   │   ├── organization.py          # EXISTING: Reference for folder operations
│   │   ├── tasks.py                 # NEW: Tasks plugin support (filesystem)
│   │   ├── dataview_fs.py           # NEW: Dataview inline fields (filesystem)
│   │   ├── dataview_api.py          # NEW: Dataview query execution (API)
│   │   ├── kanban.py                # NEW: Kanban board manipulation (filesystem)
│   │   ├── templates_fs.py          # NEW: Basic template application (filesystem)
│   │   ├── templates_api.py         # NEW: Templater execution (API)
│   │   ├── canvas_fs.py             # NEW: Canvas file manipulation (filesystem)
│   │   ├── canvas_api.py            # NEW: Canvas UI control (API)
│   │   ├── workspace_api.py         # NEW: Workspace control (API)
│   │   ├── commands_api.py          # NEW: Command execution (API)
│   │   └── graph_analysis.py        # NEW: Orphan/hub detection (filesystem)
│   └── utils/
│       ├── validators.py            # EXISTING: Enhanced with new validation patterns
│       ├── validation.py            # EXISTING: Used for input validation
│       ├── patterns.py              # EXISTING: Enhanced with task/dataview/kanban regex
│       ├── obsidian_api.py          # EXISTING: Reference (unused in this feature)
│       ├── obsidian_api_client.py   # NEW: HTTP client for Local REST API
│       └── api_availability.py      # NEW: API detection and graceful degradation
├── tests/
│   ├── unit/
│   │   ├── test_backlinks.py        # EXISTING: Enhanced with new link types
│   │   ├── test_tags.py             # EXISTING: Enhanced with Dataview fields
│   │   ├── test_smart_insert.py     # EXISTING: Reference
│   │   ├── test_statistics.py       # EXISTING: Enhanced with new metrics
│   │   ├── test_tasks.py            # NEW: Tasks plugin parsing and manipulation
│   │   ├── test_dataview_fs.py      # NEW: Dataview inline field extraction
│   │   ├── test_dataview_api.py     # NEW: Dataview query execution (requires Obsidian)
│   │   ├── test_kanban.py           # NEW: Kanban board operations
│   │   ├── test_templates_fs.py     # NEW: Template substitution
│   │   ├── test_templates_api.py    # NEW: Templater execution (requires Obsidian)
│   │   ├── test_canvas_fs.py        # NEW: Canvas JSON manipulation
│   │   ├── test_canvas_api.py       # NEW: Canvas UI operations (requires Obsidian)
│   │   ├── test_workspace_api.py    # NEW: Workspace control (requires Obsidian)
│   │   ├── test_commands_api.py     # NEW: Command execution (requires Obsidian)
│   │   ├── test_graph_analysis.py   # NEW: Graph metrics
│   │   └── test_api_client.py       # NEW: API client behavior
│   ├── integration/
│   │   └── test_hybrid_workflows.py # NEW: End-to-end hybrid scenarios
│   └── conftest.py                  # EXTEND: Add fixtures for API mocking, test vaults
├── specs/                           # EXISTING: Feature specifications
├── pyproject.toml                   # EXTEND: Version bump, maintain dependencies
├── README.md                        # EXTEND: Document new tools, hybrid architecture
└── TESTING.md                       # EXTEND: Document API testing requirements
```

**Structure Decision**: Single project structure is appropriate. This is an extension of an existing MCP server, not a new service. All tools are registered in `server.py` and organized by functional area (tasks, dataview, kanban, etc.) under `src/tools/`. The hybrid architecture (filesystem + API) is a deployment choice, not a code structure distinction—both types of tools coexist in the same server process.

## Complexity Tracking

No constitutional violations to justify. All gates passed in Constitution Check.
