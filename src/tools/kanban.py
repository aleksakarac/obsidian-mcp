"""Filesystem-native tools for Kanban board manipulation.

Supports the Kanban plugin's markdown format:
- ## Column headings for columns
- - [ ] checkbox items for cards
- Indentation for subtasks
- @{YYYY-MM-DD} for due dates
- #tags and [[wikilinks]] in cards
"""

import os
import re
from pathlib import Path
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Literal, Tuple

from ..models.obsidian import KanbanBoard, KanbanColumn, KanbanCard
from ..utils.patterns import (
    KANBAN_COLUMN,
    KANBAN_CARD,
    KANBAN_DATE,
    TAG_PATTERN,
    WIKILINK_PATTERN,
)


def parse_card_metadata(card_text: str) -> Dict[str, Any]:
    """Extract metadata from card text.

    Args:
        card_text: Card text content

    Returns:
        Dictionary with due_date, tags, wikilinks
    """
    metadata = {
        "due_date": None,
        "tags": [],
        "wikilinks": [],
    }

    # Extract due date @{YYYY-MM-DD}
    date_match = KANBAN_DATE.search(card_text)
    if date_match:
        try:
            metadata["due_date"] = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
        except ValueError:
            pass

    # Extract tags
    metadata["tags"] = [match.group(1) for match in TAG_PATTERN.finditer(card_text)]

    # Extract wikilinks
    metadata["wikilinks"] = [match.group(1) for match in WIKILINK_PATTERN.finditer(card_text)]

    return metadata


def format_kanban_card(card: KanbanCard, indent: int = 0) -> str:
    """Format a KanbanCard into markdown text.

    Args:
        card: KanbanCard object
        indent: Indentation level

    Returns:
        Formatted card line
    """
    indent_str = "  " * indent
    checkbox = "[x]" if card.status == "completed" else "[ ]"

    # Build text with metadata
    text = card.text

    # Add due date if present
    if card.due_date:
        text += f" @{{{card.due_date.strftime('%Y-%m-%d')}}}"

    return f"{indent_str}- {checkbox} {text}"


def parse_kanban_structure(content: str, file_path: str) -> KanbanBoard:
    """Parse Kanban board markdown structure.

    Args:
        content: Markdown content
        file_path: Path to board file

    Returns:
        KanbanBoard object with columns and cards
    """
    lines = content.splitlines()
    columns = []
    current_column = None
    card_stack = []  # Stack to track nested cards

    for line_num, line in enumerate(lines, start=1):
        # Check for column heading (## Column Name)
        column_match = KANBAN_COLUMN.match(line)
        if column_match and column_match.group(1) == "##":
            # Save previous column
            if current_column:
                columns.append(current_column)

            # Start new column
            column_name = column_match.group(2).strip()
            current_column = KanbanColumn(
                name=column_name,
                cards=[],
                line_number=line_num,
            )
            card_stack = []
            continue

        # Check for card (- [ ] or - [x])
        card_match = KANBAN_CARD.match(line)
        if card_match and current_column:
            indent_str = card_match.group(1)
            checkbox_status = card_match.group(2)
            card_text = card_match.group(3).strip()

            # Calculate indent level
            indent_level = len(indent_str) // 2

            status = "completed" if checkbox_status.lower() == "x" else "incomplete"

            # Parse metadata
            metadata = parse_card_metadata(card_text)

            # Remove metadata from displayed text
            clean_text = card_text
            # Remove due date
            clean_text = KANBAN_DATE.sub("", clean_text).strip()

            card = KanbanCard(
                text=clean_text,
                status=status,
                due_date=metadata["due_date"],
                tags=metadata["tags"],
                wikilinks=metadata["wikilinks"],
                subtasks=[],
                indent_level=indent_level,
                line_number=line_num,
            )

            # Handle nesting
            if indent_level == 0:
                # Root level card
                current_column.cards.append(card)
                card_stack = [card]
            else:
                # Nested card (subtask)
                # Find parent at indent_level - 1
                while card_stack and card_stack[-1].indent_level >= indent_level:
                    card_stack.pop()

                if card_stack:
                    parent = card_stack[-1]
                    parent.subtasks.append(card)
                    card_stack.append(card)
                else:
                    # Orphaned subtask, add as root
                    current_column.cards.append(card)
                    card_stack = [card]

    # Save last column
    if current_column:
        columns.append(current_column)

    # Parse frontmatter settings if present
    settings = {}
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if frontmatter_match:
        # Simple YAML parsing for kanban-plugin setting
        fm_content = frontmatter_match.group(1)
        if "kanban-plugin:" in fm_content:
            settings["kanban-plugin"] = "basic"

    return KanbanBoard(
        file_path=file_path,
        columns=columns,
        settings=settings,
    )


