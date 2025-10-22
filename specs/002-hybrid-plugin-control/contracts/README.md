# MCP Tool Contracts Summary

This directory contains detailed specifications for all 40+ MCP tools in the hybrid plugin control system.

## Tool Organization

### Filesystem-Native Tools (~25 tools)
These tools work without Obsidian running and use direct file I/O:

- **tasks-fs.md**: Tasks plugin support (5 tools)
  - search_tasks_fs_tool
  - create_task_fs_tool
  - toggle_task_status_fs_tool
  - update_task_metadata_fs_tool
  - get_task_statistics_fs_tool

- **dataview-fs.md**: Dataview inline fields (4 tools)
  - extract_dataview_fields_fs_tool
  - search_by_dataview_field_fs_tool
  - add_dataview_field_fs_tool
  - remove_dataview_field_fs_tool

- **kanban-fs.md**: Kanban board manipulation (5 tools)
  - parse_kanban_board_fs_tool
  - add_kanban_card_fs_tool
  - move_kanban_card_fs_tool
  - toggle_kanban_card_fs_tool
  - get_kanban_statistics_fs_tool

- **links-fs.md**: Enhanced link tracking (4 tools)
  - get_all_link_types_fs_tool
  - get_embed_references_fs_tool
  - get_block_references_fs_tool
  - get_section_links_fs_tool

- **templates-fs.md**: Basic template application (3 tools)
  - list_templates_fs_tool
  - apply_template_fs_tool
  - create_note_from_template_fs_tool

- **canvas-fs.md**: Canvas file manipulation (4 tools)
  - create_canvas_fs_tool
  - add_canvas_node_fs_tool
  - add_canvas_edge_fs_tool
  - parse_canvas_fs_tool

- **graph-fs.md**: Graph analysis (3 tools)
  - find_orphan_notes_fs_tool
  - analyze_note_connections_fs_tool
  - find_hub_notes_fs_tool

### API-Based Tools (~15 tools)
These tools require Obsidian running with Local REST API plugin:

- **dataview-api.md**: Dataview query execution (2 tools)
  - execute_dataview_query_api_tool
  - execute_dataviewjs_api_tool

- **templates-api.md**: Templater execution (2 tools)
  - execute_templater_template_api_tool
  - list_templater_templates_api_tool

- **canvas-api.md**: Canvas UI control (2 tools)
  - open_canvas_api_tool
  - get_canvas_viewport_api_tool

- **workspace-api.md**: Workspace control (5 tools)
  - open_file_in_pane_api_tool
  - control_sidebar_api_tool
  - save_workspace_layout_api_tool
  - load_workspace_layout_api_tool
  - get_active_file_api_tool

- **commands-api.md**: Command execution (4 tools)
  - list_obsidian_commands_api_tool
  - execute_obsidian_command_api_tool
  - execute_command_batch_api_tool
  - search_commands_api_tool

## Tool Naming Convention

- `*_fs_tool`: Filesystem-native (works offline)
- `*_api_tool`: API-based (requires Obsidian)

All tool descriptions clearly indicate whether Obsidian is required.

## Contract Structure

Each contract file contains:
1. Tool purpose and requirements
2. Input/output schemas (TypeScript notation)
3. Error cases and handling
4. Usage examples
5. Implementation notes
6. Performance targets
7. Testing requirements

## Performance Targets

- Filesystem operations: <500ms (most <100ms)
- API operations: <3s with 30s timeout
- Vault-wide scans: <5s for 1,000 notes
- Memory: <100MB for normal operations

## Error Handling

All tools follow consistent error patterns:
- Descriptive error messages
- Specific error codes (FILE_NOT_FOUND, API_UNAVAILABLE, etc.)
- Graceful degradation for API tools
- Never silent failures

## Documentation

See individual contract files for detailed specifications of each tool.
