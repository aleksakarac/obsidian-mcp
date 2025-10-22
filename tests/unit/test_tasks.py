"""Unit tests for Tasks plugin filesystem-native tools."""

import pytest
from datetime import date, timedelta
from pathlib import Path

from src.tools.tasks import (
    parse_task_line,
    format_task_line,
    filter_tasks,
    sort_tasks,
    scan_vault_for_tasks,
    search_tasks_fs_tool,
    create_task_fs_tool,
    toggle_task_status_fs_tool,
    update_task_metadata_fs_tool,
    get_task_statistics_fs_tool,
)
from src.models.obsidian import Task


class TestParseTaskLine:
    """Tests for parse_task_line function."""

    def test_parse_simple_incomplete_task(self):
        """Test parsing a simple incomplete task."""
        line = "- [ ] Write documentation"
        task = parse_task_line(line, 1, "test.md")

        assert task is not None
        assert task.content == "Write documentation"
        assert task.status == "incomplete"
        assert task.priority == "normal"
        assert task.line_number == 1
        assert task.source_file == "test.md"

    def test_parse_completed_task(self):
        """Test parsing a completed task."""
        line = "- [x] Completed task"
        task = parse_task_line(line, 5, "done.md")

        assert task is not None
        assert task.content == "Completed task"
        assert task.status == "completed"

    def test_parse_task_with_due_date(self):
        """Test parsing task with due date emoji."""
        line = "- [ ] Review PR 📅 2025-10-30"
        task = parse_task_line(line, 1, "test.md")

        assert task is not None
        assert task.content == "Review PR"
        assert task.due_date == date(2025, 10, 30)

    def test_parse_task_with_priority(self):
        """Test parsing task with priority emoji."""
        test_cases = [
            ("- [ ] Urgent task ⏫", "highest"),
            ("- [ ] Important task 🔼", "high"),
            ("- [ ] Low priority 🔽", "low"),
            ("- [ ] Lowest priority ⏬", "lowest"),
        ]

        for line, expected_priority in test_cases:
            task = parse_task_line(line, 1, "test.md")
            assert task is not None
            assert task.priority == expected_priority

    def test_parse_task_with_all_metadata(self):
        """Test parsing task with complete metadata."""
        line = "- [ ] Complex task 🛫 2025-10-20 ⏳ 2025-10-25 📅 2025-10-30 ⏫ 🔁 every week"
        task = parse_task_line(line, 1, "test.md")

        assert task is not None
        assert task.content == "Complex task"
        assert task.start_date == date(2025, 10, 20)
        assert task.scheduled_date == date(2025, 10, 25)
        assert task.due_date == date(2025, 10, 30)
        assert task.priority == "highest"
        assert task.recurrence == "every week"

    def test_parse_task_with_tags(self):
        """Test parsing task with tags."""
        line = "- [ ] Task with #project #urgent tags 📅 2025-10-30"
        task = parse_task_line(line, 1, "test.md")

        assert task is not None
        assert "project" in task.tags
        assert "urgent" in task.tags

    def test_parse_non_task_line(self):
        """Test that non-task lines return None."""
        lines = [
            "This is just text",
            "# Heading",
            "- Regular list item",
            "",
        ]

        for line in lines:
            task = parse_task_line(line, 1, "test.md")
            assert task is None

    def test_parse_task_with_indentation(self):
        """Test parsing task with indentation (subtask)."""
        line = "  - [ ] Subtask item"
        task = parse_task_line(line, 1, "test.md")

        assert task is not None
        assert task.content == "Subtask item"


