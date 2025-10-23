"""Pydantic models for Obsidian data structures."""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date
from pydantic import BaseModel, Field, validator, HttpUrl


class NoteMetadata(BaseModel):
    """Metadata for an Obsidian note."""
    
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    modified: Optional[datetime] = Field(None, description="Last modification timestamp")
    tags: List[str] = Field(default_factory=list, description="List of tags")
    aliases: List[str] = Field(default_factory=list, description="Alternative names for the note")
    frontmatter: Dict[str, Any] = Field(default_factory=dict, description="Raw frontmatter data")


class Note(BaseModel):
    """Represents an Obsidian note."""
    
    path: str = Field(..., description="Path to the note relative to vault root")
    content: str = Field(..., description="Markdown content of the note")
    metadata: NoteMetadata = Field(default_factory=NoteMetadata, description="Note metadata")
    
    @validator("path")
    def validate_path(cls, v):
        """Ensure path doesn't contain invalid characters."""
        if not v or ".." in v:
            raise ValueError("Invalid path")
        return v.strip("/")


class VaultItem(BaseModel):
    """Represents an item in the vault (file or folder)."""
    
    path: str = Field(..., description="Path relative to vault root")
    name: str = Field(..., description="Name of the file or folder")
    is_folder: bool = Field(..., description="Whether this is a folder")
    children: Optional[List["VaultItem"]] = Field(None, description="Child items if this is a folder")


class SearchResult(BaseModel):
    """Result from a search operation."""
    
    path: str = Field(..., description="Path to the matching note")
    score: float = Field(..., description="Relevance score")
    matches: List[str] = Field(default_factory=list, description="Matching text excerpts")
    context: Optional[str] = Field(None, description="Context around the match")


class Tag(BaseModel):
    """Represents a tag in the vault."""
    
    name: str = Field(..., description="Tag name without the # prefix")
    count: int = Field(default=0, description="Number of notes with this tag")
    notes: List[str] = Field(default_factory=list, description="Paths to notes with this tag")
    
    @validator("name")
    def clean_tag_name(cls, v):
        """Remove # prefix if present."""
        return v.lstrip("#")


class Backlink(BaseModel):
    """Represents a backlink to a note."""
    
    source_path: str = Field(..., description="Path of the note containing the link")
    link_text: str = Field(..., description="Text of the link")
    context: Optional[str] = Field(None, description="Text around the link for context")


# ============================================================================
# TASKS PLUGIN MODELS
# ============================================================================

class Task(BaseModel):
    """Represents a checkbox task with Tasks plugin metadata.

    The Tasks plugin uses emoji metadata at the end of task lines to encode
    information like due dates, priority, recurrence patterns, etc.
    """

    content: str = Field(..., description="Task description text (without metadata)")
    status: Literal["incomplete", "completed"] = Field(..., description="Checkbox status")
    priority: Optional[Literal["highest", "high", "normal", "low", "lowest"]] = Field(
        "normal", description="Priority level (⏫🔼🔽⏬ or none=normal)"
    )
    due_date: Optional[date] = Field(None, description="Due date (📅 emoji)")
    scheduled_date: Optional[date] = Field(None, description="Scheduled date (⏳ emoji)")
    start_date: Optional[date] = Field(None, description="Start date (🛫 emoji)")
    done_date: Optional[date] = Field(None, description="Done date (✅ emoji)")
    created_date: Optional[date] = Field(None, description="Created date (➕ emoji)")
    recurrence: Optional[str] = Field(None, description="Recurrence pattern (🔁 emoji)")
    line_number: Optional[int] = Field(None, description="Line number in source file (set after insertion)")
    source_file: str = Field(..., description="Path to file containing task")
    tags: List[str] = Field(default_factory=list, description="Extracted #tags from task")

    @validator("content")
    def validate_content(cls, v):
        """Ensure content is non-empty."""
        if not v or not v.strip():
            raise ValueError("Task content cannot be empty")
        return v.strip()

    @validator("recurrence")
    def validate_recurrence(cls, v):
        """Ensure recurrence starts with 'every' if present."""
        if v and not v.strip().lower().startswith("every"):
            raise ValueError("Recurrence pattern must start with 'every'")
        return v

    @validator("line_number")
    def validate_line_number(cls, v):
        """Ensure line number is positive when set."""
        if v is not None and v < 1:
            raise ValueError("Line number must be positive")
        return v


