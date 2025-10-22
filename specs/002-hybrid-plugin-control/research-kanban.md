# Kanban Plugin Research: Markdown Format and Manipulation

**Date**: 2025-10-22
**Purpose**: Document the Obsidian Kanban plugin's markdown file structure, manipulation requirements, and implementation patterns for filesystem-native operations

## Overview

The Obsidian Kanban plugin (by mgmeyers, 1.9M downloads, 3.8k GitHub stars) creates markdown-backed Kanban boards that can be manipulated either through the visual UI or directly via filesystem operations. This research documents the complete markdown format specification required for implementing filesystem-native Kanban board manipulation in the CustomObsidianMcp project.

**Key Principle**: The Kanban plugin stores all board data in standard markdown files with special formatting conventions. All board operations can be performed via direct file I/O without requiring Obsidian to be running.

---

## Markdown File Structure Specification

### 1. Complete Format Template

```markdown
---
kanban-plugin: basic
---

## Column Name 1
- [ ] Card text @{2024-01-15} #tag1 #tag2
- [ ] Another card with [[link]] to note
  - [ ] Nested subtask (indented)
  - [ ] Another subtask
- [ ] Card with metadata

## Column Name 2
- [ ] Card in second column @{2024-01-20} #important
- [ ] Task without metadata

## Done
**Complete**
- [x] Completed task @{2024-01-10} #finished
- [x] Another completed item
```

### 2. Frontmatter (YAML)

**Required Format**:
```yaml
---
kanban-plugin: basic
---
```

**Purpose**: Identifies the file as a Kanban board to the plugin

**Validation Rules**:
- MUST contain `kanban-plugin: basic` key-value pair
- MUST use triple-dash delimiters (`---`)
- SHOULD be first element in file
- MAY contain additional YAML fields for board settings

**Edge Cases**:
- Missing frontmatter: Plugin may not recognize file as Kanban board
- Malformed YAML: Board may fail to load in plugin UI
- Additional frontmatter fields: Safe to preserve, may be plugin settings

---

### 3. Column Representation

**Format**: Level 2 Headings (`##`)

**Pattern**:
```markdown
## Column Name
```

**Rules**:
- Each column is represented by exactly one H2 heading (`##`)
- Column name is the heading text (trimmed)
- Columns are defined by order of appearance in file
- Empty columns are valid (heading with no cards beneath)

**Regex Pattern**:
```python
COLUMN_HEADING_PATTERN = re.compile(r'^##\s+(.+)$', re.MULTILINE)
```

**Extraction Algorithm**:
```python
def parse_kanban_structure(content: str) -> dict:
    """Parse Kanban board structure from markdown content"""
    lines = content.split('\n')
    columns = []
    current_column = None

    # Skip frontmatter
    in_frontmatter = False
    start_index = 0

    for i, line in enumerate(lines):
        if line.strip() == '---':
            if not in_frontmatter:
                in_frontmatter = True
            else:
                start_index = i + 1
                break

    # Parse columns and cards
    for i in range(start_index, len(lines)):
        line = lines[i]

        # Column heading
        if line.startswith('## '):
            if current_column:
                columns.append(current_column)

            current_column = {
                'name': line[3:].strip(),
                'cards': [],
                'line_start': i
            }
        # Card (checkbox item)
        elif line.strip().startswith('- [ ]') or line.strip().startswith('- [x]'):
            if current_column:
                card = parse_card(line)
                current_column['cards'].append(card)

    # Add last column
    if current_column:
        columns.append(current_column)

    return {
        'columns': columns,
        'total_cards': sum(len(col['cards']) for col in columns)
    }
```

**Edge Cases**:
- Empty column (no cards): Valid, preserve structure
- Column with non-checkbox content: May contain markdown formatting, preserve
- Column names with special characters: Support all valid markdown text
- Duplicate column names: Valid, treat as separate columns

---

### 4. Card Representation

**Format**: Markdown checkbox list items (`- [ ]` or `- [x]`)

**Incomplete Card**:
```markdown
- [ ] Card text goes here
```

**Completed Card**:
```markdown
- [x] Card text goes here
```

