# Obsidian MCP Extension Project

## Project Overview

This project extends the `obsidian-mcp` Python-based MCP server to combine the best of both worlds:
- **Performance**: Direct filesystem access with SQLite indexing (90% less memory, 60x faster searches)
- **Features**: Advanced capabilities like backlinks, tag management, smart insertion, and statistics
- **Simplicity**: No Obsidian plugins required, works offline, instant startup

## Why This Approach?

### Current Landscape

There are two main types of Obsidian MCP servers:

1. **Filesystem-based** (`obsidian-mcp`): Fast, lightweight, no dependencies, but limited features
2. **API-based** (`mcp-obsidian`): Feature-rich but requires Obsidian running, plugin installation, slower

### Our Solution

Fork `obsidian-mcp` and add missing features using direct filesystem operations, maintaining all performance benefits while gaining full feature parity.

### Advantages

✅ Direct filesystem access (fast, works offline)  
✅ No Obsidian plugin dependency  
✅ 90% less memory usage  
✅ Instant startup with persistent SQLite index  
✅ Works without Obsidian running  
✅ All advanced features: backlinks, tags, smart insertion, statistics  
✅ Perfect for `uv`/`uvx` workflow on Arch Linux  

---

## Quick Start

### 1. Setup

```bash
# Fork and clone the repository
git clone https://github.com/punkpeye/obsidian-mcp.git obsidian-mcp-extended
cd obsidian-mcp-extended

# Install additional dependencies
uv pip install python-frontmatter

# Test the server
uv run obsidian-mcp
```

### 2. Configure Claude Code

**File Location:** `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "obsidian-extended": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/obsidian-mcp-extended",
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

**Note:** Replace `/absolute/path/to/obsidian-mcp-extended` and `/path/to/your/obsidian/vault` with your actual paths.

### 3. Restart Claude Code

After configuration, restart Claude Code to load the MCP server.

---

## Project Structure

```
obsidian-mcp-extended/
├── src/
│   ├── server.py              # Main entry point - register new tools here
│   ├── tools/
│   │   ├── note_management.py # Existing: CRUD operations
│   │   ├── search_discovery.py # Existing: Search functionality
│   │   ├── organization.py    # Existing: Basic organization
│   │   ├── backlinks.py       # NEW - Backlink analysis
│   │   ├── tags.py            # NEW - Advanced tag management
│   │   ├── smart_insert.py    # NEW - Smart content insertion
│   │   └── statistics.py      # NEW - Note statistics
│   ├── models/
│   │   └── obsidian.py        # Existing data models
│   ├── utils/
│   │   ├── validators.py      # Existing validation utilities
│   │   └── validation.py      # Existing validation logic
│   └── constants.py           # Existing constants
├── pyproject.toml             # Update dependencies here
├── README.md                  # Update with new features
└── .obsidian/                 # SQLite index stored here
    └── mcp-search-index.db
```

---

## Features to Implement

### Feature 1: Backlink Analysis

Find all notes that link to a specific note.

**Create file:** `src/tools/backlinks.py`

```python
import os
import re
from pathlib import Path

def find_backlinks(vault_path: str, note_name: str) -> list:
    """
    Find all notes that link to the specified note.
    
    Args:
        vault_path: Path to the Obsidian vault
        note_name: Name of the note to find backlinks for
        
    Returns:
        List of dicts containing file path and links found
    """
    backlinks = []
    # Match [[note]] or [[note|alias]]
    note_pattern = re.compile(r'\[\[([^\]]+)\]\]')
    
    for root, dirs, files in os.walk(vault_path):
        # Skip .obsidian directory
        dirs[:] = [d for d in dirs if d != '.obsidian']
        
        for file in files:
            if file.endswith('.md'):
                filepath = Path(root) / file
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        links = note_pattern.findall(content)
                        
                        # Check if note_name matches (handle aliases)
                        for link in links:
                            link_target = link.split('|')[0].strip()
                            if link_target == note_name or link_target.endswith(f"/{note_name}"):
                                backlinks.append({
                                    'file': str(filepath.relative_to(vault_path)),
                                    'absolute_path': str(filepath),
                                    'links': links
                                })
                                break
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
                    
    return backlinks