# ============================================================================
# DATAVIEW PLUGIN MODELS
# ============================================================================

class DataviewField(BaseModel):
    """Represents a Dataview inline field embedded in note content.

    Dataview supports three syntax variants:
    - Full-line: field:: value
    - Bracket: [field:: value]
    - Paren: (field:: value) - hidden key
    """

    key: str = Field(..., description="Original key as written")
    value: Any = Field(..., description="Parsed value (str, int, float, bool, list, date)")
    canonical_key: str = Field(..., description="Normalized key (lowercase, hyphens)")
    line_number: int = Field(..., description="Line number in source file")
    syntax_type: Literal["full-line", "bracket", "paren"] = Field(
        ..., description="Syntax variant used"
    )
    source_file: str = Field(..., description="Path to file containing field")
    value_type: Literal["string", "number", "boolean", "date", "link", "list"] = Field(
        ..., description="Detected value type"
    )

    @validator("key")
    def validate_key(cls, v):
        """Ensure key is valid identifier."""
        if not v or not v.strip():
            raise ValueError("Field key cannot be empty")
        return v.strip()

    @validator("canonical_key", pre=False, always=True)
    def set_canonical_key(cls, v, values):
        """Auto-generate canonical key from key if not provided."""
        if v:
            return v
        key = values.get("key", "")
        return key.lower().replace(" ", "-").strip("_*~")


# ============================================================================
# KANBAN PLUGIN MODELS
# ============================================================================

class KanbanCard(BaseModel):
    """Represents a card (checkbox item) within a Kanban column.

    Cards can be nested to create subtasks. The Kanban plugin uses standard
    markdown list indentation to represent hierarchy.
    """

    text: str = Field(..., description="Card description")
    status: Literal["incomplete", "completed"] = Field(..., description="Checkbox status")
    due_date: Optional[date] = Field(None, description="Due date (@{YYYY-MM-DD})")
    tags: List[str] = Field(default_factory=list, description="Extracted #tags")
    wikilinks: List[str] = Field(default_factory=list, description="Extracted [[links]]")
    subtasks: List["KanbanCard"] = Field(default_factory=list, description="Nested cards")
    indent_level: int = Field(0, description="Indentation level (0=root)")
    line_number: int = Field(..., description="Line number in source file")

    @validator("text")
    def validate_text(cls, v):
        """Ensure text is non-empty after metadata removal."""
        if not v or not v.strip():
            raise ValueError("Card text cannot be empty")
        return v.strip()

    @validator("indent_level")
    def validate_indent(cls, v):
        """Ensure indent level is non-negative."""
        if v < 0:
            raise ValueError("Indent level cannot be negative")
        return v


class KanbanColumn(BaseModel):
    """Represents a column in a Kanban board (markdown heading).

    Columns are represented as level-2 headings (##) in markdown files.
    """

    name: str = Field(..., description="Column name (heading text)")
    cards: List[KanbanCard] = Field(default_factory=list, description="Cards in column")
    card_count: int = Field(0, description="Number of cards (computed)")
    heading_level: int = Field(2, description="Markdown heading level (always 2)")
    line_number: int = Field(..., description="Line number of heading")

    @validator("name")
    def validate_name(cls, v):
        """Ensure name is non-empty."""
        if not v or not v.strip():
            raise ValueError("Column name cannot be empty")
        return v.strip()

    @validator("card_count", pre=False, always=True)
    def compute_card_count(cls, v, values):
        """Auto-compute card count from cards list."""
        cards = values.get("cards", [])
        return len(cards)


class KanbanBoard(BaseModel):
    """Represents a markdown-based Kanban board file.

    The Kanban plugin stores boards as markdown files with columns as headings
    and cards as checkbox list items.
    """

    file_path: str = Field(..., description="Path to board file")
    columns: List[KanbanColumn] = Field(default_factory=list, description="Board columns")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Board settings from frontmatter")
    total_cards: int = Field(0, description="Total cards across all columns (computed)")

    @validator("total_cards", pre=False, always=True)
    def compute_total_cards(cls, v, values):
        """Auto-compute total cards from all columns."""
        columns = values.get("columns", [])
        return sum(col.card_count for col in columns)


