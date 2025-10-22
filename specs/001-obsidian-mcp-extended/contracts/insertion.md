# MCP Tool Contracts: Smart Insertion

**Module**: `src/tools/smart_insert.py`
**Category**: Content Insertion
**Tools**: 2

---

## Tool: `insert_content_after_heading`

**Description**: Insert content immediately after a specific heading in a note.

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "filepath": {
      "type": "string",
      "description": "Path to note"
    },
    "heading": {
      "type": "string",
      "description": "Heading text (without # symbols)"
    },
    "content": {
      "type": "string",
      "description": "Content to insert"
    }
  },
  "required": ["filepath", "heading", "content"]
}
```

### Output Schema
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "message": {"type": "string"},
    "error": {"type": "string", "optional": true}
  }
}
```

### Example
**Input**:
```json
{
  "filepath": "note.md",
  "heading": "Tasks",
  "content": "- [ ] New task item"
}
```

**Output Success**: `{"success": true, "message": "Inserted content after heading 'Tasks'"}`

**Output Error**: `{"success": false, "error": "Heading 'Tasks' not found in note"}`

---

## Tool: `insert_content_after_block`

**Description**: Insert content immediately after a block reference.

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "filepath": {"type": "string"},
    "block_id": {
      "type": "string",
      "description": "Block reference ID (with or without ^ prefix)"
    },
    "content": {"type": "string"}
  },
  "required": ["filepath", "block_id", "content"]
}
```

### Output Schema: Same as `insert_content_after_heading`

### Example
**Input**:
```json
{
  "filepath": "note.md",
  "block_id": "summary",
  "content": "\n## Follow-up\n- Action items..."
}
```

**Output**: `{"success": true, "message": "Inserted content after block '^summary'"}`

---

## Performance Expectations

| Operation | Note Size | Expected Time |
|-----------|-----------|---------------|
| insert_content_after_heading | 10,000 words | < 500ms |
| insert_content_after_block | 10,000 words | < 500ms |

## Error Handling

- Heading/block not found: Return clear error message
- File permission denied: Return permission error
- Invalid filepath: Return file not found error
- Malformed content: Accept as-is (user responsibility)