def find_card_in_board(
    board: KanbanBoard, card_text: str, column_name: Optional[str] = None
) -> Optional[Tuple[KanbanColumn, KanbanCard, Optional[KanbanCard]]]:
    """Find a card in the board by text.

    Args:
        board: KanbanBoard to search
        card_text: Card text to find
        column_name: Optional column name to narrow search

    Returns:
        Tuple of (column, card, parent_card) if found, None otherwise
    """
    columns_to_search = board.columns
    if column_name:
        columns_to_search = [c for c in board.columns if c.name == column_name]

    def search_cards(cards: List[KanbanCard], parent=None) -> Optional[Tuple[KanbanCard, Optional[KanbanCard]]]:
        for card in cards:
            if card.text == card_text:
                return (card, parent)
            # Search subtasks
            result = search_cards(card.subtasks, parent=card)
            if result:
                return result
        return None

    for column in columns_to_search:
        result = search_cards(column.cards)
        if result:
            return (column, result[0], result[1])

    return None


def write_kanban_board(board: KanbanBoard, vault_path: str) -> bool:
    """Write KanbanBoard back to file.

    Args:
        board: KanbanBoard to write
        vault_path: Path to vault

    Returns:
        True if successful
    """
    full_path = Path(vault_path) / board.file_path

    try:
        lines = []

        # Write frontmatter if present
        if board.settings:
            lines.append("---")
            if "kanban-plugin" in board.settings:
                lines.append(f"kanban-plugin: {board.settings['kanban-plugin']}")
            lines.append("---")
            lines.append("")

        # Write columns
        for column in board.columns:
            lines.append(f"## {column.name}")
            lines.append("")

            def write_cards(cards: List[KanbanCard], indent: int = 0):
                for card in cards:
                    lines.append(format_kanban_card(card, indent))
                    if card.subtasks:
                        write_cards(card.subtasks, indent + 1)

            write_cards(column.cards)
            lines.append("")

        full_path.write_text("\n".join(lines), encoding="utf-8")
        return True

    except Exception:
        return False


# ============================================================================
# MCP TOOL FUNCTIONS
# ============================================================================