def find_broken_links(vault_path: str) -> list:
    """
    Find all broken wikilinks in the vault.
    
    Returns:
        List of dicts containing file and broken links
    """
    broken_links = []
    all_notes = set()
    
    # First, collect all note names
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d != '.obsidian']
        for file in files:
            if file.endswith('.md'):
                all_notes.add(file[:-3])  # Remove .md extension
    
    # Now find broken links
    note_pattern = re.compile(r'\[\[([^\]]+)\]\]')
    
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d != '.obsidian']
        for file in files:
            if file.endswith('.md'):
                filepath = Path(root) / file
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        links = note_pattern.findall(content)
                        
                        broken = []
                        for link in links:
                            link_target = link.split('|')[0].strip()
                            link_name = link_target.split('/')[-1]
                            
                            if link_name not in all_notes:
                                broken.append(link)
                        
                        if broken:
                            broken_links.append({
                                'file': str(filepath.relative_to(vault_path)),
                                'broken_links': broken
                            })
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return broken_links
```

---

### Feature 2: Advanced Tag Management

Extract and manage both frontmatter and inline tags.

**Create file:** `src/tools/tags.py`

```python
import frontmatter
import re
from pathlib import Path

def extract_all_tags(content: str) -> dict:
    """
    Extract both frontmatter and inline tags from a note.
    
    Args:
        content: The full content of the note
        
    Returns:
        Dict with frontmatter_tags, inline_tags, and all_tags
    """
    try:
        post = frontmatter.loads(content)
        fm_tags = post.get('tags', [])
        
        # Handle single tag as string
        if isinstance(fm_tags, str):
            fm_tags = [fm_tags]
        
        # Find inline tags (#tag)
        inline_tags = re.findall(r'#([a-zA-Z0-9_/-]+)', post.content)
        
        return {
            'frontmatter_tags': fm_tags,
            'inline_tags': inline_tags,
            'all_tags': list(set(fm_tags + inline_tags))
        }
    except Exception as e:
        # If no frontmatter, just find inline tags
        inline_tags = re.findall(r'#([a-zA-Z0-9_/-]+)', content)
        return {
            'frontmatter_tags': [],
            'inline_tags': inline_tags,
            'all_tags': inline_tags
        }

def add_tag_to_frontmatter(filepath: str, tag: str) -> dict:
    """
    Add a tag to a note's frontmatter.
    
    Args:
        filepath: Path to the note
        tag: Tag to add (without #)
        
    Returns:
        Success status and message
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        tags = post.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        
        if tag not in tags:
            tags.append(tag)
            post['tags'] = tags
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
            
            return {
                'success': True,
                'message': f"Added tag '{tag}' to frontmatter"
            }
        else:
            return {
                'success': False,
                'message': f"Tag '{tag}' already exists"
            }
    except Exception as e:
        return {
            'success': False,
            'message': f"Error: {str(e)}"
        }

def remove_tag_from_frontmatter(filepath: str, tag: str) -> dict:
    """
    Remove a tag from a note's frontmatter.
    
    Args:
        filepath: Path to the note
        tag: Tag to remove (without #)
        
    Returns:
        Success status and message
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        tags = post.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        
        if tag in tags:
            tags.remove(tag)
            post['tags'] = tags if tags else None
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
            
            return {
                'success': True,
                'message': f"Removed tag '{tag}' from frontmatter"
            }
        else:
            return {
                'success': False,
                'message': f"Tag '{tag}' not found"
            }
    except Exception as e:
        return {
            'success': False,
            'message': f"Error: {str(e)}"
        }

def find_notes_by_tag(vault_path: str, tag: str) -> list:
    """
    Find all notes containing a specific tag.
    
    Args:
        vault_path: Path to Obsidian vault
        tag: Tag to search for (with or without #)
        
    Returns:
        List of file paths containing the tag
    """
    if tag.startswith('#'):
        tag = tag[1:]
    
    matching_notes = []
    
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d != '.obsidian']
        for file in files:
            if file.endswith('.md'):
                filepath = Path(root) / file
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        tags = extract_all_tags(content)
                        
                        if tag in tags['all_tags']:
                            matching_notes.append({
                                'file': str(filepath.relative_to(vault_path)),
                                'absolute_path': str(filepath),
                                'tag_locations': {
                                    'frontmatter': tag in tags['frontmatter_tags'],
                                    'inline': tag in tags['inline_tags']
                                }
                            })
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return matching_notes
```

---

### Feature 3: Smart Content Insertion

Insert content at specific locations within notes.

**Create file:** `src/tools/smart_insert.py`

```python
import re