class TestFormatTaskLine:
    """Tests for format_task_line function."""

    def test_format_simple_task(self):
        """Test formatting a simple task."""
        task = Task(
            content="Simple task",
            status="incomplete",
            priority="normal",
            line_number=1,
            source_file="test.md",
        )

        line = format_task_line(task)
        assert line == "- [ ] Simple task"

    def test_format_completed_task(self):
        """Test formatting a completed task."""
        task = Task(
            content="Done task",
            status="completed",
            priority="normal",
            line_number=1,
            source_file="test.md",
        )

        line = format_task_line(task)
        assert line == "- [x] Done task"

    def test_format_task_with_priority(self):
        """Test formatting task with priority."""
        task = Task(
            content="Important task",
            status="incomplete",
            priority="high",
            line_number=1,
            source_file="test.md",
        )

        line = format_task_line(task)
        assert "🔼" in line
        assert line == "- [ ] Important task 🔼"

    def test_format_task_with_dates(self):
        """Test formatting task with multiple dates."""
        task = Task(
            content="Task with dates",
            status="incomplete",
            priority="normal",
            start_date=date(2025, 10, 20),
            scheduled_date=date(2025, 10, 25),
            due_date=date(2025, 10, 30),
            line_number=1,
            source_file="test.md",
        )

        line = format_task_line(task)
        assert "🛫 2025-10-20" in line
        assert "⏳ 2025-10-25" in line
        assert "📅 2025-10-30" in line

    def test_format_task_with_recurrence(self):
        """Test formatting task with recurrence."""
        task = Task(
            content="Recurring task",
            status="incomplete",
            priority="normal",
            recurrence="every week",
            line_number=1,
            source_file="test.md",
        )

        line = format_task_line(task)
        assert "🔁 every week" in line

    def test_roundtrip_parse_format(self):
        """Test that parsing and formatting are inverse operations."""
        original_line = "- [ ] Complex task 🛫 2025-10-20 📅 2025-10-30 ⏫ 🔁 every day"
        task = parse_task_line(original_line, 1, "test.md")
        formatted_line = format_task_line(task)

        # Parse again to verify
        task2 = parse_task_line(formatted_line, 1, "test.md")

        assert task.content == task2.content
        assert task.status == task2.status
        assert task.priority == task2.priority
        assert task.start_date == task2.start_date
        assert task.due_date == task2.due_date
        assert task.recurrence == task2.recurrence


class TestFilterTasks:
    """Tests for filter_tasks function."""

    @pytest.fixture
    def task_list(self):
        """Create a list of sample tasks for filtering."""
        today = date.today()
        return [
            Task(
                content="Overdue task",
                status="incomplete",
                priority="high",
                due_date=today - timedelta(days=5),
                line_number=1,
                source_file="a.md",
                tags=["work"],
            ),
            Task(
                content="Due today",
                status="incomplete",
                priority="normal",
                due_date=today,
                line_number=2,
                source_file="a.md",
                tags=["work"],
            ),
            Task(
                content="Due next week",
                status="incomplete",
                priority="low",
                due_date=today + timedelta(days=7),
                line_number=3,
                source_file="b.md",
                tags=["personal"],
            ),
            Task(
                content="Completed task",
                status="completed",
                priority="highest",
                done_date=today - timedelta(days=1),
                line_number=4,
                source_file="b.md",
                tags=["work"],
            ),
            Task(
                content="Recurring task",
                status="incomplete",
                priority="normal",
                recurrence="every week",
                line_number=5,
                source_file="c.md",
                tags=["personal"],
            ),
        ]

    def test_filter_by_status(self, task_list):
        """Test filtering by status."""
        incomplete = filter_tasks(task_list, status="incomplete")
        assert len(incomplete) == 4

        completed = filter_tasks(task_list, status="completed")
        assert len(completed) == 1

    def test_filter_by_priority(self, task_list):
        """Test filtering by priority."""
        high_priority = filter_tasks(task_list, priority="high")
        assert len(high_priority) == 1
        assert high_priority[0].content == "Overdue task"

    def test_filter_by_due_date_range(self, task_list):
        """Test filtering by due date range."""
        today = date.today()
        upcoming = filter_tasks(
            task_list, due_after=today - timedelta(days=1), due_before=today + timedelta(days=10)
        )
        assert len(upcoming) >= 2

    def test_filter_by_due_within_days(self, task_list):
        """Test filtering by due within N days."""
        due_soon = filter_tasks(task_list, due_within_days=7, status="incomplete")
        assert len(due_soon) >= 2

    def test_filter_by_recurrence(self, task_list):
        """Test filtering by recurrence."""
        recurring = filter_tasks(task_list, has_recurrence=True)
        assert len(recurring) == 1
        assert recurring[0].recurrence == "every week"

        non_recurring = filter_tasks(task_list, has_recurrence=False)
        assert len(non_recurring) == 4

    def test_filter_by_tag(self, task_list):
        """Test filtering by tag."""
        work_tasks = filter_tasks(task_list, tag="work")
        assert len(work_tasks) == 3

        personal_tasks = filter_tasks(task_list, tag="personal")
        assert len(personal_tasks) == 2

    def test_multiple_filters(self, task_list):
        """Test combining multiple filters."""
        filtered = filter_tasks(
            task_list, status="incomplete", priority="normal", has_recurrence=False
        )
        assert len(filtered) == 1
        assert filtered[0].content == "Due today"


