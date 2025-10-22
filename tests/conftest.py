"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import date
from unittest.mock import AsyncMock, MagicMock

# Add parent directory to path so we can import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.api_availability import get_api_client
from src.models.obsidian import Task, DataviewField, KanbanBoard, KanbanColumn, KanbanCard


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary Obsidian vault for testing.

    Returns:
        Path: Path to temporary vault directory
    """
    vault_path = tmp_path / "test_vault"
    vault_path.mkdir()

    # Create some basic structure
    (vault_path / "notes").mkdir()
    (vault_path / "templates").mkdir()
    (vault_path / "projects").mkdir()

    # Create sample files for testing
    (vault_path / "notes" / "test-note.md").write_text(
        "# Test Note\n\nThis is a test note.\n\n- [ ] Sample task 📅 2025-10-30\n",
        encoding="utf-8"
    )

    (vault_path / "projects" / "project-alpha.md").write_text(
        "# Project Alpha\n\nstatus:: active\npriority:: high\n\n- [ ] Review PR ⏫ 📅 2025-10-25\n",
        encoding="utf-8"
    )

    yield vault_path

    # Cleanup is automatic with tmp_path
    shutil.rmtree(vault_path, ignore_errors=True)


@pytest.fixture
def sample_tasks():
    """Provide sample Task objects for testing.

    Returns:
        List[Task]: List of sample tasks with various metadata
    """
    return [
        Task(
            content="Review PR #123",
            status="incomplete",
            priority="high",
            due_date=date(2025, 10, 25),
            line_number=1,
            source_file="work/tasks.md",
            tags=["work", "review"]
        ),
        Task(
            content="Write documentation",
            status="incomplete",
            priority="normal",
            due_date=date(2025, 10, 30),
            scheduled_date=date(2025, 10, 22),
            line_number=2,
            source_file="work/tasks.md",
            tags=["documentation"]
        ),
        Task(
            content="Completed task",
            status="completed",
            priority="highest",
            done_date=date(2025, 10, 20),
            line_number=3,
            source_file="work/done.md",
            tags=[]
        ),
        Task(
            content="Recurring task",
            status="incomplete",
            priority="low",
            recurrence="every week",
            line_number=4,
            source_file="personal/recurring.md",
            tags=["personal"]
        )
    ]


@pytest.fixture
def sample_dataview_fields():
    """Provide sample DataviewField objects for testing.

    Returns:
        List[DataviewField]: List of sample Dataview fields
    """
    return [
        DataviewField(
            key="status",
            value="active",
            canonical_key="status",
            line_number=1,
            syntax_type="full-line",
            source_file="project.md",
            value_type="string"
        ),
        DataviewField(
            key="priority",
            value="high",
            canonical_key="priority",
            line_number=2,
            syntax_type="bracket",
            source_file="project.md",
            value_type="string"
        ),
        DataviewField(
            key="completion",
            value=75,
            canonical_key="completion",
            line_number=3,
            syntax_type="paren",
            source_file="project.md",
            value_type="number"
        )
    ]


@pytest.fixture
def sample_kanban_board():
    """Provide a sample KanbanBoard for testing.

    Returns:
        KanbanBoard: Sample Kanban board with columns and cards
    """
    return KanbanBoard(
        file_path="board.md",
        columns=[
            KanbanColumn(
                name="To Do",
                cards=[
                    KanbanCard(
                        text="Task 1",
                        status="incomplete",
                        line_number=3,
                        tags=["urgent"]
                    ),
                    KanbanCard(
                        text="Task 2",
                        status="incomplete",
                        line_number=4,
                        due_date=date(2025, 10, 30)
                    )
                ],
                line_number=1
            ),
            KanbanColumn(
                name="In Progress",
                cards=[
                    KanbanCard(
                        text="Task 3",
                        status="incomplete",
                        line_number=7,
                        tags=["development"]
                    )
                ],
                line_number=5
            ),
            KanbanColumn(
                name="Done",
                cards=[
                    KanbanCard(
                        text="Completed task",
                        status="completed",
                        line_number=10
                    )
                ],
                line_number=8
            )
        ]
    )


@pytest.fixture
async def api_available():
    """Check if Obsidian Local REST API is available.

    Returns:
        bool: True if API is reachable, False otherwise

    Note:
        Use this to conditionally skip tests that require the API.
    """
    client = get_api_client()
    return await client.is_available()


@pytest.fixture
def mock_api_client():
    """Create a mock ObsidianAPIClient for testing without Obsidian.

    Returns:
        AsyncMock: Mock API client with common methods
    """
    mock_client = AsyncMock()

    # Configure common method return values
    mock_client.is_available.return_value = True
    mock_client.execute_command.return_value = {"success": True}
    mock_client.search_simple.return_value = []
    mock_client.execute_dataview_query.return_value = {"values": []}
    mock_client.list_commands.return_value = [
        {"id": "editor:toggle-bold", "name": "Toggle bold"},
        {"id": "editor:toggle-italic", "name": "Toggle italic"}
    ]
    mock_client.get_active_file.return_value = {"path": "test.md"}
    mock_client.get_file.return_value = {"content": "# Test\n\nContent"}
    mock_client.put_file.return_value = {"success": True}

    return mock_client