# MCP Tool Contracts: Statistics

**Module**: `src/tools/statistics.py`
**Category**: Statistics & Analytics
**Tools**: 2

---

## Tool: `note_statistics`

**Description**: Get comprehensive statistics about a single note.

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "filepath": {
      "type": "string",
      "description": "Path to note"
    }
  },
  "required": ["filepath"]
}
```

### Output Schema
```json
{
  "type": "object",
  "properties": {
    "word_count": {"type": "integer"},
    "character_count": {"type": "integer"},
    "character_count_no_spaces": {"type": "integer"},
    "line_count": {"type": "integer"},
    "links": {
      "type": "object",
      "properties": {
        "wikilink_count": {"type": "integer"},
        "wikilinks": {"type": "array", "items": {"type": "string"}},
        "markdown_link_count": {"type": "integer"},
        "total_links": {"type": "integer"}
      }
    },
    "tags": {
      "type": "object",
      "properties": {
        "count": {"type": "integer"},
        "unique_tags": {"type": "array", "items": {"type": "string"}},
        "all_tags": {"type": "array", "items": {"type": "string"}}
      }
    },
    "headings": {
      "type": "object",
      "properties": {
        "count": {"type": "integer"},
        "by_level": {
          "type": "object",
          "additionalProperties": {"type": "array"}
        },
        "structure": {
          "type": "array",
          "items": {"type": "array"}
        }
      }
    },
    "code": {
      "type": "object",
      "properties": {
        "code_blocks": {"type": "integer"},
        "inline_code": {"type": "integer"}
      }
    },
    "file": {
      "type": "object",
      "properties": {
        "size_bytes": {"type": "integer"},
        "size_kb": {"type": "number"},
        "created": {"type": "string", "format": "date-time"},
        "modified": {"type": "string", "format": "date-time"},
        "accessed": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

### Example
**Input**: `{"filepath": "Projects/Analysis.md"}`

**Output**:
```json
{
  "word_count": 1543,
  "character_count": 9821,
  "character_count_no_spaces": 8234,
  "line_count": 127,
  "links": {
    "wikilink_count": 15,
    "wikilinks": ["Project A", "Meeting Notes", "..."],
    "markdown_link_count": 3,
    "total_links": 18
  },
  "tags": {
    "count": 4,
    "unique_tags": ["project", "analysis", "q1-2025", "review"],
    "all_tags": ["project", "analysis", "q1-2025", "review", "project"]
  },
  "headings": {
    "count": 8,
    "by_level": {
      "1": ["Analysis"],
      "2": ["Overview", "Findings", "Conclusions"],
      "3": ["Detail 1", "Detail 2", "Detail 3", "Detail 4"]
    },
    "structure": [[1, "Analysis"], [2, "Overview"], [3, "Detail 1"], ...]
  },
  "code": {
    "code_blocks": 2,
    "inline_code": 7
  },
  "file": {
    "size_bytes": 9821,
    "size_kb": 9.59,
    "created": "2025-01-10T14:30:00",
    "modified": "2025-01-22T09:15:30",
    "accessed": "2025-01-22T10:42:18"
  }
}
```

---

## Tool: `vault_statistics`

**Description**: Get aggregate statistics for the entire vault.

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
    "total_notes": {"type": "integer"},
    "total_words": {"type": "integer"},
    "total_links": {"type": "integer"},
    "unique_tags": {"type": "integer"},
    "all_tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Sorted list of all unique tags"
    },
    "avg_words_per_note": {"type": "number"}
  }
}
```

### Example
**Input**: `{}`

**Output**:
```json
{
  "total_notes": 234,
  "total_words": 145621,
  "total_links": 1823,
  "unique_tags": 67,
  "all_tags": ["active", "archive", "important", "meeting", "project", "..."],
  "avg_words_per_note": 622.31
}
```

---

## Performance Expectations

| Operation | Vault Size | Expected Time |
|-----------|-----------|---------------|
| note_statistics | Any note size | < 1 second |
| vault_statistics | 1,000 notes | < 30 seconds |
| vault_statistics | 10,000 notes | < 5 minutes |

## Implementation Notes

- Use compiled regex patterns for performance
- Single-pass content analysis where possible
- Lazy evaluation for vault statistics (don't load all notes into memory)
- Generator-based iteration for large vaults
