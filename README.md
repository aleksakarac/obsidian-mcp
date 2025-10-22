# Obsidian MCP Extended

A comprehensive MCP server for Obsidian with **45 tools** across **hybrid filesystem-native and API-based** architectures. Extends [obsidian-mcp](https://github.com/punkpeye/obsidian-mcp) with advanced plugin control, backlinks, tag management, and analytics.

> **Note**: This project extends the base `obsidian-mcp` server. The original README is preserved as [README.upstream.md](README.upstream.md).

## 🌟 Features

### Hybrid Architecture

**Filesystem-Native Tools (33 tools)** - Work completely offline, no Obsidian required:
- ✅ Direct file access for maximum performance
- ✅ Zero Obsidian plugins needed
- ✅ Instant startup, minimal memory
- ✅ Full offline capability

**API-Based Tools (12 tools)** - Enhanced features when Obsidian is running:
- 🔌 Real-time workspace control
- 🔌 Advanced plugin integration (Templater, Dataview DQL)
- 🔌 Command palette access
- 🔌 Requires [Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api)

---

## 📦 Complete Tool List (45 Tools)

### 🔗 Backlink Analysis (2 tools - Filesystem)
- `get_backlinks_fs` - Find all notes linking to a specific note
- `get_broken_links_fs` - Identify broken wikilinks in vault

### 🏷️ Tag Management (4 tools - Filesystem)
- `analyze_note_tags_fs` - Extract frontmatter and inline tags
- `add_tag_fs` - Add tags to note frontmatter
- `remove_tag_fs` - Remove tags from frontmatter
- `search_by_tag_fs` - Find notes by tag

### ✏️ Smart Content Insertion (4 tools - Filesystem)
- `insert_after_heading_fs` - Insert content after specific headings
- `insert_after_block_fs` - Insert after block references
- `update_frontmatter_field_fs` - Update/add frontmatter fields
- `append_to_note_fs` - Append content to note end

### 📊 Statistics & Analytics (2 tools - Filesystem)
- `note_statistics_fs` - Comprehensive stats for individual notes
- `vault_statistics_fs` - Aggregate vault statistics

### ✅ Tasks Plugin (5 tools - Filesystem)
- `search_tasks` - Search tasks with emoji metadata (📅⏫🔁✅)
- `create_task` - Create tasks with metadata
- `toggle_task_status` - Toggle complete/incomplete
- `update_task_metadata` - Update due dates, priority, recurrence
- `get_task_statistics` - Task completion analytics

### 📊 Dataview Inline Fields (4 tools - Filesystem)
- `extract_dataview_fields` - Parse all syntax variants (::, [], ())
- `search_by_dataview_field` - Find notes by field values
- `add_dataview_field` - Add inline fields
- `remove_dataview_field` - Remove inline fields

### 📋 Kanban Boards (5 tools - Filesystem)
- `parse_kanban_board` - Parse markdown Kanban structure
- `add_kanban_card` - Add cards to columns
- `move_kanban_card` - Move cards between columns
- `toggle_kanban_card` - Toggle card completion
- `get_kanban_statistics` - Board analytics

### 🔗 Enhanced Link Tracking (5 tools - Filesystem)
- `get_link_graph` - Complete vault link graph
- `find_orphaned_notes` - Identify isolated notes
- `find_hub_notes` - Find highly connected notes
- `analyze_link_health` - Vault connectivity metrics
- `get_note_connections` - Multi-level connection exploration

### 🎨 Canvas Files (5 tools - Filesystem)
- `parse_canvas` - Parse JSON Canvas v1.0 files
- `add_canvas_node` - Add text/file nodes
- `add_canvas_edge` - Connect nodes with edges
- `remove_canvas_node` - Delete nodes
- `get_canvas_node_connections` - Analyze node relationships

### 📝 Templates (3 tools - Filesystem)
- `expand_template` - Simple {{variable}} expansion
- `create_note_from_template_fs` - Apply templates offline
- `list_templates` - Browse available templates

### 🔌 Dataview Query API (4 tools - Requires Obsidian + Dataview)
- `execute_dataview_query` - Execute full DQL queries (LIST/TABLE/TASK)
- `list_notes_by_tag_dql` - DQL tag-based queries
- `list_notes_by_folder_dql` - DQL folder queries
- `table_query_dql` - Create tabular data views

### 🔌 Templater Plugin API (3 tools - Requires Obsidian + Templater)
- `render_templater_template` - Dynamic template rendering
- `create_note_from_template_api` - Create notes from Templater templates
- `insert_templater_template` - Insert templates at cursor

### 🔌 Workspace Management (6 tools - Requires Obsidian)
- `get_active_file` - Get currently active file
- `open_file` - Open files in Obsidian
- `close_active_file` - Close current file
- `navigate_back` - Navigate backward in history
- `navigate_forward` - Navigate forward in history
- `toggle_edit_mode` - Switch edit/preview mode

### 🔌 Command Execution (3 tools - Requires Obsidian)
- `execute_command` - Run Obsidian commands
- `list_commands` - List all available commands
- `search_commands` - Search commands by name/ID

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.11+ required
python --version

# Install uv (recommended package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation

```bash
# Clone repository
git clone https://github.com/aleksakarac/obsidian-mcp.git
cd obsidian-mcp

# Install with uv (recommended)
uv pip install .

# Or with pip
pip install .
```

### Configuration

#### For Filesystem-Only Tools (No Obsidian Required)

Add to your Claude Code config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/obsidian-mcp",
        "run",
        "obsidian-mcp"
      ],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/path/to/your/obsidian/vault"
      }
    }
  }
}
```

#### For Full Hybrid Mode (Filesystem + API Tools)

1. Install [Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api) in Obsidian
2. Configure plugin settings:
   - Enable HTTPS: No (use HTTP for localhost)
   - API Key: Generate a secure key
   - Port: 27124 (default)

3. Update Claude Code config:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/obsidian-mcp",
        "run",
        "obsidian-mcp"
      ],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/path/to/your/obsidian/vault",
        "OBSIDIAN_REST_API_KEY": "your-api-key-here",
        "OBSIDIAN_API_URL": "http://localhost:27124"
      }
    }
  }
}
```