def insert_after_heading(content: str, heading: str, new_content: str) -> str:
    """
    Insert content after a specific heading.
    
    Args:
        content: Original note content
        heading: Heading text to search for (without #)
        new_content: Content to insert
        
    Returns:
        Updated content with insertion
    """
    # Match heading at any level (# to ######)
    pattern = rf'^(#{{{1,6}}}\s+{re.escape(heading)}\s*)$'
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if re.match(pattern, line, re.IGNORECASE):
            # Find the next heading or end of file
            next_heading = i + 1
            while next_heading < len(lines) and not re.match(r'^#{1,6}\s+', lines[next_heading]):
                next_heading += 1
            
            # Insert before the next heading or at the end
            lines.insert(next_heading, '\n' + new_content.strip())
            return '\n'.join(lines)
    
    raise ValueError(f"Heading '{heading}' not found in note")

def insert_after_block(content: str, block_id: str, new_content: str) -> str:
    """
    Insert content after a block reference.
    
    Args:
        content: Original note content
        block_id: Block reference ID (without ^)
        new_content: Content to insert
        
    Returns:
        Updated content with insertion
    """
    if not block_id.startswith('^'):
        block_id = '^' + block_id
    
    pattern = rf'{re.escape(block_id)}\s*$'
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if re.search(pattern, line):
            lines.insert(i + 1, '\n' + new_content.strip())
            return '\n'.join(lines)
    
    raise ValueError(f"Block reference '{block_id}' not found in note")

def insert_in_frontmatter(content: str, key: str, value: str) -> str:
    """
    Insert or update a field in frontmatter.
    
    Args:
        content: Original note content
        key: Frontmatter key
        value: Value to set
        
    Returns:
        Updated content
    """
    import frontmatter
    
    try:
        post = frontmatter.loads(content)
        post[key] = value
        return frontmatter.dumps(post)
    except Exception:
        # No frontmatter exists, create it
        new_frontmatter = f"---\n{key}: {value}\n---\n\n"
        return new_frontmatter + content

def append_to_note(content: str, new_content: str) -> str:
    """
    Append content to the end of a note.
    
    Args:
        content: Original note content
        new_content: Content to append
        
    Returns:
        Updated content
    """
    return content.rstrip() + '\n\n' + new_content.strip() + '\n'

def insert_at_cursor(content: str, cursor_line: int, new_content: str) -> str:
    """
    Insert content at a specific line number.
    
    Args:
        content: Original note content
        cursor_line: Line number (0-indexed)
        new_content: Content to insert
        
    Returns:
        Updated content
    """
    lines = content.split('\n')
    
    if cursor_line < 0 or cursor_line > len(lines):
        raise ValueError(f"Invalid cursor position: {cursor_line}")
    
    lines.insert(cursor_line, new_content)
    return '\n'.join(lines)
```

---

### Feature 4: Note Statistics

Get comprehensive statistics about notes.

**Create file:** `src/tools/statistics.py`

```python
import re
from pathlib import Path
from datetime import datetime

