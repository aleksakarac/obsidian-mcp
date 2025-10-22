# MCP Tool Contracts: Backlinks

**Module**: `src/tools/backlinks.py`
**Category**: Backlink Analysis
**Tools**: 2

---

## Tool: `get_backlinks`

**Description**: Find all notes that link to a specified note via wikilinks.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "note_name": {
      "type": "string",
      "description": "Name of the target note (without .md extension)",
      "example": "Project Ideas"
    }
  },
  "required": ["note_name"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "note": {
      "type": "string",
      "description": "The target note name that was queried"
    },
    "backlink_count": {
      "type": "integer",
      "description": "Number of notes linking to this note"
    },
    "backlinks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "file": {
            "type": "string",
            "description": "Relative path from vault root"
          },
          "absolute_path": {
            "type": "string",
            "description": "Full filesystem path"
          },
          "links": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "All wikilinks found in this note"
          }
        }
      }
    }
  }
}
```

### Example Usage

**Input**:
```json
{
  "note_name": "Project Ideas"
}
```

**Output**:
```json
{
  "note": "Project Ideas",
  "backlink_count": 3,
  "backlinks": [
    {
      "file": "Daily Notes/2025-01-15.md",
      "absolute_path": "/vault/Daily Notes/2025-01-15.md",
      "links": ["Project Ideas", "Meeting Notes"]
    },
    {
      "file": "Work/Active Projects.md",
      "absolute_path": "/vault/Work/Active Projects.md",
      "links": ["Project Ideas|Ideas"]
    },
    {
      "file": "Archive/Brainstorm.md",
      "absolute_path": "/vault/Archive/Brainstorm.md",
      "links": ["Project Ideas"]
    }
  ]
}
```

### Error Cases

| Error Condition | Response |
|----------------|----------|
| Vault path not set | `{"error": "OBSIDIAN_VAULT_PATH not set"}` |
| Note name empty | `{"backlink_count": 0, "backlinks": []}` |
| Permission denied | `{"error": "Permission denied: <path>"}` |
| Invalid vault path | `{"error": "Vault not found: <path>"}` |

### Implementation Requirements

- FR-001: Scan all markdown files in vault
- FR-002: Support both `[[note]]` and `[[note|alias]]` syntax
- FR-003: Handle nested folder structures and relative paths
- FR-004: Skip `.obsidian` directory
- FR-006: Return file paths and link details

---

## Tool: `get_broken_links`

**Description**: Find all wikilinks in the vault that point to non-existent notes.

### Input Schema

```json
{
  "type": "object",
  "properties": {}
}
```

*No input parameters required*

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "files_with_broken_links": {
      "type": "integer",
      "description": "Number of notes containing broken links"
    },
    "broken_links": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "file": {
            "type": "string",
            "description": "Relative path from vault root"
          },
          "broken_links": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of broken wikilink targets"
          }
        }
      }
    }
  }
}
```

### Example Usage

**Input**:
```json
{}
```

**Output**:
```json
{
  "files_with_broken_links": 2,
  "broken_links": [
    {
      "file": "Daily Notes/2025-01-10.md",
      "broken_links": ["Deleted Note", "Old Project"]
    },
    {
      "file": "Work/TODO.md",
      "broken_links": ["Missing Reference"]
    }
  ]
}
```

### Error Cases

| Error Condition | Response |
|----------------|----------|
| Vault path not set | `{"error": "OBSIDIAN_VAULT_PATH not set"}` |
| Permission denied | `{"error": "Permission denied: <path>"}` |
| Invalid vault path | `{"error": "Vault not found: <path>"}` |
| Empty vault | `{"files_with_broken_links": 0, "broken_links": []}` |

### Implementation Requirements

- FR-005: Identify broken wikilinks by comparing targets against existing notes
- FR-004: Skip `.obsidian` directory
- FR-001: Scan all markdown files

---

## Performance Expectations

| Operation | Vault Size | Expected Time |
|-----------|-----------|---------------|
| get_backlinks | 1,000 notes | < 2 seconds |
| get_backlinks | 10,000 notes | < 20 seconds |
| get_broken_links | 1,000 notes | < 10 seconds |
| get_broken_links | 10,000 notes | < 100 seconds |

## Testing Requirements

### Unit Tests
- Test wikilink pattern matching (`[[note]]`, `[[note|alias]]`, `[[folder/note]]`)
- Test backlink extraction with various link formats
- Test broken link detection logic
- Test edge cases (empty vault, no backlinks, circular links)

### Integration Tests
- Test end-to-end with sample vault
- Verify tool registration in MCP server
- Test with Claude Code/MCP Inspector
- Performance benchmarks with large vaults
