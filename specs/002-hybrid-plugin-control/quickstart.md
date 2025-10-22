# Quickstart Guide: Hybrid Plugin Control Implementation

**Feature**: 002-hybrid-plugin-control
**For**: Developers implementing the hybrid architecture
**Time to Read**: 15 minutes

---

## Overview

This feature adds comprehensive Obsidian plugin control via a hybrid architecture:
- **Filesystem-native tools** (priority): Direct file manipulation, works offline
- **API-based tools** (when needed): Obsidian Local REST API for JavaScript execution and UI control

---

## Implementation Phases

### Phase 1: Filesystem-Native Core (Week 1-2)

**Priority Order:**
1. Tasks plugin metadata parsing
2. Dataview inline field extraction
3. Enhanced link tracking
4. Kanban board manipulation

**Start Here:** `src/tools/tasks.py`

**Steps:**
1. Create `src/utils/patterns.py` with compiled regex patterns:
   ```python
   import re

   # Tasks plugin patterns
   TASK_DUE_DATE = re.compile(r'[📅📆🗓] *(\d{4}-\d{2}-\d{2})$', re.UNICODE)
   TASK_PRIORITY = re.compile(r'(⏫|🔼|🔽|⏬)$', re.UNICODE)
   TASK_RECURRENCE = re.compile(r'🔁 *(every .+)$', re.UNICODE)
   # ... more patterns
   ```

2. Implement task parsing in `src/tools/tasks.py`:
   ```python
   from src.utils.patterns import TASK_DUE_DATE, TASK_PRIORITY
   from src.models.obsidian import Task
   from fastmcp import FastMCP

   mcp = FastMCP("obsidian-extended")

   @mcp.tool()
   def search_tasks_fs_tool(filters: dict = None) -> dict:
       """Search tasks by metadata (filesystem-native)"""
       # Implementation from research.md section 1
   ```

3. Register tools in `src/server.py`:
   ```python
   from src.tools.tasks import search_tasks_fs_tool, create_task_fs_tool
   # Tools auto-register via @mcp.tool() decorator
   ```

4. Write tests in `tests/unit/test_tasks.py`:
   ```python
   def test_parse_task_metadata():
       line = "- [ ] Task 📅 2025-10-30 ⏫"
       task = parse_task_line(line)
       assert task.due_date == date(2025, 10, 30)
       assert task.priority == "highest"
   ```

---

### Phase 2: API Integration Infrastructure (Week 3)

**Create API Client:** `src/utils/obsidian_api_client.py`

```python
import httpx
import os
from typing import Optional

class ObsidianAPIClient:
    """HTTP client for Obsidian Local REST API"""

    def __init__(self):
        self.base_url = os.getenv("OBSIDIAN_API_URL", "http://localhost:27124")
        self.api_key = os.getenv("OBSIDIAN_REST_API_KEY")
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        self.timeout = 30.0

    async def is_available(self) -> bool:
        """Check if API is reachable"""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    f"{self.base_url}/",
                    headers=self.headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except:
            return False

    async def execute_command(self, command_id: str) -> dict:
        """Execute Obsidian command by ID"""
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self.base_url}/commands/{command_id}/",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def search_simple(self, query: str, context_length: int = 100) -> list:
        """Execute simple text search"""
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self.base_url}/search/simple/",
                headers=self.headers,
                json={"query": query, "contextLength": context_length},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
```

**Add Availability Checking:** `src/utils/api_availability.py`

```python
from fastmcp.exceptions import McpError
from src.utils.obsidian_api_client import ObsidianAPIClient

_api_client = None

def get_api_client() -> ObsidianAPIClient:
    """Get singleton API client"""
    global _api_client
    if _api_client is None:
        _api_client = ObsidianAPIClient()
    return _api_client

async def require_api_available():
    """Raise error if API not available"""
    client = get_api_client()
    if not await client.is_available():
        raise McpError(
            error_code="API_UNAVAILABLE",
            message=(
                "This tool requires Obsidian to be running with the Local REST API plugin enabled. "
                "Please start Obsidian and ensure the plugin is active at http://localhost:27124"
            )
        )
```

---

### Phase 3: API-Based Tools (Week 4-5)

**Implementation Pattern for All API Tools:**

