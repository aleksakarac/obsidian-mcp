# Feature Specification: Hybrid Plugin Control System

**Feature Branch**: `002-hybrid-plugin-control`
**Created**: 2025-10-22
**Status**: Draft
**Input**: User description: "Add hybrid filesystem and API-based control for Obsidian plugins including Tasks, Dataview, Templater, Kanban, Canvas, Excalidraw, and workspace management while maintaining filesystem-native priority for all operations that can be done via direct file manipulation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Tasks with Metadata (Priority: P1)

As an Obsidian user working with Claude Code, I want to search, filter, and create tasks with full Tasks plugin metadata (due dates, priorities, recurrence) so I can manage my task list programmatically without opening Obsidian.

**Why this priority**: Task management is the most common productivity workflow. The Tasks plugin is one of the top 5 most downloaded plugins (2.8M downloads), and users rely on task metadata for filtering and organizing their work. This delivers immediate value for the largest user segment and can be implemented entirely via filesystem operations.

**Independent Test**: Can be fully tested by creating tasks with metadata, searching for tasks by due date/priority, and toggling completion status. Delivers standalone value for task management workflows without requiring any other user stories.

**Acceptance Scenarios**:

1. **Given** a vault with multiple notes containing tasks with due dates, **When** I search for tasks due within the next 7 days, **Then** I receive a filtered list of upcoming tasks with their file locations and metadata
2. **Given** a note path and task details, **When** I create a task with due date "2025-10-30", priority "high", and recurrence "every Monday", **Then** the task is created with proper emoji formatting: `- [ ] Task 📅 2025-10-30 ⏫ 🔁 every Monday`
3. **Given** a task at a specific line in a file, **When** I mark the task as complete, **Then** the checkbox changes from `- [ ]` to `- [x]` and a completion date is added if configured
4. **Given** tasks with various priority levels (high ⏫, medium 🔼, low 🔽, none), **When** I search for high-priority tasks, **Then** only tasks marked with ⏫ are returned
5. **Given** tasks with recurrence patterns, **When** I complete a recurring task, **Then** the system identifies it as recurring based on the 🔁 emoji and metadata

---

### User Story 2 - Extract and Query Dataview Metadata (Priority: P1)

As an Obsidian user, I want to extract Dataview inline fields from my notes and search notes by field values so I can organize and retrieve information programmatically based on custom metadata without Obsidian running.

**Why this priority**: Dataview is the most downloaded community plugin (3.4M downloads) and users rely on inline fields for metadata-driven organization. Filesystem-based field extraction enables powerful querying without requiring Obsidian to run, making it equally important as task management for knowledge workers.

**Independent Test**: Can be fully tested by creating notes with inline fields, extracting metadata, and searching by field values. Delivers standalone value for metadata-driven workflows and doesn't depend on other stories.

**Acceptance Scenarios**:

1. **Given** a note containing inline fields like `status:: active` and `project:: MyProject`, **When** I request note statistics, **Then** the response includes extracted Dataview fields: `{"status": "active", "project": "MyProject"}`
2. **Given** multiple notes with a `status` field, **When** I search for notes where `status` equals "active", **Then** I receive all notes containing `status:: active` (in any inline format: `field::`, `[field::]`, `(field::)`)
3. **Given** a note with both frontmatter and inline Dataview fields, **When** I extract metadata, **Then** both frontmatter YAML and inline fields are returned separately and combined
4. **Given** nested inline fields like `task::[priority:: high]`, **When** parsing the note, **Then** nested fields are correctly extracted
5. **Given** inline fields with various value types (strings, numbers, lists), **When** extracting metadata, **Then** values preserve their original format

---

### User Story 3 - Manipulate Kanban Boards (Priority: P2)

As an Obsidian user, I want to read Kanban board structure, add cards, and move cards between columns programmatically so I can manage project boards through Claude Code without manual editing.

**Why this priority**: Kanban is highly popular (1.9M downloads) for visual project management, but it's less critical than tasks/metadata since board manipulation is less frequent than task management. Users can accomplish goals manually if needed, making this a productivity enhancement rather than core functionality.

**Independent Test**: Can be fully tested by parsing kanban markdown files, adding cards to columns, and moving cards between columns. Delivers standalone value for project board management workflows.

**Acceptance Scenarios**:

