# Tasks: Hybrid Plugin Control System

**Input**: Design documents from `/specs/002-hybrid-plugin-control/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the specification. Test tasks are included for quality assurance but can be implemented during or after feature development.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Project uses **single project** structure (MCP server extension):
- Source: `src/` at repository root
- Tests: `tests/` at repository root
- Models: `src/models/obsidian.py`
- Tools: `src/tools/`
- Utils: `src/utils/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Verify project structure matches plan.md (src/, tests/, src/tools/, src/utils/, src/models/)
- [ ] T002 [P] Create src/utils/patterns.py for compiled regex patterns (Tasks, Dataview, Kanban, Links)
- [ ] T003 [P] Create src/utils/obsidian_api_client.py for Local REST API HTTP client
- [ ] T004 [P] Create src/utils/api_availability.py for API detection and graceful degradation
- [ ] T005 Update pyproject.toml version to indicate hybrid plugin control feature (maintain existing dependencies)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Extend src/models/obsidian.py with Task, DataviewField, KanbanBoard, KanbanColumn, KanbanCard, CanvasNode, CanvasEdge, CanvasFile, LinkReference, TemplateFile, ObsidianCommand, WorkspaceLayout, APIClientConfig Pydantic models
- [ ] T007 [P] Implement regex patterns in src/utils/patterns.py: TASK_DUE_DATE, TASK_PRIORITY, TASK_RECURRENCE, TASK_SCHEDULED, TASK_START, TASK_DONE, TASK_CREATED
- [ ] T008 [P] Implement regex patterns in src/utils/patterns.py: DATAVIEW_FULL_LINE, DATAVIEW_BRACKET, DATAVIEW_PAREN, DATE_ISO8601, LIST_QUOTED
- [ ] T009 [P] Implement regex patterns in src/utils/patterns.py: KANBAN_COLUMN, KANBAN_CARD, KANBAN_DATE, WIKILINK, TAG
- [ ] T010 [P] Implement regex patterns in src/utils/patterns.py: LINK_EMBED, LINK_SECTION, LINK_BLOCK for enhanced link tracking
- [ ] T011 Implement ObsidianAPIClient class in src/utils/obsidian_api_client.py with is_available(), execute_command(), search_simple(), get_file(), put_file() methods
- [ ] T012 Implement require_api_available() and get_api_client() helpers in src/utils/api_availability.py
- [ ] T013 [P] Create tests/conftest.py with fixtures: temp_vault, sample_tasks, api_available, mock_api_client
- [ ] T014 [P] Update src/server.py to import and register new tool modules (will be populated in user story phases)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Manage Tasks with Metadata (Priority: P1) 🎯 MVP

**Goal**: Search, filter, and create tasks with full Tasks plugin metadata (due dates, priorities, recurrence) programmatically without opening Obsidian

**Independent Test**: Create tasks with metadata, search for tasks by due date/priority, and toggle completion status. Should work completely offline without Obsidian running.

### Implementation for User Story 1

- [ ] T015 [P] [US1] Create src/tools/tasks.py module with parse_task_line() function using regex from src/utils/patterns.py
- [ ] T016 [P] [US1] Implement format_task_line() function in src/tools/tasks.py to generate task lines with emoji metadata
- [ ] T017 [US1] Implement search_tasks_fs_tool() in src/tools/tasks.py with filters (status, priority, due_before, due_after, due_within_days, has_recurrence, tag)
- [ ] T018 [US1] Implement create_task_fs_tool() in src/tools/tasks.py with priority, due_date, scheduled_date, start_date, recurrence parameters
- [ ] T019 [US1] Implement toggle_task_status_fs_tool() in src/tools/tasks.py with add_done_date option
- [ ] T020 [US1] Implement update_task_metadata_fs_tool() in src/tools/tasks.py for updating task metadata without changing content
- [ ] T021 [US1] Implement get_task_statistics_fs_tool() in src/tools/tasks.py with scope (note/vault) and group_by options
- [ ] T022 [US1] Add validation for date formats (YYYY-MM-DD) and recurrence patterns (must start with "every")
- [ ] T023 [P] [US1] Create tests/unit/test_tasks.py with test_parse_task_metadata(), test_create_task_with_metadata(), test_toggle_task_status(), test_filter_tasks_by_priority()
- [ ] T024 [US1] Register all tasks tools in src/server.py