def get_note_stats(content: str, filepath: str) -> dict:
    """
    Get comprehensive statistics about a note.
    
    Args:
        content: The note content
        filepath: Path to the note file
        
    Returns:
        Dict with various statistics
    """
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
    heading_levels = {}
    for level, text in headings:
        level_num = len(level)
        if level_num not in heading_levels:
            heading_levels[level_num] = []
        heading_levels[level_num].append(text.strip())
    
    # Code blocks
    code_blocks = len(re.findall(r'```[\s\S]*?```', content))
    inline_code = len(re.findall(r'`[^`]+`', content))
    
    # File metadata
    path = Path(filepath)
    stat = path.stat()
    
    return {
        'word_count': words,
        'character_count': chars,
        'character_count_no_spaces': chars_no_spaces,
        'line_count': len(content.split('\n')),
        'links': {
            'wikilink_count': len(wikilinks),
            'wikilinks': wikilinks,
            'markdown_link_count': len(markdown_links),
            'total_links': len(wikilinks) + len(markdown_links)
        },
        'tags': {
            'count': len(set(tags)),
            'unique_tags': list(set(tags)),
            'all_tags': tags
        },
        'headings': {
            'count': len(headings),
            'by_level': heading_levels,
            'structure': [(len(h[0]), h[1]) for h in headings]
        },
        'code': {
            'code_blocks': code_blocks,
            'inline_code': inline_code
        },
        'file': {
            'size_bytes': stat.st_size,
            'size_kb': round(stat.st_size / 1024, 2),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'accessed': datetime.fromtimestamp(stat.st_atime).isoformat()
        }
    }

def get_vault_stats(vault_path: str) -> dict:
    """
    Get statistics for the entire vault.
    
    Args:
        vault_path: Path to the Obsidian vault
        
    Returns:
        Dict with vault-wide statistics
    """
    import os
    
    total_notes = 0
    total_words = 0
    total_links = 0
    all_tags = set()
    
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d != '.obsidian']
        for file in files:
            if file.endswith('.md'):
                total_notes += 1
                filepath = Path(root) / file
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        stats = get_note_stats(content, str(filepath))
                        total_words += stats['word_count']
                        total_links += stats['links']['total_links']
                        all_tags.update(stats['tags']['unique_tags'])
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    
    return {
        'total_notes': total_notes,
        'total_words': total_words,
        'total_links': total_links,
        'unique_tags': len(all_tags),
        'all_tags': sorted(list(all_tags)),
        'avg_words_per_note': round(total_words / total_notes, 2) if total_notes > 0 else 0
    }
```

---

## Registering New Tools

**Edit:** `src/server.py`

Add imports at the top:

```python
import os
from .tools.backlinks import find_backlinks, find_broken_links
from .tools.tags import (
    extract_all_tags, 
    add_tag_to_frontmatter, 
    remove_tag_from_frontmatter,
    find_notes_by_tag
)
from .tools.smart_insert import (
    insert_after_heading,
    insert_after_block,
    insert_in_frontmatter,
    append_to_note
)
from .tools.statistics import get_note_stats, get_vault_stats
```

Add tool definitions (find the section where other `@server.tool()` decorators are):

```python
@server.tool()
def get_backlinks(note_name: str) -> dict:
    """
    Find all notes that link to the specified note.
    
    Args:
        note_name: Name of the note (without .md extension)
    
    Returns:
        List of notes containing links to this note
    """
    vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if not vault_path:
        return {"error": "OBSIDIAN_VAULT_PATH not set"}
    
    backlinks = find_backlinks(vault_path, note_name)
    return {
        "note": note_name,
        "backlink_count": len(backlinks),
        "backlinks": backlinks
    }

@server.tool()
def get_broken_links() -> dict:
    """
    Find all broken wikilinks in the vault.
    
    Returns:
        List of files with broken links
    """
    vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if not vault_path:
        return {"error": "OBSIDIAN_VAULT_PATH not set"}
    
    broken = find_broken_links(vault_path)
    return {
        "files_with_broken_links": len(broken),
        "broken_links": broken
    }