---

## 📖 Usage Examples

### Tasks Plugin (Filesystem-Native)

```python
# Search for high-priority incomplete tasks
search_tasks(
    status="incomplete",
    priority="high",
    sort_by="due_date",
    limit=10
)

# Create task with metadata
create_task(
    file_path="Projects/Current.md",
    content="Review PR #123",
    priority="high",
    due_date="2025-11-01",
    tags=["code-review", "urgent"]
)
```

### Dataview Fields (Filesystem-Native)

```python
# Extract all inline fields
extract_dataview_fields(file_path="Project Notes.md")

# Find notes where status=active
search_by_dataview_field(
    field_name="status",
    field_value="active"
)
```

### Kanban Boards (Filesystem-Native)

```python
# Parse board structure
parse_kanban_board(file_path="Boards/Sprint.md")

# Move card between columns
move_kanban_card(
    file_path="Boards/Sprint.md",
    card_text="Implement authentication",
    from_column="To Do",
    to_column="In Progress"
)
```

### Link Analysis (Filesystem-Native)

```python
# Find orphaned notes
find_orphaned_notes()

# Get link graph
get_link_graph()

# Analyze vault health
analyze_link_health()
```

### Dataview Queries (Requires Obsidian)

```python
# Execute DQL query
execute_dataview_query(
    query="TABLE status, due FROM #project WHERE status = 'active'"
)
```

### Workspace Control (Requires Obsidian)

```python
# Open file
open_file(file_path="Daily/2025-10-22.md")

# Get active file
get_active_file()

# Execute command
execute_command(command_id="editor:toggle-bold")
```

---

## 🏗️ Architecture

### Hybrid Design Philosophy

**Filesystem-First Approach:**
- Everything that CAN be filesystem-native, IS filesystem-native
- Direct file access for reading/writing markdown
- Zero dependencies on Obsidian plugins for core features
- Full offline capability

**API Enhancement:**
- API tools complement filesystem tools
- Provide features impossible without Obsidian (workspace UI, command execution)
- Enable plugin integration (Templater, Dataview DQL)
- Graceful degradation with clear error messages

### Technology Stack

- **FastMCP**: MCP protocol implementation
- **Pydantic**: Type-safe data models with validation
- **Python Standard Library**: Zero external dependencies for filesystem operations
- **httpx**: Async HTTP client for API tools

### Performance

**Filesystem Tools:**
- 1,000 notes: < 3 seconds for full vault scans
- Single note operations: < 100ms
- Link graph generation: < 10 seconds for 1,000 notes

**API Tools:**
- Command execution: < 500ms
- Query execution: Depends on Dataview plugin
- Workspace operations: < 200ms

---

## 🧪 Testing

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

```bash
# Run all tests
uv run pytest

# Run specific test suite
uv run pytest tests/unit/test_tasks.py -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

---

## 📝 Development

### Project Structure

```
obsidian-mcp/
├── src/
│   ├── models/          # Pydantic data models
│   ├── tools/           # MCP tool implementations
│   ├── utils/           # Shared utilities (patterns, API client)
│   └── server.py        # FastMCP server with tool registrations
├── tests/
│   ├── unit/            # Unit tests for tools
│   └── integration/     # End-to-end workflow tests
├── specs/               # Feature specifications
└── pyproject.toml       # Project configuration
```

### Adding New Tools

1. Create tool module in `src/tools/`
2. Add Pydantic models to `src/models/obsidian.py` (if needed)
3. Register tool in `src/server.py` with `@mcp.tool()` decorator
4. Add unit tests in `tests/unit/`
5. Update README.md and CHANGELOG.md

---

## 🤝 Contributing

Contributions welcome! Please:
1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- Base implementation: [obsidian-mcp](https://github.com/punkpeye/obsidian-mcp)
- MCP Protocol: [Model Context Protocol](https://modelcontextprotocol.io/)
- Obsidian: [Obsidian.md](https://obsidian.md/)

---

## 📚 Additional Documentation

- [TESTING.md](TESTING.md) - Testing guide
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [README.upstream.md](README.upstream.md) - Original obsidian-mcp README
- [specs/](specs/) - Feature specifications and design docs
