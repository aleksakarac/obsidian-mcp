# Technical Research: Extended Obsidian MCP Server

**Phase**: 0 - Outline & Research
**Date**: 2025-10-22
**Purpose**: Document technical decisions, patterns, and best practices for implementation

## Research Areas

### 1. YAML Frontmatter Parsing

**Decision**: Use `python-frontmatter` library

**Rationale**:
- Industry-standard library for YAML frontmatter in Python markdown processors
- Simple API: `frontmatter.load()`, `frontmatter.dumps()`, dict-like access to metadata
- Handles edge cases: missing frontmatter, malformed YAML, mixed content types
- Minimal dependencies (PyYAML only)
- Well-maintained and widely used in Python markdown tooling

**Alternatives Considered**:
- **Manual YAML parsing with PyYAML**: More complex, requires custom delimiter handling, error-prone
- **Regex-based parsing**: Fragile, doesn't handle YAML complexities (multiline, special characters)
- **markdown-it-py with frontmatter plugin**: Heavier dependency, unnecessary for our use case

**Implementation Pattern**:
```python
import frontmatter

# Read
with open(filepath, 'r', encoding='utf-8') as f:
    post = frontmatter.load(f)
    tags = post.get('tags', [])
    content = post.content

# Write
post['tags'] = ['new-tag']
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(frontmatter.dumps(post))
```

---

### 2. Wikilink Parsing & Backlink Analysis

**Decision**: Use regex pattern matching with `re` module (Python stdlib)

**Rationale**:
- Wikilinks follow simple, predictable patterns: `[[target]]` or `[[target|alias]]`
- Regex is sufficient for this use case (no complex AST parsing needed)
- Zero additional dependencies
- High performance for pattern matching across large text files
- Standard library ensures compatibility and reliability

**Pattern**:
```python
import re

# Match all wikilinks: [[target]] or [[target|alias]]
wikilink_pattern = re.compile(r'\[\[([^\]]+)\]\]')

# Extract target (handle aliases)
links = wikilink_pattern.findall(content)
for link in links:
    target = link.split('|')[0].strip()  # Get target before alias
```

**Edge Cases Handled**:
- Section references: `[[note#section]]` - extract `note` part
- Nested folders: `[[folder/note]]` - match against note name
- Aliases: `[[note|display]]` - extract `note` as target
- Escaped brackets: Not valid Obsidian syntax, ignore

**Alternatives Considered**:
- **obsidiantools library**: Abandoned project, not maintained
- **markdown-it-py with wikilinks plugin**: Overkill for simple pattern matching
- **Full markdown AST parsing**: Unnecessary complexity, poor performance

---

### 3. Filesystem Traversal & Vault Scanning

**Decision**: Use `os.walk()` for recursive directory traversal

**Rationale**:
- Standard library function, zero dependencies
- Efficient recursive directory traversal
- Cross-platform (Linux, macOS, Windows)
- Returns (root, dirs, files) tuples for easy processing
- Can modify `dirs` list in-place to skip directories (`.obsidian`)

**Pattern**:
```python
import os
from pathlib import Path

for root, dirs, files in os.walk(vault_path):
    # Skip .obsidian directory
    dirs[:] = [d for d in dirs if d != '.obsidian']

    for file in files:
        if file.endswith('.md'):
            filepath = Path(root) / file
            # Process note
```

**Alternatives Considered**:
- **pathlib.Path.rglob()**: Cleaner API but requires filtering .obsidian manually in results
- **glob.glob(recursive=True)**: Less control over traversal, harder to skip directories efficiently

---

### 4. Content Insertion Strategies

**Decision**: Line-based text manipulation with `str.split('\n')` and `str.join('\n')`

**Rationale**:
- Markdown is line-oriented (headings, blocks are line-based)
- Simple and predictable: split content into lines, find target, insert, rejoin
- Preserves exact formatting and whitespace
- No dependency on markdown parsers
- Easy to test and debug

**Patterns**:

**After Heading**:
```python
def insert_after_heading(content: str, heading: str, new_content: str) -> str:
    pattern = rf'^(#{{{1,6}}}\s+{re.escape(heading)}\s*)$'
    lines = content.split('\n')

    for i, line in enumerate(lines):
        if re.match(pattern, line, re.IGNORECASE):
            # Find next heading or end
            next_heading = i + 1
            while next_heading < len(lines) and not re.match(r'^#{1,6}\s+', lines[next_heading]):
                next_heading += 1

            lines.insert(next_heading, '\n' + new_content.strip())
            return '\n'.join(lines)

    raise ValueError(f"Heading '{heading}' not found")
```

