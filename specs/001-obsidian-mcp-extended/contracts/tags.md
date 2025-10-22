# MCP Tool Contracts: Tags

**Module**: `src/tools/tags.py`
**Category**: Tag Management
**Tools**: 4

---

## Tool: `analyze_note_tags`

**Description**: Extract all tags (frontmatter and inline) from a specific note.

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "filepath": {
      "type": "string",
      "description": "Path to note (relative to vault or absolute)"
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
    "frontmatter_tags": {
      "type": "array",
      "items": {"type": "string"}
    },
    "inline_tags": {
      "type": "array",
      "items": {"type": "string"}
    },
    "all_tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Deduplicated union of frontmatter and inline tags"
    }
  }
}
```

### Example
**Input**: `{"filepath": "Projects/Active.md"}`

**Output**:
```json
{
  "frontmatter_tags": ["project", "active"],
  "inline_tags": ["meeting", "project/planning"],
  "all_tags": ["project", "active", "meeting", "project/planning"]
}
```

---

## Tool: `add_tag`

**Description**: Add a tag to a note's frontmatter.

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "filepath": {"type": "string"},
    "tag": {
      "type": "string",
      "description": "Tag name without # symbol"
    }
  },
  "required": ["filepath", "tag"]
}
```

### Output Schema
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "message": {"type": "string"}
  }
}
```

### Example
**Input**: `{"filepath": "note.md", "tag": "important"}`

**Output**: `{"success": true, "message": "Added tag 'important' to frontmatter"}`

---

## Tool: `remove_tag`

**Description**: Remove a tag from a note's frontmatter.

### Input/Output Schema: Same as `add_tag`

---

## Tool: `search_by_tag`

**Description**: Find all notes containing a specific tag.

### Input Schema
```json
{
  "type": "object",
  "properties": {
    "tag": {
      "type": "string",
      "description": "Tag to search for (with or without #)"
    }
  },
  "required": ["tag"]
}
```

### Output Schema
```json
{
  "type": "object",
  "properties": {
    "tag": {"type": "string"},
    "count": {"type": "integer"},
    "notes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "file": {"type": "string"},
          "absolute_path": {"type": "string"},
          "tag_locations": {
            "type": "object",
            "properties": {
              "frontmatter": {"type": "boolean"},
              "inline": {"type": "boolean"}
            }
          }
        }
      }
    }
  }
}
```

---

## Performance Expectations

| Operation | Vault Size | Expected Time |
|-----------|-----------|---------------|
| analyze_note_tags | Any | < 100ms |
| add_tag / remove_tag | Any | < 200ms |
| search_by_tag | 1,000 notes | < 3 seconds |
