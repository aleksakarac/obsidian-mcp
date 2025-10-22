# Data Model: Extended Obsidian MCP Server

**Phase**: 1 - Design & Contracts
**Date**: 2025-10-22
**Source**: Extracted from [spec.md](spec.md) Key Entities section

## Entity Definitions

### Note

A markdown file (`.md`) in the Obsidian vault with optional YAML frontmatter and markdown content.

**Attributes**:
- `file_path` (str): Relative path from vault root (e.g., `"folder/note.md"`)
- `absolute_path` (str): Full filesystem path
- `content` (str): Full markdown content including frontmatter
- `frontmatter` (dict): Parsed YAML frontmatter metadata
- `body` (str): Markdown content excluding frontmatter
- `modified_timestamp` (float): Unix timestamp of last modification

**Relationships**:
- Has many `Wikilink` (outgoing links to other notes)
- Has many `Tag` (categorization markers)
- Has many `Heading` (section headers)
- Has many `Block` (identifiable content blocks)
- Belongs to one `Vault`

**Validation Rules**:
- File must have `.md` extension
- Content must be valid UTF-8
- Frontmatter (if present) must be valid YAML between `---` delimiters
- File path must be relative to vault root

**State Transitions**:
None (stateless - notes are files on disk)

**Python Representation**:
```python
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

@dataclass
class Note:
    file_path: str
    absolute_path: str
    content: str
    frontmatter: Dict[str, any]
    body: str
    modified_timestamp: float

    @property
    def modified_date(self) -> datetime:
        return datetime.fromtimestamp(self.modified_timestamp)

    @property
    def has_frontmatter(self) -> bool:
        return len(self.frontmatter) > 0
```

---

### Wikilink

A reference to another note using Obsidian's `[[note]]` or `[[note|alias]]` syntax.

**Attributes**:
- `raw_text` (str): Full wikilink text (e.g., `"[[note|alias]]"`)
- `target` (str): Target note name (e.g., `"note"`)
- `alias` (Optional[str]): Display alias (e.g., `"alias"`)
- `section` (Optional[str]): Section reference (e.g., `"heading"` from `[[note#heading]]`)
- `line_number` (int): Line number where link appears
- `is_broken` (bool): Whether target note exists

**Relationships**:
- Originates from one `Note` (source)
- Points to one `Note` (target) or is broken

**Validation Rules**:
- Must match pattern `\[\[([^\]]+)\]\]`
- Target extracted as text before first `|` or `#`
- Section extracted as text after `#`
- Alias extracted as text after `|`

**Python Representation**:
```python
@dataclass
class Wikilink:
    raw_text: str
    target: str
    alias: Optional[str] = None
    section: Optional[str] = None
    line_number: int = 0
    is_broken: bool = False

    @classmethod
    def parse(cls, raw_text: str) -> 'Wikilink':
        """Parse wikilink text into components"""
        inner = raw_text.strip('[]')

        # Split by | for alias
        parts = inner.split('|', 1)
        target_section = parts[0]
        alias = parts[1] if len(parts) > 1 else None

        # Split by # for section
        target_parts = target_section.split('#', 1)
        target = target_parts[0].strip()
        section = target_parts[1].strip() if len(target_parts) > 1 else None

        return cls(
            raw_text=raw_text,
            target=target,
            alias=alias,
            section=section
        )
```

---

### Tag

A categorization marker appearing in frontmatter (YAML array/string) or inline content (`#tag`).

**Attributes**:
- `name` (str): Tag name without `#` prefix (e.g., `"project"`)
- `location` (Literal['frontmatter', 'inline', 'both']): Where tag appears
- `parent` (Optional[str]): Parent tag for nested tags (e.g., `"project"` from `"project/active"`)
- `full_path` (str): Full nested path (e.g., `"project/active"`)
- `depth` (int): Nesting depth (0 for root tags, 1 for one level, etc.)

**Relationships**:
- Associated with one or more `Note`
- May have parent `Tag` (nested tags)
- May have child `Tag` (nested tags)

**Validation Rules**:
- Name must match pattern `[a-zA-Z0-9_/-]+`
- Forward slashes indicate nesting hierarchy
- Leading/trailing slashes not allowed

**Python Representation**:
```python
@dataclass
class Tag:
    name: str
    location: Literal['frontmatter', 'inline', 'both']
    full_path: str

    @property
    def parent(self) -> Optional[str]:
        """Get parent tag name for nested tags"""
        parts = self.full_path.split('/')
        return '/'.join(parts[:-1]) if len(parts) > 1 else None

    @property
    def depth(self) -> int:
        """Get nesting depth"""
        return self.full_path.count('/')

    @property
    def is_nested(self) -> bool:
        return '/' in self.full_path
```

---

### Block

A markdown content block with a unique identifier (`^block-id`).

**Attributes**:
- `block_id` (str): Unique identifier without `^` prefix
- `content` (str): Block content (text on the line)
- `line_number` (int): Line number in the note

