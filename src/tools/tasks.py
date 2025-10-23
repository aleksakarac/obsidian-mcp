"""Filesystem-native tools for Tasks plugin task management.

This module provides tools for managing tasks with Tasks plugin metadata
(due dates, priorities, recurrence, etc.) without requiring Obsidian to be running.

All operations work directly on markdown files.
"""

import os
import re
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Literal
from pydantic import Field

from ..models.obsidian import Task
from ..utils.patterns import (
    TASK_DUE_DATE,
    TASK_SCHEDULED,
    TASK_START,
    TASK_DONE,
    TASK_CREATED,
    TASK_PRIORITY,
    TASK_RECURRENCE,
    TASK_CHECKBOX,
    TAG_PATTERN,
)


# Priority emoji mapping
PRIORITY_EMOJI_MAP = {
    "highest": "⏫",
    "high": "🔼",
    "low": "🔽",
    "lowest": "⏬",
}

EMOJI_PRIORITY_MAP = {v: k for k, v in PRIORITY_EMOJI_MAP.items()}


def parse_task_line(line: str, line_number: int, source_file: str) -> Optional[Task]:
    """Parse a task line into a Task object.

    Args:
        line: Line of text to parse
        line_number: Line number in source file
        source_file: Path to source file

    Returns:
        Task object if line is a task, None otherwise
    """
    # Check if this is a task line
    checkbox_match = TASK_CHECKBOX.match(line.strip())
    if not checkbox_match:
        return None

    checkbox_status = checkbox_match.group(1)
    task_content = checkbox_match.group(2)

    # Determine status
    status = "completed" if checkbox_status.lower() == "x" else "incomplete"

    # Extract metadata (work from right to left, removing matched patterns)
    remaining_text = task_content.strip()
    metadata = {}

    # Extract dates
    for pattern_name, pattern in [
        ("done_date", TASK_DONE),
        ("due_date", TASK_DUE_DATE),
        ("scheduled_date", TASK_SCHEDULED),
        ("start_date", TASK_START),
        ("created_date", TASK_CREATED),
    ]:
        match = pattern.search(remaining_text)
        if match:
            try:
                metadata[pattern_name] = datetime.strptime(match.group(1), "%Y-%m-%d").date()
                # Remove match from content
                remaining_text = remaining_text[: match.start()].rstrip()
            except ValueError:
                # Invalid date format, ignore
                pass

    # Extract priority
    priority_match = TASK_PRIORITY.search(remaining_text)
    if priority_match:
        emoji = priority_match.group(1)
        metadata["priority"] = EMOJI_PRIORITY_MAP.get(emoji, "normal")
        remaining_text = remaining_text[: priority_match.start()].rstrip()
    else:
        metadata["priority"] = "normal"

    # Extract recurrence
    recurrence_match = TASK_RECURRENCE.search(remaining_text)
    if recurrence_match:
        metadata["recurrence"] = recurrence_match.group(1).strip()
        remaining_text = remaining_text[: recurrence_match.start()].rstrip()

    # Extract tags
    tags = [match.group(1) for match in TAG_PATTERN.finditer(remaining_text)]

    # Final content is what remains
    content = remaining_text.strip()

    return Task(
        content=content,
        status=status,
        priority=metadata.get("priority", "normal"),
        due_date=metadata.get("due_date"),
        scheduled_date=metadata.get("scheduled_date"),
        start_date=metadata.get("start_date"),
        done_date=metadata.get("done_date"),
        created_date=metadata.get("created_date"),
        recurrence=metadata.get("recurrence"),
        line_number=line_number,
        source_file=source_file,
        tags=tags,
    )


def format_task_line(task: Task) -> str:
    """Format a Task object into a markdown task line with emoji metadata.

    Args:
        task: Task object to format

    Returns:
        Formatted task line string
    """
    # Start with checkbox
    checkbox = "- [x]" if task.status == "completed" else "- [ ]"

    # Build content with metadata
    parts = [task.content]

    # Add priority emoji (if not normal)
    if task.priority and task.priority != "normal":
        emoji = PRIORITY_EMOJI_MAP.get(task.priority)
        if emoji:
            parts.append(emoji)

    # Add dates
    if task.start_date:
        parts.append(f"🛫 {task.start_date.strftime('%Y-%m-%d')}")
    if task.scheduled_date:
        parts.append(f"⏳ {task.scheduled_date.strftime('%Y-%m-%d')}")
    if task.due_date:
        parts.append(f"📅 {task.due_date.strftime('%Y-%m-%d')}")
    if task.done_date:
        parts.append(f"✅ {task.done_date.strftime('%Y-%m-%d')}")
    if task.created_date:
        parts.append(f"➕ {task.created_date.strftime('%Y-%m-%d')}")

    # Add recurrence
    if task.recurrence:
        parts.append(f"🔁 {task.recurrence}")

    return f"{checkbox} {' '.join(parts)}"


