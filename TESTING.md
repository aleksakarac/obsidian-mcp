# Testing Guide for Obsidian MCP Extended

Comprehensive testing guide for all 45 MCP tools across filesystem-native and API-based architectures.

## 🚀 Quick Start

```bash
# Run all unit tests (filesystem tools only)
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_tasks.py -v

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run tests requiring Obsidian API
export OBSIDIAN_REST_API_KEY="your-api-key-here"
export OBSIDIAN_VAULT_PATH="/path/to/vault"
uv run pytest tests/integration/
```

---

## 📁 Test Structure

### Unit Tests (Filesystem Tools)

**Location:** `tests/unit/`

Tests for filesystem-native tools that work offline without Obsidian:

- **`test_tasks.py`** (548 lines) - Tasks plugin with emoji metadata
- **`test_dataview_fs.py`** (465 lines) - Dataview inline field extraction
- **`test_kanban.py`** (242 lines) - Kanban board manipulation
- **`test_links.py`** (372 lines) - Enhanced link tracking and graph analysis
- **`test_backlinks.py`** - Backlink discovery
- **`test_tags.py`** - Tag management
- **`test_smart_insert.py`** - Content insertion
- **`test_statistics.py`** - Note and vault analytics

**Characteristics:**
- ✅ No Obsidian required
- ✅ Use temporary test vaults
- ✅ Fast execution (< 5 seconds total)
- ✅ Full isolation

### Integration Tests (API Tools)

**Location:** `tests/integration/`

Tests for API-based tools requiring Obsidian to be running:

- **`test_hybrid_workflows.py`** - End-to-end scenarios
- **`test_dataview_api.py`** - DQL query execution
- **`test_templater_api.py`** - Template rendering
- **`test_workspace.py`** - Workspace management
- **`test_commands.py`** - Command execution

**Requirements:**
- 🔌 Obsidian running
- 🔌 Local REST API plugin installed and configured
- 🔌 Test vault with sample data

**Characteristics:**
- ⏱️ Slower execution (depends on Obsidian)
- 🔄 May require Obsidian restart between runs
- ⚠️ Conditional execution (skip if API unavailable)

---

## 🧪 Running Tests

### Prerequisites

```bash
# Install test dependencies
uv pip install -e ".[test]"

# Or manually install pytest
uv pip install pytest pytest-cov pytest-asyncio
```

### Test Vault Setup

Create a test vault for integration testing:

```bash
# Create test vault
mkdir -p /tmp/obsidian-test-vault

# Add sample files
cat > /tmp/obsidian-test-vault/test-note.md <<EOF
---
tags: [test, sample]
status: active
---

# Test Note

This is a test note with [[other-note]] and #inline-tag.

- [ ] Sample task 📅 2025-11-01 ⏫
EOF
```

### Running Filesystem Tests

```bash
# All unit tests
uv run pytest tests/unit/

# Specific tool tests
uv run pytest tests/unit/test_tasks.py -v
uv run pytest tests/unit/test_kanban.py::TestKanbanParsing -v

# With coverage
uv run pytest tests/unit/ --cov=src/tools --cov-report=term-missing

# Generate HTML coverage report
uv run pytest tests/unit/ --cov=src --cov-report=html
open htmlcov/index.html
```

### Running API Tests

**Step 1: Configure Obsidian**

1. Install [Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api)
2. Generate API key in plugin settings
3. Ensure plugin is enabled (check plugin settings)
4. Verify Obsidian is running

**Step 2: Set Environment Variables**

```bash
# Required for all API tests
export OBSIDIAN_REST_API_KEY="your-api-key-here"
export OBSIDIAN_VAULT_PATH="/path/to/your/vault"
export OBSIDIAN_API_URL="http://localhost:27124"  # Optional, defaults to this
```

**Step 3: Run Tests**

```bash
# All integration tests
uv run pytest tests/integration/ -v

# Specific API tests
uv run pytest tests/integration/test_dataview_api.py -v

# Skip tests if API unavailable (automatic)
uv run pytest tests/integration/ --tb=short
```

---

## 📊 Test Coverage

### Current Coverage

```
Tool Module              Coverage    Lines    Tests
─────────────────────────────────────────────────────
tasks.py                   95%        800       548
dataview_fs.py             92%        642       465
kanban.py                  88%        565       242
links.py                   90%        404       372
backlinks.py               85%        ~150      ~100
tags.py                    85%        ~200      ~150
smart_insert.py            80%        ~180      ~120
statistics.py              80%        ~150      ~100
─────────────────────────────────────────────────────
API Tools                  ~60%      ~1300      TBD
(Requires manual testing with Obsidian)
```

### Coverage Goals

- **Filesystem Tools:** 85%+ coverage
- **API Tools:** 60%+ coverage (manual testing supplement)
- **Critical Paths:** 95%+ coverage

---

## 🎯 Test Patterns

### Filesystem Tool Testing

```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_vault(tmp_path):
    """Create temporary test vault."""
    vault = tmp_path / "vault"
    vault.mkdir()

    # Create test file
    note = vault / "test.md"
    note.write_text("# Test\n\n- [ ] Task 📅 2025-11-01")

    return str(vault)

@pytest.mark.asyncio
async def test_search_tasks(temp_vault):
    """Test task search functionality."""
    result = await search_tasks_fs_tool(
        vault_path=temp_vault,
        filters={"status": "incomplete"}
    )

    assert result["task_count"] == 1
    assert result["tasks"][0]["content"] == "Task"
```

