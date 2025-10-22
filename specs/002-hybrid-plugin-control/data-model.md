# Data Model: Hybrid Plugin Control System

**Feature**: 002-hybrid-plugin-control
**Date**: 2025-10-22
**Purpose**: Define entities, relationships, and validation rules for all hybrid plugin features

---

## Entity Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          Obsidian Vault                          │
│  (existing entity from feature 001)                              │
└────────────────┬────────────────────────────────────────────────┘
                 │ contains
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                              Note                                 │
│  (existing entity from feature 001)                               │
│  - file_path: string                                             │
│  - content: string                                               │
│  - frontmatter: dict                                             │
└──┬────────┬──────────┬────────────┬──────────┬──────────────┬───┘
   │        │          │            │          │              │
   │has     │has       │has         │has       │contains      │contains
   ▼        ▼          ▼            ▼          ▼              ▼
┌─────┐ ┌──────┐  ┌────────┐  ┌────────┐  ┌─────────┐  ┌────────────┐
│Task │ │Tag   │  │Wikilink│  │Dataview│  │KanbanBrd│  │CanvasFile  │
│     │ │      │  │        │  │Field   │  │         │  │            │
└─────┘ └──────┘  └────────┘  └────────┘  └─────────┘  └────────────┘
```

---

## Core Entities

### 1. Task

**Purpose**: Represents a checkbox task with Tasks plugin metadata

**Attributes:**
```python
class Task(BaseModel):
    content: str                    # Task description text
    status: Literal["incomplete", "completed"]
    priority: Optional[Literal["highest", "high", "normal", "low", "lowest"]] = "normal"
    due_date: Optional[date] = None       # 📅
    scheduled_date: Optional[date] = None # ⏳
    start_date: Optional[date] = None     # 🛫
    done_date: Optional[date] = None      # ✅
    created_date: Optional[date] = None   # ➕
    recurrence: Optional[str] = None      # 🔁 every ...
    line_number: int                      # Source line in file
    source_file: str                      # Absolute path to note
    tags: List[str] = []                  # Extracted #tags
```

**Validation Rules:**
- `content`: Non-empty string
- `status`: Must be "incomplete" or "completed"
- `priority`: One of defined levels or null (null = normal)
- Date fields: YYYY-MM-DD format if present
- `line_number`: Positive integer
- `source_file`: Valid file path in vault
- `recurrence`: Must start with "every" if present
- Logical date ordering: `start_date <= scheduled_date <= due_date` (warning if violated)

**State Transitions:**
```
incomplete ---[toggle_task_status]--> completed
  (- [ ])                              (- [x])
                                       + done_date if enabled
```

**Relationships:**
- Belongs to one `Note` (via `source_file`)
- May have child tasks (subtasks via indentation)
- May be part of recurring series (via `recurrence`)

---

### 2. DataviewField

**Purpose**: Represents a Dataview inline field embedded in note content

**Attributes:**
```python
class DataviewField(BaseModel):
    key: str                        # Original key as written
    value: Any                      # Parsed value (str, int, float, bool, list, date)
    canonical_key: str              # Normalized key (lowercase, hyphens)
    line_number: int
    syntax_type: Literal["full-line", "bracket", "paren"]
    source_file: str
    value_type: Literal["string", "number", "boolean", "date", "link", "list"]
```

**Validation Rules:**
- `key`: Non-empty, valid identifier pattern `[-\w\s]+`
- `value`: Type-checked based on `value_type`
- `canonical_key`: Lowercase, spaces → hyphens, alphanumeric only
- `syntax_type`: One of three valid formats
- `value_type`: Determined during parsing
- Date values: ISO8601 format
- List values: Array of parsed elements

**Canonicalization:**
```python
def canonicalize_key(key: str) -> str:
    """Convert key to canonical form"""
    return key.lower().replace(' ', '-').strip('_*~')
```

**Relationships:**
- Belongs to one `Note` (via `source_file`)
- May conflict with frontmatter field (creates array)
- May be nested within other inline content

---

### 3. KanbanBoard

**Purpose**: Represents a markdown-based Kanban board file

**Attributes:**
```python
class KanbanBoard(BaseModel):
    file_path: str                  # Absolute path to board file
    columns: List[KanbanColumn]
    settings: Dict[str, Any]        # From frontmatter (kanban-plugin config)
    total_cards: int                # Computed aggregate