def scan_vault_for_tasks(vault_path: str) -> List[Task]:
    """Scan entire vault for tasks.

    Args:
        vault_path: Path to Obsidian vault

    Returns:
        List of all tasks found in vault
    """
    tasks = []
    vault_dir = Path(vault_path)

    for md_file in vault_dir.rglob("*.md"):
        # Skip hidden files and folders
        if any(part.startswith(".") for part in md_file.parts):
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
            relative_path = str(md_file.relative_to(vault_dir))

            for line_num, line in enumerate(content.splitlines(), start=1):
                task = parse_task_line(line, line_num, relative_path)
                if task:
                    tasks.append(task)
        except Exception:
            # Skip files that can't be read
            continue

    return tasks


def filter_tasks(
    tasks: List[Task],
    status: Optional[Literal["incomplete", "completed", "all"]] = None,
    priority: Optional[Literal["highest", "high", "normal", "low", "lowest"]] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    due_within_days: Optional[int] = None,
    has_recurrence: Optional[bool] = None,
    tag: Optional[str] = None,
) -> List[Task]:
    """Filter tasks by criteria.

    Args:
        tasks: List of tasks to filter
        status: Filter by status
        priority: Filter by priority
        due_before: Filter tasks due before this date
        due_after: Filter tasks due after this date
        due_within_days: Filter tasks due within N days from today
        has_recurrence: Filter tasks with/without recurrence
        tag: Filter tasks containing this tag

    Returns:
        Filtered list of tasks
    """
    filtered = tasks

    # Status filter
    if status and status != "all":
        filtered = [t for t in filtered if t.status == status]

    # Priority filter
    if priority:
        filtered = [t for t in filtered if t.priority == priority]

    # Due date filters
    if due_before:
        filtered = [t for t in filtered if t.due_date and t.due_date < due_before]

    if due_after:
        filtered = [t for t in filtered if t.due_date and t.due_date > due_after]

    if due_within_days is not None:
        cutoff_date = date.today() + timedelta(days=due_within_days)
        filtered = [
            t
            for t in filtered
            if t.due_date and date.today() <= t.due_date <= cutoff_date
        ]

    # Recurrence filter
    if has_recurrence is not None:
        if has_recurrence:
            filtered = [t for t in filtered if t.recurrence]
        else:
            filtered = [t for t in filtered if not t.recurrence]

    # Tag filter
    if tag:
        filtered = [t for t in filtered if tag in t.tags]

    return filtered


def sort_tasks(
    tasks: List[Task],
    sort_by: Literal["due_date", "priority", "file", "line_number"] = "due_date",
    sort_order: Literal["asc", "desc"] = "asc",
) -> List[Task]:
    """Sort tasks by specified criteria.

    Args:
        tasks: List of tasks to sort
        sort_by: Field to sort by
        sort_order: Sort direction

    Returns:
        Sorted list of tasks
    """
    reverse = sort_order == "desc"

    if sort_by == "due_date":
        # Tasks without due dates go to end
        tasks_with_due = [t for t in tasks if t.due_date]
        tasks_without_due = [t for t in tasks if not t.due_date]
        tasks_with_due.sort(key=lambda t: t.due_date, reverse=reverse)
        return tasks_with_due + tasks_without_due if not reverse else tasks_without_due + tasks_with_due

    elif sort_by == "priority":
        priority_order = ["highest", "high", "normal", "low", "lowest"]
        if reverse:
            priority_order = priority_order[::-1]
        return sorted(tasks, key=lambda t: priority_order.index(t.priority or "normal"))

    elif sort_by == "file":
        return sorted(tasks, key=lambda t: t.source_file, reverse=reverse)

    elif sort_by == "line_number":
        return sorted(tasks, key=lambda t: (t.source_file, t.line_number), reverse=reverse)

    return tasks