**Checkpoint**: At this point, User Story 1 should be fully functional - can manage tasks with full metadata offline

---

## Phase 4: User Story 2 - Extract and Query Dataview Metadata (Priority: P1)

**Goal**: Extract Dataview inline fields from notes and search notes by field values programmatically based on custom metadata without Obsidian running

**Independent Test**: Create notes with inline fields, extract metadata, and search by field values. Should work completely offline without Obsidian running.

### Implementation for User Story 2

- [ ] T025 [P] [US2] Create src/tools/dataview_fs.py module with extract_dataview_fields() function using regex from src/utils/patterns.py
- [ ] T026 [P] [US2] Implement canonicalize_key() function in src/tools/dataview_fs.py for field name normalization
- [ ] T027 [P] [US2] Implement detect_value_type() function in src/tools/dataview_fs.py to parse strings, numbers, booleans, dates, links, lists
- [ ] T028 [US2] Implement extract_dataview_fields_fs_tool() in src/tools/dataview_fs.py to extract all inline fields from a note
- [ ] T029 [US2] Implement search_by_dataview_field_fs_tool() in src/tools/dataview_fs.py to find notes by field name and value
- [ ] T030 [US2] Implement add_dataview_field_fs_tool() in src/tools/dataview_fs.py to add inline field to note
- [ ] T031 [US2] Implement remove_dataview_field_fs_tool() in src/tools/dataview_fs.py to remove inline field from note
- [ ] T032 [US2] Enhance src/tools/statistics.py to include dataview_fields in note statistics output
- [ ] T033 [P] [US2] Create tests/unit/test_dataview_fs.py with test_extract_all_syntax_variants(), test_canonicalize_key(), test_value_type_detection(), test_search_by_field()
- [ ] T034 [US2] Register all dataview_fs tools in src/server.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - can manage tasks and dataview fields offline

---

## Phase 5: User Story 3 - Manipulate Kanban Boards (Priority: P2)

**Goal**: Read Kanban board structure, add cards, and move cards between columns programmatically without manual editing

**Independent Test**: Parse kanban markdown files, add cards to columns, and move cards between columns. Should work completely offline without Obsidian running.

### Implementation for User Story 3

- [ ] T035 [P] [US3] Create src/tools/kanban.py module with parse_kanban_structure() function using regex from src/utils/patterns.py
- [ ] T036 [P] [US3] Implement parse_card_metadata() function in src/tools/kanban.py to extract dates, tags, wikilinks from cards
- [ ] T037 [P] [US3] Implement format_kanban_card() function in src/tools/kanban.py to generate card lines with metadata
- [ ] T038 [US3] Implement parse_kanban_board_fs_tool() in src/tools/kanban.py to extract board structure with columns and cards
- [ ] T039 [US3] Implement add_kanban_card_fs_tool() in src/tools/kanban.py to add card to specified column
- [ ] T040 [US3] Implement move_kanban_card_fs_tool() in src/tools/kanban.py to move card between columns (with subtasks)
- [ ] T041 [US3] Implement toggle_kanban_card_fs_tool() in src/tools/kanban.py to toggle card completion status
- [ ] T042 [US3] Implement get_kanban_statistics_fs_tool() in src/tools/kanban.py with card counts, completion rates per column
- [ ] T043 [P] [US3] Create tests/unit/test_kanban.py with test_parse_board_structure(), test_add_card(), test_move_card_with_subtasks(), test_preserve_metadata()
- [ ] T044 [US3] Register all kanban tools in src/server.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - tasks, dataview, kanban all offline

---

## Phase 6: User Story 4 - Track All Link Types (Priority: P2)

**Goal**: Track embedded links, block references, and section links in addition to regular wikilinks for comprehensive knowledge graph analysis

**Independent Test**: Create notes with various link types (embeds, sections, blocks) and verify all types are detected. Should work completely offline.

### Implementation for User Story 4