```

**Validation Rules:**
- `file_path`: Valid .md file in vault
- `columns`: At least one column
- Column names: Unique within board
- `settings`: Valid YAML dict or empty

**Relationships:**
- Contains multiple `KanbanColumn`
- Stored as markdown file in vault

---

### 4. KanbanColumn

**Purpose**: Represents a column in a Kanban board (markdown heading)

**Attributes:**
```python
class KanbanColumn(BaseModel):
    name: str                       # Heading text (## Column Name)
    cards: List[KanbanCard]
    card_count: int                 # Computed
    heading_level: Literal[2] = 2   # Always level 2 for Kanban
    line_number: int                # Source line of heading
```

**Validation Rules:**
- `name`: Non-empty string
- `heading_level`: Must be 2 (## headings)
- `cards`: May be empty list
- Card order: Preserved from markdown

**Relationships:**
- Belongs to one `KanbanBoard`
- Contains zero or more `KanbanCard`

---

### 5. KanbanCard

**Purpose**: Represents a card (checkbox item) within a Kanban column

**Attributes:**
```python
class KanbanCard(BaseModel):
    text: str                       # Card description
    status: Literal["incomplete", "completed"]
    due_date: Optional[date] = None # @{YYYY-MM-DD} or @[[YYYY-MM-DD]]
    tags: List[str] = []            # Extracted #tags
    wikilinks: List[str] = []       # Extracted [[links]]
    subtasks: List[KanbanCard] = [] # Nested cards
    indent_level: int = 0           # 0 = root, 1+ = nested
    line_number: int
```

**Validation Rules:**
- `text`: Non-empty after metadata removal
- `status`: Toggle between incomplete/completed
- `due_date`: YYYY-MM-DD if present
- `indent_level`: Non-negative, determines nesting
- Subtasks: Recursive structure

**State Transitions:**
```
incomplete ---[move_to_done_column]--> completed
  (- [ ])                               (- [x])
```

**Relationships:**
- Belongs to one `KanbanColumn`
- May have child `KanbanCard` (subtasks)
- May reference notes via wikilinks

---

### 6. LinkReference

**Purpose**: Enhanced link tracking for all link types (extends feature 001)

**Attributes:**
```python
class LinkReference(BaseModel):
    link_type: Literal["wikilink", "embed", "section", "block"]
    source_file: str                # File containing the link
    target_file: str                # File being referenced
    link_text: str                  # Original link syntax
    alias: Optional[str] = None     # Display alias if present
    section_name: Optional[str] = None  # For [[note#section]]
    block_id: Optional[str] = None      # For [[note#^block]]
    line_number: int
    context: str = ""               # Surrounding text (20 chars each side)
```

**Validation Rules:**
- `link_type`: One of four types
- `source_file`, `target_file`: Valid paths
- `section_name`: Non-empty if link_type="section"
- `block_id`: Non-empty if link_type="block", starts with ^
- `alias`: May differ from target filename

**Relationships:**
- Originates from one `Note` (source)
- Points to another `Note` (target) or broken link
- May have context text for search results

---

### 7. CanvasFile

**Purpose**: Represents a .canvas JSON file for visual knowledge mapping

**Attributes:**
```python
class CanvasFile(BaseModel):
    file_path: str                  # Absolute path to .canvas file
    nodes: List[CanvasNode]
    edges: List[CanvasEdge]
    node_count: int                 # Computed
    edge_count: int                 # Computed
```

**Validation Rules:**
- `file_path`: Valid .canvas file path
- `nodes`: May be empty
- `edges`: References must point to existing node IDs
- JSON structure: Must conform to JSON Canvas v1.0 spec

**Relationships:**
- Contains zero or more `CanvasNode`
- Contains zero or more `CanvasEdge`
- Stored as JSON file in vault

---

### 8. CanvasNode

**Purpose**: Represents a node (element) on a canvas

**Attributes:**
```python
class CanvasNode(BaseModel):
    id: str = Field(pattern=r'^[a-f0-9]{16}$')  # 16-char hex
    type: Literal["text", "file", "link", "group"]
    x: int                          # Cartesian coordinate (can be negative)
    y: int
    width: int                      # Pixels
    height: int
    color: Optional[str] = None     # "1"-"6" or "#RRGGBB"

    # Type-specific fields
    text: Optional[str] = None          # For type="text"
    file: Optional[str] = None          # For type="file"
    subpath: Optional[str] = None       # For type="file" (e.g., #heading)
    url: Optional[str] = None           # For type="link"
    label: Optional[str] = None         # For type="group"
    background: Optional[str] = None    # For type="group"
    backgroundStyle: Optional[str] = None  # "cover", "ratio", "repeat"