def update_task_in_file(vault_path: str, task: Task, new_line: str) -> bool:
    """Update a specific task line in its source file.

    Args:
        vault_path: Path to vault
        task: Task to update (contains file and line number)
        new_line: New content for the line

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(vault_path) / task.source_file

    try:
        lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)

        if task.line_number < 1 or task.line_number > len(lines):
            return False

        # Update the line
        lines[task.line_number - 1] = new_line.rstrip() + "\n"

        file_path.write_text("".join(lines), encoding="utf-8")
        return True

    except Exception:
        return False


def insert_task_in_file(
    vault_path: str,
    file_path: str,
    task_line: str,
    insert_at: Literal["end", "top", "after_heading"] = "end",
    heading: Optional[str] = None,
) -> Optional[int]:
    """Insert a new task into a file.

    Args:
        vault_path: Path to vault
        file_path: Relative path to file
        task_line: Task line to insert
        insert_at: Where to insert the task
        heading: Heading name if insert_at="after_heading"

    Returns:
        Line number where task was inserted, None if failed
    """
    full_path = Path(vault_path) / file_path

    try:
        if not full_path.exists():
            # Create file if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(task_line + "\n", encoding="utf-8")
            return 1

        lines = full_path.read_text(encoding="utf-8").splitlines(keepends=True)

        if insert_at == "end":
            lines.append(task_line + "\n")
            line_number = len(lines)

        elif insert_at == "top":
            lines.insert(0, task_line + "\n")
            line_number = 1

        elif insert_at == "after_heading" and heading:
            # Find the heading
            heading_pattern = re.compile(rf"^#+\s+{re.escape(heading)}\s*$", re.MULTILINE)
            content = "".join(lines)
            match = heading_pattern.search(content)

            if match:
                # Find line number of heading
                line_num = content[: match.end()].count("\n")
                lines.insert(line_num + 1, task_line + "\n")
                line_number = line_num + 2
            else:
                # Heading not found, append to end
                lines.append(task_line + "\n")
                line_number = len(lines)
        else:
            # Default to end
            lines.append(task_line + "\n")
            line_number = len(lines)

        full_path.write_text("".join(lines), encoding="utf-8")
        return line_number

    except Exception:
        return None


# ============================================================================
# MCP TOOL FUNCTIONS
# ============================================================================

async def search_tasks_fs_tool(
    vault_path: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 100,
    sort_by: Literal["due_date", "priority", "file", "line_number"] = "due_date",
    sort_order: Literal["asc", "desc"] = "asc",
) -> Dict[str, Any]:
    """Search and filter tasks by metadata across the entire vault.

    Args:
        vault_path: Path to vault (defaults to OBSIDIAN_VAULT_PATH env var)
        filters: Filter criteria (status, priority, due_before, due_after, due_within_days, has_recurrence, tag)
        limit: Maximum number of results to return
        sort_by: Field to sort by
        sort_order: Sort direction

    Returns:
        Dictionary with tasks list, total count, and truncation flag
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    # Parse filters
    filter_args = {}
    if filters:
        if "status" in filters:
            filter_args["status"] = filters["status"]
        if "priority" in filters:
            filter_args["priority"] = filters["priority"]
        if "due_before" in filters:
            filter_args["due_before"] = datetime.strptime(filters["due_before"], "%Y-%m-%d").date()
        if "due_after" in filters:
            filter_args["due_after"] = datetime.strptime(filters["due_after"], "%Y-%m-%d").date()
        if "due_within_days" in filters:
            filter_args["due_within_days"] = filters["due_within_days"]
        if "has_recurrence" in filters:
            filter_args["has_recurrence"] = filters["has_recurrence"]
        if "tag" in filters:
            filter_args["tag"] = filters["tag"]

    # Scan and filter
    all_tasks = scan_vault_for_tasks(vault)
    filtered_tasks = filter_tasks(all_tasks, **filter_args)
    sorted_tasks = sort_tasks(filtered_tasks, sort_by, sort_order)

    # Apply limit
    total_found = len(sorted_tasks)
    truncated = total_found > limit
    result_tasks = sorted_tasks[:limit]

    # Convert to dict representation
    return {
        "tasks": [
            {
                "content": t.content,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else None,
                "start_date": t.start_date.isoformat() if t.start_date else None,
                "done_date": t.done_date.isoformat() if t.done_date else None,
                "recurrence": t.recurrence,
                "tags": t.tags,
                "source_file": t.source_file,
                "absolute_path": str(Path(vault) / t.source_file),
                "line_number": t.line_number,
            }
            for t in result_tasks
        ],
        "total_found": total_found,
        "truncated": truncated,
    }


