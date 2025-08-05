---
# this_file: src_docs/md/02-installation.md
---

# Installation

This chapter covers installing uzpy, managing dependencies, and setting up your development environment.

## System Requirements

### Python Version

uzpy requires **Python 3.10 or higher**. Check your Python version:

```bash
python --version
# or
python3 --version
```

### Supported Platforms

- **Linux**: All major distributions
- **macOS**: 10.15+ (Catalina and later)  
- **Windows**: Windows 10/11 with PowerShell or WSL

### Package Manager

We recommend using `uv` for faster package management:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# or on Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Installation Methods

### Method 1: Using uv (Recommended)

Install the core package:

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

For contributing to uzpy or using the latest features:

```bash
# Clone the repository
git clone https://github.com/twardoch/uzpy.git
cd uzpy

# Install in editable mode with development dependencies
uv pip install -e .[dev,test]
```

## Optional Dependencies

uzpy has several optional dependency groups for different use cases:

### Development Tools (`dev`)

```bash
uv pip install uzpy[dev]
```

Includes:
- `pre-commit` - Git hooks for code quality
- `ruff` - Fast linter and formatter  
- `mypy` - Static type checking
- `pyupgrade` - Syntax modernization
- `autoflake` - Remove unused imports

### Testing Framework (`test`)

```bash
uv pip install uzpy[test]
```

Includes:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-xdist` - Parallel test execution
- `pytest-benchmark` - Performance testing
- `pytest-asyncio` - Async test support

### Documentation (`docs`)

```bash
uv pip install uzpy[docs]
```

Includes:
- `sphinx` - Documentation generator
- `sphinx-rtd-theme` - Read the Docs theme
- `sphinx-autodoc-typehints` - Type hint documentation
- `myst-parser` - Markdown support

### All Dependencies

Install everything:

```bash
uv pip install uzpy[all]
```

## Core Dependencies

uzpy automatically installs these core dependencies:

### Analysis Engines

- **`tree-sitter`** + **`tree-sitter-python`**: Fast, robust Python parsing
- **`jedi`**: Python completion and static analysis  
- **`rope`**: Python refactoring library
- **`pyright`**: Microsoft's static type checker
- **`ast-grep-py`**: Structural code search

### Code Modification

- **`libcst`**: Concrete syntax tree library for safe code modification
- **`pathspec`**: `.gitignore`-style pattern matching

### CLI and Configuration

- **`typer`**: Modern CLI framework
- **`rich`**: Rich text and beautiful formatting
- **`pydantic-settings`**: Configuration management
- **`loguru`**: Advanced logging

### Storage and Caching

- **`diskcache`**: Persistent caching
- **`duckdb`**: Fast analytical database (future use)
- **`sqlalchemy`**: ORM for structured storage
- **`msgpack`**: Fast binary serialization

### File Monitoring

- **`watchdog`**: File system event monitoring

## Verifying Installation

After installation, verify uzpy is working:

```bash
# Check version
uzpy --version

# Test basic functionality
uzpy --help

# Verify analyzers are available
uzpy run --help
```

You should see output similar to:

```
uzpy version 1.3.1
Python 3.11.5
```

## Virtual Environment Setup

### Using venv

```bash
# Create virtual environment
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

### Using hatch (for development)

uzpy uses hatch for development environment management:

```bash
# Install hatch
pip install hatch

# Create development environment  
hatch env create

# Enter the environment
hatch shell

# Run tests
hatch run test:test

# Run linting
hatch run lint:all
```

## Configuration Directory

uzpy creates configuration and cache directories:

### Linux/macOS

```
~/.cache/uzpy/          # Cache data
~/.config/uzpy/         # Configuration files
```

### Windows

```
%LOCALAPPDATA%\uzpy\cache\      # Cache data
%APPDATA%\uzpy\config\          # Configuration files
```

## External Tool Dependencies

Some analyzers require external tools to be installed:

### ast-grep

```bash
# Install ast-grep CLI (optional, improves performance)
npm install -g @ast-grep/cli
# or
cargo install ast-grep
```

### Pyright

Pyright is included as a Python package, but you can also install the CLI:

```bash
npm install -g pyright
```

## Troubleshooting Installation

### Common Issues

#### ImportError for tree-sitter

```bash
# Ensure tree-sitter bindings are properly compiled
uv pip uninstall tree-sitter tree-sitter-python
uv pip install tree-sitter tree-sitter-python
```

#### Permission errors on macOS/Linux

```bash
# Use user installation
uv pip install --user uzpy[all]
```

#### Windows compilation errors

```bash
# Install Microsoft C++ Build Tools
# Then try installation again
uv pip install uzpy[all]
```

### Dependency Conflicts

If you encounter dependency conflicts:

```bash
# Create a fresh virtual environment
python -m venv .venv-uzpy
source .venv-uzpy/bin/activate  # or Windows equivalent
uv pip install uzpy[all]
```

### Checking Dependencies

Verify all dependencies are correctly installed:

```bash
# List installed packages
uv pip list | grep -E "(uzpy|tree-sitter|jedi|rope|pyright)"

# Check for conflicts
uv pip check
```

## Environment Variables

Set these environment variables for system-wide configuration:

```bash
# Add to ~/.bashrc, ~/.zshrc, or equivalent
export UZPY_CACHE_DIR="$HOME/.cache/uzpy"
export UZPY_CONFIG_DIR="$HOME/.config/uzpy"
export UZPY_LOG_LEVEL="INFO"
```

## IDE Integration

### VS Code

Install the Python extension and configure your interpreter:

1. Open Command Palette (`Ctrl+Shift+P`)
2. Select "Python: Select Interpreter"
3. Choose the environment where uzpy is installed

### PyCharm

1. Go to Settings → Project → Python Interpreter
2. Add interpreter from your uzpy environment
3. Verify uzpy is listed in installed packages

## Next Steps

With uzpy installed, you're ready to:

1. **[Learn the command-line interface](03-command-line-usage.md)**
2. **[Configure uzpy for your project](04-configuration.md)**
3. **[Understand the architecture](05-architecture-overview.md)**

The next chapter provides comprehensive CLI usage examples and options.