```

**Validation Rules:**
- `id`: Exactly 16 lowercase hexadecimal characters
- `type`: One of four node types
- Dimensions: `width >= 50`, `height >= 50` (minimum canvas size)
- Coordinates: No bounds (infinite canvas)
- `color`: Preset "1"-"6" or hex "#RRGGBB" pattern
- Type-specific required fields:
  - `text`: Required if type="text"
  - `file`: Required if type="file"
  - `url`: Required if type="link"

**Relationships:**
- Belongs to one `CanvasFile`
- May be connected by `CanvasEdge` (incoming/outgoing)

---

### 9. CanvasEdge

**Purpose**: Represents a connection between two canvas nodes

**Attributes:**
```python
class CanvasEdge(BaseModel):
    id: str = Field(pattern=r'^[a-f0-9]{16}$')
    fromNode: str                   # Node ID (must exist)
    fromSide: Optional[Literal["top", "right", "bottom", "left"]] = None
    fromEnd: Optional[Literal["none", "arrow"]] = "none"
    toNode: str                     # Node ID (must exist)
    toSide: Optional[Literal["top", "right", "bottom", "left"]] = None
    toEnd: Optional[Literal["none", "arrow"]] = "arrow"
    color: Optional[str] = None
    label: Optional[str] = None
```

**Validation Rules:**
- `id`: Unique within canvas, 16-char hex
- `fromNode`, `toNode`: Must reference existing node IDs
- `fromNode != toNode`: No self-loops (warning)
- `fromSide`, `toSide`: Valid attachment points
- `fromEnd`, `toEnd`: Valid arrow styles

**Relationships:**
- Connects two `CanvasNode` instances
- Belongs to one `CanvasFile`

---

### 10. TemplateFile

**Purpose**: Represents a template file for note creation

**Attributes:**
```python
class TemplateFile(BaseModel):
    name: str                       # Template filename (without .md)
    file_path: str                  # Absolute path
    content: str                    # Template content with placeholders
    variables: List[str]            # Extracted {{variable}} names
    folder: str                     # Templates folder path
```

**Validation Rules:**
- `name`: Valid filename
- `file_path`: .md file in designated templates folder
- `variables`: Extracted via regex `{{(\w+)}}`
- `folder`: Configurable, default "Templates"

**Placeholder Syntax:**
- Built-in: `{{date}}`, `{{time}}`, `{{title}}`
- Custom: Any `{{variable_name}}`

**Relationships:**
- Stored in templates folder within vault
- May reference other notes via wikilinks

---

### 11. ObsidianCommand

**Purpose**: Represents an executable command in Obsidian (via API)

**Attributes:**
```python
class ObsidianCommand(BaseModel):
    id: str                         # Command ID (e.g., "editor:toggle-bold")
    name: str                       # Human-readable name
    plugin_source: Optional[str] = None  # Plugin providing command
    category: str = "unknown"       # Command category
```

**Validation Rules:**
- `id`: Non-empty, typically `plugin:action` format
- `name`: Non-empty display name
- Retrieved via Local REST API

**Relationships:**
- May belong to a plugin (core or community)
- Executable via API when Obsidian running

---

### 12. WorkspaceLayout

**Purpose**: Represents a saved Obsidian workspace configuration

**Attributes:**
```python
class WorkspaceLayout(BaseModel):
    name: str                       # Layout name
    pane_config: Dict[str, Any]     # Pane arrangement (Obsidian internal)
    sidebar_states: Dict[str, bool] # Left/right sidebar visibility
    open_files: List[str]           # File paths open in layout
```

**Validation Rules:**
- `name`: Non-empty, unique per vault
- `open_files`: Valid file paths in vault
- Retrieved/set via Workspaces plugin commands

**Relationships:**
- Associated with vault context
- May reference multiple notes

---

### 13. APIClientConfig

**Purpose**: Configuration for Obsidian Local REST API connection

**Attributes:**
```python
class APIClientConfig(BaseModel):
    base_url: HttpUrl = "http://localhost:27124"
    api_key: Optional[str] = None
    timeout: float = 30.0           # Seconds
    verify_ssl: bool = False        # For self-signed certs
    retry_attempts: int = 1