1. **Given** a Kanban board markdown file with columns "To Do", "In Progress", "Done", **When** I parse the board structure, **Then** I receive a structured representation with column names and cards per column
2. **Given** a Kanban board file and a column name "To Do", **When** I add a new card "Design API", **Then** the card appears as `- [ ] Design API` under the "To Do" heading
3. **Given** a card "Implement feature" in the "In Progress" column, **When** I move it to the "Done" column, **Then** the card is removed from "In Progress" and added to "Done" with checkbox updated to `- [x]`
4. **Given** a Kanban board with nested cards (subtasks), **When** parsing the board, **Then** subtask hierarchies are preserved in the structured output
5. **Given** a board with card metadata (tags, dates), **When** adding a card with metadata, **Then** the metadata is properly formatted in the markdown

---

### User Story 4 - Track All Link Types (Priority: P2)

As an Obsidian user, I want to track embedded links, block references, and section links in addition to regular wikilinks so I can understand all connections between my notes for comprehensive knowledge graph analysis.

**Why this priority**: Link tracking is important for understanding note relationships, but basic wikilink support already exists. Enhanced tracking provides deeper insights but isn't essential for basic workflows, making it a valuable enhancement rather than critical functionality.

**Independent Test**: Can be fully tested by creating notes with various link types and verifying all types are detected. Delivers standalone value for knowledge graph analysis without dependencies.

**Acceptance Scenarios**:

1. **Given** a note containing an embedded link `![[image.png]]`, **When** I search for references to "image.png", **Then** the embed is identified separately from regular wikilinks
2. **Given** a note with a block reference `[[note#^summary]]`, **When** I find backlinks to "note", **Then** block references are listed with the block ID (`^summary`)
3. **Given** a note with a section link `[[note#Heading]]`, **When** searching for references, **Then** section links are tracked with the heading name
4. **Given** multiple link types to the same note (wikilink, embed, section, block), **When** analyzing connections, **Then** each link type is counted and listed separately
5. **Given** a note with transclusions of other notes, **When** requesting embed references, **Then** all transclusions are identified with context

---

### User Story 5 - Execute Dataview Queries (Priority: P2)

As an Obsidian user, I want to execute Dataview Query Language (DQL) and DataviewJS queries through Claude Code so I can generate dynamic views and tables of my notes based on complex criteria without manually writing queries in Obsidian.

**Why this priority**: While Dataview is highly popular, query execution requires Obsidian running and is needed less frequently than metadata extraction. Users primarily need to view query results occasionally rather than constantly, making this a valuable but non-critical enhancement.

**Independent Test**: Can be fully tested by executing DQL queries (LIST, TABLE, TASK) and verifying results match expected output. Requires Obsidian running but delivers standalone value for dynamic views.

**Acceptance Scenarios**:

1. **Given** Obsidian is running with the Local REST API plugin, **When** I execute a DQL query `LIST FROM #project`, **Then** I receive a list of all notes tagged with "project"
2. **Given** a TABLE query `TABLE file.ctime, file.mtime FROM "Projects"`, **When** executed, **Then** results include file paths with creation and modification timestamps in table format
3. **Given** a TASK query `TASK WHERE !completed AND due < date(today)`, **When** executed, **Then** all overdue incomplete tasks are returned with their source files
4. **Given** a DataviewJS code block with custom JavaScript, **When** executed, **Then** the JavaScript runs in Obsidian's context and returns computed results
5. **Given** Obsidian is not running, **When** attempting to execute a Dataview query, **Then** a clear error message explains that Obsidian must be running with the Local REST API plugin enabled

---

### User Story 6 - Execute Templates with Dynamic Variables (Priority: P3)

As an Obsidian user, I want to execute Templater templates with full JavaScript support and variable substitution so I can generate notes with dynamic content programmatically through Claude Code.

**Why this priority**: Templater is popular (3.2M downloads) but template execution is less frequent than daily task/metadata operations. Users can manually apply templates if needed, and basic template support can be achieved via filesystem (User Story 7), making full Templater execution a nice-to-have enhancement.

**Independent Test**: Can be fully tested by triggering Templater templates with variables and verifying dynamic content generation. Requires Obsidian running but delivers standalone value for automated note creation.

**Acceptance Scenarios**:

1. **Given** Obsidian is running with Templater plugin, **When** I execute a template "Daily Note" with variables `{date: "2025-10-22"}`, **Then** a note is created with dynamic date substitution via Templater's JavaScript engine
2. **Given** a Templater template with `<% tp.date.now("YYYY-MM-DD") %>`, **When** executed, **Then** the current date is inserted in the specified format
3. **Given** a template with user prompts `<% tp.system.prompt("Enter title") %>`, **When** executed with provided values, **Then** prompts are automatically filled without manual input
4. **Given** a template with file operations `<% tp.file.create_new() %>`, **When** executed, **Then** Templater's file manipulation commands run successfully
5. **Given** custom user scripts defined in Templater settings, **When** a template calls these scripts, **Then** they execute with access to Templater's API

---

### User Story 7 - Apply Simple Templates (Priority: P3)

As an Obsidian user, I want to apply template files with basic variable substitution (dates, titles, custom variables) without requiring Obsidian running so I can quickly create notes from templates via filesystem operations.

**Why this priority**: Basic templating without JavaScript provides good value for simple use cases and works offline. However, it's less powerful than Templater and less frequently used than task/metadata operations, making it a lower-priority productivity enhancement.

**Independent Test**: Can be fully tested by applying templates with variable substitution and verifying output. Works without Obsidian and delivers standalone value for note creation workflows.

**Acceptance Scenarios**:

1. **Given** a template file with `{{date}}` and `{{title}}` placeholders, **When** I create a note from this template with title "Meeting Notes", **Then** placeholders are replaced with current date and provided title
2. **Given** a templates folder in the vault, **When** I list available templates, **Then** all markdown files in the templates folder are returned with their names
3. **Given** custom variables `{project: "Alpha", status: "active"}`, **When** applying a template with `{{project}}` and `{{status}}`, **Then** custom variables are substituted correctly
4. **Given** a template with formatting like `# {{title}}\nCreated: {{date}}`, **When** applied, **Then** markdown structure is preserved with variables replaced
5. **Given** a template with undefined variables, **When** applied without providing those variables, **Then** undefined variables are left as empty strings or clear placeholders

---

### User Story 8 - Control Obsidian Workspace UI (Priority: P3)

As an Obsidian user, I want to programmatically open files in specific panes, control sidebar visibility, and save/load workspace layouts so I can automate my workspace setup through Claude Code.

**Why this priority**: Workspace control is valuable for power users but not essential for core knowledge management workflows. Most users can manually arrange their workspace, and it requires Obsidian running, making this an advanced feature for automation enthusiasts rather than a broad-need enhancement.

**Independent Test**: Can be fully tested by opening files in different pane configurations and toggling UI elements. Requires Obsidian running but delivers standalone value for workspace automation.

**Acceptance Scenarios**:

1. **Given** Obsidian is running, **When** I open a file in "split-vertical" pane mode, **Then** the file opens in a new vertical split pane
2. **Given** the left sidebar is visible, **When** I toggle the left sidebar, **Then** it becomes hidden and the command confirms the new state
3. **Given** a custom workspace layout, **When** I save it with name "Writing Mode", **Then** the layout (pane arrangement, sidebar states, open files) is saved and can be restored later
4. **Given** a saved workspace layout "Writing Mode", **When** I load this layout, **Then** Obsidian restores the exact pane configuration, sidebar states, and previously open files
5. **Given** multiple files to open, **When** I specify different pane targets for each, **Then** files open in their designated panes (new tab, current pane, split, etc.)

---

### User Story 9 - Create and Edit Canvas Files (Priority: P3)

As an Obsidian user, I want to programmatically create canvas files, add nodes (notes, text, media), and define connections between nodes so I can generate visual knowledge maps and diagrams through Claude Code.

**Why this priority**: Canvas is powerful for visual thinkers but represents a smaller use case than text-based workflows. Canvas manipulation can be done via filesystem (JSON format) for creation, but viewing/editing benefits from Obsidian UI. This is a specialized feature for specific workflows rather than broad-need functionality.

**Independent Test**: Can be fully tested by creating canvas JSON files with nodes and edges, then verifying structure. Canvas viewing requires Obsidian but file creation works standalone, delivering value for visual workflow automation.

**Acceptance Scenarios**:

1. **Given** a request to create a canvas with two file nodes, **When** I create the canvas with nodes pointing to "note1.md" and "note2.md", **Then** a `.canvas` JSON file is created with properly formatted node objects including positions and file references
2. **Given** an existing canvas file, **When** I add a text node with content "Summary: Key points", **Then** the text node is added to the JSON with a unique ID and specified position
3. **Given** two nodes in a canvas, **When** I create a connection from node "A" to node "B", **Then** an edge object is added to the JSON linking the node IDs
4. **Given** a canvas file path, **When** I request to open it in Obsidian UI (API-based), **Then** Obsidian opens the canvas in canvas view mode
5. **Given** a complex canvas structure, **When** parsing the canvas file, **Then** all nodes (file, text, group, link) and edges are correctly identified with their properties

---

### User Story 10 - Execute Obsidian Commands (Priority: P3)

As an Obsidian user, I want to execute any Obsidian command (core or plugin) by command ID so I can trigger any Obsidian functionality programmatically through Claude Code, enabling automation of plugin-specific actions.

**Why this priority**: Command execution is a powerful catch-all for plugin integration but is most useful for edge cases and advanced automation. Core workflows are better served by dedicated tools. This provides flexibility but isn't essential for common tasks, making it a lower-priority enabler for power users.

**Independent Test**: Can be fully tested by listing available commands and executing specific commands by ID. Requires Obsidian running but delivers standalone value as a universal plugin integration mechanism.

**Acceptance Scenarios**:

1. **Given** Obsidian is running with Local REST API plugin, **When** I request a list of all available commands, **Then** I receive command IDs and names for all core and plugin commands
2. **Given** a command ID like "editor:toggle-bold", **When** I execute this command, **Then** the command triggers in Obsidian and returns success confirmation
3. **Given** a Dataview-specific command like "dataview:refresh-views", **When** executed, **Then** Dataview refreshes all query results in open notes
4. **Given** multiple commands to execute in sequence, **When** I batch-execute them, **Then** commands run in order and results are returned for each
5. **Given** a command that requires parameters, **When** executed with appropriate parameters, **Then** the command runs with the provided parameter values

---

### Edge Cases

- What happens when the Local REST API plugin is not installed or not running when attempting API-based operations?
- How does the system handle malformed Tasks plugin metadata (e.g., invalid date formats, unrecognized emoji)?
- What happens when a Dataview inline field has the same name as a frontmatter field?
- How does the system handle Kanban boards with non-standard column formats or nested structures?
- What happens when executing a Dataview query that takes a very long time to complete (10+ seconds)?
- How does the system handle canvas files with corrupted JSON or missing required fields?
- What happens when attempting to execute a command that doesn't exist or is disabled?
- How does the system handle race conditions when filesystem and API operations modify the same file?
- What happens when Obsidian crashes or becomes unresponsive during an API operation?
- How does the system handle very large Kanban boards (100+ cards) or canvas files (500+ nodes)?
- What happens when a template file references variables that create infinite loops or recursive expansions?
- How does the system handle workspace layouts that reference files or plugins that no longer exist?

## Requirements *(mandatory)*

### Functional Requirements

#### Tasks Plugin Support (Filesystem-Native)

- **FR-001**: System MUST parse Tasks plugin emoji metadata from markdown task lines including due dates (📅), priorities (⏫🔼🔽), recurrence (🔁), start dates (🛫), and completion dates (✅)
- **FR-002**: System MUST search and filter tasks by metadata criteria including due date ranges, priority levels, completion status, and recurrence patterns
- **FR-003**: System MUST create new tasks with properly formatted Tasks plugin metadata emojis in the correct order
- **FR-004**: System MUST toggle task completion status by changing checkboxes between `- [ ]` and `- [x]` and optionally adding completion dates
- **FR-005**: System MUST extract all tasks from a note or vault with their metadata, file locations, and line numbers

#### Dataview Plugin Support (Hybrid)

- **FR-006**: System MUST extract Dataview inline fields from markdown content using patterns `field::`, `[field::]`, and `(field::)`
- **FR-007**: System MUST search notes by inline field name and value across the entire vault
- **FR-008**: System MUST include Dataview inline fields in note statistics alongside frontmatter and tags
- **FR-009**: System MUST execute Dataview Query Language (DQL) queries via Obsidian Local REST API when Obsidian is running
- **FR-010**: System MUST execute DataviewJS code blocks via Obsidian Local REST API with access to Dataview's JavaScript API
- **FR-011**: System MUST return query results in structured format (lists, tables, task lists) matching Dataview's output format
- **FR-012**: System MUST provide clear error messages when Dataview query execution fails or Obsidian is not running

