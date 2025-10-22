"""Unit tests for Kanban filesystem-native tools."""

import pytest
from datetime import date
from pathlib import Path

from src.tools.kanban import (
    parse_card_metadata,
    format_kanban_card,
    parse_kanban_structure,
    parse_kanban_board_fs_tool,
    add_kanban_card_fs_tool,
    move_kanban_card_fs_tool,
    toggle_kanban_card_fs_tool,
    get_kanban_statistics_fs_tool,
)
from src.models.obsidian import KanbanCard


class TestParseCardMetadata:
    """Tests for parse_card_metadata function."""

    def test_parse_due_date(self):
        """Test parsing due date from card."""
        metadata = parse_card_metadata("Task with due date @{2025-10-30}")
        assert metadata["due_date"] == date(2025, 10, 30)

    def test_parse_tags(self):
        """Test parsing tags from card."""
        metadata = parse_card_metadata("Task with #urgent #work tags")
        assert "urgent" in metadata["tags"]
        assert "work" in metadata["tags"]

    def test_parse_wikilinks(self):
        """Test parsing wikilinks from card."""
        metadata = parse_card_metadata("Task with [[Note1]] and [[Note2]]")
        assert "Note1" in metadata["wikilinks"]
        assert "Note2" in metadata["wikilinks"]

    def test_parse_all_metadata(self):
        """Test parsing all metadata types."""
        metadata = parse_card_metadata("Task #urgent [[Project]] @{2025-10-30}")
        assert metadata["due_date"] == date(2025, 10, 30)
        assert "urgent" in metadata["tags"]
        assert "Project" in metadata["wikilinks"]


class TestKanbanParsing:
    """Tests for Kanban board parsing."""

    def test_parse_simple_board(self):
        """Test parsing simple board with columns."""
        content = """## To Do

- [ ] Task 1
- [ ] Task 2

## Done

- [x] Completed task
"""
        board = parse_kanban_structure(content, "board.md")

        assert len(board.columns) == 2
        assert board.columns[0].name == "To Do"
        assert board.columns[0].card_count == 2
        assert board.columns[1].name == "Done"
        assert board.columns[1].card_count == 1

    def test_parse_nested_subtasks(self):
        """Test parsing cards with subtasks."""
        content = """## In Progress

- [ ] Main task
  - [ ] Subtask 1
  - [ ] Subtask 2
"""
        board = parse_kanban_structure(content, "board.md")

        assert len(board.columns) == 1
        assert len(board.columns[0].cards) == 1
        assert len(board.columns[0].cards[0].subtasks) == 2

    def test_parse_card_with_metadata(self):
        """Test parsing card with due date and tags."""
        content = """## To Do

- [ ] Task with metadata #urgent @{2025-10-30}
"""
        board = parse_kanban_structure(content, "board.md")

        card = board.columns[0].cards[0]
        assert card.due_date == date(2025, 10, 30)
        assert "urgent" in card.tags


class TestToolFunctions:
    """Integration tests for tool functions."""

    @pytest.mark.asyncio
    async def test_parse_kanban_board_fs_tool(self, temp_vault):
        """Test parse_kanban_board_fs_tool."""
        file_path = "board.md"
        (temp_vault / file_path).write_text(
            """## To Do

- [ ] Task 1
- [ ] Task 2

## Done

- [x] Completed
""",
            encoding="utf-8",
        )

        result = await parse_kanban_board_fs_tool(
            file_path=file_path, vault_path=str(temp_vault)
        )

        assert result["total_cards"] == 3
        assert len(result["columns"]) == 2
        assert result["columns"][0]["name"] == "To Do"
        assert result["columns"][0]["card_count"] == 2

    @pytest.mark.asyncio
    async def test_add_kanban_card_fs_tool(self, temp_vault):
        """Test add_kanban_card_fs_tool."""
        file_path = "board.md"
        (temp_vault / file_path).write_text(
            """## To Do

- [ ] Existing task

## Done
""",
            encoding="utf-8",
        )

        result = await add_kanban_card_fs_tool(
            file_path=file_path,
            column_name="To Do",
            card_text="New task",
            vault_path=str(temp_vault),
        )

        assert result["success"] is True
        assert result["column"] == "To Do"

        # Verify file was updated
        content = (temp_vault / file_path).read_text(encoding="utf-8")
        assert "New task" in content

    @pytest.mark.asyncio
    async def test_move_kanban_card_fs_tool(self, temp_vault):
        """Test move_kanban_card_fs_tool."""
        file_path = "board.md"
        (temp_vault / file_path).write_text(
            """## To Do

- [ ] Task to move

## Done
""",
            encoding="utf-8",
        )

        result = await move_kanban_card_fs_tool(
            file_path=file_path,
            card_text="Task to move",
            from_column="To Do",
            to_column="Done",
            vault_path=str(temp_vault),
        )

        assert result["success"] is True
        assert result["from_column"] == "To Do"
        assert result["to_column"] == "Done"

        # Verify move
        content = (temp_vault / file_path).read_text(encoding="utf-8")
        lines = content.split("\n")

        # Task should be under Done section
        done_idx = next(i for i, line in enumerate(lines) if "## Done" in line)
        task_idx = next(i for i, line in enumerate(lines) if "Task to move" in line)
        assert task_idx > done_idx

    @pytest.mark.asyncio
    async def test_toggle_kanban_card_fs_tool(self, temp_vault):
        """Test toggle_kanban_card_fs_tool."""
        file_path = "board.md"
        (temp_vault / file_path).write_text(
            """## To Do

- [ ] Task to toggle
""",
            encoding="utf-8",
        )

        result = await toggle_kanban_card_fs_tool(
            file_path=file_path,
            card_text="Task to toggle",
            vault_path=str(temp_vault),
        )

        assert result["success"] is True
        assert result["new_status"] == "completed"

        # Verify toggle
        content = (temp_vault / file_path).read_text(encoding="utf-8")
        assert "- [x] Task to toggle" in content

    @pytest.mark.asyncio
    async def test_get_kanban_statistics_fs_tool(self, temp_vault):
        """Test get_kanban_statistics_fs_tool."""
        file_path = "board.md"
        (temp_vault / file_path).write_text(
            """## To Do

- [ ] Task 1
- [ ] Task 2

## Done

- [x] Completed 1
- [x] Completed 2
- [x] Completed 3
""",
            encoding="utf-8",
        )

        result = await get_kanban_statistics_fs_tool(
            file_path=file_path, vault_path=str(temp_vault)
        )

        assert result["total_cards"] == 5
        assert result["total_completed"] == 3
        assert result["total_incomplete"] == 2
        assert result["column_count"] == 2
        assert result["overall_completion_rate"] == 60.0