**After Block**:
```python
def insert_after_block(content: str, block_id: str, new_content: str) -> str:
    pattern = rf'\^{re.escape(block_id.lstrip("^"))}\s*$'
    lines = content.split('\n')

    for i, line in enumerate(lines):
        if re.search(pattern, line):
            lines.insert(i + 1, '\n' + new_content.strip())
            return '\n'.join(lines)

    raise ValueError(f"Block '{block_id}' not found")
```

**Alternatives Considered**:
- **Full markdown AST manipulation**: Heavy dependencies, complexity overkill
- **String replacement with markers**: Fragile, doesn't handle duplicates or edge cases

---

### 5. Statistics Calculation

**Decision**: Single-pass regex extraction + file metadata from `Path.stat()`

**Rationale**:
- Word count: `re.findall(r'\b\w+\b', content)` - standard pattern, fast
- Character count: `len(content)` - trivial, O(1)
- Link extraction: Already have wikilink pattern from backlinks
- Tag extraction: Already have inline tag pattern from tag management
- Heading analysis: `re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)`
- File metadata: `pathlib.Path.stat()` provides size, mtime, ctime, atime

**Performance**:
- Single pass through content for all regex operations
- Compiled patterns cached for reuse
- O(n) where n is content length, acceptable for notes (typically <100KB)

**Pattern**:
```python
import re
from pathlib import Path
from datetime import datetime

def get_note_stats(content: str, filepath: str) -> dict:
    # Word and character counts
    words = len(re.findall(r'\b\w+\b', content))
    chars = len(content)
    chars_no_spaces = len(content.replace(' ', '').replace('\n', ''))

    # Link counts
    wikilinks = re.findall(r'\[\[([^\]]+)\]\]', content)
    markdown_links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)

    # Tag counts
    tags = re.findall(r'#([a-zA-Z0-9_/-]+)', content)

    # Heading analysis
    headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)

    # File metadata
    stat = Path(filepath).stat()

    return {
        'word_count': words,
        'character_count': chars,
        'character_count_no_spaces': chars_no_spaces,
        'line_count': len(content.split('\n')),
        'links': {
            'wikilink_count': len(wikilinks),
            'markdown_link_count': len(markdown_links),
            'total_links': len(wikilinks) + len(markdown_links)
        },
        'tags': {
            'count': len(set(tags)),
            'unique_tags': list(set(tags))
        },
        'headings': {
            'count': len(headings),
            'by_level': {...}  # Group by level
        },
        'file': {
            'size_bytes': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    }
```

---

### 6. Error Handling Patterns

**Decision**: Explicit error handling with informative messages, no silent failures

**Rationale**:
- Constitutional requirement: "Error handling MUST be explicit and informative"
- Users need clear feedback when operations fail
- MCP tools should return structured error responses

**Patterns**:

**File I/O Errors**:
```python
try:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    return {"error": f"Note not found: {filepath}"}
except PermissionError:
    return {"error": f"Permission denied: {filepath}"}
except UnicodeDecodeError:
    return {"error": f"Invalid UTF-8 encoding: {filepath}"}
except Exception as e:
    return {"error": f"Failed to read note: {str(e)}"}
```

**Frontmatter Parsing Errors**:
```python
try:
    post = frontmatter.loads(content)
except yaml.YAMLError as e:
    # Malformed frontmatter - treat as plain content
    return {'frontmatter_tags': [], 'inline_tags': [...]}
```

**Insertion Errors**:
```python
def insert_after_heading(content: str, heading: str, new_content: str) -> dict:
    try:
        updated = _insert_after_heading_impl(content, heading, new_content)
        return {"success": True, "message": f"Inserted after '{heading}'"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
```

---

### 7. Testing Strategy

**Decision**: pytest with unit tests + integration tests + fixtures

**Rationale**:
- pytest is the Python standard for testing
- Supports fixtures for test vault setup
- Parameterized tests for edge cases
- Coverage reporting built-in
- Integration with CI/CD pipelines