```python
from src.utils.api_availability import require_api_available, get_api_client
from fastmcp import FastMCP

mcp = FastMCP("obsidian-extended")

@mcp.tool()
async def execute_dataview_query_api_tool(query: str) -> dict:
    """
    Execute Dataview Query Language (DQL) query.

    Requires: Obsidian running with Local REST API plugin

    Args:
        query: Dataview query (e.g., "LIST FROM #project")

    Returns:
        Query results in structured format
    """
    await require_api_available()  # Raises if unavailable

    client = get_api_client()
    async with httpx.AsyncClient(verify=False) as http_client:
        response = await http_client.post(
            f"{client.base_url}/search/",
            headers={
                **client.headers,
                "Content-Type": "application/vnd.olrapi.dataview.dql+txt"
            },
            data=query,
            timeout=client.timeout
        )
        response.raise_for_status()
        return response.json()
```

---

## Data Models

**Add to:** `src/models/obsidian.py`

```python
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, Literal, List, Any

class Task(BaseModel):
    """Tasks plugin task with metadata"""
    content: str
    status: Literal["incomplete", "completed"]
    priority: Optional[Literal["highest", "high", "normal", "low", "lowest"]] = "normal"
    due_date: Optional[date] = None
    scheduled_date: Optional[date] = None
    start_date: Optional[date] = None
    done_date: Optional[date] = None
    recurrence: Optional[str] = None
    line_number: int
    source_file: str
    tags: List[str] = Field(default_factory=list)

class DataviewField(BaseModel):
    """Dataview inline field"""
    key: str
    value: Any
    canonical_key: str
    line_number: int
    syntax_type: Literal["full-line", "bracket", "paren"]
    source_file: str

class KanbanBoard(BaseModel):
    """Kanban board structure"""
    file_path: str
    columns: List["KanbanColumn"]
    settings: dict = Field(default_factory=dict)

class KanbanColumn(BaseModel):
    """Kanban column (heading)"""
    name: str
    cards: List["KanbanCard"]
    heading_level: int = 2
    line_number: int

class KanbanCard(BaseModel):
    """Kanban card (checkbox item)"""
    text: str
    status: Literal["incomplete", "completed"]
    due_date: Optional[date] = None
    tags: List[str] = Field(default_factory=list)
    subtasks: List["KanbanCard"] = Field(default_factory=list)
    indent_level: int = 0
    line_number: int

class CanvasNode(BaseModel):
    """Canvas node (element)"""
    id: str = Field(pattern=r'^[a-f0-9]{16}$')
    type: Literal["text", "file", "link", "group"]
    x: int
    y: int
    width: int
    height: int
    color: Optional[str] = None
    # Type-specific fields
    text: Optional[str] = None
    file: Optional[str] = None
    url: Optional[str] = None
    label: Optional[str] = None
```

---

## Configuration

**Environment Variables:**

```bash
# Existing (required)
export OBSIDIAN_VAULT_PATH="/path/to/your/vault"

# New (optional, for API features)
export OBSIDIAN_API_URL="http://localhost:27124"
export OBSIDIAN_REST_API_KEY="your-api-key-from-obsidian-settings"
```

**Claude Desktop Config:**

```json
{
  "mcpServers": {
    "obsidian-extended": {
      "command": "uv",
      "args": ["--directory", "/path/to/CustomObsidianMcp", "run", "obsidian-mcp"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/home/user/Obsidian/MyVault",
        "OBSIDIAN_API_URL": "http://localhost:27124",
        "OBSIDIAN_REST_API_KEY": "your-api-key"
      }
    }
  }
}
```

---

## Testing Strategy

### Filesystem Tests (Always Run)

```python
# tests/unit/test_tasks.py
def test_parse_task_metadata():
    """Test task parsing (no Obsidian needed)"""
    task_line = "- [ ] Review PR 📅 2025-10-30 ⏫"
    task = parse_task_line(task_line)

    assert task.content == "Review PR"
    assert task.due_date == date(2025, 10, 30)
    assert task.priority == "highest"
    assert task.status == "incomplete"

def test_create_task_with_metadata():
    """Test task creation with emoji formatting"""
    task = Task(
        content="New task",
        priority="high",
        due_date=date(2025, 10, 30),
        status="incomplete",
        line_number=1,
        source_file="test.md"
    )

    formatted = format_task_line(task)
    assert formatted == "- [ ] New task 🔼 📅 2025-10-30"
```

### API Tests (Conditional)