# ============================================================================
# LINK TRACKING MODELS (Enhanced)
# ============================================================================

class LinkReference(BaseModel):
    """Enhanced link tracking for all link types (extends feature 001).

    Supports wikilinks, embeds, section links, and block references.
    """

    link_type: Literal["wikilink", "embed", "section", "block"] = Field(
        ..., description="Type of link"
    )
    source_file: str = Field(..., description="File containing the link")
    target_file: str = Field(..., description="File being referenced")
    link_text: str = Field(..., description="Original link syntax")
    alias: Optional[str] = Field(None, description="Display alias if present")
    section_name: Optional[str] = Field(None, description="Section for [[note#section]]")
    block_id: Optional[str] = Field(None, description="Block ID for [[note#^block]]")
    line_number: int = Field(..., description="Line number in source file")
    context: str = Field("", description="Surrounding text (20 chars each side)")

    @validator("section_name")
    def validate_section(cls, v, values):
        """Ensure section_name is present for section links."""
        if values.get("link_type") == "section" and not v:
            raise ValueError("Section name required for section links")
        return v

    @validator("block_id")
    def validate_block(cls, v, values):
        """Ensure block_id is present for block links."""
        if values.get("link_type") == "block" and not v:
            raise ValueError("Block ID required for block links")
        return v


# ============================================================================
# CANVAS MODELS
# ============================================================================

class CanvasNode(BaseModel):
    """Represents a node (element) on a canvas.

    Canvas nodes can be text, file references, web links, or groups.
    IDs are 16-character hexadecimal strings.
    """

    id: str = Field(..., pattern=r'^[a-f0-9]{16}$', description="16-char hex ID")
    type: Literal["text", "file", "link", "group"] = Field(..., description="Node type")
    x: int = Field(..., description="X coordinate (can be negative)")
    y: int = Field(..., description="Y coordinate (can be negative)")
    width: int = Field(..., ge=50, description="Width in pixels (minimum 50)")
    height: int = Field(..., ge=50, description="Height in pixels (minimum 50)")
    color: Optional[str] = Field(None, description="Color (1-6 or #RRGGBB)")

    # Type-specific fields
    text: Optional[str] = Field(None, description="Text content (type=text)")
    file: Optional[str] = Field(None, description="File path (type=file)")
    subpath: Optional[str] = Field(None, description="File subpath like #heading (type=file)")
    url: Optional[str] = Field(None, description="URL (type=link)")
    label: Optional[str] = Field(None, description="Group label (type=group)")
    background: Optional[str] = Field(None, description="Background image (type=group)")
    backgroundStyle: Optional[Literal["cover", "ratio", "repeat"]] = Field(
        None, description="Background style (type=group)"
    )

    @validator("text")
    def validate_text_required(cls, v, values):
        """Ensure text is present for text nodes."""
        if values.get("type") == "text" and not v:
            raise ValueError("Text field required for text nodes")
        return v

    @validator("file")
    def validate_file_required(cls, v, values):
        """Ensure file is present for file nodes."""
        if values.get("type") == "file" and not v:
            raise ValueError("File field required for file nodes")
        return v

    @validator("url")
    def validate_url_required(cls, v, values):
        """Ensure URL is present for link nodes."""
        if values.get("type") == "link" and not v:
            raise ValueError("URL field required for link nodes")
        return v


class CanvasEdge(BaseModel):
    """Represents a connection between two canvas nodes.

    Edges can have labels, colors, and different arrow styles.
    """

    id: str = Field(..., pattern=r'^[a-f0-9]{16}$', description="16-char hex ID")
    fromNode: str = Field(..., description="Source node ID")
    fromSide: Optional[Literal["top", "right", "bottom", "left"]] = Field(
        None, description="Attachment side on source"
    )
    fromEnd: Optional[Literal["none", "arrow"]] = Field("none", description="Source end style")
    toNode: str = Field(..., description="Target node ID")
    toSide: Optional[Literal["top", "right", "bottom", "left"]] = Field(
        None, description="Attachment side on target"
    )
    toEnd: Optional[Literal["none", "arrow"]] = Field("arrow", description="Target end style")
    color: Optional[str] = Field(None, description="Edge color")
    label: Optional[str] = Field(None, description="Edge label")

    @validator("toNode")
    def validate_no_self_loop(cls, v, values):
        """Warn about self-loops (same from and to node)."""
        from_node = values.get("fromNode")
        if from_node == v:
            # Note: This is a warning, not a hard error
            # Some use cases might intentionally create self-loops
            pass
        return v