#### Kanban Plugin Support (Filesystem-Native)

- **FR-013**: System MUST parse Kanban markdown files to extract board structure with column names and cards
- **FR-014**: System MUST add new cards to specified columns in Kanban boards with proper checkbox formatting
- **FR-015**: System MUST move cards between columns by updating markdown structure
- **FR-016**: System MUST preserve card metadata (tags, dates, priorities) when manipulating Kanban boards
- **FR-017**: System MUST handle nested cards (subtasks) in Kanban board structures

#### Enhanced Link Tracking (Filesystem-Native)

- **FR-018**: System MUST detect and track embedded links using syntax `![[note]]` separately from regular wikilinks
- **FR-019**: System MUST detect and track block references using syntax `[[note#^block-id]]` with block ID extraction
- **FR-020**: System MUST detect and track section links using syntax `[[note#heading]]` with heading name extraction
- **FR-021**: System MUST categorize and count different link types (wikilinks, embeds, block references, section links) in backlink analysis
- **FR-022**: System MUST find all notes that embed a specific note via transclusion syntax

#### Template Support (Hybrid)

- **FR-023**: System MUST apply template files with basic variable substitution for date, time, title, and custom variables (filesystem-native)
- **FR-024**: System MUST list all template files from designated template folders
- **FR-025**: System MUST execute Templater plugin templates with full JavaScript support via Obsidian Local REST API when Obsidian is running
- **FR-026**: System MUST handle Templater's dynamic variables including date functions, file operations, and system prompts
- **FR-027**: System MUST provide fallback to basic template substitution when Templater is not available or Obsidian is not running

#### Canvas File Manipulation (Hybrid)

- **FR-028**: System MUST create `.canvas` JSON files with nodes (file, text, group, link) and edges (filesystem-native)
- **FR-029**: System MUST parse existing canvas files to extract node and edge structures
- **FR-030**: System MUST add nodes to existing canvas files with position coordinates and proper formatting
- **FR-031**: System MUST create connections (edges) between canvas nodes by node IDs
- **FR-032**: System MUST open canvas files in Obsidian's canvas view via API command when Obsidian is running

#### Obsidian Local REST API Integration

- **FR-033**: System MUST establish HTTP connection to Obsidian Local REST API using configured base URL and API key
- **FR-034**: System MUST detect API availability before attempting API-based operations and provide graceful degradation
- **FR-035**: System MUST execute Obsidian commands by command ID via REST API `/commands/{id}` endpoint
- **FR-036**: System MUST retrieve list of all available commands (core and plugin) from REST API
- **FR-037**: System MUST handle API authentication using Bearer token in request headers
- **FR-038**: System MUST handle API errors with informative messages including connection failures, authentication errors, and command execution failures

#### Workspace Control (API-Based)

- **FR-039**: System MUST open files in specified pane configurations (new tab, current pane, split-vertical, split-horizontal) via API
- **FR-040**: System MUST control sidebar visibility (show, hide, toggle) for left and right sidebars via API commands
- **FR-041**: System MUST save current workspace layout with a user-specified name via Workspaces plugin commands
- **FR-042**: System MUST load saved workspace layouts by name, restoring pane configuration, sidebar states, and open files
- **FR-043**: System MUST retrieve currently active file information from Obsidian via API

#### Graph Analysis (Filesystem-Native)

- **FR-044**: System MUST identify orphan notes (notes with no incoming or outgoing links) by analyzing vault-wide link structure
- **FR-045**: System MUST calculate note connectivity metrics including incoming link count, outgoing link count, and centrality score
- **FR-046**: System MUST identify hub notes (highly connected notes) based on configurable connection thresholds

#### Configuration and Environment