async def parse_kanban_board_fs_tool(
    file_path: str,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Parse Kanban board structure from markdown file.

    Args:
        file_path: Relative path to Kanban board file
        vault_path: Path to vault (defaults to env var)

    Returns:
        Board structure with columns, cards, and metadata
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    full_path = Path(vault) / file_path

    if not full_path.exists():
        raise ValueError(f"File not found: {file_path}")

    content = full_path.read_text(encoding="utf-8")
    board = parse_kanban_structure(content, file_path)

    def card_to_dict(card: KanbanCard) -> Dict[str, Any]:
        return {
            "text": card.text,
            "status": card.status,
            "due_date": card.due_date.isoformat() if card.due_date else None,
            "tags": card.tags,
            "wikilinks": card.wikilinks,
            "subtasks": [card_to_dict(st) for st in card.subtasks],
            "line_number": card.line_number,
        }

    return {
        "file_path": board.file_path,
        "total_cards": board.total_cards,
        "columns": [
            {
                "name": col.name,
                "card_count": col.card_count,
                "cards": [card_to_dict(card) for card in col.cards],
            }
            for col in board.columns
        ],
    }


async def add_kanban_card_fs_tool(
    file_path: str,
    column_name: str,
    card_text: str,
    status: Literal["incomplete", "completed"] = "incomplete",
    due_date: Optional[str] = None,
    position: Literal["start", "end"] = "end",
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a card to a Kanban board column.

    Args:
        file_path: Relative path to board file
        column_name: Name of column to add card to
        card_text: Card text content
        status: Card status
        due_date: Optional due date (YYYY-MM-DD)
        position: Where to add card (start or end of column)
        vault_path: Path to vault (defaults to env var)

    Returns:
        Success status and updated board info
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    full_path = Path(vault) / file_path

    if not full_path.exists():
        raise ValueError(f"File not found: {file_path}")

    content = full_path.read_text(encoding="utf-8")
    board = parse_kanban_structure(content, file_path)

    # Find column
    target_column = next((c for c in board.columns if c.name == column_name), None)
    if not target_column:
        raise ValueError(f"Column not found: {column_name}")

    # Create new card
    parsed_due_date = None
    if due_date:
        parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d").date()

    new_card = KanbanCard(
        text=card_text,
        status=status,
        due_date=parsed_due_date,
        tags=[],
        wikilinks=[],
        subtasks=[],
        indent_level=0,
        line_number=0,
    )

    # Add to column
    if position == "start":
        target_column.cards.insert(0, new_card)
    else:
        target_column.cards.append(new_card)

    # Write back
    success = write_kanban_board(board, vault)

    return {
        "success": success,
        "column": column_name,
        "card_text": card_text,
        "total_cards": board.total_cards,
    }


async def move_kanban_card_fs_tool(
    file_path: str,
    card_text: str,
    from_column: str,
    to_column: str,
    position: Literal["start", "end"] = "end",
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Move a card between Kanban columns.

    Args:
        file_path: Relative path to board file
        card_text: Text of card to move
        from_column: Source column name
        to_column: Destination column name
        position: Where to place card in destination
        vault_path: Path to vault (defaults to env var)

    Returns:
        Success status and move details
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    full_path = Path(vault) / file_path

    if not full_path.exists():
        raise ValueError(f"File not found: {file_path}")

    content = full_path.read_text(encoding="utf-8")
    board = parse_kanban_structure(content, file_path)

    # Find card
    card_info = find_card_in_board(board, card_text, from_column)
    if not card_info:
        raise ValueError(f"Card not found: {card_text}")

    source_column, card, parent = card_info

    # Find destination column
    dest_column = next((c for c in board.columns if c.name == to_column), None)
    if not dest_column:
        raise ValueError(f"Destination column not found: {to_column}")

    # Remove from source
    if parent:
        parent.subtasks.remove(card)
    else:
        source_column.cards.remove(card)

    # Reset indent level (becomes root card in new column)
    card.indent_level = 0

    # Add to destination
    if position == "start":
        dest_column.cards.insert(0, card)
    else:
        dest_column.cards.append(card)

    # Write back
    success = write_kanban_board(board, vault)

    return {
        "success": success,
        "card_text": card_text,
        "from_column": from_column,
        "to_column": to_column,
        "had_subtasks": len(card.subtasks) > 0,
    }


async def toggle_kanban_card_fs_tool(
    file_path: str,
    card_text: str,
    column_name: Optional[str] = None,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Toggle Kanban card completion status.

    Args:
        file_path: Relative path to board file
        card_text: Text of card to toggle
        column_name: Optional column name to narrow search
        vault_path: Path to vault (defaults to env var)

    Returns:
        Success status and new status
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    full_path = Path(vault) / file_path

    if not full_path.exists():
        raise ValueError(f"File not found: {file_path}")

    content = full_path.read_text(encoding="utf-8")
    board = parse_kanban_structure(content, file_path)

    # Find card
    card_info = find_card_in_board(board, card_text, column_name)
    if not card_info:
        raise ValueError(f"Card not found: {card_text}")

    _, card, _ = card_info

    # Toggle status
    new_status = "completed" if card.status == "incomplete" else "incomplete"
    card.status = new_status

    # Write back
    success = write_kanban_board(board, vault)

    return {
        "success": success,
        "card_text": card_text,
        "new_status": new_status,
    }


async def get_kanban_statistics_fs_tool(
    file_path: str,
    vault_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Get statistics for Kanban board.

    Args:
        file_path: Relative path to board file
        vault_path: Path to vault (defaults to env var)

    Returns:
        Board statistics with card counts and completion rates
    """
    vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise ValueError("vault_path must be provided or OBSIDIAN_VAULT_PATH must be set")

    full_path = Path(vault) / file_path

    if not full_path.exists():
        raise ValueError(f"File not found: {file_path}")

    content = full_path.read_text(encoding="utf-8")
    board = parse_kanban_structure(content, file_path)

    def count_cards(cards: List[KanbanCard]) -> Tuple[int, int]:
        """Count total and completed cards recursively."""
        total = len(cards)
        completed = sum(1 for c in cards if c.status == "completed")

        for card in cards:
            sub_total, sub_completed = count_cards(card.subtasks)
            total += sub_total
            completed += sub_completed

        return total, completed

    # Overall stats
    total_cards = board.total_cards
    total_completed = sum(
        sum(1 for c in col.cards if c.status == "completed") for col in board.columns
    )

    # Per-column stats
    column_stats = []
    for col in board.columns:
        col_total, col_completed = count_cards(col.cards)
        completion_rate = (col_completed / col_total * 100) if col_total > 0 else 0

        column_stats.append({
            "column_name": col.name,
            "total_cards": col_total,
            "completed_cards": col_completed,
            "incomplete_cards": col_total - col_completed,
            "completion_rate": round(completion_rate, 1),
        })

    return {
        "file_path": file_path,
        "total_cards": total_cards,
        "total_completed": total_completed,
        "total_incomplete": total_cards - total_completed,
        "overall_completion_rate": round((total_completed / total_cards * 100) if total_cards > 0 else 0, 1),
        "column_count": len(board.columns),
        "columns": column_stats,
    }
