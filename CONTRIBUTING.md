# Contributing to speccheck

Thank you for your interest in contributing to speccheck! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Submitting Changes](#submitting-changes)
- [CI/CD Pipeline](#cicd-pipeline)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/speccheck.git
   cd speccheck
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/happykhan/speccheck.git
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip
- git

### Install Development Dependencies

```bash
# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package in editable mode with dev dependencies
pip install -e '.[dev]'

# Install pre-commit hooks (recommended)
pre-commit install
```

### Verify Setup

```bash
# Check installation
speccheck --version

# Run tests
pytest

# Run linters
ruff check speccheck/
black --check speccheck/
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes

### 2. Make Your Changes

- Write clear, concise code
- Follow the project's code style (enforced by Black and Ruff)
- Add tests for new functionality
- Update documentation as needed

### 3. Commit Your Changes

```bash
git add .
git commit -m "Brief description of changes"
```

**Commit message guidelines:**
- Use present tense ("Add feature" not "Added feature")
- First line: brief summary (50 chars or less)
- Blank line, then detailed description if needed
- Reference issues: "Fixes #123" or "Closes #456"

**Examples:**
```
Add metadata merge functionality to collect command

- Add --metadata option to CLI
- Implement CSV reading and merging logic
- Update tests and documentation

Fixes #42
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=speccheck

# Run specific test file
pytest tests/test_collect.py

# Run with verbose output
pytest -vv

# Run specific test
pytest tests/test_collect.py::test_collect_files -vv
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use pytest fixtures for reusable setup
- Aim for >80% code coverage

**Example test:**
```python
def test_collect_with_metadata(tmp_path):
    """Test collect command with metadata merge."""
    # Arrange
    metadata_file = tmp_path / "metadata.csv"
    metadata_file.write_text("sample_id,location\nsample1,Lab A")
    
    # Act
    result = collect(..., metadata_file=str(metadata_file))
    
    # Assert
    assert result is not None
    assert "location" in result
```

## Code Quality

### Automated Checks

The following checks run automatically on every commit (with pre-commit) and in CI:

1. **Black** - Code formatting
   ```bash
   black speccheck/ tests/
   ```

2. **isort** - Import sorting
   ```bash
   isort speccheck/ tests/
   ```

3. **Ruff** - Fast linting
   ```bash
   ruff check speccheck/ tests/
   ruff check --fix speccheck/ tests/  # Auto-fix
   ```

4. **Pylint** - Comprehensive linting
   ```bash
   pylint speccheck/
   ```

5. **Bandit** - Security checks
   ```bash
   bandit -r speccheck/
   ```

### Manual Checks

Before submitting a PR, run:

```bash
# Format code
black speccheck/ tests/
isort speccheck/ tests/

# Lint
ruff check speccheck/ tests/
pylint speccheck/

# Test
pytest --cov=speccheck

# Security
bandit -r speccheck/
safety check
```

### Pre-commit Hooks

If you installed pre-commit hooks, they run automatically on `git commit`:

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Skip hooks (not recommended)
git commit --no-verify
```

## Submitting Changes

### 1. Update Your Branch

```bash
# Fetch latest changes from upstream
git fetch upstream

# Rebase your branch
git rebase upstream/main
```

### 2. Push Your Changes

```bash
git push origin feature/your-feature-name
```

### 3. Create a Pull Request

1. Go to your fork on GitHub
2. Click "Pull Request"
3. Select your branch and `main` as the base
4. Fill in the PR template:
   - **Title**: Clear, concise description
   - **Description**: What changed and why
   - **Testing**: How you tested the changes
   - **Related Issues**: Reference issue numbers

### 4. PR Checklist

Before submitting, ensure:

- [ ] Tests pass locally (`pytest`)
- [ ] Code is formatted (`black`, `isort`)
- [ ] Linting passes (`ruff`, `pylint`)
- [ ] Coverage maintained or improved
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG updated (for significant changes)
- [ ] Commit messages are clear
- [ ] Branch is up to date with `main`

### 5. Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- CI checks must pass
- At least one approval required for merge

## CI/CD Pipeline

### Continuous Integration

Every push and PR triggers automated checks:

1. **Lint Job**: Black, isort, Ruff, Pylint
2. **Test Job**: pytest on Python 3.10, 3.11, 3.12 (Ubuntu, macOS, Windows)
3. **Build Job**: Package building and installation test
4. **Integration Job**: End-to-end functionality tests
5. **Security Job**: Bandit and Safety scans

See [CI_DOCS.md](CI_DOCS.md) for details.

### Status Checks

Your PR must pass:
- ✅ All test jobs (required)
- ✅ Build job (required)
- ⚠️ Lint jobs (non-blocking but should be addressed)
- ⚠️ Security jobs (non-blocking but should be reviewed)

## Development Tips

### Project Structure

```
speccheck/
├── speccheck/          # Main package
│   ├── __init__.py     # Package initialization, version
│   ├── main.py         # Core logic (collect, summary, check)
│   ├── collect.py      # File collection utilities
│   ├── criteria.py     # Criteria validation
│   ├── report.py       # Report generation
│   ├── modules/        # Tool-specific parsers
│   └── plot_modules/   # Visualization modules
├── tests/              # Test suite
├── templates/          # HTML templates
└── pyproject.toml      # Package configuration
```

### Adding a New Module

1. Create parser in `speccheck/modules/your_tool.py`:
   ```python
   def check_file_type(filepath):
       """Check if file is from your tool."""
       # Return True if valid, False otherwise
   
   def fetch_values(filepath):
       """Extract metrics from file."""
       # Return dict of metrics
   ```

2. Add tests in `tests/test_module_your_tool.py`

3. Module is auto-discovered by `load_modules_with_checks()`

### Adding a Plot Module

1. Create plotter in `speccheck/plot_modules/plot_your_tool.py`:
   ```python
   def plot(plot_dict, species_name):
       """Generate visualization."""
       # Return plotly figure or HTML table
   ```

2. Register in `report.py` if needed

### Debugging

```bash
# Run with verbose logging
speccheck -v collect ...

# Use Python debugger
python -m pdb speccheck.py collect ...

# VS Code debugging
# Use .vscode/launch.json configurations
```

## Questions?

- 📖 Read the [README](README.md)
- 📚 Check [CI_DOCS.md](CI_DOCS.md)
- 🐛 Search [existing issues](https://github.com/happykhan/speccheck/issues)
- 💬 Open a [new issue](https://github.com/happykhan/speccheck/issues/new)

Thank you for contributing to speccheck! 🎉