**Regex Patterns**:
```python
# Match incomplete card
INCOMPLETE_CARD_PATTERN = re.compile(r'^(\s*)- \[ \] (.+)$')

# Match completed card
COMPLETED_CARD_PATTERN = re.compile(r'^(\s*)- \[x\] (.+)$')

# Match any card (incomplete or completed)
CARD_PATTERN = re.compile(r'^(\s*)- \[([ x])\] (.+)$')
```

**Card Parsing Algorithm**:
```python
def parse_card(line: str) -> dict:
    """Parse a single Kanban card from a markdown line"""
    match = CARD_PATTERN.match(line)
    if not match:
        return None

    indentation = match.group(1)
    completion_status = match.group(2)  # ' ' or 'x'
    card_text = match.group(3)

    # Extract metadata from card text
    metadata = extract_card_metadata(card_text)

    return {
        'text': card_text,
        'completed': completion_status == 'x',
        'indentation': len(indentation),
        'nesting_level': len(indentation) // 2,  # Assuming 2-space indent
        'metadata': metadata,
        'raw_line': line
    }
```

---

### 5. Card Metadata

**Date Format**: `@{YYYY-MM-DD}` or `@[[YYYY-MM-DD]]`

**Examples**:
```markdown
- [ ] Task with due date @{2024-01-15}
- [ ] Task with daily note link @[[2024-01-15]]
```

**Date Regex Pattern**:
```python
# Match @{date} format
DATE_CURLY_PATTERN = re.compile(r'@\{(\d{4}-\d{2}-\d{2})\}')

# Match @[[date]] format (linked to daily note)
DATE_BRACKET_PATTERN = re.compile(r'@\[\[(\d{4}-\d{2}-\d{2})\]\]')

# Combined pattern
DATE_PATTERN = re.compile(r'@(?:\{|\[\[)(\d{4}-\d{2}-\d{2})(?:\}|\]\])')
```

**Tag Format**: Standard Obsidian inline tags (`#tagname`)

**Examples**:
```markdown
- [ ] Task with tags #important #project
- [ ] Multi-word tag support #multi-word-tag
```

**Tag Regex Pattern**:
```python
TAG_PATTERN = re.compile(r'#([a-zA-Z0-9_/-]+)')
```

**Wikilink Format**: Standard Obsidian wikilinks (`[[note]]` or `[[note|alias]]`)

**Examples**:
```markdown
- [ ] Task linked to [[Project Note]]
- [ ] Task with alias [[Project Note|Project]]
```

**Complete Metadata Extraction**:
```python
def extract_card_metadata(card_text: str) -> dict:
    """Extract all metadata from card text"""
    # Extract dates
    dates = DATE_PATTERN.findall(card_text)

    # Extract tags
    tags = TAG_PATTERN.findall(card_text)

    # Extract wikilinks
    wikilinks = re.findall(r'\[\[([^\]]+)\]\]', card_text)

    # Clean text (remove metadata for display)
    clean_text = card_text
    clean_text = DATE_PATTERN.sub('', clean_text)
    clean_text = TAG_PATTERN.sub('', clean_text)
    clean_text = ' '.join(clean_text.split())  # Normalize whitespace

    return {
        'dates': dates,
        'tags': tags,
        'wikilinks': [link.split('|')[0].strip() for link in wikilinks],
        'aliases': [link.split('|')[1].strip() if '|' in link else None for link in wikilinks],
        'clean_text': clean_text.strip()
    }
```

**Metadata Preservation Rules**:
- When moving cards: Preserve all metadata exactly
- When updating completion: Preserve dates, tags, links
- When adding cards: Allow optional metadata in initial text
- Order matters: Date typically before tags, but flexible

---

### 6. Nested Cards (Subtasks)

**Format**: Indented checkbox items (2-space or 4-space indent)

**Example**:
```markdown
## To Do
- [ ] Parent card @{2024-01-15} #project
  - [ ] Subtask 1
  - [ ] Subtask 2
    - [ ] Nested subtask (level 2)
- [ ] Another parent card
  - [ ] Its subtask
```

**Nesting Rules**:
- Each indentation level = 2 spaces (standard) or 4 spaces (alternative)
- Subtasks MUST be checkbox items (`- [ ]` or `- [x]`)
- Subtasks inherit parent's column context
- Unlimited nesting depth supported (practical limit: 3-4 levels)

