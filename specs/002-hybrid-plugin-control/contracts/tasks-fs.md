# MCP Tool Contracts: Tasks Plugin (Filesystem-Native)

**Category**: Filesystem-Native
**Requires Obsidian**: No
**Performance Target**: <3s for 1,000 notes

---

## Tool: `search_tasks_fs_tool`

**Purpose**: Search and filter tasks by metadata across the entire vault

**Input Schema:**
```typescript
{
  vault_path?: string;              // Optional, defaults to OBSIDIAN_VAULT_PATH
  filters?: {
    status?: "incomplete" | "completed" | "all";
    priority?: "highest" | "high" | "normal" | "low" | "lowest";
    due_before?: string;            // YYYY-MM-DD
    due_after?: string;
    due_within_days?: number;       // Relative to today
    has_recurrence?: boolean;
    tag?: string;                   // Filter by specific tag
  };
  limit?: number;                   // Max results, default 100
  sort_by?: "due_date" | "priority" | "file" | "line_number";
  sort_order?: "asc" | "desc";
}
```

**Output Schema:**
```typescript
{
  tasks: Array<{
    content: string;
    status: "incomplete" | "completed";
    priority: "highest" | "high" | "normal" | "low" | "lowest";
    due_date: string | null;        // YYYY-MM-DD
    scheduled_date: string | null;
    start_date: string | null;
    done_date: string | null;
    recurrence: string | null;
    tags: string[];
    source_file: string;            // Relative path
    absolute_path: string;
    line_number: number;
  }>;
  total_found: number;
  truncated: boolean;               // True if results limited
}
```

**Errors:**
- `VAULT_NOT_FOUND`: Vault path doesn't exist
- `INVALID_DATE_FORMAT`: Date filter not YYYY-MM-DD
- `INVALID_FILTER`: Unrecognized filter parameter

**Example:**
```json
// Input
{
  "filters": {
    "status": "incomplete",
    "due_within_days": 7,
    "priority": "high"
  },
  "limit": 10
}

// Output
{
  "tasks": [
    {
      "content": "Review PR #123",
      "status": "incomplete",
      "priority": "high",
      "due_date": "2025-10-25",
      "source_file": "work/tasks.md",
      "line_number": 42
    }
  ],
  "total_found": 3,
  "truncated": false
}
```

---

## Tool: `create_task_fs_tool`

**Purpose**: Create a new task with metadata in a specified note

**Input Schema:**
```typescript
{
  file_path: string;                // Relative or absolute
  task_content: string;
  priority?: "highest" | "high" | "normal" | "low" | "lowest";
  due_date?: string;                // YYYY-MM-DD
  scheduled_date?: string;
  start_date?: string;
  recurrence?: string;              // "every [pattern]"
  insert_at?: "end" | "top" | "after_heading";
  heading?: string;                 // If insert_at="after_heading"
}
```

**Output Schema:**
```typescript
{
  success: boolean;
  task_line: string;                // Generated task line with emojis
  line_number: number;              // Where task was inserted
  file_path: string;
}
```

**Errors:**
- `FILE_NOT_FOUND`: Target file doesn't exist
- `HEADING_NOT_FOUND`: Specified heading not found
- `INVALID_DATE`: Date not in YYYY-MM-DD format
- `INVALID_RECURRENCE`: Recurrence doesn't start with "every"

**Example:**
```json
// Input
{
  "file_path": "projects/project-alpha.md",
  "task_content": "Complete API documentation",
  "priority": "high",
  "due_date": "2025-10-30",
  "recurrence": "every week"
}

// Output
{
  "success": true,
  "task_line": "- [ ] Complete API documentation 🔼 📅 2025-10-30 🔁 every week",
  "line_number": 25,
  "file_path": "projects/project-alpha.md"
}
```

---

## Tool: `toggle_task_status_fs_tool`

**Purpose**: Toggle task completion status (incomplete ↔ completed)

**Input Schema:**
```typescript
{
  file_path: string;
  line_number: number;              // Line containing the task
  add_done_date?: boolean;          // Add ✅ date on completion (default: false)
}
```

**Output Schema:**
```typescript
{
  success: boolean;
  new_status: "incomplete" | "completed";
  done_date: string | null;         // Added if add_done_date=true
  updated_line: string;
}
```

**Errors:**
- `FILE_NOT_FOUND`: Target file doesn't exist
- `LINE_OUT_OF_RANGE`: Line number exceeds file length
- `NOT_A_TASK`: Line doesn't contain task checkbox

