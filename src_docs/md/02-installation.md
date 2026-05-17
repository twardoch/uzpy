# Installation

This chapter explains how to install uzpy, manage dependencies, and set up your development environment.

## System Requirements

### Python Version

uzpy requires **Python 3.10 or higher**. Check your version:

```bash
python --version
# or
python3 --version
```

### Supported Platforms

- **Linux**: All major distributions
- **macOS**: 10.15+ (Catalia and later)
- **Windows**: Windows 10/11 with PowerShell or WSL

### Package Manager

Use `uv` for faster package management:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# or on Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Installation Methods

### Method 1: Using uv (Recommended)

Install core package:

```bash
uv pip install uzpy
```

Install with all optional dependencies:

```bash
uv pip install uzpy[all]
```

### Method 2: Using pip

```bash
pip install uzpy
```

For all features:

```bash
pip install uzpy[all]
```

### Method 3: Development Installation

To contribute or use latest features:

```bash
# Clone repository
git clone https://github.com/twardoch/uzpy.git
cd uzpy

# Install in editable mode with development dependencies
uv pip install -e .[dev,test]
```

## Optional Dependencies

uzpy supports several dependency groups:

### Development Tools (`dev`)

```bash
uv pip install uzpy[dev]
```

Includes:
- `pre-commit` - Git hooks
- `ruff` - Linter and formatter
- `mypy` - Type checking
- `pyupgrade` - Syntax updates
- `autoflake` - Import cleanup

### Testing Framework (`test`)

```bash
uv pip install uzpy[test]
```

Includes:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reports
- `pytest-xdist` - Parallel execution
- `pytest-benchmark` - Performance tests
- `pytest-asyncio` - Async support

### Documentation (`docs`)

```bash
uv pip install uzpy[docs]
```

Includes:
- `sphinx` - Documentation generator
- `sphinx-rtd-theme` - Theme
- `sphinx-autodoc-typehints` - Type hint docs
- `myst-parser` - Markdown support

### All Dependencies

Install everything:

```bash
uv pip install uzpy[all]
```

## Core Dependencies

uzpy automatically installs these:

### Analysis Engines

- **`tree-sitter`** + **`tree-sitter-python`**: Fast Python parsing
- **`jedi`**: Code completion
- **`rope`**: Refactoring library
- **`pyright`**: Type checker
- **`ast-grep-py`**: Code search

### Code Modification

- **`libcst`**: Syntax tree modification
- **`pathspec`**: Gitignore-style patterns

### CLI and Configuration

- **`typer`**: Command-line interface
- **`rich`**: Terminal formatting
- **`pydantic-settings`**: Config management
- **`loguru`**: Logging

### Storage and Caching

- **`diskcache`**: File caching
- **`duckdb`**: Analytical database (future use)
- **`sqlalchemy`**: Database ORM
- **`msgpack`**: Binary serialization

### File Monitoring

- **`watchdog`**: File system events

## Verifying Installation

Test uzpy after installation:

```bash
# Check version
uzpy --version

# Basic help
uzpy --help

# Command help
uzpy run --help
```

Expected output:

```
uzpy version 1.3.1
Python 3.11.5
```

## Virtual Environment Setup

### Using venv

```bash
# Create environment
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install uzpy
uv pip install uzpy[all]
```

### Using conda

```bash
# Create environment
conda create -n uzpy python=3.11

# Activate
conda activate uzpy

# Install uzpy
pip install uzpy[all]
```

### Using hatch (Development)

uzpy uses hatch for development:

```bash
# Install hatch
pip install hatch

# Create environment
hatch env create

# Enter environment
hatch shell

# Run tests
hatch run test:test

# Lint code
hatch run lint:all
```

## Configuration Directory

uzpy creates these directories:

### Linux/macOS

```
~/.cache/uzpy/          # Cache files
~/.config/uzpy/         # Config files
```

### Windows

```
%LOCALAPPDATA%\uzpy\cache\      # Cache files
%APPDATA%\uzpy\config\          # Config files
```

## External Tool Dependencies

Some features need external tools:

### ast-grep

```bash
# Install CLI tool (optional)
npm install -g @ast-grep/cli
# or
cargo install ast-grep
```

### Pyright

Pyright is included, but you can install the CLI version:

```bash
npm install -g pyright
```

## Troubleshooting

### Common Issues

#### ImportError for tree-sitter

```bash
# Reinstall bindings
uv pip uninstall tree-sitter tree-sitter-python
uv pip install tree-sitter tree-sitter-python
```

#### Permission errors (macOS/Linux)

```bash
# Install for current user
uv pip install --user uzpy[all]
```

#### Windows compilation errors

```bash
# Install Microsoft C++ Build Tools first
uv pip install uzpy[all]
```

### Dependency Conflicts

If conflicts occur:

```bash
# Fresh environment
python -m venv .venv-uzpy
source .venv-uzpy/bin/activate  # or Windows equivalent
uv pip install uzpy[all]
```

### Checking Dependencies

Verify installation:

```bash
# List packages
uv pip list | grep -E "(uzpy|tree-sitter|jedi|rope|pyright)"

# Check conflicts
uv pip check
```

## Environment Variables

Set these for system-wide config:

```bash
# Add to ~/.bashrc, ~/.zshrc, or equivalent
export UZPY_CACHE_DIR="$HOME/.cache/uzpy"
export UZPY_CONFIG_DIR="$HOME/.config/uzpy"
export UZPY_LOG_LEVEL="INFO"
```

## IDE Integration

### VS Code

1. Open Command Palette (`Ctrl+Shift+P`)
2. Select "Python: Select Interpreter"
3. Choose your uzpy environment

### PyCharm

1. Settings → Project → Python Interpreter
2. Add interpreter from uzpy environment
3. Confirm uzpy appears in package list

## Next Steps

With uzpy installed:

1. **[Learn the command-line interface](03-command-line-usage.md)**
2. **[Configure uzpy for your project](04-configuration.md)**
3. **[Understand the architecture](05-architecture-overview.md)**

Next chapter covers CLI usage in detail.