class TestSortTasks:
    """Tests for sort_tasks function."""

    @pytest.fixture
    def unsorted_tasks(self):
        """Create unsorted task list."""
        today = date.today()
        return [
            Task(
                content="Task C",
                status="incomplete",
                priority="low",
                due_date=today + timedelta(days=10),
                line_number=3,
                source_file="z.md",
            ),
            Task(
                content="Task A",
                status="incomplete",
                priority="highest",
                due_date=today,
                line_number=1,
                source_file="a.md",
            ),
            Task(
                content="Task B",
                status="incomplete",
                priority="high",
                due_date=today + timedelta(days=5),
                line_number=2,
                source_file="b.md",
            ),
        ]

    def test_sort_by_due_date_asc(self, unsorted_tasks):
        """Test sorting by due date ascending."""
        sorted_tasks = sort_tasks(unsorted_tasks, sort_by="due_date", sort_order="asc")
        assert sorted_tasks[0].content == "Task A"
        assert sorted_tasks[1].content == "Task B"
        assert sorted_tasks[2].content == "Task C"

    def test_sort_by_due_date_desc(self, unsorted_tasks):
        """Test sorting by due date descending."""
        sorted_tasks = sort_tasks(unsorted_tasks, sort_by="due_date", sort_order="desc")
        assert sorted_tasks[0].content == "Task C"
        assert sorted_tasks[-1].content == "Task A"

    def test_sort_by_priority(self, unsorted_tasks):
        """Test sorting by priority."""
        sorted_tasks = sort_tasks(unsorted_tasks, sort_by="priority", sort_order="asc")
        assert sorted_tasks[0].priority == "highest"
        assert sorted_tasks[1].priority == "high"
        assert sorted_tasks[2].priority == "low"

    def test_sort_by_file(self, unsorted_tasks):
        """Test sorting by file path."""
        sorted_tasks = sort_tasks(unsorted_tasks, sort_by="file", sort_order="asc")
        assert sorted_tasks[0].source_file == "a.md"
        assert sorted_tasks[1].source_file == "b.md"
        assert sorted_tasks[2].source_file == "z.md"


