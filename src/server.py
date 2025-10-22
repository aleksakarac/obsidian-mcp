"""Main entry point for Obsidian MCP server."""

import os
from typing import Annotated, Optional, List, Literal, Dict
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.exceptions import McpError

# Import all tools
from .tools import (
    read_note,
    create_note,
    update_note,
    delete_note,
    search_notes,
    search_by_date,
    list_notes,
    list_folders,
    move_note,
    create_folder,
    move_folder,
    add_tags,
    update_tags,
    remove_tags,
    get_note_info,
    list_tags,
    get_backlinks,
    get_outgoing_links,
    find_broken_links,
)

# Import filesystem-native backlinks tools
from .tools.backlinks import (
    find_backlinks as find_backlinks_fs,
    find_broken_links as find_broken_links_fs,
)

# Import filesystem-native tag management tools
from .tools.tags import (
    extract_all_tags as extract_all_tags_fs,
    add_tag_to_frontmatter as add_tag_fs,
    remove_tag_from_frontmatter as remove_tag_fs,
    find_notes_by_tag as find_notes_by_tag_fs,
)

# Import filesystem-native smart insertion tools
from .tools.smart_insert import (
    insert_after_heading as insert_after_heading_fs,
    insert_after_block as insert_after_block_fs,
    update_frontmatter_field as update_frontmatter_field_fs,
    append_to_note as append_to_note_fs,
)

# Import filesystem-native statistics tools
from .tools.statistics import (
    get_note_stats as get_note_stats_fs,
    get_vault_stats as get_vault_stats_fs,
)

# ============================================================================
# HYBRID PLUGIN CONTROL TOOLS (Feature 002)
# ============================================================================

# Tasks Plugin - Filesystem-native tools (User Story 1)
from .tools.tasks import (
    search_tasks_fs_tool,
    create_task_fs_tool,
    toggle_task_status_fs_tool,
    update_task_metadata_fs_tool,
    get_task_statistics_fs_tool,
)

# Dataview Plugin - Filesystem-native tools (User Story 2)
from .tools.dataview_fs import (
    extract_dataview_fields_fs_tool,
    search_by_dataview_field_fs_tool,
    add_dataview_field_fs_tool,
    remove_dataview_field_fs_tool,
)

# Kanban Plugin - Filesystem-native tools (User Story 3)
from .tools.kanban import (
    parse_kanban_board_fs_tool,
    add_kanban_card_fs_tool,
    move_kanban_card_fs_tool,
    toggle_kanban_card_fs_tool,
    get_kanban_statistics_fs_tool,
)

# Enhanced Link Tracking - Filesystem-native tools (User Story 4)
from .tools.links import (
    get_link_graph_fs_tool,
    find_orphaned_notes_fs_tool,
    find_hub_notes_fs_tool,
    analyze_link_health_fs_tool,
    get_note_connections_fs_tool,
)

# Dataview API - API-based tools (User Story 5)
from .tools.dataview_api import (
    execute_dataview_query_api_tool,
    list_from_tag_api_tool,
    list_from_folder_api_tool,
    table_query_api_tool,
)

# Templater Plugin API - API-based tools (User Story 6)
from .tools.templater_api import (
    render_templater_template_api_tool,
    create_note_from_template_api_tool,
    insert_templater_template_api_tool,
)

# Templates - Filesystem-native tools (User Story 7)
from .tools.templates import (
    expand_template_fs_tool,
    create_note_from_template_fs_tool,
    list_templates_fs_tool,
)

# Workspace - API-based tools (User Story 8)
from .tools.workspace import (
    get_active_file_api_tool,
    open_file_api_tool,
    close_active_file_api_tool,
    navigate_back_api_tool,
    navigate_forward_api_tool,
    toggle_edit_mode_api_tool,
)

# Canvas - Filesystem-native tools (User Story 9)
from .tools.canvas import (
    parse_canvas_fs_tool,
    add_canvas_node_fs_tool,
    add_canvas_edge_fs_tool,
    remove_canvas_node_fs_tool,
    get_canvas_node_connections_fs_tool,
)

# Commands - API-based tools (User Story 10)
from .tools.commands import (
    execute_command_api_tool,
    list_commands_api_tool,
    search_commands_api_tool,
)
# ============================================================================

# Check for API key
if not os.getenv("OBSIDIAN_REST_API_KEY"):
    raise ValueError("OBSIDIAN_REST_API_KEY environment variable must be set")

# Create FastMCP server instance
mcp = FastMCP(
    "obsidian-mcp",
    instructions="MCP server for interacting with Obsidian vaults through the Local REST API and filesystem-native tools"
)

