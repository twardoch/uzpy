# uzpy

**A Python tool that automatically analyzes code usage patterns and updates docstrings with "Used in:" documentation.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

uzpy scans Python codebases to find where each function, class, and method is used, then automatically updates their docstrings with comprehensive usage information. This helps developers understand code dependencies and maintain better documentation.

## Features

- **🔍 Smart Analysis**: Uses Tree-sitter for fast, error-resilient Python parsing
- **🎯 Accurate References**: Combines Rope and Jedi for comprehensive usage detection
- **📝 Safe Modifications**: Preserves code formatting using LibCST (planned)
- **⚡ High Performance**: Optimized for large codebases with hybrid analysis strategies
- **🎨 Beautiful Output**: Rich terminal interface with progress indicators and summaries
- **🛡️ Error Recovery**: Graceful handling of syntax errors and edge cases

## Installation

```bash
# Install from PyPI (when published)
pip install uzpy

# Or install from source
git clone https://github.com/yourusername/uzpy.git
cd uzpy
pip install -e .
```

## Quick Start

```bash
# Analyze a single file
uzpy run --edit myproject/utils.py

# Analyze entire directory 
uzpy run --edit src/ --ref .

# Dry run to see what would change
uzpy run --edit src/ --dry-run --verbose

# Get detailed help
uzpy run --help
```

## Usage Examples

### Basic Analysis

```bash
# Analyze functions in utils.py and search for usage across the current directory
uzpy run --edit utils.py --ref .
```

### Advanced Options

```bash
# Comprehensive analysis with verbose output
uzpy run \
  --edit src/mypackage/ \
  --ref . \
  --verbose \
  --include-methods \
  --include-classes \
  --include-functions \
  --exclude-patterns="tests/*,build/*"
```

### Configuration Examples

```bash
# Focus on specific construct types
uzpy run --edit src/ --include-functions --no-include-methods

# Exclude test directories
uzpy run --edit src/ --exclude-patterns="**/test_*,**/tests/*"

# Dry run to preview changes
uzpy run --edit src/ --dry-run
```

## How It Works

uzpy uses a sophisticated three-phase pipeline:

1. **🔍 Discovery Phase**: Finds all Python files while respecting gitignore patterns
2. **📊 Parsing Phase**: Uses Tree-sitter to extract functions, classes, and methods with their docstrings
3. **🔗 Analysis Phase**: Employs a hybrid approach combining Rope and Jedi to find usage patterns

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   File Discovery │───▶│  Tree-sitter     │───▶│  Hybrid Analyzer│
│   (gitignore +   │    │  Parser          │    │  (Rope + Jedi)  │
│   pathspec)      │    │  (AST + constructs)│   │  (usage finding)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  LibCST Modifier│
                                               │  (docstring     │
                                               │   updates)      │
                                               └─────────────────┘
```

## Example Output

When you run uzpy, you'll see beautiful terminal output like this:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ uzpy Configuration     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Edit Path              │ src/myproject/     │
│ Reference Path         │ .                  │
│ Dry Run                │ No                 │
│ Verbose                │ Yes                │
└────────────────────────┴────────────────────┘

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ File Discovery Summary         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Edit Files      │ 23  │ utils.py, models.py, ... │
│ Reference Files │ 156 │ main.py, tests.py, ...   │
└─────────────────┴─────┴──────────────────────────┘

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Construct Parsing Summary        ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Module   │ 23   │ 12/23 │
│ Class    │ 45   │ 31/45 │
│ Function │ 128  │ 89/128│
│ Method   │ 267  │ 156/267│
│ Total    │ 463  │ 288/463│
└──────────┴──────┴───────┘
```

## CLI Reference

### Commands

- `uzpy run` - Main analysis command

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--edit` | Path to analyze and modify | Required |
| `--ref` | Reference path to search for usage | Same as edit |
| `--verbose` | Enable detailed logging | `False` |
| `--dry-run` | Show changes without modifying files | `False` |
| `--include-methods` | Include method definitions | `True` |
| `--include-classes` | Include class definitions | `True` |
| `--include-functions` | Include function definitions | `True` |
| `--exclude-patterns` | Comma-separated glob patterns to exclude | None |

## Development

uzpy is built with modern Python practices and comprehensive testing.

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/uzpy.git
cd uzpy

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Development Workflow

```bash
# Run tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=uzpy

# Lint and format code
ruff check --fix
ruff format

# Type checking
mypy src/uzpy

# Full development pipeline
fd -e py -x autoflake {}; fd -e py -x pyupgrade --py311-plus {}; fd -e py -x ruff check --output-format=github --fix --unsafe-fixes {}; fd -e py -x ruff format --respect-gitignore --target-version py311 {}; python -m pytest;
```

### Architecture Overview

uzpy is designed with modularity and extensibility in mind:

- **`src/uzpy/cli.py`** - Command-line interface using Fire and Rich
- **`src/uzpy/discovery.py`** - File discovery with gitignore support
- **`src/uzpy/parser/`** - Tree-sitter based Python parsing
- **`src/uzpy/analyzer/`** - Hybrid analysis using Rope and Jedi
- **`src/uzpy/modifier/`** - LibCST-based code modification (planned)

## Contributing

Contributions are welcome! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the full development pipeline
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

We follow strict code quality standards:

- **Formatting**: Ruff with line length 88
- **Type Hints**: Full type annotations required
- **Documentation**: Comprehensive docstrings for all public APIs
- **Testing**: Minimum 90% test coverage

## Current Status

**Version**: 0.1.0 (Development)

**Completed Features**:
- ✅ CLI interface with Rich formatting
- ✅ File discovery with gitignore support
- ✅ Tree-sitter Python parsing
- ✅ Rope and Jedi analysis integration
- ✅ Hybrid analysis strategies
- ✅ Comprehensive test suite

**Planned Features**:
- 🔄 LibCST-based docstring modification
- 🔄 Configuration file support
- 🔄 Language Server Protocol integration
- 🔄 CI/CD integration tools

## Requirements

- **Python**: 3.11+ (uses modern Python features)
- **Dependencies**: All managed automatically via pip
  - `tree-sitter` and `tree-sitter-python` for parsing
  - `rope` for accurate reference finding
  - `jedi` for fast symbol resolution
  - `fire` for CLI generation
  - `rich` for beautiful terminal output
  - `loguru` for structured logging
  - `pathspec` for gitignore pattern matching

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

---

**Built with ❤️ using modern Python tools and best practices.**