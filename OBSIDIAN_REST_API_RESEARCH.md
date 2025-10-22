# Obsidian Local REST API - Comprehensive Documentation

Research conducted: 2025-10-22
Plugin: obsidian-local-rest-api by coddingtonbear
Documentation: https://coddingtonbear.github.io/obsidian-local-rest-api/
Repository: https://github.com/coddingtonbear/obsidian-local-rest-api

## Table of Contents

1. [Overview](#overview)
2. [Authentication and Connection](#authentication-and-connection)
3. [Complete Endpoint Reference](#complete-endpoint-reference)
4. [Error Handling](#error-handling)
5. [Example API Calls](#example-api-calls)
6. [MCP Integration Patterns](#mcp-integration-patterns)

---

## Overview

The Obsidian Local REST API plugin provides a secure HTTPS interface gated behind API key authentication, enabling programmatic interaction with Obsidian vaults. It supports reading, creating, updating, and deleting notes, executing commands, searching, and managing periodic notes.

### Key Capabilities

- **File Operations**: CRUD operations on notes with PATCH support for section-specific insertion
- **Search**: Simple text search and complex queries using Dataview DQL or JSONLogic
- **Commands**: List and execute Obsidian commands programmatically
- **Periodic Notes**: Manage daily, weekly, monthly, quarterly, and yearly notes
- **Extension API**: Other plugins can register custom endpoints

---

## Authentication and Connection

### Server Configuration

**Default Endpoints:**
- HTTPS (Secure): `https://127.0.0.1:27124` (recommended)
- HTTP (Insecure): `http://127.0.0.1:27123`

**Port Configuration:**
Ports can be customized in Obsidian plugin settings if defaults conflict with other services.

**SSL Certificate:**
The plugin uses a self-signed certificate by default. You can download it from:
```
GET https://127.0.0.1:27124/obsidian-local-rest-api.crt
```

### API Key Generation

1. Install the "Local REST API" plugin in Obsidian
2. Enable the plugin in Settings → Community Plugins
3. Go to Settings → Local REST API
4. Copy the API key displayed in the settings panel

### Authentication Method

**Type:** Bearer Token (HTTP)
**Header:** `Authorization: Bearer {API_KEY}`

All endpoints except `GET /` require authentication.

### Connection Testing

Test connection without authentication:
```bash
curl --insecure https://127.0.0.1:27124/
```

Expected response:
```json
{
  "status": "OK",
  "authenticated": false,
  "versions": {
    "obsidian": "1.5.3",
    "self": "3.2.0"
  },
  "service": "obsidian-local-rest-api"
}
```

Test with authentication:
```bash
curl --insecure -H "Authorization: Bearer YOUR_API_KEY" https://127.0.0.1:27124/
```

Expected response:
```json
{
  "status": "OK",
  "authenticated": true,
  "versions": {
    "obsidian": "1.5.3",
    "self": "3.2.0"
  },
  "service": "obsidian-local-rest-api"
}
```

### Python Connection Example

```python
import requests

API_URL = "https://127.0.0.1:27124"
API_KEY = "your_api_key_here"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

# Test connection
response = requests.get(
    f"{API_URL}/",
    headers=headers,
    verify=False  # For self-signed certificate
)
print(response.json())
```

### Environment Variables

Standard configuration for MCP servers and automation:
```bash
OBSIDIAN_API_KEY=your_api_key
OBSIDIAN_HOST=127.0.0.1
OBSIDIAN_PORT=27124
```

---

## Complete Endpoint Reference

### System Operations

#### Get Server Status
```
GET /
```
**Authentication:** Not required
**Description:** Returns server status and version information

**Response:**
```json
{
  "status": "OK",
  "authenticated": boolean,
  "versions": {
    "obsidian": "1.5.3",
    "self": "3.2.0"
  },
  "service": "obsidian-local-rest-api"
}
```

#### Get OpenAPI Specification
```
GET /openapi.yaml
```
**Authentication:** Required
**Description:** Returns the OpenAPI specification for runtime endpoint inspection
**Added in:** Version 3.2.0

#### Get SSL Certificate
```
GET /obsidian-local-rest-api.crt
```
**Authentication:** Not required
**Description:** Download the self-signed SSL certificate

---

### Active File Operations

The active file is the currently focused/open file in Obsidian.

#### Get Active File
```
GET /active/
```
**Authentication:** Required
**Accept Headers:**
- `text/markdown` - Returns raw markdown content
- `application/vnd.olrapi.note+json` - Returns rich note metadata (default)

**Response (application/vnd.olrapi.note+json):**
```json
{
  "content": "# My Note\n\nContent here",
  "path": "folder/note.md",
  "frontmatter": {
    "tags": ["example"],
    "created": "2025-01-15"
  },
  "tags": ["#example"],
  "stat": {
    "ctime": 1705334400000,
    "mtime": 1705420800000,
    "size": 1234
  }
}
```

#### Append to Active File
```
POST /active/
```
**Authentication:** Required
**Content-Type:** `text/markdown`
**Request Body:** Markdown text to append

**Example:**
```bash
curl --insecure -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: text/markdown" \
  -d "New paragraph to append" \
  https://127.0.0.1:27124/active/
```

#### Replace Active File
```
PUT /active/
```
**Authentication:** Required
**Content-Type:** `text/markdown`
**Request Body:** Complete markdown content

**Example:**
```bash
curl --insecure -X PUT \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: text/markdown" \
  -d "# New Content\n\nComplete replacement" \
  https://127.0.0.1:27124/active/
```

#### Patch Active File
```
PATCH /active/
```
**Authentication:** Required
**Description:** Insert content relative to headings, blocks, or frontmatter

**Headers:**
- `Operation`: `append`, `prepend`, or `replace`
- `Target-Type`: `heading`, `block`, or `frontmatter`
- `Target`: The target identifier (heading text, block ID, or frontmatter key)
- `Target-Delimiter` (optional): For nested headings, default is `::`
- `Trim-Target-Whitespace` (optional): `true` or `false`

**Examples:**

Append after a heading:
```bash
curl --insecure -X PATCH \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: text/markdown" \
  -H "Operation: append" \
  -H "Target-Type: heading" \
  -H "Target: Section Title" \
  -d "Content to add after heading" \
  https://127.0.0.1:27124/active/
```

Nested heading (e.g., "Main::Subsection::Subsubsection"):
```bash
curl --insecure -X PATCH \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: text/markdown" \
  -H "Operation: append" \
  -H "Target-Type: heading" \
  -H "Target: Main::Subsection" \
  -H "Target-Delimiter: ::" \
  -d "Content under nested heading" \
  https://127.0.0.1:27124/active/
```

Update frontmatter:
```bash
curl --insecure -X PATCH \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: text/markdown" \
  -H "Operation: replace" \
  -H "Target-Type: frontmatter" \
  -H "Target: tags" \
  -d "- new\n- tags" \
  https://127.0.0.1:27124/active/
```

Block reference:
```bash
curl --insecure -X PATCH \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: text/markdown" \
  -H "Operation: append" \
  -H "Target-Type: block" \
  -H "Target: block-id-123" \
  -d "Content after block" \
  https://127.0.0.1:27124/active/
```

#### Delete Active File
```
DELETE /active/
```
**Authentication:** Required
**Description:** Deletes the currently active file

---

### Vault File Operations

#### List Root Directory
```
GET /vault/
```
**Authentication:** Required
**Response:** Array of file/directory names in vault root

**Example Response:**
```json
{
  "files": [
    "Daily Notes/",
    "Projects/",
    "README.md",
    "Index.md"
  ]
}
```

#### List Directory Contents
```
GET /vault/{pathToDirectory}/
```
**Authentication:** Required
**Path Parameter:** Directory path (must end with `/`)

**Example:**
```bash
curl --insecure -H "Authorization: Bearer YOUR_API_KEY" \
  https://127.0.0.1:27124/vault/Daily%20Notes/
```

#### Get File
```
GET /vault/{filename}
```
**Authentication:** Required
**Path Parameter:** File path relative to vault root
**Accept Headers:**
- `text/markdown` - Raw markdown content
- `application/vnd.olrapi.note+json` - Rich metadata (default)

**Example:**
```bash
curl --insecure -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: application/vnd.olrapi.note+json" \
  https://127.0.0.1:27124/vault/Projects/MyProject.md
```

#### Create/Update File
```
PUT /vault/{filename}
```
**Authentication:** Required
**Content-Type:** `text/markdown`
**Description:** Creates new file or replaces existing file

**Example:**
```bash
curl --insecure -X PUT \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: text/markdown" \
  -d "# New Note\n\nContent here" \
  https://127.0.0.1:27124/vault/NewNote.md
```

#### Append to File
```
POST /vault/{filename}
```
**Authentication:** Required
**Content-Type:** `text/markdown`
**Description:** Appends content to existing file or creates new file

#### Patch File
```
PATCH /vault/{filename}
```
**Authentication:** Required
**Description:** Same as PATCH /active/ but targets specific file
**Headers:** Same as active file PATCH operation

#### Delete File
```
DELETE /vault/{filename}
```
**Authentication:** Required
**Description:** Deletes the specified file

---

### Periodic Notes

Manage daily, weekly, monthly, quarterly, and yearly notes.

#### Supported Periods
- `daily`
- `weekly`
- `monthly`
- `quarterly`
- `yearly`

#### Get Current Period Note
```
GET /periodic/{period}/
```
**Authentication:** Required
**Example:** `GET /periodic/daily/` - Gets today's daily note

#### Get Specific Date Note
```
GET /periodic/{period}/{year}/{month}/{day}/
```
**Authentication:** Required
**Path Parameters:**
- `period`: One of the supported periods
- `year`: 4-digit year
- `month`: 2-digit month (01-12)
- `day`: 2-digit day (01-31)

**Example:** `GET /periodic/daily/2025/01/15/`

#### Create/Update Period Note
```
PUT /periodic/{period}/
PUT /periodic/{period}/{year}/{month}/{day}/
```
**Authentication:** Required
**Content-Type:** `text/markdown`

#### Append to Period Note
```
POST /periodic/{period}/
POST /periodic/{period}/{year}/{month}/{day}/
```
**Authentication:** Required
**Content-Type:** `text/markdown`

#### Patch Period Note
```
PATCH /periodic/{period}/
PATCH /periodic/{period}/{year}/{month}/{day}/
```
**Authentication:** Required
**Description:** Uses same PATCH headers as file operations

#### Delete Period Note
```
DELETE /periodic/{period}/
DELETE /periodic/{period}/{year}/{month}/{day}/
```
**Authentication:** Required

---

### Search Operations

#### Simple Text Search
```
POST /search/simple/
```
**Authentication:** Required
**Content-Type:** `text/markdown` or `text/plain`
**Request Body:** Search query text

**Query Parameters:**
- `contextLength` (optional): Number of characters of context around matches

**Example:**
```bash
curl --insecure -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: text/plain" \
  -d "search term" \
  https://127.0.0.1:27124/search/simple/?contextLength=100
```

**Response:**
```json
{
  "results": [
    {
      "filename": "Projects/MyProject.md",
      "score": 2,
      "matches": [
        {
          "match": {
            "start": 45,
            "end": 56
          },
          "context": "...text before search term text after..."
        }
      ]
    }
  ]
}
```

#### Complex Search
```
POST /search/
```
**Authentication:** Required
**Content-Type:**
- `application/vnd.olrapi.dataview.dql+txt` - Dataview query
- `application/vnd.olrapi.jsonlogic+json` - JSONLogic query

**Dataview Query Example:**
```bash
curl --insecure -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/vnd.olrapi.dataview.dql+txt" \
  -d "TABLE time-played, rating FROM #game SORT rating DESC" \
  https://127.0.0.1:27124/search/
```

**JSONLogic Query Example:**
```bash
curl --insecure -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/vnd.olrapi.jsonlogic+json" \
  -d '{"and": [{"in": ["#project", {"var": "tags"}]}, {">": [{"var": "stat.mtime"}, 1704067200000]}]}' \
  https://127.0.0.1:27124/search/
```

**JSONLogic Available Variables:**
- `path` - File path
- `content` - File content
- `frontmatter` - Frontmatter object
- `tags` - Array of tags
- `stat.ctime` - Creation timestamp
- `stat.mtime` - Modification timestamp
- `stat.size` - File size in bytes

**JSONLogic Operators:**
- Standard logic: `and`, `or`, `not`
- Comparison: `==`, `!=`, `>`, `>=`, `<`, `<=`
- String: `in`, `substr`
- Pattern matching: `glob`, `regexp` (custom operators)

---

### Command Execution

#### List Available Commands
```
GET /commands/
```
**Authentication:** Required
**Description:** Returns all Obsidian commands available for execution

**Response:**
```json
{
  "commands": [
    {
      "id": "editor:toggle-bold",
      "name": "Toggle bold"
    },
    {
      "id": "workspace:split-vertical",
      "name": "Split vertically"
    },
    {
      "id": "daily-notes",
      "name": "Open today's daily note"
    }
  ]
}
```

#### Execute Command
```
POST /commands/{commandId}/
```
**Authentication:** Required
**Path Parameter:** Command ID from list commands

**Note:** Most commands don't accept parameters via the API. Parameter passing is limited by Obsidian's command architecture.

**Example:**
```bash
curl --insecure -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  https://127.0.0.1:27124/commands/daily-notes/
```

---

### File Navigation

#### Open File in UI
```
POST /open/{filename}
```
**Authentication:** Required
**Path Parameter:** File path relative to vault root
**Query Parameters:**
- `newLeaf` (optional): `true` to open in new pane/tab

**Example - Open in current pane:**
```bash
curl --insecure -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  https://127.0.0.1:27124/open/Projects/MyProject.md
```

**Example - Open in new pane:**
```bash
curl --insecure -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  "https://127.0.0.1:27124/open/Projects/MyProject.md?newLeaf=true"
```

**Python Example:**
```python
import urllib.parse
import requests

def open_file(file_path: str, new_leaf: bool = False):
    url = f"{API_URL}/open/{urllib.parse.quote(file_path, safe='/')}"
    params = {"newLeaf": "true"} if new_leaf else {}

    response = requests.post(
        url,
        headers=headers,
        params=params,
        verify=False
    )
    return response.json()
```

---

## Error Handling

### HTTP Status Codes

The API uses standard HTTP status codes:

- **200 OK** - Successful request
- **201 Created** - Resource created successfully
- **204 No Content** - Successful deletion
- **400 Bad Request** - Invalid request format or parameters
- **401 Unauthorized** - Missing or invalid API key
- **404 Not Found** - File or resource not found (Error Code 40400)
- **409 Conflict** - Resource conflict (e.g., file already exists)
- **500 Internal Server Error** - Server-side error

### Error Response Format

```json
{
  "errorCode": 40400,
  "message": "File not found: NonExistent.md"
}
```

**Error Code Format:** 5-digit integer combining HTTP status with additional context

### Common Errors

**Authentication Failure:**
```json
{
  "errorCode": 40100,
  "message": "Invalid or missing API key"
}
```

**File Not Found:**
```json
{
  "errorCode": 40400,
  "message": "The requested file does not exist in the vault"
}
```

**Invalid PATCH Target:**
```json
{
  "errorCode": 40000,
  "message": "Target heading 'NonExistent Section' not found in file"
}
```

### Python Error Handling Example

```python
import requests
from typing import Dict, Any

def safe_api_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Make API request with error handling"""
    try:
        response = requests.request(
            method,
            f"{API_URL}{endpoint}",
            headers=headers,
            verify=False,
            timeout=30,
            **kwargs
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        raise Exception("API request timed out after 30 seconds")

    except requests.exceptions.ConnectionError:
        raise Exception(
            "Could not connect to Obsidian. "
            "Ensure the Local REST API plugin is running."
        )

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception("Invalid API key. Check your credentials.")
        elif e.response.status_code == 404:
            error_data = e.response.json()
            raise Exception(f"Not found: {error_data.get('message', 'Unknown')}")
        else:
            try:
                error_data = e.response.json()
                raise Exception(
                    f"API error {error_data.get('errorCode', 'unknown')}: "
                    f"{error_data.get('message', str(e))}"
                )
            except ValueError:
                raise Exception(f"HTTP {e.response.status_code}: {str(e)}")
```

### Timeout Behavior

- **Recommended timeout:** 30 seconds for most operations
- **Long operations:** Search and complex queries may take longer on large vaults
- **Connection timeout:** 10 seconds recommended for initial connection
- **Read timeout:** 30-60 seconds for response data

---

## Example API Calls

### Complete Python Wrapper Class

```python
import requests
import urllib.parse
from typing import Dict, List, Any, Optional
import warnings

# Suppress SSL warnings for self-signed certificate
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class ObsidianAPI:
    """Python wrapper for Obsidian Local REST API"""

    def __init__(self, api_url: str = "https://127.0.0.1:27124", api_key: str = ""):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request to API"""
        url = f"{self.api_url}{endpoint}"
        return requests.request(
            method,
            url,
            headers={**self.headers, **kwargs.pop('headers', {})},
            verify=False,
            timeout=30,
            **kwargs
        )

    def test_connection(self) -> Dict[str, Any]:
        """Test API connection and authentication"""
        response = self._request("GET", "/")
        return response.json()

    # Active File Operations

    def get_active_file(self, as_json: bool = True) -> Dict[str, Any] | str:
        """Get currently active file content"""
        headers = {}
        if not as_json:
            headers["Accept"] = "text/markdown"
        response = self._request("GET", "/active/", headers=headers)
        return response.json() if as_json else response.text

    def append_to_active(self, content: str) -> None:
        """Append content to active file"""
        self._request(
            "POST",
            "/active/",
            headers={"Content-Type": "text/markdown"},
            data=content
        )

    def replace_active(self, content: str) -> None:
        """Replace active file content"""
        self._request(
            "PUT",
            "/active/",
            headers={"Content-Type": "text/markdown"},
            data=content
        )

    def patch_active(
        self,
        content: str,
        operation: str,
        target_type: str,
        target: str,
        delimiter: str = "::"
    ) -> None:
        """Patch active file relative to heading/block/frontmatter"""
        self._request(
            "PATCH",
            "/active/",
            headers={
                "Content-Type": "text/markdown",
                "Operation": operation,
                "Target-Type": target_type,
                "Target": target,
                "Target-Delimiter": delimiter
            },
            data=content
        )

    # Vault File Operations

    def list_vault_files(self, directory: str = "") -> List[str]:
        """List files in vault directory"""
        path = f"/vault/{directory}/" if directory else "/vault/"
        response = self._request("GET", path)
        return response.json().get("files", [])

    def get_file(
        self,
        file_path: str,
        as_json: bool = True
    ) -> Dict[str, Any] | str:
        """Get file content"""
        encoded_path = urllib.parse.quote(file_path, safe='/')
        headers = {}
        if not as_json:
            headers["Accept"] = "text/markdown"
        response = self._request("GET", f"/vault/{encoded_path}", headers=headers)
        return response.json() if as_json else response.text

    def create_file(self, file_path: str, content: str) -> None:
        """Create or replace file"""
        encoded_path = urllib.parse.quote(file_path, safe='/')
        self._request(
            "PUT",
            f"/vault/{encoded_path}",
            headers={"Content-Type": "text/markdown"},
            data=content
        )

    def append_to_file(self, file_path: str, content: str) -> None:
        """Append to file"""
        encoded_path = urllib.parse.quote(file_path, safe='/')
        self._request(
            "POST",
            f"/vault/{encoded_path}",
            headers={"Content-Type": "text/markdown"},
            data=content
        )

    def patch_file(
        self,
        file_path: str,
        content: str,
        operation: str,
        target_type: str,
        target: str,
        delimiter: str = "::"
    ) -> None:
        """Patch file relative to heading/block/frontmatter"""
        encoded_path = urllib.parse.quote(file_path, safe='/')
        self._request(
            "PATCH",
            f"/vault/{encoded_path}",
            headers={
                "Content-Type": "text/markdown",
                "Operation": operation,
                "Target-Type": target_type,
                "Target": target,
                "Target-Delimiter": delimiter
            },
            data=content
        )

    def delete_file(self, file_path: str) -> None:
        """Delete file"""
        encoded_path = urllib.parse.quote(file_path, safe='/')
        self._request("DELETE", f"/vault/{encoded_path}")

    # Periodic Notes

    def get_periodic_note(
        self,
        period: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        as_json: bool = True
    ) -> Dict[str, Any] | str:
        """Get periodic note (current or specific date)"""
        if year and month and day:
            path = f"/periodic/{period}/{year:04d}/{month:02d}/{day:02d}/"
        else:
            path = f"/periodic/{period}/"

        headers = {}
        if not as_json:
            headers["Accept"] = "text/markdown"
        response = self._request("GET", path, headers=headers)
        return response.json() if as_json else response.text

    def update_periodic_note(
        self,
        period: str,
        content: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None
    ) -> None:
        """Update periodic note"""
        if year and month and day:
            path = f"/periodic/{period}/{year:04d}/{month:02d}/{day:02d}/"
        else:
            path = f"/periodic/{period}/"

        self._request(
            "PUT",
            path,
            headers={"Content-Type": "text/markdown"},
            data=content
        )

    # Search

    def simple_search(
        self,
        query: str,
        context_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """Simple text search"""
        params = {"contextLength": context_length} if context_length else {}
        response = self._request(
            "POST",
            "/search/simple/",
            headers={"Content-Type": "text/plain"},
            data=query,
            params=params
        )
        return response.json()

    def dataview_search(self, query: str) -> Dict[str, Any]:
        """Search using Dataview DQL query"""
        response = self._request(
            "POST",
            "/search/",
            headers={"Content-Type": "application/vnd.olrapi.dataview.dql+txt"},
            data=query
        )
        return response.json()

    def jsonlogic_search(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Search using JSONLogic query"""
        import json
        response = self._request(
            "POST",
            "/search/",
            headers={"Content-Type": "application/vnd.olrapi.jsonlogic+json"},
            data=json.dumps(query)
        )
        return response.json()

    # Commands

    def list_commands(self) -> List[Dict[str, str]]:
        """List available Obsidian commands"""
        response = self._request("GET", "/commands/")
        return response.json().get("commands", [])

    def execute_command(self, command_id: str) -> None:
        """Execute Obsidian command by ID"""
        encoded_id = urllib.parse.quote(command_id, safe='')
        self._request("POST", f"/commands/{encoded_id}/")

    # File Navigation

    def open_file(self, file_path: str, new_leaf: bool = False) -> None:
        """Open file in Obsidian UI"""
        encoded_path = urllib.parse.quote(file_path, safe='/')
        params = {"newLeaf": "true"} if new_leaf else {}
        self._request("POST", f"/open/{encoded_path}", params=params)


# Usage Examples
if __name__ == "__main__":
    # Initialize
    api = ObsidianAPI(
        api_url="https://127.0.0.1:27124",
        api_key="your_api_key_here"
    )

    # Test connection
    status = api.test_connection()
    print(f"Connected: {status['authenticated']}")

    # Get active file
    active = api.get_active_file()
    print(f"Active file: {active['path']}")

    # Create a new note
    api.create_file(
        "Projects/NewProject.md",
        "# New Project\n\n## Goals\n\n- Goal 1\n- Goal 2"
    )

    # Append to existing note
    api.append_to_file(
        "Projects/NewProject.md",
        "\n## Notes\n\nAdditional information"
    )

    # Patch - add content after heading
    api.patch_file(
        "Projects/NewProject.md",
        "\n- Goal 3\n- Goal 4",
        operation="append",
        target_type="heading",
        target="Goals"
    )

    # Get daily note
    daily = api.get_periodic_note("daily")
    print(f"Daily note: {daily['path']}")

    # Simple search
    results = api.simple_search("project", context_length=50)
    print(f"Found {len(results['results'])} matches")

    # Dataview search
    dataview_results = api.dataview_search(
        "TABLE rating FROM #project SORT rating DESC"
    )

    # JSONLogic search - files with tag and modified recently
    jsonlogic_results = api.jsonlogic_search({
        "and": [
            {"in": ["#project", {"var": "tags"}]},
            {">": [{"var": "stat.mtime"}, 1704067200000]}
        ]
    })

    # List and execute command
    commands = api.list_commands()
    daily_note_cmd = next(
        (cmd for cmd in commands if "daily" in cmd["name"].lower()),
        None
    )
    if daily_note_cmd:
        api.execute_command(daily_note_cmd["id"])

    # Open file in new pane
    api.open_file("Projects/NewProject.md", new_leaf=True)
```

### Curl Examples

**Create a daily journal entry:**
```bash
#!/bin/bash
API_KEY="your_api_key"
API_URL="https://127.0.0.1:27124"

# Get today's daily note
DAILY_NOTE=$(curl --insecure -s \
  -H "Authorization: Bearer $API_KEY" \
  "$API_URL/periodic/daily/" | jq -r '.path')

# Append journal entry
curl --insecure -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: text/markdown" \
  -d "

## $(date '+%H:%M')

Journal entry text here
" \
  "$API_URL/active/"
```

**Batch file creation:**
```bash
#!/bin/bash
API_KEY="your_api_key"
API_URL="https://127.0.0.1:27124"

# Create multiple project files
for project in "Project Alpha" "Project Beta" "Project Gamma"; do
  FILE_NAME=$(echo "$project" | tr ' ' '-').md

  curl --insecure -X PUT \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: text/markdown" \
    -d "# $project

## Overview

Project description here

## Status

- [ ] Planning
- [ ] In Progress
- [ ] Complete
" \
    "$API_URL/vault/Projects/$FILE_NAME"
done
```

---

## MCP Integration Patterns

### Overview

Multiple MCP (Model Context Protocol) servers have been built on top of the Obsidian Local REST API, providing AI agents with access to Obsidian vaults.

### Popular MCP Implementations

1. **mcp-obsidian** (MarkusPfundstein)
   - PyPI: `mcp-obsidian`
   - Language: TypeScript/JavaScript
   - Tools: list_files_in_vault, get_file_contents, search, patch_content, append_content, delete_file

2. **obsidian-api-mcp-server**
   - PyPI: `obsidian-api-mcp-server`
   - Language: Python
   - Focus: Knowledge discovery and analysis

3. **obsidian-mcp-rest** (PublikPrinciple)
   - Repository: PublikPrinciple/obsidian-mcp-rest
   - Language: TypeScript
   - Tools: readNote, writeNote, listNotes, searchNotes

### Configuration Example (Claude Desktop)

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uvx",
      "args": ["mcp-obsidian"],
      "env": {
        "OBSIDIAN_API_KEY": "your_api_key_here",
        "OBSIDIAN_HOST": "127.0.0.1",
        "OBSIDIAN_PORT": "27124"
      }
    }
  }
}
```

### Best Practices for MCP Integration

1. **Connection Management**
   - Test connection on initialization
   - Implement retry logic with exponential backoff
   - Handle connection timeouts gracefully

2. **Error Handling**
   - Wrap all API calls in try-catch blocks
   - Provide meaningful error messages to AI agents
   - Log errors for debugging

3. **Security**
   - Store API keys in environment variables
   - Never commit API keys to version control
   - Use HTTPS endpoint (27124) for encrypted communication
   - Consider disabling SSL verification only for localhost self-signed certs

4. **Performance**
   - Cache frequently accessed data (command list, file list)
   - Implement rate limiting to avoid overwhelming Obsidian
   - Use simple search for quick queries, complex search only when needed

5. **File Path Handling**
   - Always URL-encode file paths
   - Handle spaces and special characters properly
   - Use forward slashes (/) consistently
   - Preserve vault-relative paths

6. **Tool Design**
   - Provide granular tools (get, update, append, patch)
   - Include file listing and search capabilities
   - Support both active file and vault file operations
   - Expose command execution for advanced use cases

### MCP Tool Interface Example

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

def create_obsidian_tools(api: ObsidianAPI) -> List[Tool]:
    """Create MCP tools for Obsidian API"""

    return [
        Tool(
            name="obsidian_get_file",
            description="Get content of a file from Obsidian vault",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file relative to vault root"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="obsidian_search",
            description="Search for text across all files in vault",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to search for"
                    },
                    "context_length": {
                        "type": "integer",
                        "description": "Characters of context around match"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="obsidian_update_file",
            description="Create or update a file in Obsidian vault",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file relative to vault root"
                    },
                    "content": {
                        "type": "string",
                        "description": "Markdown content for the file"
                    }
                },
                "required": ["file_path", "content"]
            }
        ),
        Tool(
            name="obsidian_patch_file",
            description="Insert content relative to heading, block, or frontmatter",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file relative to vault root"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to insert"
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["append", "prepend", "replace"],
                        "description": "How to insert content"
                    },
                    "target_type": {
                        "type": "string",
                        "enum": ["heading", "block", "frontmatter"],
                        "description": "Type of target"
                    },
                    "target": {
                        "type": "string",
                        "description": "Target identifier (heading text, block ID, or frontmatter key)"
                    }
                },
                "required": ["file_path", "content", "operation", "target_type", "target"]
            }
        )
    ]
```

---

## Workspace Endpoints Research

**Finding:** The Obsidian Local REST API **does not currently provide** endpoints for:
- Workspace layout save/load
- Direct pane control (split, close, resize)
- Sidebar control (show, hide, toggle)

**Workaround:** Use command execution endpoints to trigger workspace-related commands:
- List available commands with `GET /commands/`
- Look for commands like `workspace:split-vertical`, `workspace:toggle-sidebar`
- Execute them with `POST /commands/{commandId}/`

**Limitation:** Commands may not accept parameters through the API, limiting fine-grained control.

**Alternative:** For workspace management, consider:
- Using Obsidian URI scheme (obsidian://...)
- Direct file system manipulation of workspace JSON files
- Advanced URI plugin for more control

---

## Additional Resources

- **Interactive Documentation:** https://coddingtonbear.github.io/obsidian-local-rest-api/
- **GitHub Repository:** https://github.com/coddingtonbear/obsidian-local-rest-api
- **OpenAPI Spec (live):** https://127.0.0.1:27124/openapi.yaml (when plugin running)
- **Python Wrapper Example:** https://github.com/evelynkyl/obsidian_python_api
- **MCP Server Example:** https://github.com/MarkusPfundstein/mcp-obsidian

---

## Version Information

This documentation is based on:
- **Plugin Version:** 3.2.0 (Latest as of 2025-10-22)
- **OpenAPI Version:** 3.0.2
- **Minimum Obsidian Version:** Not specified in docs

---

## Changelog Highlights

- **3.2.0** - Added `/openapi.yaml` endpoint for runtime API discovery
- **3.1.0** - Added periodic notes API endpoints for arbitrary dates
- **3.0.1** - Enhanced PATCH to support blocks and frontmatter (not just headings)
- **3.0.0** - Major PATCH API redesign (breaking change from v2.x)
- **2.5.4** - Added Extension API for custom plugin endpoints

---

## Notes for Hybrid MCP Implementation

### Recommended Approach

1. **Start with Core Tools:**
   - File CRUD (get, create, update, delete)
   - Simple search
   - Active file operations

2. **Add Advanced Features:**
   - PATCH operations for surgical edits
   - Periodic notes management
   - Complex search (Dataview/JSONLogic)

3. **Optional Enhancements:**
   - Command execution
   - File navigation (open in UI)
   - Directory listing

### Implementation Priority

**High Priority:**
- Connection testing and authentication
- Get file content
- Update file content
- Simple search
- List files in directory

**Medium Priority:**
- PATCH operations (heading-based)
- Periodic notes
- Append operations
- Delete operations

**Low Priority:**
- Command execution
- Open file in UI
- Complex search queries
- PATCH operations (block/frontmatter)

### Testing Strategy

1. **Connection Test:** Verify plugin is running and API key is valid
2. **Read Test:** Get active file or known file
3. **Write Test:** Create test file in safe location
4. **Search Test:** Simple text search for known content
5. **PATCH Test:** Insert content after heading in test file
6. **Cleanup:** Delete test files

### Known Limitations

- No workspace layout control via API
- Command parameters not supported
- Self-signed SSL certificate requires verification bypass
- Large vault searches may timeout (increase timeout for complex queries)
- File paths must be URL-encoded
- PATCH operations require exact target matching

---

*End of Research Documentation*
