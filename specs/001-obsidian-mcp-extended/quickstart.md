# Developer Quickstart: Extended Obsidian MCP Server

**Target Audience**: Developers implementing the extended Obsidian MCP features
**Prerequisites**: Python 3.11+, `uv` package manager, Git, familiarity with MCP SDK

---

## Initial Setup

### 1. Fork and Clone Base Repository

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/obsidian-mcp.git obsidian-mcp-extended
cd obsidian-mcp-extended

# Add upstream remote for syncing
git remote add upstream https://github.com/punkpeye/obsidian-mcp.git
```

### 2. Install Dependencies

```bash
# Install existing dependencies
uv pip install .

# Install new dependency for frontmatter parsing
uv pip install python-frontmatter

# Install development dependencies
uv pip install pytest pytest-cov

# Verify installation
uv run obsidian-mcp --help
```

### 3. Set Up Test Vault

```bash
# Create a sample vault for testing
mkdir -p ~/test-vault
export OBSIDIAN_VAULT_PATH=~/test-vault

# Create sample notes
cat > ~/test-vault/note1.md <<EOF
---
tags: [test, sample]
---
# Note 1

This links to [[note2]] and has #inline-tag.
EOF

cat > ~/test-vault/note2.md <<EOF
# Note 2

Referenced by note1.
EOF
```

---

## Project Structure Overview

```
obsidian-mcp-extended/
├── src/
│   ├── server.py           # MCP server - REGISTER NEW TOOLS HERE
│   ├── tools/              # Tool implementations
│   │   ├── backlinks.py    # NEW: Implement backlink functions
│   │   ├── tags.py         # NEW: Implement tag functions
│   │   ├── smart_insert.py # NEW: Implement insertion functions
│   │   └── statistics.py   # NEW: Implement statistics functions
│   ├── models/             # Data models (may extend)
│   └── utils/              # Utilities (validators, etc.)
│
├── tests/
│   ├── unit/               # Unit tests for functions
│   └── integration/        # Integration tests for MCP tools
│
├── specs/001-obsidian-mcp-extended/
│   ├── spec.md             # Feature specification
│   ├── plan.md             # Implementation plan
│   ├── research.md         # Technical decisions
│   ├── data-model.md       # Entity definitions
│   ├── contracts/          # MCP tool contracts
│   └── quickstart.md       # This file
│
└── pyproject.toml          # Update dependencies here
```

---

## Development Workflow

### Step 1: Implement Tool Functions

Start with one module at a time. Example for backlinks:

```python
# src/tools/backlinks.py

import os
import re
from pathlib import Path
from typing import List, Dict

def find_backlinks(vault_path: str, note_name: str) -> List[Dict]:
    """
    Find all notes that link to the specified note.

    Args:
        vault_path: Path to the Obsidian vault
        note_name: Name of the note to find backlinks for

    Returns:
        List of dicts containing file path and links found
    """
    backlinks = []
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

                        # Check if note_name matches
                        for link in links:
                            link_target = link.split('|')[0].strip()
                            if link_target == note_name:
                                backlinks.append({
                                    'file': str(filepath.relative_to(vault_path)),
                                    'absolute_path': str(filepath),
                                    'links': links
                                })
                                break
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

    return backlinks
```

### Step 2: Write Unit Tests

```python
# tests/unit/test_backlinks.py

import pytest
from pathlib import Path
from src.tools.backlinks import find_backlinks

@pytest.fixture
def sample_vault(tmp_path):
    """Create a temporary test vault"""
    vault = tmp_path / "vault"
    vault.mkdir()

    # Create note with backlink
    (vault / "note1.md").write_text("Content with [[note2]] link")
    (vault / "note2.md").write_text("Target note")

    return str(vault)

def test_find_backlinks(sample_vault):
    result = find_backlinks(sample_vault, "note2")

    assert len(result) == 1
    assert "note1.md" in result[0]['file']
    assert "note2" in result[0]['links']

def test_find_backlinks_no_matches(sample_vault):
    result = find_backlinks(sample_vault, "nonexistent")

    assert len(result) == 0
```

Run tests:
```bash
pytest tests/unit/test_backlinks.py -v
```

### Step 3: Register MCP Tool

```python
# src/server.py

import os
from .tools.backlinks import find_backlinks

# ... existing code ...

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
```

### Step 4: Test with MCP Inspector

```bash
# Start MCP Inspector
npx @modelcontextprotocol/inspector uv --directory $(pwd) run obsidian-mcp