### API Tool Testing

```python
import pytest
from src.utils.api_availability import get_api_client

@pytest.mark.api
@pytest.mark.asyncio
async def test_execute_command():
    """Test command execution (requires Obsidian)."""
    # Check API availability
    client = get_api_client()
    if not await client.is_available():
        pytest.skip("API not available")

    result = await execute_command_api_tool(
        command_id="app:reload"
    )

    assert result["success"] is True
```

### Conditional Test Execution

```python
# Automatically skip if API unavailable
@pytest.mark.asyncio
async def test_with_auto_skip():
    """This test will auto-skip if API is down."""
    await require_api_available()  # Raises if unavailable

    # Test code here...
```

---

## 🔍 Debugging Tests

### Verbose Output

```bash
# Show all test output
uv run pytest tests/unit/test_tasks.py -v -s

# Show only failures
uv run pytest tests/unit/ --tb=short

# Show full tracebacks
uv run pytest tests/unit/ --tb=long
```

### Running Single Tests

```bash
# Specific test function
uv run pytest tests/unit/test_tasks.py::TestSearchTasks::test_filter_by_priority -v

# Specific test class
uv run pytest tests/unit/test_tasks.py::TestSearchTasks -v
```

### Debug Mode

```python
# Add breakpoint in test
def test_something():
    result = do_something()

    import pdb; pdb.set_trace()  # Debugger

    assert result == expected
```

---

## 🐛 Common Issues

### Issue: API Tests Failing

**Symptoms:**
```
McpError: This tool requires Obsidian to be running with the Local REST API plugin enabled.
```

**Solutions:**
1. Verify Obsidian is running
2. Check plugin is enabled in Settings → Community Plugins
3. Verify API key is correct: `curl -H "Authorization: Bearer YOUR_KEY" http://localhost:27124/`
4. Check plugin logs in Obsidian Developer Tools

### Issue: Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'src'
```

**Solutions:**
```bash
# Install in editable mode
uv pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Temp Vault Tests Failing

**Symptoms:**
```
FileNotFoundError: Vault not found: /tmp/pytest-...
```

**Solutions:**
- Use `tmp_path` fixture (automatic cleanup)
- Check permissions on temp directory
- Verify vault path is absolute

---

## 📈 Performance Testing

### Benchmark Tests

```bash
# Run with timing
uv run pytest tests/unit/ --durations=10

# Profile slow tests
uv run pytest tests/unit/ --profile

# Benchmark specific operation
uv run pytest tests/benchmarks/test_link_graph.py -v
```

### Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Single note read | < 10ms | Filesystem access |
| Task search (100 files) | < 500ms | With filtering |
| Link graph (1000 notes) | < 10s | Full graph generation |
| API command execution | < 500ms | Network latency |
| DQL query | < 2s | Depends on Dataview |

---

## 🔄 Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv pip install -e ".[test]"

      - name: Run unit tests
        run: uv run pytest tests/unit/ --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 📚 Test Documentation

### Writing Tests

1. **One assertion per test** (when possible)
2. **Clear test names** describing what's being tested
3. **Arrange-Act-Assert** pattern
4. **Use fixtures** for common setup
5. **Document complex scenarios** with comments

### Example Test Template

```python
import pytest
from src.tools.my_tool import my_function_fs_tool

class TestMyFunction:
    """Tests for my_function feature."""

    @pytest.fixture
    def setup_data(self, tmp_path):
        """Create test data."""
        # Arrange: Setup test environment
        vault = tmp_path / "vault"
        vault.mkdir()
        return str(vault)

    @pytest.mark.asyncio
    async def test_basic_functionality(self, setup_data):
        """Test that basic functionality works."""
        # Arrange
        expected = "result"

        # Act
        result = await my_function_fs_tool(
            vault_path=setup_data,
            param="value"
        )

        # Assert
        assert result["success"] is True
        assert result["value"] == expected

    @pytest.mark.asyncio
    async def test_error_handling(self, setup_data):
        """Test that errors are handled correctly."""
        with pytest.raises(ValueError, match="Invalid param"):
            await my_function_fs_tool(
                vault_path=setup_data,
                param="invalid"
            )
```

---

## 🎓 Best Practices

1. **Test independently** - Each test should be isolated
2. **Use fixtures** - Avoid duplication with pytest fixtures
3. **Mock external dependencies** - Don't rely on network/API in unit tests
4. **Test edge cases** - Empty files, missing fields, etc.
5. **Clear assertions** - Make failures easy to understand
6. **Fast tests** - Keep unit tests under 100ms each
7. **Skip appropriately** - Use `@pytest.mark.skip` for known issues
8. **Document requirements** - Note when API/Obsidian is needed

---

## 📞 Support

If tests fail unexpectedly:

1. Check [CHANGELOG.md](CHANGELOG.md) for breaking changes
2. Review test output carefully
3. Verify environment variables are set
4. Check Obsidian plugin logs
5. Open an issue with test output and environment details

---

## 📝 Contributing Tests

When adding new features:

1. Write tests first (TDD)
2. Achieve 85%+ coverage for new code
3. Add integration tests if API-based
4. Update this guide with new test patterns
5. Ensure CI passes before submitting PR