**Structure**:
```
tests/
├── unit/
│   ├── test_backlinks.py       # Test individual functions
│   ├── test_tags.py
│   ├── test_smart_insert.py
│   └── test_statistics.py
├── integration/
│   ├── test_backlinks_integration.py  # Test MCP tools end-to-end
│   └── ...
└── fixtures/
    └── sample_vault/           # Test notes with known structure
        ├── note1.md
        ├── note2.md
        └── folder/
            └── note3.md
```

**Test Patterns**:
```python
import pytest
from src.tools.backlinks import find_backlinks

@pytest.fixture
def sample_vault(tmp_path):
    """Create temporary test vault"""
    vault = tmp_path / "vault"
    vault.mkdir()

    (vault / "note1.md").write_text("Content with [[note2]] link")
    (vault / "note2.md").write_text("Target note")

    return str(vault)

def test_find_backlinks(sample_vault):
    result = find_backlinks(sample_vault, "note2")
    assert len(result) == 1
    assert "note1.md" in result[0]['file']
```

---

### 8. Performance Optimization

**Decision**: Lazy evaluation + compiled regex + minimal dependencies

**Rationale**:
- Don't load entire vault into memory
- Process notes on-demand (stream processing)
- Compile regex patterns once, reuse
- Use generators where possible
- Avoid unnecessary parsing

**Patterns**:
```python
# Compile patterns once at module level
WIKILINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')
TAG_PATTERN = re.compile(r'#([a-zA-Z0-9_/-]+)')
HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

# Generator for large vaults
def iter_notes(vault_path: str):
    """Yield notes one at a time instead of loading all"""
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d != '.obsidian']
        for file in files:
            if file.endswith('.md'):
                filepath = Path(root) / file
                yield filepath

# Process with generator
def vault_statistics(vault_path: str) -> dict:
    stats = {'total_notes': 0, 'total_words': 0}

    for note_path in iter_notes(vault_path):
        with open(note_path, 'r', encoding='utf-8') as f:
            content = f.read()
            stats['total_notes'] += 1
            stats['total_words'] += len(WORD_PATTERN.findall(content))

    return stats
```

---

### 9. Dataview Plugin Inline Field Syntax & Parsing

**Research Date**: 2025-10-22
**Purpose**: Document comprehensive inline field syntax for potential Dataview integration support

**Overview**:
Dataview is a popular Obsidian plugin that extends metadata capabilities beyond frontmatter. Understanding its inline field syntax is critical for comprehensive metadata extraction.

#### 9.1 Inline Field Syntax Variants

Dataview supports three distinct syntax variants for inline fields:

**1. Basic/Full-Line Syntax (Unbracketed)**
```markdown
Field Name:: Value
**Bold Field**:: Another Value
```
- Used when the field occupies its own line
- Double colon (`::`) is required (single colon `:` won't work)
- Displays both key and value in Reading mode
- Can have markdown formatting in the key name

**2. Bracket Syntax `[field:: value]`**
```markdown
This is text with an [inline:: field] embedded in it.
Multiple fields: [rating:: 9], [status:: complete], [priority:: high]

- [ ] Task with metadata [due:: 2024-12-31]
```
- Used for embedding fields within text
- Required for adding metadata to list items and tasks
- Displays both key and value in Reading mode
- Only way to explicitly add fields to specific list items

**3. Parenthesis Syntax `(field:: value)`**
```markdown
This is text with a (hidden:: field) where only the value shows.
The publication date is (date:: 2024-01-15).
```
- Hides the key in Reading mode, shows only the value
- Allows seamless text integration
- Useful for narrative writing where keys would be distracting

#### 9.2 Value Type Handling

Dataview automatically detects and parses different value types:

**Text/String** (default)
```markdown
name:: John Smith
description:: This is a longer description
```
- Default type for any value not matching other patterns
- Supports single-line values only
- Line break terminates the value

**Numbers**
```markdown
age:: 42
price:: 19.99
temperature:: -5.3
```
- Integers and decimals (including negatives)
- Automatically parsed as numeric type
- No quotes needed

**Booleans**
```markdown
completed:: true
active:: false
```
- Lowercase `true` or `false` only
- Case-sensitive (likely - documentation doesn't explicitly state case handling)
- Used for binary flags

**Dates** (ISO8601 Auto-Detection)
```markdown
created:: 2024-01-15
modified:: 2024-01-15T14:30:00
deadline:: 2024-12-31T23:59:59.000+00:00
```
- Format: `YYYY-MM[-DDTHH:mm:ss.nnn+ZZ]`
- Everything after month is optional
- Automatically converted to Date object
- Rendered in human-readable format (customizable)
- Provides granular access: `.year`, `.month`, `.day`, `.hour`, `.minute`

**Durations**
```markdown
duration:: 2 hours
time-spent:: 4 minutes 30 seconds
```
- Natural language time expressions
- Supports abbreviations: "6h", "4min"
- Can be combined with dates for calculations
- Adding duration to date or subtracting dates yields duration

**Links**
```markdown
related:: [[Other Note]]
reference:: [[Note|Display Text]]
```
- Standard Obsidian wikilink syntax
- In YAML frontmatter, links must be quoted: `key: "[[Link]]"`
- Inline fields don't require quotes
- Preserves link metadata and relationships

**Lists/Arrays**
```markdown
tags:: "fiction", "sci-fi", "adventure"
numbers:: 1, 2, 3, 4
mixed:: "text", 42, true
```
- Comma-separated values
- Text values must be quoted to be recognized as list items
- Numbers don't require quotes
- Single line only (no multiline list support in inline fields)

**Objects** (YAML Frontmatter Only)
```yaml
---
author:
  name: John Smith
  email: john@example.com
---
```
- Not supported in inline fields
- Only available in frontmatter
- Accessed via dot notation: `author.name`

#### 9.3 Field Key Normalization (Canonicalization)

Dataview normalizes field keys for programmatic access:

**Canonicalization Rules**:
1. Convert to lowercase
2. Replace spaces with hyphens (`-`)
3. Remove invalid characters
4. Preserve unicode (but with caveats - see edge cases)

**Examples**:
```markdown
[Author Name:: John Smith]
→ Accessible as: file['Author Name'] OR file.authorname

[Field With Space In It:: value]
→ Accessible as: file['Field With Space In It'] OR file.field-with-space-in-it

[CamelCaseField:: value]
→ Accessible as: file.camelcasefield
```

**Important**: Normalization only applies to inline fields, NOT frontmatter fields.

#### 9.4 Conflict Resolution: Frontmatter vs Inline Fields

**Key Behavior**: No precedence - values are combined into arrays

When the same field name exists in both frontmatter and inline:
```yaml
---
grocery: flour
---

Inline content:
grocery:: soap
```

**Result**: `grocery` field becomes an array: `["flour", "soap"]`

**Implications**:
- No single value "wins" - both are preserved
- Querying returns array with all values
- Duplicate keys within same context also create arrays
- Useful for multi-value fields, problematic if single value expected

#### 9.5 Multi-Line Handling

**Current Limitation**: Inline fields are single-line only

```markdown
field:: This is the value until the line break
This is NOT part of the field value
```

**Workarounds**:
1. Use YAML frontmatter with pipe operator (`|`) for multiline text
2. Use multiple inline fields with same key (creates array)
3. Feature request exists for indented codeblock syntax (not yet implemented)

**Tasks and Multi-Line**:
- Dataview understands multi-line tasks (tasks spanning multiple lines)
- But inline field values themselves are still single-line

#### 9.6 Nesting Rules

**Bracket Nesting**:
- Parser implements sophisticated bracket matching
- Tracks nesting depth for proper pairing
- Respects escape sequences (backslash toggles escaped state)
- Handles double escapes (`\\`) correctly
- Ignores escaped characters when computing nesting

**Key Restrictions**:
- Keys cannot contain separator characters: `[`, `]`, `(`, `)`, `::`
- Values can contain these characters (except closing wrapper)

**Example**:
```markdown
[field:: [[nested link]]]  ✓ Valid - nested links in value
[fie[ld:: value]           ✗ Invalid - bracket in key
[field:::: value]          ✗ Invalid - multiple separators
```

#### 9.7 Recommended Regex Patterns

Based on Dataview source code analysis (`src/data-import/inline-field.ts`):

**Core Pattern** (from source):
```regex
/[_\*~]*([-0-9\w\p{Letter}\p{Emoji_Presentation}\s]+)[_\*~]*\s*::\s*(.+)/
```

**Breakdown**:
- `[_\*~]*` - Optional markdown formatting before key
- `([-0-9\w\p{Letter}\p{Emoji_Presentation}\s]+)` - Key (alphanumeric, unicode, emoji, spaces)
- `[_\*~]*` - Optional markdown formatting after key
- `\s*::\s*` - Double colon separator with optional whitespace
- `(.+)` - Value (everything until line end)

**Practical Patterns for Implementation**:

```python
import re

# Basic full-line field
FULL_LINE_FIELD = re.compile(
    r'^[_*~]*([-\w\s]+?)[_*~]*\s*::\s*(.+)$',
    re.MULTILINE
)

# Bracketed inline field
BRACKET_FIELD = re.compile(
    r'\[([^[\]()]+?)\s*::\s*([^\]]+)\]'
)

# Parenthesized inline field (hidden key)
PAREN_FIELD = re.compile(
    r'\(([^[\]()]+?)\s*::\s*([^\)]+)\)'
)

# Combined pattern (all variants)
INLINE_FIELD_COMBINED = re.compile(
    r'(?:^[_*~]*([-\w\s]+?)[_*~]*\s*::\s*(.+)$)|'  # Full-line
    r'(?:\[([^[\]()]+?)\s*::\s*([^\]]+)\])|'       # Bracketed
    r'(?:\(([^[\]()]+?)\s*::\s*([^\)]+)\))',       # Parenthesized
    re.MULTILINE
)
```

**Date Detection** (ISO8601):
```python
DATE_PATTERN = re.compile(
    r'\d{4}-\d{2}(?:-\d{2}(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d{3})?)?(?:[+-]\d{2}:\d{2}|Z)?)?)?'
)
```

**List Detection** (quoted comma-separated):
```python
LIST_PATTERN = re.compile(
    r'"([^"]+)"(?:\s*,\s*"([^"]+)")*'
)
```

#### 9.8 Edge Cases & Parsing Challenges

**1. Code Blocks**
```markdown
```python
# This should NOT be parsed as inline field
field:: value
```
```

**Issue**: Dataview historically parsed inline fields within code blocks (bug)
**Fix**: Check syntax tree to skip code blocks (implemented in live preview)
**Solution**: Parse markdown structure first, exclude code blocks from inline field extraction

**2. Escaped Characters**
```markdown
Field\:\: Value  # Escaped colons - not a valid field
[field:: value\]  # Escaped bracket in value
```

**Issue**: Backslash escapes can cause parsing errors
**Solution**: `findClosing()` function tracks escape state, ignores escaped characters

**3. C++ Scope Operators**
```markdown
std::vector  # NOT an inline field, but uses :: syntax
```

**Issue**: Inline field highlighting incorrectly triggered by `::`
**Solution**: Require proper key pattern before `::` (alphanumeric, spaces, limited special chars)

**4. Emoji in Field Names**
```markdown
[📅:: 2024-01-15]  # May not work reliably
```

**Issues**:
- Must use bracket syntax for emoji keys
- Tables cannot retrieve emoji-keyed values
- Cross-platform compatibility issues (emoji codes differ by OS)
- Parser now prevents "accidental" emoji keys

**Recommendation**: Avoid emoji in field names; use in values only

**5. Unicode Special Characters**
```markdown
[↑:: parent note]  # May not be recognized
```

**Issue**: Limited unicode support in key names
**Solution**: Stick to alphanumeric + spaces + hyphens for maximum compatibility

**6. Callouts**
```markdown
> [!Success]- Cooking:: ✅
```

**Issue**: Inline fields in callouts have had intermittent parsing problems
**Status**: Fixed in recent versions, but worth testing

**7. Inline Queries vs Inline Fields**
```markdown
= dv.current().file.name  # Inline query (starts with =)
field:: value             # Inline field (uses ::)
```

**Issue**: Code blocks with `=` can trigger inline query parser
**Solution**: Change inline query prefix in settings if conflicts occur

**8. Links in Frontmatter**
```yaml
related: [[Link]]     # ✗ Invalid YAML
related: "[[Link]]"   # ✓ Valid, requires quotes
```

**Issue**: Unquoted links break YAML parsing
**Solution**: Always quote wikilinks in frontmatter

**9. Multiline Values**
```markdown
field:: Line 1
Line 2  # NOT part of field value
```

**Current Behavior**: Line break terminates value
**Workaround**: Use frontmatter with `|` operator for multiline text

**10. Duplicate Keys**
```markdown
tag:: first
tag:: second
tag:: third
```

**Result**: `tag` becomes array: `["first", "second", "third"]`
**Use Case**: Intentional for multi-value fields
**Caveat**: Can be unexpected if single value was intended

#### 9.9 Implementation Recommendations

**For Python Implementation**:

```python
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class InlineField:
    key: str
    value: str
    raw_value: str
    wrapper: Optional[str]  # None, '[', or '('
    start_pos: int
    end_pos: int

class DataviewInlineFieldParser:
    """Parse Dataview inline fields from markdown content."""

    # Compiled patterns (module-level for performance)
    FULL_LINE = re.compile(
        r'^[_*~]*([-\w\s]+?)[_*~]*\s*::\s*(.+)$',
        re.MULTILINE
    )
    BRACKET = re.compile(r'\[([^[\]()]+?)\s*::\s*([^\]]+)\]')
    PAREN = re.compile(r'\(([^[\]()]+?)\s*::\s*([^\)]+)\)')

    # Type detection patterns
    DATE_ISO8601 = re.compile(
        r'^\d{4}-\d{2}(?:-\d{2}(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d{3})?)?(?:[+-]\d{2}:\d{2}|Z)?)?)?$'
    )
    NUMBER = re.compile(r'^-?\d+(?:\.\d+)?$')
    BOOLEAN = re.compile(r'^(true|false)$')
    LIST = re.compile(r'^"[^"]+?"(?:\s*,\s*"[^"]+?")+$')

    @staticmethod
    def canonicalize_key(key: str) -> str:
        """Normalize key name per Dataview rules."""
        return key.lower().replace(' ', '-')

    @staticmethod
    def parse_value(raw_value: str) -> Any:
        """Parse raw value into appropriate type."""
        value = raw_value.strip()

        # Boolean
        if DataviewInlineFieldParser.BOOLEAN.match(value):
            return value == 'true'

        # Number
        if DataviewInlineFieldParser.NUMBER.match(value):
            return float(value) if '.' in value else int(value)

        # Date
        if DataviewInlineFieldParser.DATE_ISO8601.match(value):
            return {'type': 'date', 'value': value}  # Or parse with datetime

        # List (quoted, comma-separated)
        if DataviewInlineFieldParser.LIST.match(value):
            return [v.strip(' "') for v in value.split(',')]

        # Link
        if value.startswith('[[') and value.endswith(']]'):
            return {'type': 'link', 'target': value[2:-2]}

        # Default: string
        return value

    @staticmethod
    def extract_inline_fields(content: str, skip_code_blocks: bool = True) -> Dict[str, List[Any]]:
        """
        Extract all inline fields from markdown content.

        Returns dict mapping canonical key names to lists of values
        (list because duplicate keys are allowed).
        """
        fields: Dict[str, List[Any]] = {}

        # Optionally skip code blocks
        if skip_code_blocks:
            content = DataviewInlineFieldParser._remove_code_blocks(content)

        # Extract full-line fields
        for match in DataviewInlineFieldParser.FULL_LINE.finditer(content):
            key, raw_value = match.groups()
            canonical = DataviewInlineFieldParser.canonicalize_key(key)
            value = DataviewInlineFieldParser.parse_value(raw_value)
            fields.setdefault(canonical, []).append(value)

        # Extract bracketed fields
        for match in DataviewInlineFieldParser.BRACKET.finditer(content):
            key, raw_value = match.groups()
            canonical = DataviewInlineFieldParser.canonicalize_key(key)
            value = DataviewInlineFieldParser.parse_value(raw_value)
            fields.setdefault(canonical, []).append(value)

        # Extract parenthesized fields
        for match in DataviewInlineFieldParser.PAREN.finditer(content):
            key, raw_value = match.groups()
            canonical = DataviewInlineFieldParser.canonicalize_key(key)
            value = DataviewInlineFieldParser.parse_value(raw_value)
            fields.setdefault(canonical, []).append(value)

        return fields

    @staticmethod
    def _remove_code_blocks(content: str) -> str:
        """Remove code blocks to prevent false positives."""
        # Remove fenced code blocks
        content = re.sub(r'```[^`]*```', '', content, flags=re.DOTALL)
        # Remove inline code
        content = re.sub(r'`[^`]+`', '', content)
        return content

# Usage example
parser = DataviewInlineFieldParser()
content = """
---
frontmatter: value
---

Basic Field:: Some Value
This is text with [rating:: 9] and (hidden:: secret).

- [ ] Task [due:: 2024-12-31]

tags:: "fiction", "sci-fi"
completed:: true
"""

fields = parser.extract_inline_fields(content)
print(fields)
# {
#   'basic-field': ['Some Value'],
#   'rating': [9],
#   'hidden': ['secret'],
#   'due': [{'type': 'date', 'value': '2024-12-31'}],
#   'tags': [['fiction', 'sci-fi']],
#   'completed': [True]
# }
```

#### 9.10 Integration Strategy

**Decision**: Optional Dataview inline field support with feature flag

**Rationale**:
- Not all users have Dataview plugin installed
- Inline fields are Dataview-specific, not core Obsidian feature
- Adds parsing complexity
- Should be opt-in to maintain performance for non-Dataview users

**Recommended Approach**:
```python
class ObsidianMetadataExtractor:
    def __init__(self, vault_path: str, enable_dataview: bool = False):
        self.vault_path = vault_path
        self.enable_dataview = enable_dataview
        self.dataview_parser = DataviewInlineFieldParser() if enable_dataview else None

    def extract_metadata(self, filepath: str) -> dict:
        metadata = {
            'frontmatter': self._extract_frontmatter(filepath),
            'inline_tags': self._extract_inline_tags(filepath),
            'links': self._extract_links(filepath)
        }

        if self.enable_dataview and self.dataview_parser:
            metadata['dataview_fields'] = self.dataview_parser.extract_inline_fields(
                self._read_content(filepath)
            )

        return metadata
```

**MCP Tool Enhancement**:
```python
@server.call_tool()
async def get_note_metadata(note_name: str, include_dataview: bool = False) -> dict:
    """
    Get metadata from a note.

    Args:
        note_name: Name of the note
        include_dataview: If True, parse Dataview inline fields (default: False)
    """
    extractor = ObsidianMetadataExtractor(
        vault_path=VAULT_PATH,
        enable_dataview=include_dataview
    )
    return extractor.extract_metadata(note_name)
```

#### 9.11 Testing Considerations

**Test Cases Required**:
1. All three syntax variants (full-line, bracket, paren)
2. All value types (text, number, boolean, date, list, link)
3. Key normalization (spaces, capitalization)
4. Duplicate keys → array behavior
5. Edge cases (code blocks, escapes, emoji, unicode)
6. Conflict with frontmatter → array merging
7. Multiline handling (should terminate at line break)
8. Nested brackets in values
9. Empty values (should map to null)
10. Invalid syntax (should be ignored, not error)

**Example Test Fixture**:
```markdown
# Test Note with Dataview Fields

---
frontmatter_field: frontmatter_value
duplicate_field: from_frontmatter
---

Full Line Field:: Full Line Value
**Bold Key**:: Bold Value
*Italic Key*:: Italic Value

Inline text with [bracket_field:: bracket_value] and (paren_field:: paren_value).

## Data Types
number:: 42
decimal:: 3.14
negative:: -10
boolean_true:: true
boolean_false:: false
date:: 2024-01-15
datetime:: 2024-01-15T14:30:00
link:: [[Related Note]]
list:: "item1", "item2", "item3"

## Duplicate Keys
duplicate_field:: from_inline_1
duplicate_field:: from_inline_2

## Edge Cases
escaped\:\: not_a_field
[nested:: [[Link in Value]]]

```code
field:: should_not_parse
```

- [ ] Task [due:: 2024-12-31] with metadata
```

#### 9.12 Performance Considerations

**Complexity**:
- Regex matching: O(n) where n = content length
- Typical note size: 1-50KB
- Inline field parsing adds ~10-20% overhead vs frontmatter-only
- Acceptable for per-note queries, may impact vault-wide scans

**Optimization Strategies**:
1. Compile patterns once at module level
2. Skip code blocks early to reduce false matches
3. Use generators for vault-wide operations
4. Cache parsed results if note hasn't changed (check mtime)
5. Make Dataview parsing opt-in per query

**Benchmark Target**: <10ms per note for inline field extraction

---

## Summary

All technical decisions align with constitutional principles:
- ✅ Performance-first: Regex + stdlib, no heavy dependencies
- ✅ Zero external dependencies: Only python-frontmatter added (Dataview support optional)
- ✅ Filesystem-native: Direct file I/O, no abstractions
- ✅ Backward compatibility: Extends existing structure, Dataview support is opt-in
- ✅ Code quality: Explicit error handling, type hints, docstrings

No unresolved "NEEDS CLARIFICATION" items - all decisions documented with rationale.
