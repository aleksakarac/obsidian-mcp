"""Compiled regex patterns for parsing Obsidian markdown syntax.

This module provides pre-compiled regex patterns for performance when
parsing Obsidian-specific markdown features across the vault.

Performance Note: Compiling regex patterns once at module load time
provides significant performance benefits when parsing multiple notes.
"""

import re

# Wikilink pattern: [[note]] or [[note|alias]] or [[note#heading]]
# Captures: full match, target (note/note#heading), optional alias
# Examples:
#   [[note1]] -> groups: ('note1', None)
#   [[note2|My Alias]] -> groups: ('note2', 'My Alias')
#   [[note3#heading]] -> groups: ('note3#heading', None)
#   [[note4#section|Link Text]] -> groups: ('note4#section', 'Link Text')
WIKILINK_PATTERN = re.compile(
    r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
)

# Markdown link pattern: [text](url)
# Captures: link text, URL
# Examples:
#   [Click here](page.md) -> groups: ('Click here', 'page.md')
#   [External](https://example.com) -> groups: ('External', 'https://example.com')
MARKDOWN_LINK = re.compile(
    r'\[([^\]]+)\]\(([^\)]+)\)'
)

# Embed pattern: ![[file]] or ![[file|alias]]
# Captures: embedded file path
# Examples:
#   ![[image.png]] -> groups: ('image.png',)
#   ![[Note#section]] -> groups: ('Note#section',)
EMBED_PATTERN = re.compile(
    r'!\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
)

# Tag pattern: #tag or #nested/tag
# Captures: tag content without the # prefix
# Valid characters: alphanumeric, underscore, hyphen, forward slash
# Examples:
#   #project -> 'project'
#   #project/planning -> 'project/planning'
#   #status-active -> 'status-active'
#   #project_2024 -> 'project_2024'
TAG_PATTERN = re.compile(
    r'#([a-zA-Z0-9_/-]+)'
)

# Heading pattern: # Heading or ## Heading or ### Heading (up to ######)
# Captures: heading level markers, heading text
# Multiline mode to match ^ at start of lines
# Examples:
#   # Main Heading -> groups: ('#', 'Main Heading')
#   ## Sub Heading -> groups: ('##', 'Sub Heading')
#   ### Level 3 -> groups: ('###', 'Level 3')
HEADING_PATTERN = re.compile(
    r'^(#{1,6})\s+(.+)$',
    re.MULTILINE
)

# Block reference pattern: ^block-id at end of line
# Captures: block ID without the ^ prefix
# Valid characters: alphanumeric, underscore, hyphen
# Must be at end of line (optionally followed by whitespace)
# Examples:
#   Some text ^important-block -> 'important-block'
#   Task item ^task-1 -> 'task-1'
#   Paragraph content ^ref_2024 -> 'ref_2024'
BLOCK_PATTERN = re.compile(
    r'\^([a-zA-Z0-9_-]+)\s*$',
    re.MULTILINE
)

# Frontmatter detection pattern: YAML frontmatter block at start of file
# Matches: ---\n ... \n---
# Used to detect presence of frontmatter (parsing done by python-frontmatter)
FRONTMATTER_PATTERN = re.compile(
    r'^---\s*\n.*?\n---\s*\n',
    re.DOTALL | re.MULTILINE
)

# ============================================================================
# TASKS PLUGIN PATTERNS (Tasks plugin emoji metadata)
# ============================================================================

# Task due date: 📅 2025-10-30 (also supports 📆 🗓)
# Captures: YYYY-MM-DD date
# Position: End of line anchor ensures metadata, not description
TASK_DUE_DATE = re.compile(
    r'[📅📆🗓]\s*(\d{4}-\d{2}-\d{2})\s*$',
    re.UNICODE
)

# Task scheduled date: ⏳ 2025-10-30
# Captures: YYYY-MM-DD date
TASK_SCHEDULED = re.compile(
    r'⏳\s*(\d{4}-\d{2}-\d{2})\s*$',
    re.UNICODE
)

# Task start date: 🛫 2025-10-30
# Captures: YYYY-MM-DD date
TASK_START = re.compile(
    r'🛫\s*(\d{4}-\d{2}-\d{2})\s*$',
    re.UNICODE
)

# Task done date: ✅ 2025-10-30
# Captures: YYYY-MM-DD date
TASK_DONE = re.compile(
    r'✅\s*(\d{4}-\d{2}-\d{2})\s*$',
    re.UNICODE
)