**Relationships**:
- Exists within one `Note`
- Can be referenced by other `Note` via wikilinks (`[[note^block-id]]`)

**Validation Rules**:
- Block ID must be at end of line: `^block-id`
- Block ID format: `[a-zA-Z0-9_-]+`
- Must be unique within the note

**Python Representation**:
```python
@dataclass
class Block:
    block_id: str
    content: str
    line_number: int

    @property
    def reference_syntax(self) -> str:
        """Get the syntax to reference this block"""
        return f"^{self.block_id}"

    @classmethod
    def parse_line(cls, line: str, line_number: int) -> Optional['Block']:
        """Parse block ID from line if present"""
        match = re.search(r'\^([a-zA-Z0-9_-]+)\s*$', line)
        if match:
            return cls(
                block_id=match.group(1),
                content=line[:match.start()].strip(),
                line_number=line_number
            )
        return None
```

---

### Heading

A markdown section header (`#` to `######`).

**Attributes**:
- `level` (int): Heading level (1-6)
- `text` (str): Heading text content
- `line_number` (int): Line number in the note
- `raw_line` (str): Full line including `#` markers

**Relationships**:
- Exists within one `Note`
- May have parent `Heading` (higher level heading above it)
- May have child `Heading` (lower level headings below it)

**Validation Rules**:
- Level must be 1-6
- Must match pattern `^#{1,6}\s+.+$`

**Python Representation**:
```python
@dataclass
class Heading:
    level: int
    text: str
    line_number: int
    raw_line: str

    @classmethod
    def parse_line(cls, line: str, line_number: int) -> Optional['Heading']:
        """Parse heading from line if present"""
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            return cls(
                level=level,
                text=text,
                line_number=line_number,
                raw_line=line
            )
        return None

    def __lt__(self, other: 'Heading') -> bool:
        """Compare headings by level (for hierarchy)"""
        return self.level < other.level
```

---

### Vault

The root directory containing all Obsidian notes.

**Attributes**:
- `path` (str): Absolute path to vault root directory
- `note_count` (int): Total number of `.md` files
- `total_words` (int): Aggregate word count across all notes
- `total_links` (int): Aggregate wikilink + markdown link count
- `unique_tags` (Set[str]): Set of all unique tag names
- `index_path` (str): Path to SQLite index (`.obsidian/mcp-search-index.db`)

**Relationships**:
- Contains many `Note`
- Has one `.obsidian` metadata directory (excluded from processing)

**Validation Rules**:
- Path must be a valid directory
- Must have read permissions
- `.obsidian` directory optional (may not exist)

**Python Representation**:
```python
@dataclass
class Vault:
    path: str

    @property
    def obsidian_dir(self) -> Path:
        """Get .obsidian directory path"""
        return Path(self.path) / '.obsidian'

    @property
    def index_path(self) -> Path:
        """Get SQLite index path"""
        return self.obsidian_dir / 'mcp-search-index.db'

    def iter_notes(self) -> Iterator[Path]:
        """Yield all note paths in vault"""
        for root, dirs, files in os.walk(self.path):
            dirs[:] = [d for d in dirs if d != '.obsidian']
            for file in files:
                if file.endswith('.md'):
                    yield Path(root) / file

    def get_statistics(self) -> Dict[str, any]:
        """Calculate vault-wide statistics"""
        # Implementation uses iter_notes() to process
        pass
```

---

## Entity Relationships Diagram

```
┌─────────────────┐
│     Vault       │
│                 │
│ - path          │
│ - note_count    │
│ - total_words   │
└────────┬────────┘
         │
         │ contains many
         │
         ▼
┌─────────────────┐
│      Note       │
│                 │
│ - file_path     │
│ - content       │
│ - frontmatter   │
└────────┬────────┘
         │
         ├─────── has many ────┐
         │                     │
         ▼                     ▼
┌───────────────┐     ┌─────────────────┐
│   Wikilink    │     │      Tag        │
│               │     │                 │
│ - target      │     │ - name          │
│ - alias       │     │ - location      │
│ - is_broken   │     │ - full_path     │
└───────────────┘     └─────────────────┘
         │
         ├─────── has many ────┐
         │                     │
         ▼                     ▼
┌───────────────┐     ┌─────────────────┐
│    Heading    │     │      Block      │
│               │     │                 │
│ - level       │     │ - block_id      │
│ - text        │     │ - content       │
│ - line_number │     │ - line_number   │
└───────────────┘     └─────────────────┘
```

---

## Implementation Notes

### Storage
All entities except `Vault` are derived from filesystem data. No database persistence needed for entities - they are extracted on-demand from markdown files.

### Caching Strategy
SQLite index (from base `obsidian-mcp`) may cache note metadata for search performance. Extended features query files directly for accuracy.

### Immutability
Entities are read-only data structures. Modifications happen at the file level, then entities are re-extracted.

### Type Safety
All entities use `@dataclass` with type hints for IDE support and runtime validation.