**Example:**
```json
// Input
{
  "file_path": "work/tasks.md",
  "line_number": 42,
  "add_done_date": true
}

// Output
{
  "success": true,
  "new_status": "completed",
  "done_date": "2025-10-22",
  "updated_line": "- [x] Review PR #123 🔼 📅 2025-10-25 ✅ 2025-10-22"
}
```

---

## Tool: `update_task_metadata_fs_tool`

**Purpose**: Update task metadata (due date, priority, etc.) without changing content

**Input Schema:**
```typescript
{
  file_path: string;
  line_number: number;
  updates: {
    priority?: "highest" | "high" | "normal" | "low" | "lowest" | null;
    due_date?: string | null;       // Set or clear
    scheduled_date?: string | null;
    start_date?: string | null;
    recurrence?: string | null;
  };
}
```

**Output Schema:**
```typescript
{
  success: boolean;
  updated_line: string;
  changes_made: string[];           // List of fields updated
}
```

**Errors:**
- `FILE_NOT_FOUND`: Target file doesn't exist
- `LINE_OUT_OF_RANGE`: Line number invalid
- `NOT_A_TASK`: Line doesn't contain task
- `INVALID_DATE`: Date format incorrect

**Example:**
```json
// Input
{
  "file_path": "work/tasks.md",
  "line_number": 42,
  "updates": {
    "priority": "highest",
    "due_date": "2025-10-28"
  }
}

// Output
{
  "success": true,
  "updated_line": "- [ ] Review PR #123 ⏫ 📅 2025-10-28",
  "changes_made": ["priority", "due_date"]
}
```

---

## Tool: `get_task_statistics_fs_tool`

**Purpose**: Get aggregate task statistics for a note or entire vault

**Input Schema:**
```typescript
{
  scope: "note" | "vault";
  file_path?: string;               // Required if scope="note"
  group_by?: "priority" | "status" | "file";
}
```

**Output Schema:**
```typescript
{
  total_tasks: number;
  incomplete_tasks: number;
  completed_tasks: number;
  by_priority: {
    highest: number;
    high: number;
    normal: number;
    low: number;
    lowest: number;
  };
  overdue_tasks: number;            // Tasks with due_date < today
  upcoming_tasks: number;           // Tasks due within 7 days
  recurring_tasks: number;
  grouped_data?: Array<{           // If group_by specified
    group_key: string;
    count: number;
  }>;
}
```

**Example:**
```json
// Input
{
  "scope": "vault",
  "group_by": "priority"
}

// Output
{
  "total_tasks": 127,
  "incomplete_tasks": 89,
  "completed_tasks": 38,
  "by_priority": {
    "highest": 12,
    "high": 34,
    "normal": 65,
    "low": 10,
    "lowest": 6
  },
  "overdue_tasks": 15,
  "upcoming_tasks": 23,
  "recurring_tasks": 8
}
```

---

## Implementation Notes

### Parsing Algorithm

1. **Scan vault for tasks:**
   - Read all .md files
   - Filter lines starting with `- [ ]` or `- [x]`
   - Extract emoji metadata from end of line

2. **Metadata extraction (right-to-left):**
   ```python
   remaining_line = task_line
   metadata = {}

   # Extract each emoji pattern from end
   for pattern, key in PATTERNS:
       match = re.search(pattern, remaining_line)
       if match:
           metadata[key] = match.group(1)
           remaining_line = remaining_line[:match.start()].rstrip()

   # Remaining text is task content
   metadata['content'] = remaining_line
   ```

3. **Filtering:**
   - Apply filters in-memory after parsing
   - Use indexed search for large vaults (future optimization)

### Performance Optimizations

- Compile regex patterns at module level
- Use generators for lazy evaluation
- Stream process files (don't load entire vault in memory)
- Cache parsed results with mtime checking (future)

### Edge Case Handling

- **Emoji in description**: Safe due to `$` anchor
- **Malformed dates**: Ignore, log warning
- **Multiple priorities**: Last one wins
- **Tasks without checkbox**: Skip as non-task lines
- **Unicode normalization**: Handle emoji variants

---

## Testing Requirements

**Unit Tests:**
- Parse task lines with all metadata combinations
- Filter tasks by each criterion
- Create tasks with emoji formatting
- Toggle task status correctly
- Update metadata preserves content

**Integration Tests:**
- Search across multi-file vault
- Handle concurrent task modifications
- Performance test with 1,000+ tasks

**Edge Case Tests:**
- Malformed emoji metadata
- Empty task content
- Very long task descriptions
- Tasks in code blocks (should ignore)
- Unicode edge cases (emoji variants)