```

**Validation Rules:**
- `base_url`: Valid HTTP/HTTPS URL
- `timeout`: Positive float
- `verify_ssl`: False for local HTTPS
- `retry_attempts`: Non-negative integer

**Relationships:**
- Singleton configuration per MCP server instance
- Used by all API-based tools

---

## Aggregated Statistics Entities

### VaultStatistics (Enhanced)

**Extended from feature 001 with new metrics:**

```python
class VaultStatistics(BaseModel):
    # Existing fields
    total_notes: int
    total_words: int
    total_links: int
    unique_tags: int

    # New fields for hybrid features
    total_tasks: int
    incomplete_tasks: int
    completed_tasks: int
    overdue_tasks: int
    dataview_fields_count: int
    unique_dataview_keys: int
    kanban_boards: int
    total_kanban_cards: int
    canvas_files: int
    total_canvas_nodes: int
    orphan_notes: int
    hub_notes: List[str]            # Notes with >10 connections
```

---

## Entity Relationships Summary

**One-to-Many:**
- `Note` → `Task` (one note has many tasks)
- `Note` → `DataviewField` (one note has many inline fields)
- `KanbanBoard` → `KanbanColumn` (one board has many columns)
- `KanbanColumn` → `KanbanCard` (one column has many cards)
- `CanvasFile` → `CanvasNode` (one canvas has many nodes)
- `CanvasFile` → `CanvasEdge` (one canvas has many edges)

**Many-to-Many:**
- `Note` ↔ `LinkReference` (notes link to each other)
- `CanvasNode` ↔ `CanvasEdge` (nodes connected by edges)

**Hierarchical:**
- `KanbanCard` → `KanbanCard` (subtasks)
- `Task` → `Task` (conceptual subtasks via indentation)

---

## Persistence Strategy

**Filesystem-Native Entities:**
- `Task`: Parsed from markdown, written to note files
- `DataviewField`: Parsed from markdown, written inline
- `KanbanBoard`, `KanbanColumn`, `KanbanCard`: Parsed from markdown, written to board files
- `CanvasFile`, `CanvasNode`, `CanvasEdge`: Parsed from JSON, written to .canvas files
- `LinkReference`: Parsed from markdown, written to notes
- `TemplateFile`: Read from markdown files

**API-Dependent Entities:**
- `ObsidianCommand`: Retrieved via REST API
- `WorkspaceLayout`: Managed via Workspaces plugin API

**Ephemeral Entities:**
- `APIClientConfig`: In-memory configuration
- `VaultStatistics`: Computed on-demand, not persisted

---

## Validation Layers

### 1. Input Validation (Pydantic)
- Type checking
- Field constraints
- Required vs optional
- Pattern matching (regex)

### 2. Business Logic Validation
- Date ordering (start <= scheduled <= due)
- Node ID uniqueness in canvas
- Command ID existence (API check)
- File path existence in vault

### 3. Consistency Validation
- Canvas edge references valid nodes
- Kanban card indentation consistency
- Task recurrence "every" keyword
- Dataview field duplicate handling

---

## Error Handling Strategy

**Validation Errors:**
```python
class TaskValidationError(ValueError):
    """Raised when task metadata is malformed"""

class CanvasValidationError(ValueError):
    """Raised when canvas structure is invalid"""

class APIUnavailableError(ConnectionError):
    """Raised when Obsidian API is unreachable"""
```

**Recovery Strategies:**
- Malformed task metadata: Ignore emoji, treat as plain text
- Invalid canvas JSON: Raise error, don't corrupt file
- Missing API: Clear error message with troubleshooting steps
- Duplicate IDs: Generate new ID, log warning

---

## Summary

This data model supports the hybrid architecture by:
1. **Filesystem entities** (Task, DataviewField, Kanban*, Canvas*, LinkReference, Template) can be created/modified without Obsidian
2. **API entities** (ObsidianCommand, WorkspaceLayout) require Obsidian running
3. **Validation** ensures data integrity at multiple layers
4. **Relationships** preserve vault structure and inter-note connections
5. **Pydantic models** provide type safety and automatic serialization

All entities align with constitutional principles:
- ✅ Performance-first (no ORM, direct parsing)
- ✅ Zero dependencies (Pydantic already in project)
- ✅ Filesystem-native (primary entities)
- ✅ Backward compatible (extends feature 001)