# Task created date: ➕ 2025-10-30
# Captures: YYYY-MM-DD date
TASK_CREATED = re.compile(
    r'➕\s*(\d{4}-\d{2}-\d{2})\s*$',
    re.UNICODE
)

# Task priority: ⏫ (highest), 🔼 (high), 🔽 (low), ⏬ (lowest)
# Captures: The emoji itself
# Note: No emoji = normal priority
TASK_PRIORITY = re.compile(
    r'(⏫|🔼|🔽|⏬)\s*$',
    re.UNICODE
)

# Task recurrence: 🔁 every week
# Captures: The recurrence pattern (e.g., "every week", "every 2 days")
TASK_RECURRENCE = re.compile(
    r'🔁\s*(every\s+.+?)\s*$',
    re.UNICODE
)

# Task checkbox status: - [ ] or - [x]
# Captures: checkbox status character (space or x/X)
TASK_CHECKBOX = re.compile(
    r'^[\s]*-\s*\[([ xX])\]\s+(.+)$',
    re.MULTILINE
)

# ============================================================================
# DATAVIEW PLUGIN PATTERNS (Inline field syntax variants)
# ============================================================================

# Full-line syntax: field:: value
# Captures: (key, value)
# Example: "status:: active" -> ("status", "active")
# Handles formatting: _field_:: value, **field**:: value
DATAVIEW_FULL_LINE = re.compile(
    r'^[_*~]*([-\w\s]+?)[_*~]*\s*::\s*(.+)$',
    re.MULTILINE
)

# Bracket syntax: [field:: value]
# Captures: (key, value)
# Example: "[priority:: high]" -> ("priority", "high")
DATAVIEW_BRACKET = re.compile(
    r'\[([^[\]()]+?)\s*::\s*([^\]]+)\]'
)

# Paren syntax: (field:: value) - hidden key
# Captures: (key, value)
# Example: "(rating:: 5)" -> ("rating", "5")
DATAVIEW_PAREN = re.compile(
    r'\(([^[\]()]+?)\s*::\s*([^\)]+)\)'
)

# ISO8601 date pattern for Dataview field value parsing
# Matches: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
DATE_ISO8601 = re.compile(
    r'^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?$'
)

# Quoted list pattern: ["item1", "item2", "item3"]
# Used for parsing Dataview list values
LIST_QUOTED = re.compile(
    r'"([^"]*)"'
)

# ============================================================================
# KANBAN PLUGIN PATTERNS (Markdown heading-based board structure)
# ============================================================================

# Kanban column heading: ## To Do
# Captures: (heading level markers, column name)
KANBAN_COLUMN = re.compile(
    r'^(#{2,3})\s+(.+)$',
    re.MULTILINE
)

# Kanban card: - [ ] Task name
# Captures: (checkbox status, card text)
KANBAN_CARD = re.compile(
    r'^([\s]*)-\s*\[([ xX])\]\s+(.+)$',
    re.MULTILINE
)

# Kanban card due date: @{2025-10-30}
# Captures: YYYY-MM-DD date
KANBAN_DATE = re.compile(
    r'@\{(\d{4}-\d{2}-\d{2})\}'
)

# ============================================================================
# ENHANCED LINK TRACKING PATTERNS
# ============================================================================

# Wikilink (already exists as WIKILINK_PATTERN, but adding related patterns)

# Embed syntax: ![[file]] or ![[image.png]]
# Captures: (embedded file path)
LINK_EMBED = re.compile(
    r'!\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
)

# Section link: [[note#section]]
# Captures: (note, section/heading)
LINK_SECTION = re.compile(
    r'\[\[([^#\]]+)#([^\]|]+)(?:\|[^\]]+)?\]\]'
)

# Block reference link: [[note^block-id]]
# Captures: (note, block-id)
LINK_BLOCK = re.compile(
    r'\[\[([^\^]+)\^([^\]|]+)(?:\|[^\]]+)?\]\]'
)

# ============================================================================
# TAG PATTERN (enhanced version already exists, keeping original)
# ============================================================================
# TAG_PATTERN already defined above

# ============================================================================
# HELPER PATTERNS FOR VALIDATION
# ============================================================================

# Valid Obsidian filename characters
# Used for validation before file operations
VALID_FILENAME = re.compile(
    r'^[^<>:"/\\|?*\x00-\x1f]+$'
)
