# Contributing to Rekall

Thanks for your interest in contributing to Rekall! This document provides guidelines for contributing.

## Code of Conduct

Be respectful and inclusive. We're all here to build something useful together.

## Ways to Contribute

- **Report bugs**: Open an issue with reproduction steps
- **Suggest features**: Open an issue describing the feature and use case
- **Fix bugs**: Submit a PR with tests
- **Add features**: Discuss in an issue first, then submit PR
- **Improve docs**: PRs for documentation are always welcome

## Development Setup

### Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

```bash
# Clone the repository
git clone https://github.com/guthubrx/rekall.git
cd rekall

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rekall

# Run specific test file
pytest tests/test_db.py
```

### Code Style

We use:
- **Ruff** for linting and formatting
- **Type hints** throughout the codebase

```bash
# Check code style
ruff check .

# Format code
ruff format .

# Type checking (optional)
mypy rekall
```

## Submitting Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Write clear, concise code
- Add tests for new functionality
- Update documentation if needed

### 3. Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new search filter option
fix: handle empty query edge case
docs: update MCP integration guide
test: add tests for consolidation scoring
refactor: simplify search pipeline
```

### 4. Submit a Pull Request

1. Push your branch: `git push origin feature/your-feature-name`
2. Open a PR against `main`
3. Fill out the PR template
4. Wait for review

### PR Checklist

- [ ] Tests pass (`pytest`)
- [ ] Code is formatted (`ruff format .`)
- [ ] No linting errors (`ruff check .`)
- [ ] Documentation updated (if applicable)
- [ ] Commit messages follow convention

## Project Structure

```
rekall/
├── rekall/
│   ├── __init__.py      # Package init, version
│   ├── cli.py           # CLI commands (Click)
│   ├── db.py            # Database operations
│   ├── models.py        # Data models
│   ├── tui.py           # Terminal UI (Textual)
│   ├── embeddings.py    # Embedding generation
│   ├── mcp_server.py    # MCP server
│   └── i18n.py          # Internationalization
├── tests/
│   ├── conftest.py      # Test fixtures
│   ├── test_cli.py
│   ├── test_db.py
│   └── ...
├── docs/                # Documentation
└── pyproject.toml       # Project config
```

## Architecture Decisions

Before making significant changes, please:

1. Check existing issues and discussions
2. Open an issue to discuss the approach
3. Reference relevant research (for algorithm changes)

Key design principles:
- **Local-first**: No network calls, no cloud dependencies
- **Cognitive science**: Features should have research backing
- **Simplicity**: Prefer simple solutions over complex ones
- **Performance**: Sub-second operations for all commands

## Testing Guidelines

### Test Structure

```python
def test_search_finds_exact_match(db):
    """Search should find entries with exact keyword match."""
    # Arrange
    entry = db.add_entry(type="bug", title="CORS error", tags=["cors"])

    # Act
    results = db.search("cors")

    # Assert
    assert len(results) == 1
    assert results[0].id == entry.id
```

### What to Test

- Happy path (normal usage)
- Edge cases (empty input, special characters)
- Error conditions (invalid input, missing data)

## Release Process

Releases are managed by maintainers:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.x.x`
4. Push tag: `git push --tags`

## Questions?

- Open an issue for questions
- Check existing issues first
- Be specific and provide context

Thank you for contributing!