class TestToolFunctions:
    """Integration tests for tool functions."""

    @pytest.mark.asyncio
    async def test_search_tasks_fs_tool(self, temp_vault):
        """Test search_tasks_fs_tool."""
        # Create test files with tasks
        (temp_vault / "work.md").write_text(
            "# Work Tasks\n\n- [ ] Review PR ⏫ 📅 2025-10-25\n- [x] Deploy app\n",
            encoding="utf-8",
        )
        (temp_vault / "personal.md").write_text(
            "# Personal\n\n- [ ] Buy groceries 📅 2025-10-22\n", encoding="utf-8"
        )

        result = await search_tasks_fs_tool(
            vault_path=str(temp_vault),
            filters={"status": "incomplete"},
            limit=100,
        )

        assert result["total_found"] >= 2
        assert not result["truncated"]
        assert len(result["tasks"]) >= 2

    @pytest.mark.asyncio
    async def test_create_task_fs_tool(self, temp_vault):
        """Test create_task_fs_tool."""
        file_path = "notes/new-tasks.md"

        result = await create_task_fs_tool(
            file_path=file_path,
            task_content="New task with metadata",
            priority="high",
            due_date="2025-11-01",
            vault_path=str(temp_vault),
        )

        assert result["success"] is True
        assert result["line_number"] == 1

        # Verify file was created
        created_file = temp_vault / file_path
        assert created_file.exists()
        content = created_file.read_text(encoding="utf-8")
        assert "New task with metadata" in content
        assert "🔼" in content
        assert "2025-11-01" in content

    @pytest.mark.asyncio
    async def test_toggle_task_status_fs_tool(self, temp_vault):
        """Test toggle_task_status_fs_tool."""
        file_path = "tasks.md"
        (temp_vault / file_path).write_text("- [ ] Task to toggle\n", encoding="utf-8")

        # Toggle to completed
        result = await toggle_task_status_fs_tool(
            file_path=file_path,
            line_number=1,
            add_done_date=True,
            vault_path=str(temp_vault),
        )

        assert result["success"] is True
        assert result["new_status"] == "completed"
        assert result["done_date"] is not None

        # Verify file was updated
        content = (temp_vault / file_path).read_text(encoding="utf-8")
        assert "- [x]" in content

    @pytest.mark.asyncio
    async def test_update_task_metadata_fs_tool(self, temp_vault):
        """Test update_task_metadata_fs_tool."""
        file_path = "tasks.md"
        (temp_vault / file_path).write_text("- [ ] Task to update\n", encoding="utf-8")

        result = await update_task_metadata_fs_tool(
            file_path=file_path,
            line_number=1,
            updates={
                "priority": "highest",
                "due_date": "2025-10-31",
                "recurrence": "every day",
            },
            vault_path=str(temp_vault),
        )

        assert result["success"] is True
        assert "priority" in result["changes_made"]
        assert "due_date" in result["changes_made"]
        assert "recurrence" in result["changes_made"]

        # Verify file was updated
        content = (temp_vault / file_path).read_text(encoding="utf-8")
        assert "⏫" in content
        assert "2025-10-31" in content
        assert "every day" in content

    @pytest.mark.asyncio
    async def test_get_task_statistics_fs_tool_note_scope(self, temp_vault):
        """Test get_task_statistics_fs_tool with note scope."""
        file_path = "tasks.md"
        (temp_vault / file_path).write_text(
            "- [ ] Task 1 ⏫\n- [ ] Task 2\n- [x] Task 3\n", encoding="utf-8"
        )

        result = await get_task_statistics_fs_tool(
            scope="note", file_path=file_path, vault_path=str(temp_vault)
        )

        assert result["total_tasks"] == 3
        assert result["incomplete_tasks"] == 2
        assert result["completed_tasks"] == 1
        assert result["by_priority"]["highest"] == 1

    @pytest.mark.asyncio
    async def test_get_task_statistics_fs_tool_vault_scope(self, temp_vault):
        """Test get_task_statistics_fs_tool with vault scope."""
        (temp_vault / "a.md").write_text("- [ ] Task A\n", encoding="utf-8")
        (temp_vault / "b.md").write_text("- [x] Task B\n", encoding="utf-8")

        result = await get_task_statistics_fs_tool(
            scope="vault", vault_path=str(temp_vault)
        )

        assert result["total_tasks"] >= 2
        assert result["incomplete_tasks"] >= 1
        assert result["completed_tasks"] >= 1


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_task_with_malformed_date(self):
        """Test parsing task with invalid date format."""
        line = "- [ ] Task with bad date 📅 2025-13-45"
        task = parse_task_line(line, 1, "test.md")

        # Should still parse, but without the invalid date
        assert task is not None
        assert task.content == "Task with bad date 📅 2025-13-45"  # Date not removed
        assert task.due_date is None

    def test_format_task_without_metadata(self):
        """Test formatting task with minimal data."""
        task = Task(
            content="Minimal task",
            status="incomplete",
            line_number=1,
            source_file="test.md",
        )

        line = format_task_line(task)
        assert line == "- [ ] Minimal task"

    @pytest.mark.asyncio
    async def test_create_task_invalid_recurrence(self, temp_vault):
        """Test creating task with invalid recurrence pattern."""
        with pytest.raises(ValueError, match="must start with 'every'"):
            await create_task_fs_tool(
                file_path="test.md",
                task_content="Invalid task",
                recurrence="daily",  # Should be "every day"
                vault_path=str(temp_vault),
            )

    @pytest.mark.asyncio
    async def test_toggle_nonexistent_line(self, temp_vault):
        """Test toggling task on invalid line number."""
        file_path = "test.md"
        (temp_vault / file_path).write_text("Single line\n", encoding="utf-8")

        result = await toggle_task_status_fs_tool(
            file_path=file_path,
            line_number=99,
            vault_path=str(temp_vault),
        )

        assert result["success"] is False
        assert "out of range" in result["error"]