# In the browser interface:
# 1. Connect to server
# 2. Select "get_backlinks" tool
# 3. Input: {"note_name": "note2"}
# 4. Verify output matches expected schema
```

### Step 5: Integration Testing

```python
# tests/integration/test_backlinks_integration.py

import subprocess
import json

def test_get_backlinks_tool():
    """Test the MCP tool end-to-end"""
    # This would use MCP SDK to actually invoke the tool
    # For now, demonstrates the pattern
    result = {
        "note": "note2",
        "backlink_count": 1,
        "backlinks": [...]
    }

    assert result["note"] == "note2"
    assert result["backlink_count"] > 0
```

---

## Implementation Order

Follow this order for efficient development:

1. **Backlinks Module** (P1 - foundational)
   - `find_backlinks()`
   - `find_broken_links()`
   - Register `get_backlinks` and `get_broken_links` tools

2. **Tags Module** (P1 - independent)
   - `extract_all_tags()`
   - `add_tag_to_frontmatter()`
   - `remove_tag_from_frontmatter()`
   - `find_notes_by_tag()`
   - Register 4 tag tools

3. **Smart Insertion Module** (P2 - uses tag functions)
   - `insert_after_heading()`
   - `insert_after_block()`
   - `insert_in_frontmatter()` (uses frontmatter library)
   - Register insertion tools

4. **Statistics Module** (P3 - uses all previous patterns)
   - `get_note_stats()`
   - `get_vault_stats()`
   - Register statistics tools

---

## Testing Guidelines

### Unit Tests
- Test each function independently
- Use fixtures for test vaults (temporary directories)
- Test edge cases: empty inputs, malformed files, permissions
- Aim for 80%+ code coverage

### Integration Tests
- Test MCP tools end-to-end
- Verify tool registration
- Test with various vault configurations
- Use MCP Inspector for manual testing

### Performance Tests
- Create vaults with 100, 1000, 10000 notes
- Measure execution time for each tool
- Verify memory usage stays under 100MB
- Document performance metrics

```python
# Example performance test
import time
from src.tools.backlinks import find_backlinks

def test_backlinks_performance_1000_notes(large_vault):
    start = time.time()
    result = find_backlinks(large_vault, "target-note")
    duration = time.time() - start

    assert duration < 2.0  # Must complete under 2 seconds
    print(f"Processed 1000 notes in {duration:.2f}s")
```

---

## Common Patterns

### Reading Notes with Error Handling

```python
def read_note_safe(filepath: str) -> tuple[str, str | None]:
    """Read note with error handling"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read(), None
    except FileNotFoundError:
        return "", f"Note not found: {filepath}"
    except PermissionError:
        return "", f"Permission denied: {filepath}"
    except UnicodeDecodeError:
        return "", f"Invalid UTF-8 encoding: {filepath}"
    except Exception as e:
        return "", f"Error reading note: {str(e)}"
```

### Vault Path Resolution

```python
def resolve_filepath(vault_path: str, filepath: str) -> str:
    """Resolve relative or absolute filepath"""
    if not filepath.startswith('/'):
        filepath = os.path.join(vault_path, filepath)
    return filepath
```

### Regex Pattern Compilation

```python
# At module level - compile once
WIKILINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')
TAG_PATTERN = re.compile(r'#([a-zA-Z0-9_/-]+)')
HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
```

---

## Debugging Tips

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Functions
```python
# In Python REPL
from src.tools.backlinks import find_backlinks
result = find_backlinks('/path/to/vault', 'note-name')
print(result)
```

### MCP Inspector Console
- Open browser console to see MCP protocol messages
- Check tool input/output schemas
- Verify error responses

---

## Documentation Requirements

As you implement each feature:

1. **Update README.md**
   - Add tool descriptions
   - Include usage examples
   - Update feature comparison table

2. **Update CHANGELOG.md**
   - Document new features
   - Note any behavior changes
   - Credit contributors

3. **Add Docstrings**
   - Every function needs docstring
   - Include Args, Returns, Raises
   - Provide example usage in docstring

---

## Ready to Start?

1. Choose a module to implement (recommend starting with backlinks)
2. Read the relevant contract in `specs/001-obsidian-mcp-extended/contracts/`
3. Implement functions following patterns in `research.md`
4. Write unit tests
5. Register MCP tool in `server.py`
6. Test with MCP Inspector
7. Commit and move to next module

**Questions?** Refer to:
- [spec.md](spec.md) for requirements
- [plan.md](plan.md) for architecture
- [research.md](research.md) for implementation patterns
- [data-model.md](data-model.md) for entity definitions
- [contracts/](contracts/) for API specifications