async def create_task_fs_tool(
    file_path: str,
    task_content: str,
    priority: Optional[Literal["highest", "high", "normal", "low", "lowest"]] = "normal",
    due_date: Optional[str] = None,
    scheduled_date: Optional[str] = None,
    start_date: Optional[str] = None,
    recurrence: Optional[str] = None,
    insert_at: Literal["end", "top", "after_heading"] = "end",
    heading: Optional[str] = None,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new task with metadata in a specified note.

    Args:
        file_path: Relative or absolute path to file
        task_content: Task description text
        priority: Priority level
        due_date: Due date (YYYY-MM-DD)
        scheduled_date: Scheduled date (YYYY-MM-DD)
        start_date: Start date (YYYY-MM-DD)
        recurrence: Recurrence pattern (must start with "every")
        insert_at: Where to insert the task
        heading: Heading name if insert_at="after_heading"
        vault_path: Path to vault (defaults to env var)

    Returns:
        Dictionary with success status, task line, line number, and file path
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    # Validate dates
    dates = {}
    if due_date:
        dates["due_date"] = datetime.strptime(due_date, "%Y-%m-%d").date()
    if scheduled_date:
        dates["scheduled_date"] = datetime.strptime(scheduled_date, "%Y-%m-%d").date()
    if start_date:
        dates["start_date"] = datetime.strptime(start_date, "%Y-%m-%d").date()

    # Validate recurrence
    if recurrence and not recurrence.strip().lower().startswith("every"):
        raise ValueError("Recurrence pattern must start with 'every'")

    # Create Task object
    task = Task(
        content=task_content,
        status="incomplete",
        priority=priority,
        due_date=dates.get("due_date"),
        scheduled_date=dates.get("scheduled_date"),
        start_date=dates.get("start_date"),
        recurrence=recurrence,
        line_number=None,  # Will be set after insertion
        source_file=file_path,
        tags=[],
    )

    # Format task line
    task_line = format_task_line(task)

    # Insert into file
    line_number = insert_task_in_file(vault, file_path, task_line, insert_at, heading)

    if line_number is None:
        return {
            "success": False,
            "task_line": task_line,
            "line_number": None,
            "file_path": file_path,
            "error": "Failed to insert task"
        }

    return {
        "success": True,
        "task_line": task_line,
        "line_number": line_number,
        "file_path": file_path,
    }


async def toggle_task_status_fs_tool(
    file_path: str,
    line_number: int,
    add_done_date: bool = False,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Toggle task completion status (incomplete ↔ completed).

    Args:
        file_path: Relative path to file
        line_number: Line number containing the task
        add_done_date: Add ✅ date on completion
        vault_path: Path to vault (defaults to env var)

    Returns:
        Dictionary with success status, new status, done date, and updated line
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    full_path = Path(vault) / file_path

    try:
        lines = full_path.read_text(encoding="utf-8").splitlines(keepends=True)

        if line_number < 1 or line_number > len(lines):
            return {
                "success": False,
                "error": f"Line {line_number} out of range (file has {len(lines)} lines)"
            }

        line = lines[line_number - 1]

        # Parse current task
        task = parse_task_line(line, line_number, file_path)
        if not task:
            return {
                "success": False,
                "error": "Line is not a task"
            }

        # Toggle status
        new_status = "completed" if task.status == "incomplete" else "incomplete"
        task.status = new_status

        # Add done date if completing and requested
        if new_status == "completed" and add_done_date:
            task.done_date = date.today()
        elif new_status == "incomplete":
            task.done_date = None

        # Format new line
        new_line = format_task_line(task)

        # Update file
        lines[line_number - 1] = new_line + "\n"
        full_path.write_text("".join(lines), encoding="utf-8")

        return {
            "success": True,
            "new_status": new_status,
            "done_date": task.done_date.isoformat() if task.done_date else None,
            "updated_line": new_line,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def update_task_metadata_fs_tool(
    file_path: str,
    line_number: int,
    updates: Dict[str, Any],
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Update task metadata without changing content.

    Args:
        file_path: Relative path to file
        line_number: Line number containing the task
        updates: Fields to update (priority, due_date, scheduled_date, start_date, recurrence)
        vault_path: Path to vault (defaults to env var)

    Returns:
        Dictionary with success status, updated line, and changes made
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    full_path = Path(vault) / file_path

    try:
        lines = full_path.read_text(encoding="utf-8").splitlines(keepends=True)

        if line_number < 1 or line_number > len(lines):
            return {
                "success": False,
                "error": f"Line {line_number} out of range"
            }

        line = lines[line_number - 1]
        task = parse_task_line(line, line_number, file_path)

        if not task:
            return {
                "success": False,
                "error": "Line is not a task"
            }

        changes_made = []

        # Apply updates
        if "priority" in updates:
            value = updates["priority"]
            if value is None or value in ["highest", "high", "normal", "low", "lowest"]:
                task.priority = value or "normal"
                changes_made.append("priority")

        for date_field in ["due_date", "scheduled_date", "start_date"]:
            if date_field in updates:
                value = updates[date_field]
                if value:
                    setattr(task, date_field, datetime.strptime(value, "%Y-%m-%d").date())
                else:
                    setattr(task, date_field, None)
                changes_made.append(date_field)

        if "recurrence" in updates:
            value = updates["recurrence"]
            if value is None or (value and value.strip().lower().startswith("every")):
                task.recurrence = value
                changes_made.append("recurrence")

        # Format and update
        new_line = format_task_line(task)
        lines[line_number - 1] = new_line + "\n"
        full_path.write_text("".join(lines), encoding="utf-8")

        return {
            "success": True,
            "updated_line": new_line,
            "changes_made": changes_made,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def get_task_statistics_fs_tool(
    scope: Literal["note", "vault"],
    file_path: Optional[str] = None,
    group_by: Optional[Literal["priority", "status", "file"]] = None,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Get aggregate task statistics for a note or entire vault.

    Args:
        scope: "note" or "vault"
        file_path: Required if scope="note"
        group_by: Optional grouping (priority, status, file)
        vault_path: Path to vault (defaults to env var)

    Returns:
        Dictionary with task statistics
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    # Gather tasks
    if scope == "note":
        if not file_path:
            raise ValueError("file_path required when scope='note'")

        full_path = Path(vault) / file_path
        if not full_path.exists():
            raise ValueError(f"File not found: {file_path}")

        content = full_path.read_text(encoding="utf-8")
        tasks = []
        for line_num, line in enumerate(content.splitlines(), start=1):
            task = parse_task_line(line, line_num, file_path)
            if task:
                tasks.append(task)

    else:  # vault scope
        tasks = scan_vault_for_tasks(vault)

    # Calculate statistics
    total_tasks = len(tasks)
    incomplete_tasks = sum(1 for t in tasks if t.status == "incomplete")
    completed_tasks = sum(1 for t in tasks if t.status == "completed")

    by_priority = {
        "highest": sum(1 for t in tasks if t.priority == "highest"),
        "high": sum(1 for t in tasks if t.priority == "high"),
        "normal": sum(1 for t in tasks if t.priority == "normal"),
        "low": sum(1 for t in tasks if t.priority == "low"),
        "lowest": sum(1 for t in tasks if t.priority == "lowest"),
    }

    today = date.today()
    overdue_tasks = sum(1 for t in tasks if t.due_date and t.due_date < today and t.status == "incomplete")
    upcoming_tasks = sum(
        1 for t in tasks
        if t.due_date and today <= t.due_date <= today + timedelta(days=7) and t.status == "incomplete"
    )
    recurring_tasks = sum(1 for t in tasks if t.recurrence)

    result = {
        "total_tasks": total_tasks,
        "incomplete_tasks": incomplete_tasks,
        "completed_tasks": completed_tasks,
        "by_priority": by_priority,
        "overdue_tasks": overdue_tasks,
        "upcoming_tasks": upcoming_tasks,
        "recurring_tasks": recurring_tasks,
    }

    # Optional grouping
    if group_by:
        grouped_data = {}
        for task in tasks:
            if group_by == "priority":
                key = task.priority or "normal"
            elif group_by == "status":
                key = task.status
            elif group_by == "file":
                key = task.source_file
            else:
                key = "unknown"

            grouped_data[key] = grouped_data.get(key, 0) + 1

        result["grouped_data"] = [
            {"group_key": k, "count": v}
            for k, v in sorted(grouped_data.items(), key=lambda x: -x[1])
        ]

    return result