**Parsing Nested Structure**:
```python
def parse_cards_with_nesting(lines: list, start_index: int, end_index: int) -> list:
    """Parse cards including nested subtasks"""
    cards = []
    card_stack = []  # Track parent cards by indentation level

    for i in range(start_index, end_index):
        line = lines[i]

        # Parse card
        card = parse_card(line)
        if not card:
            continue

        indent_level = card['nesting_level']

        # Root-level card
        if indent_level == 0:
            card['subtasks'] = []
            cards.append(card)
            card_stack = [card]

        # Nested card (subtask)
        else:
            # Find parent at previous indent level
            if indent_level <= len(card_stack):
                parent = card_stack[indent_level - 1]
                card['subtasks'] = []
                parent['subtasks'].append(card)

                # Update stack
                card_stack = card_stack[:indent_level] + [card]

    return cards
```

**Subtask Display in Kanban UI**:
- Plugin UI shows only parent cards on board by default
- Subtasks visible when parent card is expanded/opened
- Filesystem representation always includes full hierarchy

**Edge Cases**:
- Orphan subtasks (indented without parent): Treat as root-level cards
- Mixed indentation (2-space and 4-space): Normalize to project standard
- Deep nesting (5+ levels): Support but may be impractical in UI

---

## Board Manipulation Patterns

### 1. Adding Cards to Columns

**Algorithm**:
```python
def add_card_to_column(filepath: str, column_name: str, card_text: str,
                       metadata: dict = None) -> dict:
    """Add a new card to a specific column"""
    try:
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')

        # Find column
        column_index = None
        next_column_index = len(lines)

        for i, line in enumerate(lines):
            if line.startswith('## '):
                current_column = line[3:].strip()
                if current_column == column_name:
                    column_index = i
                elif column_index is not None:
                    # Found next column after target
                    next_column_index = i
                    break

        if column_index is None:
            return {"success": False, "error": f"Column '{column_name}' not found"}

        # Build card line
        card_line = build_card_line(card_text, metadata)

        # Find insertion point (after last card in column or after column heading)
        insert_index = column_index + 1

        # Find last card in this column
        for i in range(column_index + 1, next_column_index):
            if lines[i].strip().startswith('- [ ]') or lines[i].strip().startswith('- [x]'):
                insert_index = i + 1

        # Insert card
        lines.insert(insert_index, card_line)

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return {
            "success": True,
            "message": f"Added card to column '{column_name}'",
            "card": card_line
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def build_card_line(card_text: str, metadata: dict = None) -> str:
    """Build a complete card line with metadata"""
    parts = [f"- [ ] {card_text}"]

    if metadata:
        # Add date
        if 'date' in metadata:
            parts.append(f"@{{{metadata['date']}}}")

        # Add tags
        if 'tags' in metadata:
            for tag in metadata['tags']:
                parts.append(f"#{tag}")

    return ' '.join(parts)
```

**Edge Cases**:
- Empty column: Insert immediately after heading
- Column with only completed cards: Insert after last card
- Column with markdown content (non-cards): Insert after heading, before content
- Metadata with special characters: Escape or validate

---

### 2. Moving Cards Between Columns