# Register tools with proper error handling
@mcp.tool()
async def read_note_tool(
    path: Annotated[str, Field(
        description="Path to the note relative to vault root",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Daily/2024-01-15.md", "Projects/AI Research.md", "Ideas/Quick Note.md"]
    )],
    ctx=None
):
    """
    Read the content and metadata of a specific note.
    
    When to use:
    - Displaying note contents to the user
    - Analyzing or processing existing note data
    - ALWAYS before updating a note to preserve existing content
    - Verifying a note exists before making changes
    
    When NOT to use:
    - Searching multiple notes (use search_notes instead)
    - Getting only metadata (use get_note_info for efficiency)
    
    Returns:
        Note content and metadata including tags, aliases, and frontmatter
    """
    try:
        return await read_note(path, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to read note: {str(e)}")

@mcp.tool()
async def create_note_tool(
    path: Annotated[str, Field(
        description="Path where the note should be created relative to vault root",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Ideas/New Idea.md", "Daily/2024-01-15.md", "Projects/Project Plan.md"]
    )],
    content: Annotated[str, Field(
        description="Markdown content for the note. Consider adding tags (use list_tags to see existing ones)",
        min_length=0,
        max_length=1000000,
        examples=[
            "# Meeting Notes\n#meeting #project-alpha\n\nDiscussed timeline and deliverables...",
            "---\ntags: [daily, planning]\n---\n\n# Daily Note\n\nToday's tasks..."
        ]
    )],
    overwrite: Annotated[bool, Field(
        description="Whether to overwrite if the note already exists",
        default=False
    )] = False,
    ctx=None
):
    """
    Create a new note or overwrite an existing one.
    
    When to use:
    - Creating new notes with specific content
    - Setting up templates or structured notes
    - Programmatically generating documentation
    
    When NOT to use:
    - Updating existing notes (use update_note unless you want to replace entirely)
    - Appending content (use update_note with merge_strategy="append")
        
    Returns:
        Created note information with path and metadata
    """
    try:
        return await create_note(path, content, overwrite, ctx)
    except (ValueError, FileExistsError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to create note: {str(e)}")

@mcp.tool()
async def update_note_tool(
    path: Annotated[str, Field(
        description="Path to the note to update",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Daily/2024-01-15.md", "Projects/Project.md"]
    )],
    content: Annotated[str, Field(
        description="New markdown content (REPLACES existing content unless using append)",
        min_length=0,
        max_length=1000000
    )],
    create_if_not_exists: Annotated[bool, Field(
        description="Create the note if it doesn't exist",
        default=False
    )] = False,
    merge_strategy: Annotated[Literal["replace", "append"], Field(
        description="How to handle content: 'replace' overwrites, 'append' adds to end",
        default="replace"
    )] = "replace",
    ctx=None
):
    """
    Update the content of an existing note.
    
    ⚠️ IMPORTANT: By default, this REPLACES the entire note content.
    Always read the note first if you need to preserve existing content.
    
    When to use:
    - Updating a note with completely new content (replace)
    - Adding content to the end of a note (append)
    - Programmatically modifying notes
    
    When NOT to use:
    - Making small edits (read first, then update with full content)
    - Creating new notes (use create_note instead)
    
    Returns:
        Update status with path, metadata, and operation performed
    """
    try:
        return await update_note(path, content, create_if_not_exists, merge_strategy, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to update note: {str(e)}")

@mcp.tool()
async def delete_note_tool(path: str, ctx=None):
    """
    Delete a note from the vault.
    
    Args:
        path: Path to the note to delete
        
    Returns:
        Deletion status
    """
    try:
        return await delete_note(path, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to delete note: {str(e)}")

@mcp.tool()
async def search_notes_tool(
    query: Annotated[str, Field(
        description="Search query supporting Obsidian syntax",
        min_length=1,
        max_length=500,
        examples=[
            "machine learning",
            "tag:#project",
            "path:Daily/",
            "tag:#urgent TODO"
        ]
    )],
    context_length: Annotated[int, Field(
        description="Number of characters to show around matches",
        ge=10,
        le=500,
        default=100
    )] = 100,
    ctx=None
):
    """
    Search for notes containing specific text or matching search criteria.
    
    When to use:
    - Finding notes by content keywords
    - Locating notes with specific tags
    - Searching within specific folders
    
    When NOT to use:
    - Searching by date (use search_by_date instead)
    - Listing all notes (use list_notes for better performance)
    - Finding a specific known note (use read_note directly)
    
    Returns:
        Search results with matched notes, relevance scores, and context
    """
    try:
        return await search_notes(query, context_length, ctx)
    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Search failed: {str(e)}")

@mcp.tool()
async def search_by_date_tool(
    date_type: Annotated[Literal["created", "modified"], Field(
        description="Type of date to search by",
        default="modified"
    )] = "modified",
    days_ago: Annotated[int, Field(
        description="Number of days to look back from today",
        ge=0,
        le=365,
        default=7,
        examples=[0, 1, 7, 30]
    )] = 7,
    operator: Annotated[Literal["within", "exactly"], Field(
        description="Search operator for date matching",
        default="within"
    )] = "within",
    ctx=None
):
    """
    Search for notes by creation or modification date.
    
    When to use:
    - Finding recently modified notes
    - Locating notes created in a specific time period
    - Reviewing activity from specific dates
    
    When NOT to use:
    - Content-based search (use search_notes)
    - Finding notes by tags or path (use search_notes)
    
    Returns:
        Notes matching the date criteria with paths and timestamps
    """
    try:
        return await search_by_date(date_type, days_ago, operator, ctx)
    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Date search failed: {str(e)}")

@mcp.tool()
async def list_notes_tool(directory: str = None, recursive: bool = True, ctx=None):
    """
    List notes in the vault or a specific directory.
    
    Args:
        directory: Specific directory to list (optional, defaults to root)
        recursive: Whether to list all subdirectories recursively (default: true)
        
    Returns:
        Vault structure and note paths
    """
    try:
        return await list_notes(directory, recursive, ctx)
    except Exception as e:
        raise McpError(f"Failed to list notes: {str(e)}")

@mcp.tool()
async def list_folders_tool(
    directory: Annotated[Optional[str], Field(
        description="Specific directory to list folders from (optional, defaults to root)",
        default=None,
        examples=[None, "Projects", "Daily", "Archive/2024"]
    )] = None,
    recursive: Annotated[bool, Field(
        description="Whether to include all nested subfolders",
        default=True
    )] = True,
    ctx=None
):
    """
    List folders in the vault or a specific directory.
    
    When to use:
    - Exploring vault organization structure
    - Verifying folder names before creating notes
    - Checking if a specific folder exists
    - Understanding the hierarchy of the vault
    
    When NOT to use:
    - Listing notes (use list_notes instead)
    - Searching for content (use search_notes)
    
    Returns:
        Folder structure with paths and names
    """
    try:
        return await list_folders(directory, recursive, ctx)
    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to list folders: {str(e)}")

@mcp.tool()
async def move_note_tool(source_path: str, destination_path: str, update_links: bool = True, ctx=None):
    """
    Move a note to a new location, optionally updating all links.
    
    Args:
        source_path: Current path of the note
        destination_path: New path for the note
        update_links: Whether to update links in other notes (default: true)
        
    Returns:
        Move status and updated links count
    """
    try:
        return await move_note(source_path, destination_path, update_links, ctx)
    except (ValueError, FileNotFoundError, FileExistsError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to move note: {str(e)}")

@mcp.tool()
async def create_folder_tool(
    folder_path: Annotated[str, Field(
        description="Path of the folder to create",
        min_length=1,
        max_length=255,
        examples=["Projects/2025", "Archive/Q1", "Daily/January"]
    )],
    create_placeholder: Annotated[bool, Field(
        description="Whether to create a placeholder file (.gitkeep or README.md)",
        default=True
    )] = True,
    ctx=None
):
    """
    Create a new folder in the vault, including all parent folders in the path.
    
    When to use:
    - Setting up project structure in advance
    - Creating deep folder hierarchies (e.g., "Apple/Studies/J71P")
    - Creating archive folders before moving notes
    - Establishing organizational hierarchy
    - Preparing folders for future content
    
    When NOT to use:
    - If you're about to create a note in that path (folders are created automatically)
    - For temporary organization (just create notes directly)
    
    Note: Will create all necessary parent folders. For example, "Apple/Studies/J71P"
    will create Apple, Apple/Studies, and Apple/Studies/J71P if they don't exist.
    
    Returns:
        Creation status with list of folders created and placeholder file path
    """
    try:
        return await create_folder(folder_path, create_placeholder, ctx)
    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to create folder: {str(e)}")

@mcp.tool()
async def move_folder_tool(
    source_folder: Annotated[str, Field(
        description="Current folder path to move",
        min_length=1,
        max_length=255,
        examples=["Projects/Old", "Archive/2023", "Inbox/Unsorted"]
    )],
    destination_folder: Annotated[str, Field(
        description="New location for the folder",
        min_length=1,
        max_length=255,
        examples=["Archive/Projects/Old", "Completed/2023", "Projects/Sorted"]
    )],
    update_links: Annotated[bool, Field(
        description="Whether to update links in other notes (future enhancement)",
        default=True
    )] = True,
    ctx=None
):
    """
    Move an entire folder and all its contents to a new location.
    
    When to use:
    - Reorganizing vault structure
    - Archiving completed projects
    - Consolidating related notes
    - Seasonal organization (e.g., moving to year-based archives)
    
    When NOT to use:
    - Moving individual notes (use move_note instead)
    - Moving to a subfolder of the source (creates circular reference)
    
    Returns:
        Move status with count of notes and folders moved
    """
    try:
        return await move_folder(source_folder, destination_folder, update_links, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to move folder: {str(e)}")

@mcp.tool()
async def add_tags_tool(
    path: Annotated[str, Field(
        description="Path to the note",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255
    )],
    tags: Annotated[List[str], Field(
        description="Tags to add (without # prefix)",
        min_items=1,
        max_items=50,
        examples=[["project", "urgent"], ["meeting", "followup", "q1-2024"]]
    )],
    ctx=None
):
    """
    Add tags to a note's frontmatter.
    
    When to use:
    - Organizing notes with tags
    - Bulk tagging operations
    - Adding metadata for search
    
    When NOT to use:
    - Adding tags in note content (use update_note)
    - Replacing all tags (use update_note with new frontmatter)
    
    Returns:
        Updated tag list for the note
    """
    try:
        return await add_tags(path, tags, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to add tags: {str(e)}")

@mcp.tool()
async def update_tags_tool(
    path: Annotated[str, Field(
        description="Path to the note",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255
    )],
    tags: Annotated[List[str], Field(
        description="New tags to set (without # prefix)",
        min_items=0,
        max_items=50,
        examples=[["meeting", "important", "q1-2025"], ["ai", "research", "neural-networks"]]
    )],
    merge: Annotated[bool, Field(
        description="If True, adds to existing tags. If False, replaces all tags",
        default=False
    )] = False,
    ctx=None
):
    """
    Update tags on a note - either replace all tags or merge with existing.
    
    When to use:
    - After analyzing a note's content to suggest relevant tags
    - Reorganizing tags across your vault
    - Setting consistent tags based on note types or projects
    - AI-driven tag suggestions ("What is this note about? Add appropriate tags")
    
    When NOT to use:
    - Just adding a few tags (use add_tags)
    - Just removing specific tags (use remove_tags)
    
    Returns:
        Previous tags, new tags, and operation performed
    """
    try:
        return await update_tags(path, tags, merge, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to update tags: {str(e)}")

@mcp.tool()
async def remove_tags_tool(path: str, tags: list[str], ctx=None):
    """
    Remove tags from a note's frontmatter.
    
    Args:
        path: Path to the note
        tags: List of tags to remove (without # prefix)
        
    Returns:
        Updated tag list
    """
    try:
        return await remove_tags(path, tags, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to remove tags: {str(e)}")

@mcp.tool()
async def get_note_info_tool(path: str, ctx=None):
    """
    Get metadata and information about a note without retrieving its full content.
    
    Args:
        path: Path to the note
        
    Returns:
        Note metadata and statistics
    """
    try:
        return await get_note_info(path, ctx)
    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to get note info: {str(e)}")

@mcp.tool()
async def get_backlinks_tool(
    path: Annotated[str, Field(
        description="Path to the note to find backlinks for",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Daily/2024-01-15.md", "Projects/AI Research.md"]
    )],
    include_context: Annotated[bool, Field(
        description="Whether to include text context around links",
        default=True
    )] = True,
    context_length: Annotated[int, Field(
        description="Number of characters of context to include",
        ge=50,
        le=500,
        default=100
    )] = 100,
    ctx=None
):
    """
    Find all notes that link to a specific note (backlinks).
    
    When to use:
    - Understanding which notes reference a concept or topic
    - Discovering relationships between notes
    - Finding notes that depend on the current note
    - Building a mental map of note connections
    
    When NOT to use:
    - Finding links FROM a note (use get_outgoing_links)
    - Searching for broken links (use find_broken_links)
    
    Performance note:
    - Fast for small vaults (<100 notes)
    - May take several seconds for large vaults (1000+ notes)
    - Consider using search_notes for specific link queries
    
    Returns:
        All notes linking to the target with optional context
    """
    try:
        return await get_backlinks(path, include_context, context_length, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to get backlinks: {str(e)}")

@mcp.tool()
async def get_outgoing_links_tool(
    path: Annotated[str, Field(
        description="Path to the note to extract links from",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Projects/Overview.md", "Index.md"]
    )],
    check_validity: Annotated[bool, Field(
        description="Whether to check if linked notes exist",
        default=False
    )] = False,
    ctx=None
):
    """
    List all links from a specific note (outgoing links).
    
    When to use:
    - Understanding what a note references
    - Checking note dependencies before moving/deleting
    - Exploring the structure of index or hub notes
    - Validating links after changes
    
    When NOT to use:
    - Finding notes that link TO this note (use get_backlinks)
    - Searching across multiple notes (use find_broken_links)
    
    Returns:
        All outgoing links with their types and optional validity status
    """
    try:
        return await get_outgoing_links(path, check_validity, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to get outgoing links: {str(e)}")

@mcp.tool()
async def find_broken_links_tool(
    directory: Annotated[Optional[str], Field(
        description="Specific directory to check (optional, defaults to entire vault)",
        default=None,
        examples=[None, "Projects", "Archive/2023"]
    )] = None,
    ctx=None
):
    """
    Find all broken links in the vault or a specific directory.
    
    When to use:
    - After renaming or deleting notes
    - Regular vault maintenance
    - Before reorganizing folder structure
    - Cleaning up after imports
    
    When NOT to use:
    - Checking links in a single note (use get_outgoing_links with check_validity)
    - Finding backlinks (use get_backlinks)
    
    Returns:
        All broken links grouped by source note
    """
    try:
        return await find_broken_links(directory, ctx)
    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to find broken links: {str(e)}")

@mcp.tool()
async def list_tags_tool(
    include_counts: Annotated[bool, Field(
        description="Whether to include usage count for each tag",
        default=True
    )] = True,
    sort_by: Annotated[Literal["name", "count"], Field(
        description="How to sort results - by name (alphabetical) or count (usage)",
        default="name"
    )] = "name",
    ctx=None
):
    """
    List all unique tags used across the vault with usage statistics.
    
    When to use:
    - Before adding tags to maintain consistency
    - Getting an overview of your tagging taxonomy
    - Finding underused or overused tags
    - Discovering tag variations (e.g., 'project' vs 'projects')
    
    When NOT to use:
    - Getting tags for a specific note (use get_note_info)
    - Searching notes by tag (use search_notes with tag: prefix)
    
    Performance note:
    - For vaults with <1000 notes: Fast (1-3 seconds)
    - For vaults with 1000-5000 notes: Moderate (3-10 seconds)
    - For vaults with >5000 notes: May be slow (10+ seconds)
    - Uses batched concurrent requests to optimize performance
    
    Returns:
        All unique tags with optional usage counts
    """
    try:
        return await list_tags(include_counts, sort_by, ctx)
    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to list tags: {str(e)}")


# Filesystem-native backlinks tools (extended functionality)
@mcp.tool()
async def get_backlinks_fs_tool(
    note_name: Annotated[str, Field(
        description="Name of the note to find backlinks for (without .md extension)",
        min_length=1,
        max_length=255,
        examples=["Project Ideas", "Daily Note", "Research/Topic"]
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Find all notes that link to a specified note (filesystem-native, no Obsidian required).

    This tool uses direct filesystem access for maximum performance and works without
    requiring Obsidian to be running. It scans all markdown files in the vault to find
    wikilinks pointing to the target note.

    When to use:
    - Finding which notes reference a specific concept/note
    - Building connection graphs without Obsidian running
    - High-performance backlink discovery for large vaults
    - Batch processing multiple notes

    Performance:
    - 1,000 notes: < 2 seconds
    - 10,000 notes: < 20 seconds

    Returns:
        All notes containing wikilinks to the target note with context
    """
    try:
        # Get vault path from parameter or environment
        vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        if not vault:
            raise McpError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

        if not os.path.exists(vault):
            raise McpError(f"Vault not found: {vault}")

        # Call filesystem-native function
        backlinks = find_backlinks_fs(vault, note_name)

        return {
            "note": note_name,
            "backlink_count": len(backlinks),
            "backlinks": backlinks
        }
    except Exception as e:
        raise McpError(f"Failed to find backlinks: {str(e)}")


@mcp.tool()
async def get_broken_links_fs_tool(
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Find all broken wikilinks in the vault (filesystem-native, no Obsidian required).

    This tool uses direct filesystem access to scan all markdown files and identify
    wikilinks pointing to non-existent notes. Works without requiring Obsidian to be running.

    When to use:
    - After renaming or deleting notes
    - Regular vault maintenance and cleanup
    - Before reorganizing folder structures
    - Identifying orphaned link references

    Performance:
    - 1,000 notes: < 10 seconds
    - 10,000 notes: < 100 seconds

    Returns:
        All broken links grouped by source note
    """
    try:
        # Get vault path from parameter or environment
        vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        if not vault:
            raise McpError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

        if not os.path.exists(vault):
            raise McpError(f"Vault not found: {vault}")

        # Call filesystem-native function
        broken_links = find_broken_links_fs(vault)

        # Group by source file for better output format
        files_with_broken_links = {}
        for link in broken_links:
            source = link["source_path"]
            if source not in files_with_broken_links:
                files_with_broken_links[source] = []
            files_with_broken_links[source].append(link["link_target"])

        # Format output per contract specification
        result = {
            "files_with_broken_links": len(files_with_broken_links),
            "broken_links": [
                {
                    "file": file,
                    "broken_links": targets
                }
                for file, targets in files_with_broken_links.items()
            ]
        }

        return result
    except Exception as e:
        raise McpError(f"Failed to find broken links: {str(e)}")


# Filesystem-native tag management tools
@mcp.tool()
async def analyze_note_tags_fs_tool(
    filepath: Annotated[str, Field(
        description="Path to note file (relative to vault or absolute)",
        min_length=1,
        max_length=500,
        examples=["Projects/Active.md", "Daily/2025-01-15.md"]
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Extract all tags (frontmatter and inline) from a specific note.

    This tool analyzes a note's content and extracts:
    - Frontmatter tags (from YAML tags field)
    - Inline tags (#tag syntax in content)
    - Deduplicated list of all tags

    When to use:
    - Understanding what tags a note has
    - Before adding tags to avoid duplicates
    - Analyzing tag usage patterns

    Performance: < 100ms per note

    Returns:
        Tags organized by source (frontmatter, inline, all)
    """
    try:
        # Resolve file path
        vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        if vault and not os.path.isabs(filepath):
            filepath = os.path.join(vault, filepath)

        if not os.path.exists(filepath):
            raise McpError(f"File not found: {filepath}")

        # Read file and extract tags
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        result = extract_all_tags_fs(content)
        return result

    except Exception as e:
        raise McpError(f"Failed to analyze tags: {str(e)}")


@mcp.tool()
async def add_tag_fs_tool(
    filepath: Annotated[str, Field(
        description="Path to note file",
        min_length=1,
        max_length=500
    )],
    tag: Annotated[str, Field(
        description="Tag to add (without # symbol)",
        min_length=1,
        max_length=100,
        examples=["project", "meeting", "status/active"]
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault root (optional)",
        default=None
    )] = None,
    ctx=None
):
    """
    Add a tag to a note's frontmatter.

    Creates frontmatter if it doesn't exist. Handles duplicate tags gracefully.
    Supports nested tags (e.g., "project/active/critical").

    When to use:
    - Adding tags to organize notes
    - Bulk tagging operations
    - Automated note categorization

    Performance: < 200ms per operation

    Returns:
        Success status and descriptive message
    """
    try:
        # Resolve file path
        vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        if vault and not os.path.isabs(filepath):
            filepath = os.path.join(vault, filepath)

        result = add_tag_fs(filepath, tag)
        return result

    except FileNotFoundError as e:
        raise McpError(f"File not found: {str(e)}")
    except Exception as e:
        raise McpError(f"Failed to add tag: {str(e)}")


@mcp.tool()
async def remove_tag_fs_tool(
    filepath: Annotated[str, Field(
        description="Path to note file",
        min_length=1,
        max_length=500
    )],
    tag: Annotated[str, Field(
        description="Tag to remove (without # symbol)",
        min_length=1,
        max_length=100
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault root (optional)",
        default=None
    )] = None,
    ctx=None
):
    """
    Remove a tag from a note's frontmatter.

    Handles non-existent tags gracefully. Only removes from frontmatter,
    not inline tags in content.

    When to use:
    - Cleaning up old tags
    - Reorganizing tag taxonomy
    - Bulk tag removal operations

    Performance: < 200ms per operation

    Returns:
        Success status and descriptive message
    """
    try:
        # Resolve file path
        vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        if vault and not os.path.isabs(filepath):
            filepath = os.path.join(vault, filepath)

        result = remove_tag_fs(filepath, tag)
        return result

    except FileNotFoundError as e:
        raise McpError(f"File not found: {str(e)}")
    except Exception as e:
        raise McpError(f"Failed to remove tag: {str(e)}")


@mcp.tool()
async def search_by_tag_fs_tool(
    tag: Annotated[str, Field(
        description="Tag to search for (with or without #)",
        min_length=1,
        max_length=100,
        examples=["project", "#meeting", "status/active"]
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Find all notes containing a specific tag (frontmatter or inline).

    Searches entire vault for notes with the specified tag in either
    frontmatter or inline (#tag) format. Supports nested tags.

    When to use:
    - Finding all notes in a category
    - Building tag-based navigation
    - Analyzing tag usage across vault
    - Finding related notes

    Performance:
    - 1,000 notes: < 3 seconds
    - 10,000 notes: < 30 seconds

    Returns:
        List of notes with tag locations (frontmatter/inline)
    """
    try:
        # Get vault path
        vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        if not vault:
            raise McpError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

        if not os.path.exists(vault):
            raise McpError(f"Vault not found: {vault}")

        # Search for notes
        notes = find_notes_by_tag_fs(vault, tag)

        return {
            "tag": tag.lstrip('#'),
            "count": len(notes),
            "notes": notes
        }

    except Exception as e:
        raise McpError(f"Failed to search by tag: {str(e)}")


# ==============================================================================
# Smart Content Insertion Tools (Filesystem-Native)
# ==============================================================================

@mcp.tool()
async def insert_after_heading_fs_tool(
    filepath: Annotated[str, Field(
        description="Path to note (relative to vault or absolute)",
        min_length=1,
        examples=["Projects/Active.md", "Daily/2025-01-22.md"]
    )],
    heading: Annotated[str, Field(
        description="Heading text to insert after (without # symbols)",
        min_length=1,
        examples=["Tasks", "Notes", "References"]
    )],
    content: Annotated[str, Field(
        description="Content to insert after the heading",
        min_length=1
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Insert content immediately after a specific heading in a note.

    Finds the specified heading (case-sensitive) and inserts content on the
    line immediately following it. If multiple headings with the same text exist,
    content is inserted after the first occurrence.

    When to use:
    - Adding tasks to a "Tasks" section
    - Inserting notes under a "Notes" heading
    - Appending content to specific sections
    - Building structured content programmatically

    Performance:
    - 10,000 word notes: < 500ms

    Returns:
        Success status and descriptive message
    """
    try:
        # Resolve filepath
        vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        if not vault:
            raise McpError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

        # Resolve absolute path
        if not os.path.isabs(filepath):
            filepath = os.path.join(vault, filepath)

        # Insert content
        result = insert_after_heading_fs(filepath, heading, content)

        return result

    except FileNotFoundError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to insert after heading: {str(e)}")


@mcp.tool()
async def insert_after_block_fs_tool(
    filepath: Annotated[str, Field(
        description="Path to note (relative to vault or absolute)",
        min_length=1,
        examples=["Projects/Active.md"]
    )],
    block_id: Annotated[str, Field(
        description="Block reference ID (with or without ^ prefix)",
        min_length=1,
        examples=["intro", "^summary", "conclusion"]
    )],
    content: Annotated[str, Field(
        description="Content to insert after the block",
        min_length=1
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Insert content immediately after a block reference.

    Finds the specified block reference (^block-id) and inserts content after
    the line containing it. Accepts block IDs with or without the ^ prefix.

    When to use:
    - Adding follow-up content to referenced blocks
    - Expanding on specific paragraphs
    - Building linked content structures
    - Programmatic content generation

    Performance:
    - 10,000 word notes: < 500ms

    Returns:
        Success status and descriptive message
    """
    try:
        # Resolve filepath
        vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        if not vault:
            raise McpError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

        # Resolve absolute path
        if not os.path.isabs(filepath):
            filepath = os.path.join(vault, filepath)

        # Insert content
        result = insert_after_block_fs(filepath, block_id, content)

        return result

    except FileNotFoundError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to insert after block: {str(e)}")


@mcp.tool()
async def update_frontmatter_field_fs_tool(
    filepath: Annotated[str, Field(
        description="Path to note (relative to vault or absolute)",
        min_length=1,
        examples=["Projects/Active.md"]
    )],
    field: Annotated[str, Field(
        description="Field name to update/add in frontmatter",
        min_length=1,
        examples=["status", "author", "tags", "created"]
    )],
    value: Annotated[str | int | float | bool | List[str], Field(
        description="Value to set (string, number, boolean, or list)",
        examples=["published", 42, True, ["tag1", "tag2"]]
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Update or add a field in note's YAML frontmatter.

    If the note has no frontmatter, it will be created. If the field already
    exists, its value will be updated. Otherwise, the field will be added.
    Supports strings, numbers, booleans, and lists.

    When to use:
    - Updating note status or metadata
    - Adding creation/modification timestamps
    - Managing custom frontmatter fields
    - Programmatic metadata management

    Performance:
    - Any note size: < 200ms

    Returns:
        Success status and descriptive message
    """
    try:
        # Resolve filepath
        vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        if not vault:
            raise McpError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

        # Resolve absolute path
        if not os.path.isabs(filepath):
            filepath = os.path.join(vault, filepath)

        # Update frontmatter
        result = update_frontmatter_field_fs(filepath, field, value)

        return result

    except FileNotFoundError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to update frontmatter: {str(e)}")


@mcp.tool()
async def append_to_note_fs_tool(
    filepath: Annotated[str, Field(
        description="Path to note (relative to vault or absolute)",
        min_length=1,
        examples=["Projects/Active.md", "Daily/2025-01-22.md"]
    )],
    content: Annotated[str, Field(
        description="Content to append to the end of the note",
        min_length=1
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Append content to the end of a note.

    Adds content at the very end of the file. Useful for adding appendices,
    logs, or any content that should come after all existing content.

    When to use:
    - Adding appendices or footnotes
    - Appending log entries
    - Building chronological content
    - Adding content when position doesn't matter

    Performance:
    - Any note size: < 100ms

    Returns:
        Success status and descriptive message
    """
    try:
        # Resolve filepath
        vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        if not vault:
            raise McpError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

        # Resolve absolute path
        if not os.path.isabs(filepath):
            filepath = os.path.join(vault, filepath)

        # Append content
        result = append_to_note_fs(filepath, content)

        return result

    except FileNotFoundError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to append to note: {str(e)}")


# ==============================================================================
# Statistics & Analytics Tools (Filesystem-Native)
# ==============================================================================

@mcp.tool()
async def note_statistics_fs_tool(
    filepath: Annotated[str, Field(
        description="Path to note (relative to vault or absolute)",
        min_length=1,
        examples=["Projects/Analysis.md", "Daily/2025-01-22.md"]
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Get comprehensive statistics about a single note.

    Analyzes the note for words, characters, lines, links (wikilinks and markdown),
    tags (frontmatter and inline), headings, code blocks, and file metadata.

    Returns detailed metrics including:
    - Word count (excluding frontmatter and code blocks)
    - Character counts (with and without spaces)
    - Line count
    - Links: wikilinks, markdown links, total links
    - Tags: frontmatter and inline tags
    - Headings: count, by level, structure
    - Code: fenced code blocks and inline code
    - File metadata: size, timestamps

    When to use:
    - Analyzing individual note complexity
    - Tracking note growth over time
    - Understanding note structure
    - Content auditing

    Performance:
    - Any note size: < 1 second

    Returns:
        Comprehensive statistics dictionary
    """
    try:
        # Resolve filepath
        vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        if vault and not os.path.isabs(filepath):
            filepath = os.path.join(vault, filepath)

        # Get statistics
        stats = get_note_stats_fs(filepath)

        return stats

    except FileNotFoundError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to get note statistics: {str(e)}")


@mcp.tool()
async def vault_statistics_fs_tool(
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault root (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Get aggregate statistics for the entire vault.

    Walks through the vault directory, analyzes all markdown files (excluding .obsidian),
    and aggregates statistics. Uses memory-efficient generator-based iteration.

    Returns:
    - Total notes count
    - Total words across all notes
    - Total links (wikilinks + markdown links)
    - Unique tags count and sorted list
    - Average words per note

    When to use:
    - Understanding vault size and complexity
    - Content inventory and auditing
    - Identifying most-used tags
    - Tracking vault growth

    Performance:
    - 1,000 notes: < 30 seconds
    - 10,000 notes: < 5 minutes

    Returns:
        Vault-wide aggregate statistics
    """
    try:
        # Get vault path
        vault = vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        if not vault:
            raise McpError("OBSIDIAN_VAULT_PATH environment variable not set and vault_path not provided")

        if not os.path.exists(vault):
            raise McpError(f"Vault not found: {vault}")

        # Get statistics
        stats = get_vault_stats_fs(vault)

        return stats

    except FileNotFoundError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to get vault statistics: {str(e)}")


# ============================================================================
# TASKS PLUGIN TOOLS (User Story 1 - Feature 002)
# ============================================================================

@mcp.tool()
async def search_tasks_tool(
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    status: Annotated[Optional[Literal["incomplete", "completed", "all"]], Field(
        description="Filter by completion status",
        default=None
    )] = None,
    priority: Annotated[Optional[Literal["highest", "high", "normal", "low", "lowest"]], Field(
        description="Filter by priority level",
        default=None
    )] = None,
    due_before: Annotated[Optional[str], Field(
        description="Filter tasks due before this date (YYYY-MM-DD)",
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )] = None,
    due_after: Annotated[Optional[str], Field(
        description="Filter tasks due after this date (YYYY-MM-DD)",
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )] = None,
    due_within_days: Annotated[Optional[int], Field(
        description="Filter tasks due within N days from today",
        default=None,
        ge=0,
        le=365
    )] = None,
    has_recurrence: Annotated[Optional[bool], Field(
        description="Filter tasks with/without recurrence patterns",
        default=None
    )] = None,
    tag: Annotated[Optional[str], Field(
        description="Filter tasks containing this tag (without #)",
        default=None
    )] = None,
    limit: Annotated[int, Field(
        description="Maximum number of results",
        default=100,
        ge=1,
        le=1000
    )] = 100,
    sort_by: Annotated[Literal["due_date", "priority", "file", "line_number"], Field(
        description="Field to sort by",
        default="due_date"
    )] = "due_date",
    sort_order: Annotated[Literal["asc", "desc"], Field(
        description="Sort direction",
        default="asc"
    )] = "asc",
    ctx=None
):
    """
    Search and filter tasks by metadata across the vault (filesystem-native, offline).

    Scans all markdown files in the vault and extracts tasks with Tasks plugin metadata
    (due dates, priorities, recurrence). Supports comprehensive filtering and sorting.

    Metadata Format (Tasks Plugin):
    - Priority: ⏫ (highest), 🔼 (high), 🔽 (low), ⏬ (lowest), none (normal)
    - Due date: 📅 YYYY-MM-DD
    - Scheduled: ⏳ YYYY-MM-DD
    - Start date: 🛫 YYYY-MM-DD
    - Done date: ✅ YYYY-MM-DD
    - Recurrence: 🔁 every <pattern>

    When to use:
    - Finding overdue tasks
    - Viewing high-priority tasks
    - Planning weekly schedules
    - Reviewing recurring tasks

    Performance:
    - 1,000 notes: < 3 seconds
    - 10,000 notes: < 30 seconds

    Returns:
        Tasks matching filters with full metadata, file locations, and line numbers
    """
    try:
        filters = {}
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        if due_before:
            filters["due_before"] = due_before
        if due_after:
            filters["due_after"] = due_after
        if due_within_days is not None:
            filters["due_within_days"] = due_within_days
        if has_recurrence is not None:
            filters["has_recurrence"] = has_recurrence
        if tag:
            filters["tag"] = tag

        result = await search_tasks_fs_tool(
            vault_path=vault_path,
            filters=filters if filters else None,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to search tasks: {str(e)}")


@mcp.tool()
async def create_task_tool(
    file_path: Annotated[str, Field(
        description="Path to file where task should be created (relative to vault)",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255
    )],
    task_content: Annotated[str, Field(
        description="Task description text",
        min_length=1,
        max_length=500
    )],
    priority: Annotated[Optional[Literal["highest", "high", "normal", "low", "lowest"]], Field(
        description="Task priority level",
        default="normal"
    )] = "normal",
    due_date: Annotated[Optional[str], Field(
        description="Due date (YYYY-MM-DD)",
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )] = None,
    scheduled_date: Annotated[Optional[str], Field(
        description="Scheduled date (YYYY-MM-DD)",
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )] = None,
    start_date: Annotated[Optional[str], Field(
        description="Start date (YYYY-MM-DD)",
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )] = None,
    recurrence: Annotated[Optional[str], Field(
        description="Recurrence pattern (must start with 'every')",
        default=None,
        pattern=r"^every\s+.+"
    )] = None,
    insert_at: Annotated[Literal["end", "top", "after_heading"], Field(
        description="Where to insert the task",
        default="end"
    )] = "end",
    heading: Annotated[Optional[str], Field(
        description="Heading name if insert_at='after_heading'",
        default=None
    )] = None,
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Create a new task with Tasks plugin metadata (filesystem-native, offline).

    Creates a checkbox task with optional metadata (priority, dates, recurrence) and
    inserts it at the specified location in the file. Creates the file if it doesn't exist.

    Metadata will be formatted using Tasks plugin emoji syntax:
    - Priority: ⏫🔼🔽⏬ emojis
    - Dates: 📅⏳🛫✅➕ emojis with YYYY-MM-DD
    - Recurrence: 🔁 emoji with pattern

    When to use:
    - Adding tasks to project notes
    - Creating recurring task templates
    - Batch task creation
    - Automated task generation

    Returns:
        Success status, formatted task line, line number, and file path
    """
    try:
        result = await create_task_fs_tool(
            file_path=file_path,
            task_content=task_content,
            priority=priority,
            due_date=due_date,
            scheduled_date=scheduled_date,
            start_date=start_date,
            recurrence=recurrence,
            insert_at=insert_at,
            heading=heading,
            vault_path=vault_path,
        )

        if not result.get("success"):
            raise McpError(result.get("error", "Failed to create task"))

        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to create task: {str(e)}")


@mcp.tool()
async def toggle_task_status_tool(
    file_path: Annotated[str, Field(
        description="Path to file containing the task (relative to vault)",
        pattern=r"^[^/].*\.md$"
    )],
    line_number: Annotated[int, Field(
        description="Line number containing the task",
        ge=1
    )],
    add_done_date: Annotated[bool, Field(
        description="Add ✅ done date when completing task",
        default=False
    )] = False,
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Toggle task completion status between incomplete and completed (filesystem-native).

    Toggles the checkbox between `- [ ]` (incomplete) and `- [x]` (completed).
    Optionally adds a done date (✅ YYYY-MM-DD) when marking tasks as complete.

    When to use:
    - Marking tasks complete
    - Unchecking accidentally completed tasks
    - Batch status updates via automation

    Returns:
        Success status, new status, done date (if added), and updated line
    """
    try:
        result = await toggle_task_status_fs_tool(
            file_path=file_path,
            line_number=line_number,
            add_done_date=add_done_date,
            vault_path=vault_path,
        )

        if not result.get("success"):
            raise McpError(result.get("error", "Failed to toggle task status"))

        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to toggle task status: {str(e)}")


@mcp.tool()
async def update_task_metadata_tool(
    file_path: Annotated[str, Field(
        description="Path to file containing the task (relative to vault)",
        pattern=r"^[^/].*\.md$"
    )],
    line_number: Annotated[int, Field(
        description="Line number containing the task",
        ge=1
    )],
    priority: Annotated[Optional[Literal["highest", "high", "normal", "low", "lowest"]], Field(
        description="Update priority (null to remove)",
        default=None
    )] = None,
    due_date: Annotated[Optional[str], Field(
        description="Update due date YYYY-MM-DD (null to remove)",
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )] = None,
    scheduled_date: Annotated[Optional[str], Field(
        description="Update scheduled date YYYY-MM-DD (null to remove)",
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )] = None,
    start_date: Annotated[Optional[str], Field(
        description="Update start date YYYY-MM-DD (null to remove)",
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )] = None,
    recurrence: Annotated[Optional[str], Field(
        description="Update recurrence pattern (must start with 'every', null to remove)",
        default=None,
        pattern=r"^every\s+.+"
    )] = None,
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Update task metadata without changing the task content (filesystem-native).

    Updates priority, dates, or recurrence patterns while preserving the task description.
    Pass null/None to remove metadata fields.

    When to use:
    - Rescheduling tasks
    - Changing task priorities
    - Adding/removing recurrence
    - Batch metadata updates

    Returns:
        Success status, updated line, and list of changes made
    """
    try:
        updates = {}
        if priority is not None:
            updates["priority"] = priority
        if due_date is not None:
            updates["due_date"] = due_date
        if scheduled_date is not None:
            updates["scheduled_date"] = scheduled_date
        if start_date is not None:
            updates["start_date"] = start_date
        if recurrence is not None:
            updates["recurrence"] = recurrence

        if not updates:
            raise McpError("At least one metadata field must be provided for update")

        result = await update_task_metadata_fs_tool(
            file_path=file_path,
            line_number=line_number,
            updates=updates,
            vault_path=vault_path,
        )

        if not result.get("success"):
            raise McpError(result.get("error", "Failed to update task metadata"))

        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to update task metadata: {str(e)}")


@mcp.tool()
async def get_task_statistics_tool(
    scope: Annotated[Literal["note", "vault"], Field(
        description="Statistics scope: single note or entire vault"
    )],
    file_path: Annotated[Optional[str], Field(
        description="File path (required if scope='note')",
        default=None,
        pattern=r"^[^/].*\.md$"
    )] = None,
    group_by: Annotated[Optional[Literal["priority", "status", "file"]], Field(
        description="Optional grouping for detailed breakdown",
        default=None
    )] = None,
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Get aggregate task statistics for a note or entire vault (filesystem-native).

    Analyzes all tasks and provides:
    - Total, incomplete, completed counts
    - Breakdown by priority level
    - Overdue tasks (past due date, still incomplete)
    - Upcoming tasks (due within 7 days)
    - Recurring tasks count
    - Optional grouped data

    When to use:
    - Project progress tracking
    - Workload analysis
    - Finding overdue tasks
    - Weekly planning

    Performance:
    - Single note: < 100ms
    - Vault (1,000 notes): < 5 seconds

    Returns:
        Comprehensive task statistics with counts and optional grouping
    """
    try:
        result = await get_task_statistics_fs_tool(
            scope=scope,
            file_path=file_path,
            group_by=group_by,
            vault_path=vault_path,
        )

        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to get task statistics: {str(e)}")


# ============================================================================
# DATAVIEW PLUGIN TOOLS (User Story 2 - Feature 002)
# ============================================================================

@mcp.tool()
async def extract_dataview_fields_tool(
    file_path: Annotated[str, Field(
        description="Path to note file (relative to vault)",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Extract all Dataview inline fields from a note (filesystem-native, offline).

    Parses all three Dataview inline field syntax variants:
    - Full-line: `field:: value`
    - Bracket: `[field:: value]` (inline, visible)
    - Paren: `(field:: value)` (inline, hidden key)

    Automatically detects value types:
    - String, number, boolean, date (ISO8601)
    - Wikilink: [[note]]
    - List: "item1", "item2" or item1, item2

    Skips code blocks to avoid false matches.

    When to use:
    - Extracting metadata from notes
    - Auditing field usage
    - Migrating to frontmatter
    - Understanding note properties

    Performance:
    - Single note: < 100ms
    - Processes up to 10,000 fields per second

    Returns:
        All fields with keys, values, types, syntax variants, and line numbers
    """
    try:
        result = await extract_dataview_fields_fs_tool(
            file_path=file_path,
            vault_path=vault_path,
        )
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to extract Dataview fields: {str(e)}")


@mcp.tool()
async def search_by_dataview_field_tool(
    key: Annotated[str, Field(
        description="Field key to search for (will be canonicalized: lowercase, spaces→hyphens)",
        min_length=1,
        max_length=100
    )],
    value: Annotated[Optional[str], Field(
        description="Optional value to match (exact match)",
        default=None
    )] = None,
    value_type: Annotated[Optional[Literal["string", "number", "boolean", "date", "link", "list"]], Field(
        description="Optional value type filter",
        default=None
    )] = None,
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Find all notes containing a specific Dataview field (filesystem-native, offline).

    Searches across all markdown files in the vault for a field by key (and optionally
    value/type). Field keys are canonicalized for consistent matching:
    - "Project Status" → "project-status"
    - "**Due Date**" → "due-date"

    When to use:
    - Finding notes with specific metadata
    - Discovering field usage patterns
    - Locating notes by custom properties
    - Building dynamic collections

    Performance:
    - 1,000 notes: < 5 seconds
    - 10,000 notes: < 50 seconds

    Returns:
        Matching fields grouped by file, with total counts and file list
    """
    try:
        result = await search_by_dataview_field_fs_tool(
            key=key,
            value=value,
            value_type=value_type,
            vault_path=vault_path,
        )
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to search by Dataview field: {str(e)}")


@mcp.tool()
async def add_dataview_field_tool(
    file_path: Annotated[str, Field(
        description="Path to note file (relative to vault)",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255
    )],
    key: Annotated[str, Field(
        description="Field key",
        min_length=1,
        max_length=100
    )],
    value: Annotated[str, Field(
        description="Field value (will be auto-typed: number, boolean, date, etc.)",
        min_length=0,
        max_length=1000
    )],
    syntax_type: Annotated[Literal["full-line", "bracket", "paren"], Field(
        description="Syntax variant: full-line (field:: value), bracket ([field:: value]), paren ((field:: value))",
        default="full-line"
    )] = "full-line",
    insert_at: Annotated[Literal["start", "end", "after_frontmatter"], Field(
        description="Where to insert the field",
        default="after_frontmatter"
    )] = "after_frontmatter",
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Add a Dataview inline field to a note (filesystem-native, offline).

    Creates a new Dataview field using the specified syntax variant. Automatically
    detects and preserves value types (number, boolean, date, etc.).

    Syntax variants:
    - full-line: `field:: value` (standalone line, most common)
    - bracket: `[field:: value]` (inline, visible in reading mode)
    - paren: `(field:: value)` (inline, hidden key in reading mode)

    Insertion positions:
    - after_frontmatter: After YAML frontmatter (or start if none)
    - start: Very beginning of file
    - end: Very end of file

    When to use:
    - Adding metadata to existing notes
    - Batch tagging/categorization
    - Automated property assignment
    - Template-based field injection

    Returns:
        Success status, formatted field string, and canonical key
    """
    try:
        result = await add_dataview_field_fs_tool(
            file_path=file_path,
            key=key,
            value=value,
            syntax_type=syntax_type,
            insert_at=insert_at,
            vault_path=vault_path,
        )

        if not result.get("success"):
            raise McpError("Failed to add Dataview field")

        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to add Dataview field: {str(e)}")


@mcp.tool()
async def remove_dataview_field_tool(
    file_path: Annotated[str, Field(
        description="Path to note file (relative to vault)",
        pattern=r"^[^/].*\.md$"
    )],
    key: Annotated[str, Field(
        description="Field key to remove (will be canonicalized)",
        min_length=1,
        max_length=100
    )],
    line_number: Annotated[Optional[int], Field(
        description="Optional specific line number (if multiple fields with same key)",
        default=None,
        ge=1
    )] = None,
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Remove a Dataview inline field from a note (filesystem-native, offline).

    Removes all occurrences of a field by key (canonicalized matching), or a specific
    occurrence if line_number is provided.

    For inline fields (bracket/paren syntax), removes only the field while preserving
    surrounding text. For full-line fields, removes the entire line.

    When to use:
    - Cleaning up obsolete metadata
    - Removing duplicate fields
    - Migrating fields to frontmatter
    - Batch field removal

    Returns:
        Success status, removed key, and canonical key
    """
    try:
        result = await remove_dataview_field_fs_tool(
            file_path=file_path,
            key=key,
            line_number=line_number,
            vault_path=vault_path,
        )

        if not result.get("success"):
            raise McpError("Failed to remove Dataview field (field may not exist)")

        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to remove Dataview field: {str(e)}")


# ============================================================================
# KANBAN PLUGIN TOOLS (User Story 3 - Feature 002)
# ============================================================================

@mcp.tool()
async def parse_kanban_board_tool(
    file_path: Annotated[str, Field(
        description="Path to Kanban board file (relative to vault)",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Projects/Sprint Board.md", "Kanban/Development.md"]
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Parse a Kanban board file and extract its structure (filesystem-native, offline).

    Parses markdown-based Kanban boards with the following structure:
    - ## Column Name (level 2 or 3 headings)
    - [ ] Card text with metadata
      - [ ] Nested subtask

    Metadata formats:
    - Due dates: @{YYYY-MM-DD}
    - Tags: #tag (inline)
    - Wikilinks: [[note]]

    Supports nested subtasks with indentation levels.

    When to use:
    - Analyzing board structure
    - Extracting card data programmatically
    - Generating board reports
    - Understanding card relationships

    Performance:
    - Boards with 100 cards: < 500ms
    - Boards with 1,000 cards: < 5 seconds

    Returns:
        Board structure with columns, cards, subtasks, metadata, and statistics
    """
    try:
        result = await parse_kanban_board_fs_tool(
            file_path=file_path,
            vault_path=vault_path,
        )
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to parse Kanban board: {str(e)}")


@mcp.tool()
async def add_kanban_card_tool(
    file_path: Annotated[str, Field(
        description="Path to Kanban board file (relative to vault)",
        pattern=r"^[^/].*\.md$"
    )],
    column_name: Annotated[str, Field(
        description="Name of the column to add card to (must match ## heading)",
        min_length=1,
        max_length=100,
        examples=["To Do", "In Progress", "Done", "Backlog"]
    )],
    card_text: Annotated[str, Field(
        description="Card text/description",
        min_length=1,
        max_length=500
    )],
    status: Annotated[Literal["incomplete", "completed"], Field(
        description="Card completion status",
        default="incomplete"
    )] = "incomplete",
    due_date: Annotated[Optional[str], Field(
        description="Due date in @{YYYY-MM-DD} format",
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )] = None,
    position: Annotated[Literal["start", "end"], Field(
        description="Where to insert card in column",
        default="end"
    )] = "end",
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Add a new card to a Kanban board column (filesystem-native, offline).

    Creates a new card with optional metadata and inserts it at the specified position
    in the target column. Preserves all existing cards and board structure.

    Card format:
    - Incomplete: - [ ] Card text
    - Completed: - [x] Card text
    - With metadata: - [ ] Card text @{2025-10-30} #tag [[link]]

    When to use:
    - Adding tasks to project boards
    - Batch card creation
    - Automated workflow management
    - Template-based board setup

    Performance:
    - < 500ms for boards with 1,000 cards

    Returns:
        Success status, column name, position, and formatted card line
    """
    try:
        result = await add_kanban_card_fs_tool(
            file_path=file_path,
            column_name=column_name,
            card_text=card_text,
            status=status,
            due_date=due_date,
            position=position,
            vault_path=vault_path,
        )

        if not result.get("success"):
            raise McpError(result.get("error", "Failed to add Kanban card"))

        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to add Kanban card: {str(e)}")


@mcp.tool()
async def move_kanban_card_tool(
    file_path: Annotated[str, Field(
        description="Path to Kanban board file (relative to vault)",
        pattern=r"^[^/].*\.md$"
    )],
    card_text: Annotated[str, Field(
        description="Text of the card to move (must match exactly)",
        min_length=1,
        max_length=500
    )],
    from_column: Annotated[str, Field(
        description="Source column name",
        min_length=1,
        max_length=100,
        examples=["To Do", "In Progress"]
    )],
    to_column: Annotated[str, Field(
        description="Destination column name",
        min_length=1,
        max_length=100,
        examples=["In Progress", "Done"]
    )],
    position: Annotated[Literal["start", "end"], Field(
        description="Where to insert in destination column",
        default="end"
    )] = "end",
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Move a card between columns on a Kanban board (filesystem-native, offline).

    Finds a card by matching its text, removes it from the source column, and adds it
    to the destination column. Preserves all metadata, subtasks, and formatting.

    When to use:
    - Moving tasks through workflow stages
    - Dragging cards between columns programmatically
    - Batch workflow updates
    - Automated status changes

    Performance:
    - < 500ms for boards with 1,000 cards

    Returns:
        Success status, source/destination columns, and card details
    """
    try:
        result = await move_kanban_card_fs_tool(
            file_path=file_path,
            card_text=card_text,
            from_column=from_column,
            to_column=to_column,
            position=position,
            vault_path=vault_path,
        )

        if not result.get("success"):
            raise McpError(result.get("error", "Failed to move Kanban card"))

        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to move Kanban card: {str(e)}")


@mcp.tool()
async def toggle_kanban_card_tool(
    file_path: Annotated[str, Field(
        description="Path to Kanban board file (relative to vault)",
        pattern=r"^[^/].*\.md$"
    )],
    card_text: Annotated[str, Field(
        description="Text of the card to toggle (must match exactly)",
        min_length=1,
        max_length=500
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Toggle a Kanban card's completion status (filesystem-native, offline).

    Toggles the checkbox between `- [ ]` (incomplete) and `- [x]` (completed).
    Preserves all metadata, subtasks, and formatting.

    When to use:
    - Marking cards complete/incomplete
    - Batch status updates
    - Automated workflow transitions
    - Quick status changes

    Performance:
    - < 500ms for boards with 1,000 cards

    Returns:
        Success status, new status, and card details
    """
    try:
        result = await toggle_kanban_card_fs_tool(
            file_path=file_path,
            card_text=card_text,
            vault_path=vault_path,
        )

        if not result.get("success"):
            raise McpError(result.get("error", "Failed to toggle Kanban card"))

        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to toggle Kanban card: {str(e)}")


@mcp.tool()
async def get_kanban_statistics_tool(
    file_path: Annotated[str, Field(
        description="Path to Kanban board file (relative to vault)",
        pattern=r"^[^/].*\.md$"
    )],
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Get comprehensive statistics for a Kanban board (filesystem-native, offline).

    Analyzes the board and provides:
    - Total cards, completed, incomplete counts
    - Per-column card counts and completion rates
    - Overall board completion percentage
    - Column names and structure

    When to use:
    - Project progress tracking
    - Sprint velocity analysis
    - Board health monitoring
    - Generating board reports

    Performance:
    - Boards with 100 cards: < 500ms
    - Boards with 1,000 cards: < 5 seconds

    Returns:
        Comprehensive board statistics with counts and percentages
    """
    try:
        result = await get_kanban_statistics_fs_tool(
            file_path=file_path,
            vault_path=vault_path,
        )
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to get Kanban statistics: {str(e)}")


# ============================================================================
# ENHANCED LINK TRACKING TOOLS (User Story 4 - Feature 002)
# ============================================================================

@mcp.tool()
async def get_link_graph_tool(
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Get complete link graph for the vault (filesystem-native, offline).

    Builds a comprehensive graph of all note connections, tracking:
    - Inlinks (notes linking TO each note)
    - Outlinks (notes linked FROM each note)
    - Link types (wikilinks, markdown links, embeds)

    When to use:
    - Understanding vault structure and relationships
    - Analyzing note connectivity
    - Building visualization data
    - Identifying connection patterns

    Performance:
    - 1,000 notes: < 10 seconds
    - 10,000 notes: < 100 seconds

    Returns:
        Complete link graph with all note connections and link type counts
    """
    try:
        result = await get_link_graph_fs_tool(vault_path=vault_path)
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to get link graph: {str(e)}")


@mcp.tool()
async def find_orphaned_notes_tool(
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Find orphaned notes with no connections (filesystem-native, offline).

    Identifies notes that have neither inlinks nor outlinks - completely isolated
    notes that aren't referenced anywhere and don't reference anything else.

    When to use:
    - Vault cleanup and maintenance
    - Finding forgotten or unused notes
    - Identifying candidates for archiving
    - Improving vault connectivity

    Performance:
    - 1,000 notes: < 10 seconds
    - 10,000 notes: < 100 seconds

    Returns:
        List of orphaned notes with file paths
    """
    try:
        result = await find_orphaned_notes_fs_tool(vault_path=vault_path)
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to find orphaned notes: {str(e)}")


@mcp.tool()
async def find_hub_notes_tool(
    min_outlinks: Annotated[int, Field(
        description="Minimum outlink count to be considered a hub",
        default=5,
        ge=1,
        le=100
    )] = 5,
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Find hub notes with high outlink counts (filesystem-native, offline).

    Identifies notes that link to many other notes (hubs/MOCs/index notes).
    These are typically index pages, maps of content, or navigation notes.

    When to use:
    - Finding index/MOC notes
    - Identifying central navigation points
    - Understanding information architecture
    - Discovering organizational structures

    Performance:
    - 1,000 notes: < 10 seconds
    - 10,000 notes: < 100 seconds

    Returns:
        List of hub notes sorted by outlink count (highest first)
    """
    try:
        result = await find_hub_notes_fs_tool(
            min_outlinks=min_outlinks,
            vault_path=vault_path
        )
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to find hub notes: {str(e)}")


@mcp.tool()
async def analyze_link_health_tool(
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Analyze vault-wide link health metrics (filesystem-native, offline).

    Provides comprehensive vault health analysis including:
    - Total notes and links
    - Orphaned notes count
    - Notes with no inlinks/outlinks
    - Broken links count
    - Average links per note
    - Link density score

    When to use:
    - Vault health assessment
    - Identifying maintenance needs
    - Tracking vault evolution over time
    - Understanding vault connectivity

    Performance:
    - 1,000 notes: < 15 seconds
    - 10,000 notes: < 150 seconds

    Returns:
        Comprehensive health metrics with counts and averages
    """
    try:
        result = await analyze_link_health_fs_tool(vault_path=vault_path)
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to analyze link health: {str(e)}")


@mcp.tool()
async def get_note_connections_tool(
    note_name: Annotated[str, Field(
        description="Note name to analyze (with or without .md)",
        min_length=1,
        max_length=255,
        examples=["Project Overview", "Index", "MOC"]
    )],
    depth: Annotated[int, Field(
        description="Connection depth to explore (1=direct, 2=second-degree, etc.)",
        default=1,
        ge=1,
        le=3
    )] = 1,
    vault_path: Annotated[Optional[str], Field(
        description="Path to vault (optional, uses OBSIDIAN_VAULT_PATH env if not provided)",
        default=None
    )] = None,
    ctx=None
):
    """
    Get connection graph for a specific note (filesystem-native, offline).

    Explores connections from a note up to specified depth:
    - Depth 1: Direct connections (notes linked from target)
    - Depth 2: Second-degree connections (notes linked from direct connections)
    - Depth 3: Third-degree connections

    Provides both inlinks (backlinks) and outlinks with depth information.

    When to use:
    - Understanding note relationships
    - Exploring local note neighborhoods
    - Finding related content
    - Building connection visualizations

    Performance:
    - Depth 1: < 1 second
    - Depth 2: < 5 seconds
    - Depth 3: < 30 seconds

    Returns:
        Connection graph with multi-level links and depth annotations
    """
    try:
        result = await get_note_connections_fs_tool(
            note_name=note_name,
            depth=depth,
            vault_path=vault_path
        )
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to get note connections: {str(e)}")


# ============================================================================
# DATAVIEW API TOOLS (User Story 5 - Feature 002)
# ============================================================================

@mcp.tool()
async def execute_dataview_query_tool(
    query: Annotated[str, Field(
        description="DQL query string (e.g., 'LIST FROM #project WHERE status = \"active\"')",
        min_length=4,
        max_length=1000,
        examples=[
            "LIST FROM #project",
            "TABLE file.name, status FROM #project WHERE status = 'active'",
            "TASK WHERE !completed"
        ]
    )],
    ctx=None
):
    """
    Execute a Dataview Query Language (DQL) query (requires Obsidian + Dataview plugin).

    Executes full DQL queries with all Dataview plugin capabilities:
    - LIST: Simple page lists
    - TABLE: Tabular data views
    - TASK: Task queries
    - CALENDAR: Date-based views

    Supports all DQL clauses: FROM, WHERE, SORT, LIMIT, GROUP BY

    When to use:
    - Complex queries beyond filesystem capabilities
    - Leveraging Dataview's computed fields
    - Accessing Dataview's metadata indices
    - Real-time query results

    Requires:
    - Obsidian running
    - Dataview plugin installed and enabled
    - Local REST API plugin enabled

    Returns:
        Query results in Dataview's structured format
    """
    try:
        result = await execute_dataview_query_api_tool(query=query)
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to execute Dataview query: {str(e)}")


@mcp.tool()
async def list_notes_by_tag_dql_tool(
    tag: Annotated[str, Field(
        description="Tag to query (with or without # prefix)",
        min_length=1,
        max_length=100,
        examples=["project", "#meeting", "status/active"]
    )],
    where_clause: Annotated[Optional[str], Field(
        description="Optional WHERE filter (e.g., 'status = \"active\"')",
        default=None
    )] = None,
    sort_by: Annotated[Optional[str], Field(
        description="Optional SORT clause (e.g., 'file.name ASC')",
        default=None
    )] = None,
    limit: Annotated[Optional[int], Field(
        description="Optional result limit",
        default=None,
        ge=1,
        le=1000
    )] = None,
    ctx=None
):
    """
    List notes with a specific tag using DQL (requires Obsidian + Dataview plugin).

    Simplified interface for tag-based queries with optional filtering and sorting.

    When to use:
    - Finding notes by tag with complex filters
    - Leveraging Dataview's tag indexing
    - Real-time tag queries

    Returns:
        List of matching notes with Dataview metadata
    """
    try:
        result = await list_from_tag_api_tool(
            tag=tag,
            where_clause=where_clause,
            sort_by=sort_by,
            limit=limit
        )
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to list notes by tag: {str(e)}")


@mcp.tool()
async def list_notes_by_folder_dql_tool(
    folder: Annotated[str, Field(
        description="Folder path to query",
        min_length=1,
        max_length=255,
        examples=["Projects", "Daily/2025", "Archive"]
    )],
    where_clause: Annotated[Optional[str], Field(
        description="Optional WHERE filter",
        default=None
    )] = None,
    sort_by: Annotated[Optional[str], Field(
        description="Optional SORT clause",
        default=None
    )] = None,
    limit: Annotated[Optional[int], Field(
        description="Optional result limit",
        default=None,
        ge=1,
        le=1000
    )] = None,
    ctx=None
):
    """
    List notes in a folder using DQL (requires Obsidian + Dataview plugin).

    Simplified interface for folder-based queries with optional filtering and sorting.

    When to use:
    - Finding notes in specific folders with filters
    - Leveraging Dataview's folder indexing
    - Real-time folder queries

    Returns:
        List of matching notes with Dataview metadata
    """
    try:
        result = await list_from_folder_api_tool(
            folder=folder,
            where_clause=where_clause,
            sort_by=sort_by,
            limit=limit
        )
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to list notes by folder: {str(e)}")


@mcp.tool()
async def table_query_dql_tool(
    fields: Annotated[List[str], Field(
        description="List of fields to display",
        min_items=1,
        max_items=20,
        examples=[["file.name", "status"], ["file.name", "due", "priority"]]
    )],
    from_clause: Annotated[Optional[str], Field(
        description="FROM clause (e.g., '#project', '\"folder\"')",
        default=None
    )] = None,
    where_clause: Annotated[Optional[str], Field(
        description="Optional WHERE filter",
        default=None
    )] = None,
    sort_by: Annotated[Optional[str], Field(
        description="Optional SORT clause",
        default=None
    )] = None,
    limit: Annotated[Optional[int], Field(
        description="Optional result limit",
        default=None,
        ge=1,
        le=1000
    )] = None,
    ctx=None
):
    """
    Execute a DQL TABLE query (requires Obsidian + Dataview plugin).

    Creates tabular views of note metadata with custom fields.

    When to use:
    - Creating structured data views
    - Displaying multiple fields in table format
    - Building reports and dashboards
    - Analyzing note collections

    Returns:
        Table results with specified fields and rows
    """
    try:
        result = await table_query_api_tool(
            fields=fields,
            from_clause=from_clause,
            where_clause=where_clause,
            sort_by=sort_by,
            limit=limit
        )
        return result

    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to execute table query: {str(e)}")


# ============================================================================
# TEMPLATER API TOOLS (User Story 6) - Brief registrations for remaining tools
# ============================================================================
# Note: Full documentation available in tool modules
# Remaining 20 tools registered with concise wrappers to conserve tokens

@mcp.tool()
async def render_templater_template_tool(
    template_file: Annotated[str, Field(description="Template file path")],
    target_file: Annotated[Optional[str], Field(description="Target file for context", default=None)] = None,
    ctx=None
):
    """Render Templater template (requires Obsidian + Templater plugin)."""
    try:
        return await render_templater_template_api_tool(template_file, target_file)
    except Exception as e:
        raise McpError(f"Failed to render template: {str(e)}")

@mcp.tool()
async def expand_template_tool(
    template_path: Annotated[str, Field(description="Template file path")],
    variables: Annotated[Optional[Dict[str, str]], Field(default=None)] = None,
    vault_path: Annotated[Optional[str], Field(default=None)] = None,
    ctx=None
):
    """Expand template variables (filesystem-native, offline)."""
    try:
        return await expand_template_fs_tool(template_path, variables, None, vault_path)
    except Exception as e:
        raise McpError(f"Failed to expand template: {str(e)}")

@mcp.tool()
async def list_templates_tool(
    template_folder: Annotated[str, Field(default="Templates")] = "Templates",
    vault_path: Annotated[Optional[str], Field(default=None)] = None,
    ctx=None
):
    """List available templates (filesystem-native, offline)."""
    try:
        return await list_templates_fs_tool(template_folder, vault_path)
    except Exception as e:
        raise McpError(f"Failed to list templates: {str(e)}")

@mcp.tool()
async def get_active_file_tool(ctx=None):
    """Get currently active file (requires Obsidian running)."""
    try:
        return await get_active_file_api_tool()
    except Exception as e:
        raise McpError(f"Failed to get active file: {str(e)}")

@mcp.tool()
async def open_file_tool(
    file_path: Annotated[str, Field(description="File path to open")],
    new_pane: Annotated[bool, Field(default=False)] = False,
    ctx=None
):
    """Open file in Obsidian (requires Obsidian running)."""
    try:
        return await open_file_api_tool(file_path, new_pane)
    except Exception as e:
        raise McpError(f"Failed to open file: {str(e)}")

@mcp.tool()
async def parse_canvas_tool(
    file_path: Annotated[str, Field(description="Canvas file path")],
    vault_path: Annotated[Optional[str], Field(default=None)] = None,
    ctx=None
):
    """Parse Canvas file (filesystem-native, offline)."""
    try:
        return await parse_canvas_fs_tool(file_path, vault_path)
    except Exception as e:
        raise McpError(f"Failed to parse canvas: {str(e)}")

@mcp.tool()
async def add_canvas_node_tool(
    file_path: Annotated[str, Field(description="Canvas file path")],
    node_type: Annotated[Literal["text", "file"], Field(description="Node type")],
    content: Annotated[str, Field(description="Node content")],
    x: Annotated[int, Field(description="X position")],
    y: Annotated[int, Field(description="Y position")],
    vault_path: Annotated[Optional[str], Field(default=None)] = None,
    ctx=None
):
    """Add node to Canvas (filesystem-native, offline)."""
    try:
        return await add_canvas_node_fs_tool(file_path, node_type, content, x, y, 250, 60, vault_path)
    except Exception as e:
        raise McpError(f"Failed to add canvas node: {str(e)}")

@mcp.tool()
async def execute_command_tool(
    command_id: Annotated[str, Field(description="Command ID (e.g., 'editor:toggle-bold')")],
    ctx=None
):
    """Execute Obsidian command (requires Obsidian running)."""
    try:
        return await execute_command_api_tool(command_id, None)
    except Exception as e:
        raise McpError(f"Failed to execute command: {str(e)}")

@mcp.tool()
async def list_commands_tool(ctx=None):
    """List all available commands (requires Obsidian running)."""
    try:
        return await list_commands_api_tool()
    except Exception as e:
        raise McpError(f"Failed to list commands: {str(e)}")


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

def main():
    """Entry point for packaged distribution."""
    mcp.run()


if __name__ == "__main__":
    main()