class CanvasFile(BaseModel):
    """Represents a .canvas JSON file for visual knowledge mapping.

    Canvas files follow the JSON Canvas v1.0 specification.
    """

    file_path: str = Field(..., description="Path to .canvas file")
    nodes: List[CanvasNode] = Field(default_factory=list, description="Canvas nodes")
    edges: List[CanvasEdge] = Field(default_factory=list, description="Canvas edges")
    node_count: int = Field(0, description="Number of nodes (computed)")
    edge_count: int = Field(0, description="Number of edges (computed)")

    @validator("node_count", pre=False, always=True)
    def compute_node_count(cls, v, values):
        """Auto-compute node count."""
        nodes = values.get("nodes", [])
        return len(nodes)

    @validator("edge_count", pre=False, always=True)
    def compute_edge_count(cls, v, values):
        """Auto-compute edge count."""
        edges = values.get("edges", [])
        return len(edges)


# ============================================================================
# TEMPLATE MODELS
# ============================================================================

class TemplateFile(BaseModel):
    """Represents a template file for note creation.

    Templates can contain placeholder variables like {{date}}, {{time}}, {{title}}.
    """

    name: str = Field(..., description="Template filename (without .md)")
    file_path: str = Field(..., description="Path to template file")
    content: str = Field(..., description="Template content with placeholders")
    variables: List[str] = Field(default_factory=list, description="Extracted {{variable}} names")
    folder: str = Field(..., description="Templates folder path")

    @validator("name")
    def validate_name(cls, v):
        """Ensure name is valid filename."""
        if not v or not v.strip():
            raise ValueError("Template name cannot be empty")
        # Remove .md extension if present
        return v.replace(".md", "").strip()


# ============================================================================
# API AND WORKSPACE MODELS
# ============================================================================

class ObsidianCommand(BaseModel):
    """Represents an executable command in Obsidian (via API).

    Commands are exposed by core Obsidian and plugins, accessible via
    the Local REST API.
    """

    id: str = Field(..., description="Command ID (e.g., editor:toggle-bold)")
    name: str = Field(..., description="Human-readable name")
    plugin_source: Optional[str] = Field(None, description="Plugin providing command")
    category: str = Field("unknown", description="Command category")

    @validator("id")
    def validate_id(cls, v):
        """Ensure ID is non-empty."""
        if not v or not v.strip():
            raise ValueError("Command ID cannot be empty")
        return v.strip()


class WorkspaceLayout(BaseModel):
    """Represents a saved Obsidian workspace configuration.

    Workspaces store pane arrangements, sidebar states, and open files.
    """

    name: str = Field(..., description="Layout name")
    pane_config: Dict[str, Any] = Field(
        default_factory=dict, description="Pane arrangement (Obsidian internal)"
    )
    sidebar_states: Dict[str, bool] = Field(
        default_factory=dict, description="Left/right sidebar visibility"
    )
    open_files: List[str] = Field(default_factory=list, description="File paths open in layout")

    @validator("name")
    def validate_name(cls, v):
        """Ensure name is non-empty."""
        if not v or not v.strip():
            raise ValueError("Workspace name cannot be empty")
        return v.strip()


class APIClientConfig(BaseModel):
    """Configuration for Obsidian Local REST API connection.

    Used to configure the HTTP client for API-based tools.
    """

    base_url: str = Field("http://localhost:27124", description="API base URL")
    api_key: Optional[str] = Field(None, description="API authentication key")
    timeout: float = Field(30.0, gt=0, description="Request timeout in seconds")
    verify_ssl: bool = Field(False, description="Verify SSL certificates")
    retry_attempts: int = Field(1, ge=0, description="Number of retry attempts")

    @validator("timeout")
    def validate_timeout(cls, v):
        """Ensure timeout is positive."""
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v


# Enable forward references for recursive models
VaultItem.model_rebuild()
KanbanCard.model_rebuild()