**Algorithm**:
```python
def move_card_between_columns(filepath: str, card_text: str,
                              from_column: str, to_column: str,
                              mark_complete: bool = False) -> dict:
    """Move a card from one column to another"""
    try:
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')

        # Find and remove card from source column
        card_line = None
        card_index = None

        in_from_column = False

        for i, line in enumerate(lines):
            # Track current column
            if line.startswith('## '):
                current_column = line[3:].strip()
                in_from_column = (current_column == from_column)

            # Look for card in from_column
            if in_from_column and card_text in line and (
                line.strip().startswith('- [ ]') or line.strip().startswith('- [x]')
            ):
                card_line = line
                card_index = i
                break

        if card_index is None:
            return {"success": False, "error": f"Card not found in column '{from_column}'"}

        # Remove card from original location
        removed_line = lines.pop(card_index)

        # Update completion status if moving to "Done" or mark_complete is True
        if mark_complete:
            removed_line = removed_line.replace('- [ ]', '- [x]', 1)

        # Find insertion point in destination column
        to_column_index = None
        next_column_index = len(lines)

        for i, line in enumerate(lines):
            if line.startswith('## '):
                current_column = line[3:].strip()
                if current_column == to_column:
                    to_column_index = i
                elif to_column_index is not None:
                    next_column_index = i
                    break

        if to_column_index is None:
            # Restore removed card if destination not found
            lines.insert(card_index, removed_line)
            return {"success": False, "error": f"Column '{to_column}' not found"}

        # Find last card in destination column
        insert_index = to_column_index + 1
        for i in range(to_column_index + 1, next_column_index):
            if lines[i].strip().startswith('- [ ]') or lines[i].strip().startswith('- [x]'):
                insert_index = i + 1

        # Insert card at new location
        lines.insert(insert_index, removed_line)

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return {
            "success": True,
            "message": f"Moved card from '{from_column}' to '{to_column}'",
            "card": removed_line
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Edge Cases**:
- Card with subtasks: Move entire tree (parent + all subtasks)
- Card text appears multiple times: Match first occurrence or require unique identifier
- Source/destination column not found: Return error, don't modify file
- Move to same column: No-op, return success

---

### 3. Updating Card Status

**Algorithm**:
```python
def toggle_card_completion(filepath: str, card_text: str, column_name: str = None) -> dict:
    """Toggle card completion status (incomplete <-> complete)"""
    try:
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')

        # Find card
        card_index = None
        in_target_column = (column_name is None)  # Search all columns if not specified

        for i, line in enumerate(lines):
            # Track current column
            if line.startswith('## '):
                current_column = line[3:].strip()
                in_target_column = (column_name is None or current_column == column_name)

            # Look for card
            if in_target_column and card_text in line and (
                line.strip().startswith('- [ ]') or line.strip().startswith('- [x]')
            ):
                card_index = i
                break

        if card_index is None:
            return {"success": False, "error": f"Card not found"}

        # Toggle completion
        original_line = lines[card_index]

        if '- [ ]' in original_line:
            # Mark as complete
            updated_line = original_line.replace('- [ ]', '- [x]', 1)
            status = 'completed'
        elif '- [x]' in original_line:
            # Mark as incomplete
            updated_line = original_line.replace('- [x]', '- [ ]', 1)
            status = 'incomplete'
        else:
            return {"success": False, "error": "Line is not a valid card"}

        lines[card_index] = updated_line

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return {
            "success": True,
            "message": f"Card marked as {status}",
            "original": original_line,
            "updated": updated_line
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Completion Date Handling**:
- Kanban plugin can add completion dates automatically (plugin setting)
- Filesystem implementation: Optional feature, can append `@{YYYY-MM-DD}` on completion
- Format: `- [x] Task completed @{2024-01-15}` (append current date)

---

### 4. Preserving Card Metadata

**Rules**:
- **Never remove metadata** unless explicitly requested
- **Preserve order** of metadata elements (dates before tags recommended)
- **Maintain formatting** including whitespace around metadata
- **Handle duplicates** gracefully (e.g., multiple dates or tags)

**Metadata Preservation Algorithm**:
```python
def update_card_preserve_metadata(original_line: str, new_text: str = None,
                                  new_metadata: dict = None) -> str:
    """Update card while preserving existing metadata"""
    # Parse original card
    match = CARD_PATTERN.match(original_line)
    if not match:
        return original_line

    indentation = match.group(1)
    completion = match.group(2)
    card_text = match.group(3)

    # Extract existing metadata
    existing_metadata = extract_card_metadata(card_text)

    # Build updated card
    if new_text:
        # Replace text but keep metadata
        clean_text = new_text
    else:
        clean_text = existing_metadata['clean_text']

    # Merge metadata (new values override existing)
    merged_metadata = existing_metadata.copy()
    if new_metadata:
        for key, value in new_metadata.items():
            if value:  # Only override if new value provided
                merged_metadata[key] = value

    # Rebuild card line
    parts = [clean_text]

    # Add dates
    for date in merged_metadata.get('dates', []):
        parts.append(f"@{{{date}}}")

    # Add tags
    for tag in merged_metadata.get('tags', []):
        parts.append(f"#{tag}")

    # Add wikilinks (if not already in clean_text)
    for i, link in enumerate(merged_metadata.get('wikilinks', [])):
        alias = merged_metadata.get('aliases', [])[i] if i < len(merged_metadata.get('aliases', [])) else None
        if alias:
            link_text = f"[[{link}|{alias}]]"
        else:
            link_text = f"[[{link}]]"

        if link_text not in clean_text:
            parts.append(link_text)

    card_content = ' '.join(parts)

    return f"{indentation}- [{completion}] {card_content}"
```

---

## Edge Cases and Handling Strategies

### 1. Empty Columns

**Scenario**: Column heading with no cards beneath it

**Example**:
```markdown
## To Do

## In Progress
- [ ] Some task

## Done
```

**Handling**:
- **Parsing**: Recognize as valid column with 0 cards
- **Adding cards**: Insert immediately after heading
- **Removal**: Empty columns are preserved (don't auto-delete)
- **UI behavior**: Plugin may hide empty columns (filesystem keeps them)

**Known Issue**: Empty last column may disappear in plugin UI (GitHub issue #346)

**Filesystem Strategy**: Always preserve empty columns in markdown file

---

### 2. Cards Without Checkboxes

**Scenario**: List items without checkbox syntax

**Example**:
```markdown
## Notes
- Regular bullet point (not a card)
- [ ] This is a card
- Another bullet point
```

**Handling**:
- **Parsing**: Ignore non-checkbox items, don't treat as cards
- **Preservation**: Keep non-checkbox content intact during manipulation
- **Validation**: Warn user if attempting to move non-card items

**Edge Case**: Plugin UI may convert non-checkbox items to cards automatically

---

### 3. Nested Subtasks

**Scenario**: Deep nesting, orphan subtasks, mixed indentation

**Example**:
```markdown
## Tasks
- [ ] Parent
  - [ ] Subtask level 1
    - [ ] Subtask level 2
      - [ ] Subtask level 3
- [ ] Another parent
  - [ ] Orphan (missing middle level)
```

**Handling Strategies**:

**Deep Nesting (3+ levels)**:
- Support unlimited depth in parsing
- Preserve exact indentation
- Consider practical limit warning (4+ levels may be unwieldy)

**Orphan Subtasks**:
- If indented item has no parent: Treat as root-level card
- Preserve indentation in file (user intent)
- Option to "fix" by de-indenting or creating implicit parent

**Mixed Indentation** (2-space vs 4-space):
- Detect dominant pattern (count occurrences)
- Normalize on write operations to project standard (2-space default)
- Preserve original if no pattern detected

**Moving Parent with Subtasks**:
- Always move entire subtree together
- Preserve relative indentation
- Maintain subtask order

```python
def extract_card_subtree(lines: list, card_index: int) -> list:
    """Extract a card and all its subtasks as a subtree"""
    subtree = [lines[card_index]]

    # Get parent indentation
    parent_match = CARD_PATTERN.match(lines[card_index])
    if not parent_match:
        return subtree

    parent_indent = len(parent_match.group(1))

    # Collect all subtasks (lines with greater indentation)
    for i in range(card_index + 1, len(lines)):
        line = lines[i]

        # Stop at next heading
        if line.startswith('##'):
            break

        # Check if card
        match = CARD_PATTERN.match(line)
        if match:
            current_indent = len(match.group(1))
            if current_indent > parent_indent:
                subtree.append(line)
            else:
                # Same or less indentation = end of subtree
                break
        elif line.strip() == '':
            # Preserve blank lines within subtree
            subtree.append(line)
        else:
            # Non-card line = end of subtree
            break

    return subtree
```

---

### 4. Non-Standard Column Names

**Scenario**: Columns with special characters, emojis, very long names

**Examples**:
```markdown
## 📋 To Do (Q1 2024)
## Done ✓
## In Progress... 🚧
## ⚠️ Blocked!
```

**Handling**:
- **Support**: All valid markdown heading text is valid column name
- **Matching**: Exact string match (case-sensitive by default)
- **Normalization**: Trim leading/trailing whitespace only
- **Emojis**: Full Unicode support, no special handling needed
- **Length**: No artificial limits (markdown supports long headings)

**Case Sensitivity**:
- Default: Case-sensitive matching
- Option: Provide case-insensitive search helper

```python
def find_column_case_insensitive(columns: list, name: str) -> str:
    """Find column by name (case-insensitive)"""
    name_lower = name.lower()
    for col in columns:
        if col['name'].lower() == name_lower:
            return col['name']  # Return actual name
    return None
```

---

### 5. Malformed Metadata

**Scenario**: Invalid date formats, unrecognized emoji, broken wikilinks

**Examples**:
```markdown
- [ ] Invalid date @{2024-13-45}
- [ ] Malformed link [[note
- [ ] Unclosed date @{2024-01-15
- [ ] Mixed formats @2024-01-15 (missing braces)
```

**Handling Strategies**:

**Invalid Dates**:
- Regex won't match invalid formats (e.g., month > 12)
- Preserve as plain text, don't extract as metadata
- Option: Validate with `datetime.strptime()` and warn

```python
from datetime import datetime

def validate_date(date_str: str) -> bool:
    """Validate date format"""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def extract_dates_validated(card_text: str) -> list:
    """Extract only valid dates"""
    potential_dates = DATE_PATTERN.findall(card_text)
    return [d for d in potential_dates if validate_date(d)]
```

**Malformed Wikilinks**:
- Unclosed brackets: `[[note` - ignore (regex won't match)
- Nested brackets: `[[note [[inner]]]]` - extract outer match
- Empty links: `[[]]` - ignore or warn

**Missing Metadata Delimiters**:
- `@2024-01-15` (no braces): Won't match date pattern, treated as text
- `#{tag}` (extra braces): Won't match tag pattern
- Preserve as-is, don't attempt to "fix"

**Best Practice**: Strict parsing prevents false positives

---

### 6. Special Kanban Plugin Syntax

**Archive Metadata**:
- Plugin can add archived date when archiving cards
- Format: `- [x] Task **Completed: 2024-01-15**`
- Parsing: Treat as part of card text, extract separately if needed

**Board Settings in Frontmatter**:
```yaml
---
kanban-plugin: basic
hide-tags: true
hide-dates: false
archive-with-date: true
---
```

**Handling**:
- Parse frontmatter with `python-frontmatter`
- Preserve all settings when modifying board
- Don't modify settings unless explicitly requested

**Linked Page Metadata**:
- Cards can display metadata from first linked note
- Format: `[[Note]]` displays note's frontmatter fields
- Filesystem: No special handling, standard wikilink

**Card Metadata Display** (Plugin-specific, not in markdown):
- Tags and dates rendered below card title in UI
- Markdown file: Inline in card text
- Filesystem operations: Ignore UI rendering, work with markdown source

---

## Parsing Regex Patterns Summary

```python
import re

# Frontmatter
FRONTMATTER_DELIMITER = re.compile(r'^---\s*$', re.MULTILINE)

# Column headings
COLUMN_HEADING = re.compile(r'^##\s+(.+)$', re.MULTILINE)

# Cards
CARD_INCOMPLETE = re.compile(r'^(\s*)- \[ \] (.+)$')
CARD_COMPLETE = re.compile(r'^(\s*)- \[x\] (.+)$')
CARD_ANY = re.compile(r'^(\s*)- \[([ x])\] (.+)$')

# Metadata
DATE_CURLY = re.compile(r'@\{(\d{4}-\d{2}-\d{2})\}')
DATE_BRACKET = re.compile(r'@\[\[(\d{4}-\d{2}-\d{2})\]\]')
DATE_ANY = re.compile(r'@(?:\{|\[\[)(\d{4}-\d{2}-\d{2})(?:\}|\]\])')

TAG = re.compile(r'#([a-zA-Z0-9_/-]+)')

WIKILINK = re.compile(r'\[\[([^\]]+)\]\]')
WIKILINK_WITH_ALIAS = re.compile(r'\[\[([^|\]]+)(?:\|([^\]]+))?\]\]')

# Completion date (plugin-added)
COMPLETION_DATE = re.compile(r'\*\*Completed:\s*(\d{4}-\d{2}-\d{2})\*\*')

# Archive marker (plugin-added)
ARCHIVE_MARKER = re.compile(r'%%\s*kanban:archive\s*%%')
```

---

## Complete Implementation Example

```python
"""
Kanban Board Manipulation - Complete Reference Implementation
"""

import re
import frontmatter
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class KanbanBoard:
    """Represents and manipulates an Obsidian Kanban board"""

    # Regex patterns
    COLUMN_HEADING = re.compile(r'^##\s+(.+)$')
    CARD_ANY = re.compile(r'^(\s*)- \[([ x])\] (.+)$')
    DATE_ANY = re.compile(r'@(?:\{|\[\[)(\d{4}-\d{2}-\d{2})(?:\}|\]\])')
    TAG = re.compile(r'#([a-zA-Z0-9_/-]+)')
    WIKILINK = re.compile(r'\[\[([^|\]]+)(?:\|([^\]]+))?\]\]')

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.content = ""
        self.frontmatter = {}
        self.columns = []
        self.load()

    def load(self):
        """Load and parse Kanban board from file"""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            self.frontmatter = dict(post)
            self.content = post.content

        self._parse_structure()

    def save(self):
        """Save Kanban board to file"""
        # Rebuild content from columns
        content_lines = []

        for column in self.columns:
            content_lines.append(f"## {column['name']}")

            for card in column['cards']:
                content_lines.append(self._card_to_line(card))

            content_lines.append('')  # Blank line after column

        # Create frontmatter post
        post = frontmatter.Post('\n'.join(content_lines))
        for key, value in self.frontmatter.items():
            post[key] = value

        # Write to file
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

    def _parse_structure(self):
        """Parse columns and cards from content"""
        lines = self.content.split('\n')
        self.columns = []
        current_column = None

        for i, line in enumerate(lines):
            # Column heading
            if line.startswith('## '):
                if current_column:
                    self.columns.append(current_column)

                current_column = {
                    'name': line[3:].strip(),
                    'cards': []
                }

            # Card
            elif current_column and (line.strip().startswith('- [ ]') or
                                    line.strip().startswith('- [x]')):
                card = self._parse_card(line)
                if card:
                    current_column['cards'].append(card)

        # Add last column
        if current_column:
            self.columns.append(current_column)

    def _parse_card(self, line: str) -> Optional[Dict]:
        """Parse a single card line"""
        match = self.CARD_ANY.match(line)
        if not match:
            return None

        indentation = match.group(1)
        completion = match.group(2)
        card_text = match.group(3)

        # Extract metadata
        dates = self.DATE_ANY.findall(card_text)
        tags = self.TAG.findall(card_text)
        wikilinks = self.WIKILINK.findall(card_text)

        return {
            'text': card_text,
            'completed': completion == 'x',
            'indentation': len(indentation),
            'dates': dates,
            'tags': tags,
            'wikilinks': [link[0] for link in wikilinks],
            'aliases': [link[1] if link[1] else None for link in wikilinks]
        }

    def _card_to_line(self, card: Dict) -> str:
        """Convert card dict to markdown line"""
        indent = ' ' * card['indentation']
        check = 'x' if card['completed'] else ' '
        return f"{indent}- [{check}] {card['text']}"

    def add_card(self, column_name: str, card_text: str,
                 date: str = None, tags: List[str] = None) -> bool:
        """Add a new card to a column"""
        # Find column
        column = None
        for col in self.columns:
            if col['name'] == column_name:
                column = col
                break

        if not column:
            raise ValueError(f"Column '{column_name}' not found")

        # Build card text with metadata
        text_parts = [card_text]
        if date:
            text_parts.append(f"@{{{date}}}")
        if tags:
            for tag in tags:
                text_parts.append(f"#{tag}")

        full_text = ' '.join(text_parts)

        # Create card
        card = {
            'text': full_text,
            'completed': False,
            'indentation': 0,
            'dates': [date] if date else [],
            'tags': tags or [],
            'wikilinks': [],
            'aliases': []
        }

        column['cards'].append(card)
        return True

    def move_card(self, card_text: str, from_column: str,
                  to_column: str, mark_complete: bool = False) -> bool:
        """Move a card between columns"""
        # Find source column and card
        source_col = None
        card_index = None

        for col in self.columns:
            if col['name'] == from_column:
                source_col = col
                for i, card in enumerate(col['cards']):
                    if card_text in card['text']:
                        card_index = i
                        break
                break

        if not source_col or card_index is None:
            raise ValueError(f"Card not found in column '{from_column}'")

        # Find destination column
        dest_col = None
        for col in self.columns:
            if col['name'] == to_column:
                dest_col = col
                break

        if not dest_col:
            raise ValueError(f"Column '{to_column}' not found")

        # Move card
        card = source_col['cards'].pop(card_index)

        if mark_complete:
            card['completed'] = True

        dest_col['cards'].append(card)
        return True

    def toggle_card(self, card_text: str, column_name: str = None) -> bool:
        """Toggle card completion status"""
        # Search in specified column or all columns
        columns_to_search = [col for col in self.columns
                            if column_name is None or col['name'] == column_name]

        for col in columns_to_search:
            for card in col['cards']:
                if card_text in card['text']:
                    card['completed'] = not card['completed']
                    return True

        raise ValueError("Card not found")

    def get_statistics(self) -> Dict:
        """Get board statistics"""
        total_cards = sum(len(col['cards']) for col in self.columns)
        completed = sum(1 for col in self.columns
                       for card in col['cards'] if card['completed'])

        return {
            'total_columns': len(self.columns),
            'total_cards': total_cards,
            'completed_cards': completed,
            'incomplete_cards': total_cards - completed,
            'columns': [
                {
                    'name': col['name'],
                    'card_count': len(col['cards']),
                    'completed': sum(1 for c in col['cards'] if c['completed'])
                }
                for col in self.columns
            ]
        }


# Usage example
if __name__ == '__main__':
    # Load board
    board = KanbanBoard('/path/to/board.md')

    # Add card
    board.add_card('To Do', 'Implement feature X',
                   date='2024-01-15', tags=['important', 'backend'])

    # Move card
    board.move_card('Implement feature X', 'To Do', 'In Progress')

    # Toggle completion
    board.toggle_card('Implement feature X')

    # Get stats
    stats = board.get_statistics()
    print(f"Board has {stats['total_cards']} cards across {stats['total_columns']} columns")

    # Save changes
    board.save()
```

---

## Summary

### Markdown Structure Specification

1. **Frontmatter**: `kanban-plugin: basic` in YAML frontmatter
2. **Columns**: Level 2 headings (`## Column Name`)
3. **Cards**: Checkbox list items (`- [ ]` or `- [x]`)
4. **Metadata**: Dates `@{YYYY-MM-DD}`, tags `#tag`, wikilinks `[[note]]`
5. **Nesting**: 2-space indentation for subtasks

### Card Manipulation Algorithms

1. **Add Card**: Find column, insert after last card or heading
2. **Move Card**: Remove from source, insert into destination
3. **Toggle Status**: Find card, swap `[ ]` ↔ `[x]`
4. **Preserve Metadata**: Parse, update, rebuild with all metadata intact

### Parsing Regex Patterns

1. Column: `^##\s+(.+)$`
2. Card: `^(\s*)- \[([ x])\] (.+)$`
3. Date: `@(?:\{|\[\[)(\d{4}-\d{2}-\d{2})(?:\}|\]\])`
4. Tag: `#([a-zA-Z0-9_/-]+)`
5. Wikilink: `\[\[([^|\]]+)(?:\|([^\]]+))?\]\]`

### Edge Case Handling Strategies

1. **Empty columns**: Preserve, insert after heading
2. **Cards without checkboxes**: Ignore, preserve
3. **Nested subtasks**: Move entire tree, preserve indentation
4. **Non-standard columns**: Support all valid heading text
5. **Malformed metadata**: Ignore invalid formats, preserve as text

---

## References

- **Obsidian Kanban Plugin**: https://github.com/mgmeyers/obsidian-kanban
- **Plugin Stats**: 1.9M downloads, 3.8k GitHub stars
- **Documentation**: https://publish.obsidian.md/kanban/
- **Known Issues**: Empty last column (GitHub #346)
- **Date Format Compatibility**: Tasks plugin uses `📅 YYYY-MM-DD`, Kanban uses `@{YYYY-MM-DD}`

---

**Research Complete**: 2025-10-22
**Next Steps**: Implement `src/tools/kanban.py` using patterns documented above