- [ ] T045 [P] [US4] Enhance src/tools/backlinks.py with get_all_link_types() function using enhanced regex from src/utils/patterns.py
- [ ] T046 [US4] Implement get_all_link_types_fs_tool() in src/tools/backlinks.py to categorize links by type (wikilink/embed/section/block)
- [ ] T047 [US4] Implement get_embed_references_fs_tool() in src/tools/backlinks.py to find all ![[note]] transclusions
- [ ] T048 [US4] Implement get_block_references_fs_tool() in src/tools/backlinks.py to find all [[note#^block]] references with block IDs
- [ ] T049 [US4] Implement get_section_links_fs_tool() in src/tools/backlinks.py to find all [[note#heading]] references with section names
- [ ] T050 [US4] Enhance existing get_backlinks_fs_tool() in src/tools/backlinks.py to include link_type field in output
- [ ] T051 [P] [US4] Create tests/unit/test_links.py with test_detect_all_link_types(), test_embed_extraction(), test_block_reference_extraction(), test_section_link_extraction()
- [ ] T052 [US4] Register enhanced link tracking tools in src/server.py

**Checkpoint**: At this point, User Stories 1-4 work independently - comprehensive offline note analysis capabilities

---

## Phase 7: User Story 5 - Execute Dataview Queries (Priority: P2)

**Goal**: Execute Dataview Query Language (DQL) and DataviewJS queries through Claude Code to generate dynamic views and tables

**Independent Test**: Execute DQL queries (LIST, TABLE, TASK) and verify results. Requires Obsidian running with Local REST API plugin.

### Implementation for User Story 5

- [ ] T053 [P] [US5] Create src/tools/dataview_api.py module importing get_api_client() and require_api_available() from src/utils/api_availability.py
- [ ] T054 [US5] Implement execute_dataview_query_api_tool() in src/tools/dataview_api.py for DQL query execution via POST /search/ with Content-Type application/vnd.olrapi.dataview.dql+txt
- [ ] T055 [US5] Implement execute_dataviewjs_api_tool() in src/tools/dataview_api.py for DataviewJS code block execution
- [ ] T056 [US5] Add error handling for API unavailable, timeout (30s), and query execution errors with clear user messages
- [ ] T057 [P] [US5] Create tests/unit/test_dataview_api.py with conditional skip decorator @pytest.mark.skipif for API tests
- [ ] T058 [US5] Register dataview_api tools in src/server.py

**Checkpoint**: User Story 5 adds API-based Dataview queries while maintaining Stories 1-4 offline functionality

---

## Phase 8: User Story 6 - Execute Templates with Dynamic Variables (Priority: P3)

**Goal**: Execute Templater templates with full JavaScript support and variable substitution programmatically through Claude Code

**Independent Test**: Trigger Templater templates with variables and verify dynamic content generation. Requires Obsidian running with Templater plugin and Local REST API.

### Implementation for User Story 6

- [ ] T059 [P] [US6] Create src/tools/templates_api.py module importing API client utilities
- [ ] T060 [US6] Implement execute_templater_template_api_tool() in src/tools/templates_api.py using command execution (templater-obsidian:create-new-note-from-template or similar)
- [ ] T061 [US6] Implement list_templater_templates_api_tool() in src/tools/templates_api.py to get available templates
- [ ] T062 [US6] Add support for dynamic variables (date functions, file operations, system prompts) via Templater API
- [ ] T063 [P] [US6] Create tests/unit/test_templates_api.py with conditional API availability checks
- [ ] T064 [US6] Register templates_api tools in src/server.py

**Checkpoint**: User Story 6 adds Templater execution while maintaining all previous stories

---

## Phase 9: User Story 7 - Apply Simple Templates (Priority: P3)

**Goal**: Apply template files with basic variable substitution (dates, titles, custom variables) without requiring Obsidian running

**Independent Test**: Apply templates with variable substitution and verify output. Should work completely offline.

### Implementation for User Story 7

- [ ] T065 [P] [US7] Create src/tools/templates_fs.py module with parse_template_variables() function
- [ ] T066 [P] [US7] Implement substitute_variables() function in src/tools/templates_fs.py for {{variable}} replacement
- [ ] T067 [US7] Implement list_templates_fs_tool() in src/tools/templates_fs.py to find all templates in designated folder
- [ ] T068 [US7] Implement apply_template_fs_tool() in src/tools/templates_fs.py with built-in variables (date, time, title) and custom variables
- [ ] T069 [US7] Implement create_note_from_template_fs_tool() in src/tools/templates_fs.py combining template application and note creation
- [ ] T070 [P] [US7] Create tests/unit/test_templates_fs.py with test_variable_substitution(), test_builtin_variables(), test_custom_variables()
- [ ] T071 [US7] Register templates_fs tools in src/server.py

**Checkpoint**: User Story 7 adds offline templating while maintaining API-based Templater (US6) and all other stories

---

## Phase 10: User Story 8 - Control Obsidian Workspace UI (Priority: P3)

**Goal**: Programmatically open files in specific panes, control sidebar visibility, and save/load workspace layouts

**Independent Test**: Open files in different pane configurations and toggle UI elements. Requires Obsidian running with Local REST API and Workspaces plugin.

### Implementation for User Story 8

- [ ] T072 [P] [US8] Create src/tools/workspace_api.py module importing API client utilities
- [ ] T073 [US8] Implement open_file_in_pane_api_tool() in src/tools/workspace_api.py using POST /open/{filename} with newLeaf parameter
- [ ] T074 [US8] Implement control_sidebar_api_tool() in src/tools/workspace_api.py using command execution (workspace:toggle-sidebar, etc.)
- [ ] T075 [US8] Implement save_workspace_layout_api_tool() in src/tools/workspace_api.py using Workspaces plugin commands
- [ ] T076 [US8] Implement load_workspace_layout_api_tool() in src/tools/workspace_api.py to restore saved layouts
- [ ] T077 [US8] Implement get_active_file_api_tool() in src/tools/workspace_api.py using GET /active/
- [ ] T078 [P] [US8] Create tests/unit/test_workspace_api.py with conditional API checks
- [ ] T079 [US8] Register workspace_api tools in src/server.py

**Checkpoint**: User Story 8 adds workspace control while maintaining all previous functionality

---

## Phase 11: User Story 9 - Create and Edit Canvas Files (Priority: P3)

**Goal**: Programmatically create canvas files, add nodes (notes, text, media), and define connections between nodes

**Independent Test**: Create canvas JSON files with nodes and edges, verify structure. Canvas viewing requires Obsidian but file creation works standalone.

### Implementation for User Story 9

- [ ] T080 [P] [US9] Create src/tools/canvas_fs.py module with generate_canvas_id() function using secrets.token_hex(8)
- [ ] T081 [P] [US9] Implement create_canvas_node() function in src/tools/canvas_fs.py for all node types (text, file, link, group)
- [ ] T082 [P] [US9] Implement create_canvas_edge() function in src/tools/canvas_fs.py with fromNode, toNode, sides, ends
- [ ] T083 [P] [US9] Implement validate_canvas() function in src/tools/canvas_fs.py to check JSON structure, node ID uniqueness, edge references
- [ ] T084 [US9] Implement create_canvas_fs_tool() in src/tools/canvas_fs.py to generate new .canvas file with nodes and edges
- [ ] T085 [US9] Implement add_canvas_node_fs_tool() in src/tools/canvas_fs.py to add node to existing canvas
- [ ] T086 [US9] Implement add_canvas_edge_fs_tool() in src/tools/canvas_fs.py to create connection between nodes
- [ ] T087 [US9] Implement parse_canvas_fs_tool() in src/tools/canvas_fs.py to extract node and edge structures
- [ ] T088 [P] [US9] Create src/tools/canvas_api.py module for UI operations
- [ ] T089 [US9] Implement open_canvas_api_tool() in src/tools/canvas_api.py using command execution to open canvas in Obsidian
- [ ] T090 [P] [US9] Create tests/unit/test_canvas_fs.py with test_generate_id(), test_create_nodes(), test_validate_structure(), test_canvas_json()
- [ ] T091 [P] [US9] Create tests/unit/test_canvas_api.py with conditional API checks
- [ ] T092 [US9] Register all canvas tools (fs and api) in src/server.py

**Checkpoint**: User Story 9 adds canvas manipulation while maintaining all previous stories

---

## Phase 12: User Story 10 - Execute Obsidian Commands (Priority: P3)

**Goal**: Execute any Obsidian command (core or plugin) by command ID programmatically through Claude Code

**Independent Test**: List available commands and execute specific commands by ID. Requires Obsidian running with Local REST API plugin.

### Implementation for User Story 10

- [ ] T093 [P] [US10] Create src/tools/commands_api.py module importing API client utilities
- [ ] T094 [US10] Implement list_obsidian_commands_api_tool() in src/tools/commands_api.py using GET /commands/
- [ ] T095 [US10] Implement execute_obsidian_command_api_tool() in src/tools/commands_api.py using POST /commands/{commandId}/
- [ ] T096 [US10] Implement execute_command_batch_api_tool() in src/tools/commands_api.py for sequential command execution
- [ ] T097 [US10] Implement search_commands_api_tool() in src/tools/commands_api.py to filter commands by name or ID pattern
- [ ] T098 [P] [US10] Create tests/unit/test_commands_api.py with conditional API checks
- [ ] T099 [US10] Register commands_api tools in src/server.py

**Checkpoint**: User Story 10 completes all 10 user stories - full hybrid plugin control system

---

## Phase 13: Graph Analysis (Filesystem-Native Enhancement)

**Goal**: Provide graph analysis features (orphan notes, hub detection) that enhance existing backlink functionality

**Independent Test**: Identify orphan notes and hub notes in vaults. Should work completely offline.

### Implementation for Graph Analysis

- [ ] T100 [P] Create src/tools/graph_analysis.py module using link tracking from backlinks
- [ ] T101 [P] Implement calculate_link_metrics() function in src/tools/graph_analysis.py to count incoming/outgoing links per note
- [ ] T102 Implement find_orphan_notes_fs_tool() in src/tools/graph_analysis.py to identify notes with no incoming or outgoing links
- [ ] T103 Implement analyze_note_connections_fs_tool() in src/tools/graph_analysis.py with incoming count, outgoing count, centrality score
- [ ] T104 Implement find_hub_notes_fs_tool() in src/tools/graph_analysis.py based on configurable connection threshold (default 10)
- [ ] T105 [P] Create tests/unit/test_graph_analysis.py with test_orphan_detection(), test_hub_identification(), test_centrality_calculation()
- [ ] T106 Register graph_analysis tools in src/server.py

**Checkpoint**: Graph analysis enhancement adds analytical capabilities to existing link tracking

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T107 [P] Update README.md with all new tools, hybrid architecture explanation, configuration examples
- [ ] T108 [P] Update TESTING.md with API testing requirements, conditional skip patterns, test vault setup
- [ ] T109 Enhance src/tools/statistics.py to include task_count, dataview_fields_count, kanban_boards_count in vault statistics
- [ ] T110 [P] Create tests/integration/test_hybrid_workflows.py with end-to-end scenarios (task → kanban, dataview extraction → statistics)
- [ ] T111 Add performance logging to identify slow operations (>1s for filesystem, >5s for API)
- [ ] T112 [P] Add comprehensive error messages with troubleshooting steps for common issues (API unavailable, invalid metadata, etc.)
- [ ] T113 Run validation tests from quickstart.md examples to ensure all documented patterns work
- [ ] T114 Code cleanup: Remove any debug logging, ensure consistent error handling, verify all tools follow naming conventions
- [ ] T115 Update CHANGELOG.md with feature 002 hybrid plugin control additions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-12)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
  - **P1 Stories** (US1, US2): Critical value, implement first
  - **P2 Stories** (US3, US4, US5): High value enhancements
  - **P3 Stories** (US6, US7, US8, US9, US10): Nice-to-have features
- **Graph Analysis (Phase 13)**: Depends on Foundational + US4 (link tracking)
- **Polish (Phase 14)**: Depends on all desired user stories being complete

### User Story Dependencies

**No Dependencies (Can Start After Foundational):**
- User Story 1 (Tasks) - T015-T024
- User Story 2 (Dataview FS) - T025-T034
- User Story 3 (Kanban) - T035-T044
- User Story 5 (Dataview API) - T053-T058
- User Story 6 (Templater API) - T059-T064
- User Story 7 (Templates FS) - T065-T071
- User Story 8 (Workspace) - T072-T079
- User Story 9 (Canvas) - T080-T092
- User Story 10 (Commands) - T093-T099

**Soft Dependency:**
- User Story 4 (Link Tracking) - Should complete before Graph Analysis (Phase 13)
- Graph Analysis - Uses outputs from US4

### Within Each User Story

- All [P] tasks within a story can run in parallel
- Non-[P] tasks may depend on [P] tasks completing first
- Tool registration (last task in each story) depends on all implementations

### Parallel Opportunities

- **Setup Phase**: T002, T003, T004 can run in parallel (different files)
- **Foundational Phase**: T007, T008, T009, T010, T013, T014 can run in parallel (different files)
- **Within User Stories**: All tasks marked [P] can run in parallel
- **Across User Stories**: After Foundational completes, all user stories can progress in parallel
- **Polish Phase**: T107, T108, T110, T112 can run in parallel (different files)

---

## Parallel Example: User Story 1 (Tasks)

```bash
# After Foundational Phase completes, launch all [P] tasks together:
Task T015: "Create src/tools/tasks.py module..."
Task T016: "Implement format_task_line() function..."
Task T023: "Create tests/unit/test_tasks.py..."

# Then launch sequential tasks:
Task T017: "Implement search_tasks_fs_tool()..." (depends on T015, T016)
Task T018: "Implement create_task_fs_tool()..." (depends on T015, T016)
# ... etc
```

---

## Parallel Example: Cross-Story Parallelization

```bash
# After Foundational Phase completes, all stories can start in parallel:

# Developer 1 (or Agent 1):
User Story 1: T015-T024 (Tasks plugin)

# Developer 2 (or Agent 2):
User Story 2: T025-T034 (Dataview filesystem)

# Developer 3 (or Agent 3):
User Story 3: T035-T044 (Kanban boards)

# All three streams can progress independently and in parallel
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T014) - **CRITICAL BLOCKER**
3. Complete Phase 3: User Story 1 - Tasks (T015-T024)
4. Complete Phase 4: User Story 2 - Dataview FS (T025-T034)
5. **STOP and VALIDATE**: Test offline task management and dataview field extraction
6. Deploy/demo MVP

**MVP Scope**: 34 tasks (T001-T034)
**MVP Value**: Complete offline task and metadata management for most popular plugins

### Incremental Delivery (Priority-Based)

1. Foundation: Setup + Foundational (T001-T014) → 14 tasks
2. **MVP**: + US1 + US2 (T015-T034) → 20 tasks added = 34 total
3. **Enhanced**: + US3 + US4 + US5 (T035-T058) → 24 tasks added = 58 total
4. **Full**: + US6-US10 + Graph + Polish (T059-T115) → 57 tasks added = 115 total

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With 3 developers after Foundational phase completes:

**Week 1-2**:
- Dev A: User Story 1 (Tasks) + User Story 2 (Dataview FS)
- Dev B: User Story 3 (Kanban) + User Story 4 (Links)
- Dev C: User Story 5 (Dataview API) + User Story 7 (Templates FS)

**Week 3**:
- Dev A: User Story 6 (Templater API) + User Story 8 (Workspace)
- Dev B: User Story 9 (Canvas) + User Story 10 (Commands)
- Dev C: Graph Analysis + Polish

All stories integrate independently.

---

## Task Statistics

**Total Tasks**: 115

**By Phase**:
- Setup: 5 tasks (T001-T005)
- Foundational: 9 tasks (T006-T014) - **BLOCKS all stories**
- User Story 1 (P1): 10 tasks (T015-T024)
- User Story 2 (P1): 10 tasks (T025-T034)
- User Story 3 (P2): 10 tasks (T035-T044)
- User Story 4 (P2): 8 tasks (T045-T052)
- User Story 5 (P2): 6 tasks (T053-T058)
- User Story 6 (P3): 6 tasks (T059-T064)
- User Story 7 (P3): 7 tasks (T065-T071)
- User Story 8 (P3): 8 tasks (T072-T079)
- User Story 9 (P3): 13 tasks (T080-T092)
- User Story 10 (P3): 7 tasks (T093-T099)
- Graph Analysis: 7 tasks (T100-T106)
- Polish: 9 tasks (T107-T115)

**Parallelizable Tasks**: 42 tasks marked [P] (36% can run in parallel)

**Critical Path** (shortest path to MVP):
1. Setup (5 tasks)
2. Foundational (9 tasks) - **Must complete serially due to dependencies**
3. US1 implementation (10 tasks - some parallel)
4. US2 implementation (10 tasks - some parallel)
**Total**: ~34 tasks for MVP

**Estimated Effort**:
- MVP (US1+US2): 2-3 weeks
- Enhanced (US1-US5): 4-5 weeks
- Full (US1-US10 + Graph + Polish): 6-7 weeks

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [US#] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MVP scope (US1+US2) delivers maximum value for offline workflows
- All filesystem tools work without Obsidian running (constitutional compliance)
- All API tools gracefully degrade with clear error messages when Obsidian unavailable
- Performance targets validated in research.md for all operations