```python
# tests/unit/test_dataview_api.py
import pytest
from src.utils.api_availability import get_api_client

@pytest.fixture
async def api_available():
    """Check API availability"""
    client = get_api_client()
    return await client.is_available()

@pytest.mark.asyncio
@pytest.mark.skipif(
    not await get_api_client().is_available(),
    reason="Requires Obsidian with REST API"
)
async def test_execute_dataview_query():
    """Test DQL query execution"""
    result = await execute_dataview_query_api_tool("LIST FROM #test")
    assert isinstance(result, dict)
    assert "results" in result
```

### Integration Tests

```python
# tests/integration/test_hybrid_workflow.py
@pytest.mark.integration
async def test_task_to_kanban_workflow(temp_vault):
    """Test creating task and moving to kanban"""
    # 1. Create task (filesystem)
    await create_task_fs_tool(
        file_path="tasks.md",
        task_content="Test task",
        priority="high"
    )

    # 2. Parse kanban board (filesystem)
    board = await parse_kanban_board_fs_tool("board.md")

    # 3. Add card from task (filesystem)
    await add_kanban_card_fs_tool(
        board_path="board.md",
        column="To Do",
        card_text="Test task from tasks.md"
    )

    # Verify
    updated_board = await parse_kanban_board_fs_tool("board.md")
    assert len(updated_board.columns[0].cards) == 1
```

---

## Common Patterns

### Pattern 1: Regex-Based Parsing

```python
import re

# Module-level compiled patterns
PATTERN = re.compile(r'pattern$', re.UNICODE | re.MULTILINE)

def parse_entity(content: str) -> dict:
    """Parse entity from content"""
    matches = {}
    for pattern_name, pattern in PATTERNS.items():
        match = pattern.search(content)
        if match:
            matches[pattern_name] = match.group(1)
            content = content[:match.start()].rstrip()
    return matches
```

### Pattern 2: Line-Based File Manipulation

```python
from pathlib import Path

def update_line(file_path: str, line_number: int, new_content: str):
    """Update specific line in file"""
    path = Path(file_path)
    lines = path.read_text(encoding='utf-8').splitlines(keepends=True)

    if line_number < 1 or line_number > len(lines):
        raise ValueError(f"Line {line_number} out of range")

    lines[line_number - 1] = new_content + '\n'
    path.write_text(''.join(lines), encoding='utf-8')
```

### Pattern 3: JSON Canvas Manipulation

```python
import json
import secrets

def generate_canvas_id() -> str:
    """Generate 16-char hex ID"""
    return secrets.token_hex(8)

def create_canvas_node(node_type: str, x: int, y: int, **kwargs) -> dict:
    """Create canvas node"""
    node = {
        "id": generate_canvas_id(),
        "type": node_type,
        "x": x,
        "y": y,
        "width": kwargs.get("width", 250),
        "height": kwargs.get("height", 160)
    }
    node.update(kwargs)
    return node
```

---

## Performance Tips

1. **Compile regex once** at module level
2. **Stream files** for vault-wide operations
3. **Use generators** for lazy evaluation
4. **Cache with mtime** checking for repeated access
5. **Timeout API calls** at 30s default
6. **Batch operations** when possible

---

## Debugging

**Enable Debug Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Test API Connection:**
```bash
curl --insecure -H "Authorization: Bearer YOUR_KEY" \
  http://localhost:27124/
```

**Check Tool Registration:**
```python
# In src/server.py
mcp = FastMCP("obsidian-extended")
print(mcp.list_tools())  # See all registered tools
```

---

## Next Steps

1. ✅ Complete Phase 0 (Research) - DONE
2. ✅ Complete Phase 1 (Design) - DONE
3. → Run `/speckit.tasks` to generate implementation tasks
4. → Follow task dependency order from tasks.md
5. → Implement filesystem tools first (Week 1-2)
6. → Add API infrastructure (Week 3)
7. → Implement API tools (Week 4-5)
8. → Testing and documentation (Week 6-7)

**Total Estimated Time:** 6-7 weeks for complete implementation

---

## Resources

- **Research**: [research.md](./research.md)
- **Data Model**: [data-model.md](./data-model.md)
- **Contracts**: [contracts/](./contracts/)
- **Spec**: [spec.md](./spec.md)
- **Plan**: [plan.md](./plan.md)

**Questions?** Refer to the comprehensive research document for implementation details on any component.