@server.tool()
def analyze_note_tags(filepath: str) -> dict:
    """
    Extract all tags (frontmatter and inline) from a note.
    
    Args:
        filepath: Path to the note (relative or absolute)
    
    Returns:
        Dict with frontmatter_tags, inline_tags, and all_tags
    """
    vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if not filepath.startswith('/'):
        filepath = os.path.join(vault_path, filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return extract_all_tags(content)

@server.tool()
def add_tag(filepath: str, tag: str) -> dict:
    """
    Add a tag to a note's frontmatter.
    
    Args:
        filepath: Path to the note
        tag: Tag to add (without # symbol)
    
    Returns:
        Success status and message
    """
    vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if not filepath.startswith('/'):
        filepath = os.path.join(vault_path, filepath)
    
    return add_tag_to_frontmatter(filepath, tag)

@server.tool()
def remove_tag(filepath: str, tag: str) -> dict:
    """
    Remove a tag from a note's frontmatter.
    
    Args:
        filepath: Path to the note
        tag: Tag to remove (without # symbol)
    
    Returns:
        Success status and message
    """
    vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if not filepath.startswith('/'):
        filepath = os.path.join(vault_path, filepath)
    
    return remove_tag_from_frontmatter(filepath, tag)

@server.tool()
def search_by_tag(tag: str) -> dict:
    """
    Find all notes containing a specific tag.
    
    Args:
        tag: Tag to search for (with or without # symbol)
    
    Returns:
        List of notes with the tag
    """
    vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if not vault_path:
        return {"error": "OBSIDIAN_VAULT_PATH not set"}
    
    notes = find_notes_by_tag(vault_path, tag)
    return {
        "tag": tag,
        "count": len(notes),
        "notes": notes
    }

@server.tool()
def insert_content_after_heading(filepath: str, heading: str, content: str) -> dict:
    """
    Insert content after a specific heading in a note.
    
    Args:
        filepath: Path to the note
        heading: Heading text (without # symbols)
        content: Content to insert
    
    Returns:
        Success status
    """
    vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if not filepath.startswith('/'):
        filepath = os.path.join(vault_path, filepath)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original = f.read()
        
        updated = insert_after_heading(original, heading, content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated)
        
        return {"success": True, "message": f"Inserted content after heading '{heading}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@server.tool()
def insert_content_after_block(filepath: str, block_id: str, content: str) -> dict:
    """
    Insert content after a block reference in a note.
    
    Args:
        filepath: Path to the note
        block_id: Block reference ID (with or without ^)
        content: Content to insert
    
    Returns:
        Success status
    """
    vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if not filepath.startswith('/'):
        filepath = os.path.join(vault_path, filepath)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original = f.read()
        
        updated = insert_after_block(original, block_id, content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated)
        
        return {"success": True, "message": f"Inserted content after block '{block_id}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@server.tool()
def note_statistics(filepath: str) -> dict:
    """
    Get comprehensive statistics about a note.
    
    Args:
        filepath: Path to the note
    
    Returns:
        Dict with word count, links, tags, headings, and file info
    """
    vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if not filepath.startswith('/'):
        filepath = os.path.join(vault_path, filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return get_note_stats(content, filepath)

@server.tool()
def vault_statistics() -> dict:
    """
    Get statistics for the entire Obsidian vault.
    
    Returns:
        Dict with vault-wide statistics
    """
    vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if not vault_path:
        return {"error": "OBSIDIAN_VAULT_PATH not set"}
    
    return get_vault_stats(vault_path)
```

---

## Update Dependencies

**Edit:** `pyproject.toml`

Add `python-frontmatter` to the dependencies section:

```toml
[project]
dependencies = [
    "mcp>=0.1.0",
    "python-frontmatter>=1.0.0",
    # ... other existing dependencies
]
```

Then install:

```bash
uv pip install python-frontmatter
```

---

## Testing

### 1. Test the Server Directly

```bash
cd obsidian-mcp-extended
uv run obsidian-mcp
```

### 2. Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/obsidian-mcp-extended run obsidian-mcp
```

This will open a browser interface to test individual tools.

### 3. Test in Claude Code

1. Ensure configuration is correct in `~/.config/claude/claude_desktop_config.json`
2. Restart Claude Code
3. Try commands like:
   - "Find all backlinks to my 'Project Ideas' note"
   - "Show me statistics for my daily note"
   - "Add the tag 'important' to this note"
   - "Insert a task list after the 'Todo' heading"

---

## New Tools Available

After implementation, these tools will be available:

### Backlink Tools
- `get_backlinks(note_name)` - Find notes linking to a specific note
- `get_broken_links()` - Find all broken wikilinks in vault

### Tag Tools
- `analyze_note_tags(filepath)` - Extract all tags from a note
- `add_tag(filepath, tag)` - Add tag to frontmatter
- `remove_tag(filepath, tag)` - Remove tag from frontmatter
- `search_by_tag(tag)` - Find all notes with a tag

### Smart Insertion Tools
- `insert_content_after_heading(filepath, heading, content)` - Insert after heading
- `insert_content_after_block(filepath, block_id, content)` - Insert after block reference

### Statistics Tools
- `note_statistics(filepath)` - Get stats for a specific note
- `vault_statistics()` - Get stats for entire vault

---

## Comparison with Original Options

| Feature | Original obsidian-mcp | Our Extended Version | API-based mcp-obsidian |
|---------|----------------------|---------------------|----------------------|
| Setup Complexity | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Performance | ⚡ Very Fast | ⚡ Very Fast | 🐢 Slower |
| Memory Usage | 📉 Low | 📉 Low | 📈 High |
| Obsidian Running | ❌ Not Required | ❌ Not Required | ✅ Required |
| Backlinks | ❌ | ✅ | ✅ |
| Tag Management | ❌ | ✅ | ✅ |
| Smart Insertion | ❌ | ✅ | ✅ |
| Statistics | ❌ | ✅ | ✅ |
| Plugin Required | ❌ | ❌ | ✅ |
| Works Offline | ✅ | ✅ | ❌ |

---

## Future Enhancements

Additional features you could implement:

1. **Graph Analysis**: Visualize note connections
2. **Template System**: Create notes from templates
3. **Daily Notes Helper**: Smart daily note creation
4. **Dataview-like Queries**: Query notes by properties
5. **Auto-linking**: Suggest links between related notes
6. **Duplicate Detection**: Find similar/duplicate content
7. **Orphan Notes**: Find notes with no links
8. **Link Refactoring**: Bulk rename/update links
9. **Export Tools**: Export to various formats
10. **Sync Conflict Detection**: Identify sync conflicts

---

## Contributing

If you make improvements:

1. Fork the original repository on GitHub
2. Create a feature branch
3. Add your features with tests
4. Submit a pull request to the original project

This helps the entire community benefit from your work!

---

## Troubleshooting

### Server won't start
- Check that `uv` is installed: `which uv`
- Verify vault path is correct
- Check file permissions on vault directory

### Tools not appearing
- Restart Claude Code after config changes
- Check `~/.config/claude/claude_desktop_config.json` syntax
- Look at logs: `tail -f ~/Library/Logs/Claude/mcp-server-obsidian-extended.log` (macOS)

### Import errors
- Ensure `python-frontmatter` is installed: `uv pip install python-frontmatter`
- Check Python version: Should be 3.11+

### Performance issues with large vaults
- The SQLite index should handle large vaults well
- If issues persist, consider adding pagination to search results

---

## Resources

- **Original Project**: https://github.com/punkpeye/obsidian-mcp
- **MCP Documentation**: https://modelcontextprotocol.io
- **Obsidian Documentation**: https://help.obsidian.md
- **Python Frontmatter**: https://python-frontmatter.readthedocs.io
- **uv Documentation**: https://docs.astral.sh/uv/

---

## License

Maintain the same license as the original project (typically MIT). Check the original repository for details.

---

## Summary

This project gives you:
- ✅ All the speed and simplicity of filesystem access
- ✅ All the features of API-based solutions
- ✅ No dependencies on Obsidian being running
- ✅ Perfect integration with uv and Claude Code
- ✅ Easy to extend with your own features

Happy coding! 🚀