- **FR-047**: System MUST read Obsidian Local REST API configuration from environment variables (API URL, API key)
- **FR-048**: System MUST provide default API URL (http://localhost:27124) when not explicitly configured
- **FR-049**: System MUST maintain existing OBSIDIAN_VAULT_PATH environment variable for filesystem operations
- **FR-050**: System MUST use OBSIDIAN_REST_API_KEY environment variable for API authentication

#### Tool Naming and Organization

- **FR-051**: All filesystem-native tools MUST use `_fs_tool` suffix in their names (e.g., `search_tasks_fs_tool`)
- **FR-052**: All API-based tools MUST use `_api_tool` suffix in their names (e.g., `execute_dataview_query_api_tool`)
- **FR-053**: Tool descriptions MUST clearly indicate whether Obsidian running is required
- **FR-054**: System MUST maintain backward compatibility with all existing filesystem-native tools from feature 001

#### Error Handling and Validation

- **FR-055**: System MUST validate Tasks plugin emoji formats and provide clear error messages for invalid metadata
- **FR-056**: System MUST validate Dataview inline field syntax before extraction
- **FR-057**: System MUST validate Kanban board markdown structure before manipulation
- **FR-058**: System MUST validate canvas JSON structure for required fields before file creation
- **FR-059**: System MUST timeout API requests after 30 seconds and return timeout error messages
- **FR-060**: System MUST retry failed API requests once before returning failure to user

### Key Entities

- **Task**: A checkbox item in markdown with optional Tasks plugin metadata
  - Attributes: content text, completion status, due date, priority level, recurrence pattern, start date, completion date, tags, line number, source file
  - Relationships: Belongs to a note, may have subtasks, may be part of a recurring series

- **Dataview Inline Field**: A key-value metadata pair embedded in note content
  - Attributes: field name, field value, field type (string/number/list), syntax format (bare/bracketed/parenthesized), line number, source file
  - Relationships: Belongs to a note, may duplicate frontmatter fields, may be nested

- **Kanban Board**: A markdown file representing a visual project board
  - Attributes: file path, column list, total card count
  - Relationships: Contains columns, columns contain cards, stored as markdown file in vault

- **Kanban Column**: A section in a Kanban board headed by a heading
  - Attributes: column name (heading text), card list, card count, heading level
  - Relationships: Belongs to a Kanban board, contains multiple cards

- **Kanban Card**: A task or text item within a Kanban column
  - Attributes: card text, completion status, metadata (tags/dates), nesting level
  - Relationships: Belongs to a column, may have subtasks (nested cards)

- **Link Reference**: A connection from one note to another
  - Attributes: link type (wikilink/embed/section/block), source file, target file, link text, alias, section name, block ID, line number
  - Relationships: Originates from source note, points to target note, may have context text

- **Canvas File**: A JSON file representing a visual knowledge map
  - Attributes: file path, node list, edge list, canvas dimensions
  - Relationships: Contains nodes and edges, stored as `.canvas` JSON in vault

- **Canvas Node**: An element on a canvas (file reference, text, group, link)
  - Attributes: node ID, node type, position (x/y coordinates), dimensions (width/height), content (file path or text), color
  - Relationships: Belongs to a canvas, may be connected by edges

- **Canvas Edge**: A connection between two canvas nodes
  - Attributes: edge ID, source node ID, target node ID, label (optional)
  - Relationships: Connects two canvas nodes within a canvas

- **Template File**: A markdown file used as a blueprint for new notes
  - Attributes: template name, file path, variable placeholders, template folder
  - Relationships: Stored in templates folder, may reference Templater functions

- **Obsidian Command**: An executable action in Obsidian (core or plugin)
  - Attributes: command ID, command name, plugin source, parameter requirements
  - Relationships: May belong to a plugin, may modify notes/workspace/settings

- **Workspace Layout**: A saved configuration of Obsidian's UI state
  - Attributes: layout name, pane arrangement, sidebar states, open file list
  - Relationships: Saved via Workspaces plugin, can be restored

- **API Client Configuration**: Connection settings for Local REST API
  - Attributes: base URL, API key, timeout duration, retry policy
  - Relationships: Used by all API-based tools, configured via environment variables

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can search and filter tasks by metadata (due date, priority, completion status) across their entire vault in under 3 seconds for vaults with up to 1,000 notes
- **SC-002**: Users can extract Dataview inline fields from notes with 100% accuracy for all supported syntax formats (`field::`, `[field::]`, `(field::)`)
- **SC-003**: Users can execute Dataview queries and receive results in under 5 seconds for queries scanning up to 500 notes
- **SC-004**: Users can create and manipulate Kanban boards (add cards, move cards between columns) via filesystem operations completing in under 500ms per operation
- **SC-005**: Users can track all link types (wikilinks, embeds, section links, block references) with backlink analysis completing in under 5 seconds for vaults with up to 1,000 notes
- **SC-006**: Users can apply basic templates with variable substitution without requiring Obsidian to be running, completing in under 200ms per template
- **SC-007**: Users can execute Templater templates with full JavaScript support when Obsidian is running, completing in under 2 seconds for templates with up to 10 dynamic operations
- **SC-008**: Users can create canvas files with up to 50 nodes and connections via filesystem operations, completing in under 1 second
- **SC-009**: Users can execute any Obsidian command via API with command execution completing within 3 seconds or providing timeout feedback
- **SC-010**: Users can control workspace UI (panes, sidebars, layouts) with operations completing in under 1 second when Obsidian is running
- **SC-011**: System gracefully handles API unavailability, providing clear error messages indicating Obsidian must be running for API-based features within 500ms of detection
- **SC-012**: All filesystem-native tools continue to work without Obsidian running, maintaining 100% offline functionality for core operations
- **SC-013**: Users can identify orphan notes and hub notes in vaults with up to 1,000 notes with graph analysis completing in under 10 seconds
- **SC-014**: Task metadata parsing achieves 95% accuracy for common Tasks plugin emoji patterns in real-world notes
- **SC-015**: System handles edge cases (malformed metadata, API timeouts, corrupted files) with informative error messages and graceful degradation, maintaining stability across 1,000+ operations

### Assumptions

- **Vault Size**: Performance targets assume vaults with up to 1,000 notes; larger vaults may require additional optimization
- **Obsidian Local REST API**: Users have installed and configured the Local REST API plugin when using API-based features
- **Plugin Installation**: Users have installed target plugins (Tasks, Dataview, Templater, Kanban, Workspaces) if they want to use features requiring those plugins
- **Network Availability**: Local REST API is accessible via localhost/configured URL when Obsidian is running
- **API Version**: Local REST API plugin version 1.6.0 or higher is installed
- **File Encoding**: All markdown files and canvas files use UTF-8 encoding
- **Markdown Format**: Notes follow standard Obsidian markdown conventions for tasks, links, and formatting
- **Tasks Plugin Emoji**: Standard Tasks plugin emoji conventions are used (📅 due, ⏫🔼🔽 priority, 🔁 recurrence, etc.)
- **Dataview Syntax**: Inline fields follow Dataview's documented syntax patterns
- **Kanban Structure**: Kanban markdown files use standard heading-based column structure
- **Canvas Format**: Canvas files follow Obsidian's `.canvas` JSON schema
- **Concurrent Access**: No external processes modify files during MCP operations (single-user assumption for filesystem operations)
- **API Authentication**: Users provide valid API key in environment configuration
- **Command Availability**: Obsidian commands maintain stable IDs across plugin updates

### Out of Scope

- Real-time synchronization between filesystem and Obsidian's internal state when both are active
- Graph view visualization rendering or export (only graph analysis/metrics)
- Excalidraw drawing creation/manipulation (requires complex rendering engine; command execution for opening drawings is in scope)
- Advanced Tables plugin specific features (basic table editing via markdown is supported)
- Style Settings plugin manipulation (CSS variable management is complex and rarely automated)
- Iconize plugin icon assignment (metadata reading possible, icon selection requires UI)
- Plugin installation or configuration via MCP
- Obsidian settings modification (theme, hotkeys, core plugin settings)
- Vault-to-vault synchronization or multi-vault operations
- Mobile-specific optimizations or mobile API endpoints
- Obsidian Publish or Sync feature integration
- Custom Dataview queries optimization or query result caching
- Templater user scripts creation or modification (execution only)
- Workspace layout version control or diff/merge operations
- Canvas auto-layout algorithms or smart positioning
- Task recurrence calculation or automatic next-occurrence generation
- Natural language to Dataview query conversion (users provide DQL directly)
- Link suggestion or auto-linking based on content similarity
- Note merging or splitting beyond existing note composer features
- PDF or image file analysis within embedded canvas nodes
- Audio/video file transcription or metadata extraction
- Encrypted note support or vault encryption integration
