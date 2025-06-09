# uzpy

**A Python tool that automatically analyzes code usage patterns and updates docstrings with "Used in:" documentation.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)]()

`uzpy` scans Python codebases to find where each function, class, and method is used, then automatically updates their docstrings with comprehensive usage information. It helps developers understand code dependencies and maintain better documentation.

## ✨ Features

- **🔍 Fast Parsing**: Uses Tree-sitter for efficient, error-resilient Python parsing
- **🎯 Hybrid Analysis**: Combines Rope and Jedi for comprehensive usage detection with fallback strategies
- **📝 Safe Modifications**: Preserves all code formatting using LibCST with lossless editing
- **🛡️ Error Recovery**: Graceful handling of syntax errors, analysis failures, and edge cases
- **🧹 Cleanup Support**: Clean command to remove all "Used in:" sections

## 🚀 Installation

```bash
# Install with uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e .

# Or with pip
pip install -e .
```

## 📖 Quick Start

```bash
# Analyze and update docstrings in current directory
python -m uzpy run

# Analyze specific path
python -m uzpy run --edit src/myproject/

# Preview changes without modification (dry-run mode)
python -m uzpy test --edit src/myproject/ --verbose

# Remove all "Used in:" sections
python -m uzpy clean --edit src/myproject/
```

## 💡 Usage Examples

### Basic Analysis

```bash
# Analyze current directory
python -m uzpy run

# Analyze specific path
python -m uzpy run --edit src/myproject/

# Analyze with custom exclusions
python -m uzpy run --edit src/ --xclude_patterns tests,migrations
```

### Preview Mode

```bash
# Dry run to see what would change
python -m uzpy test --edit src/myproject/ --verbose

# Test specific file
python -m uzpy test --edit src/utils.py --verbose
```

### Cleanup

```bash
# Remove all "Used in:" sections
python -m uzpy clean --edit src/

# Clean with verbose output
python -m uzpy clean --edit src/ --verbose
```

## 🔧 How It Works

uzpy uses a four-phase pipeline:

1. **🔍 Discovery Phase**: Finds Python files using pathspec while respecting gitignore patterns
2. **📊 Parsing Phase**: Uses Tree-sitter to extract functions, classes, methods, and modules with their docstrings
3. **🔗 Analysis Phase**: Employs hybrid Rope+Jedi analysis with intelligent strategy selection
4. **📝 Modification Phase**: Uses LibCST to safely update docstrings while preserving all formatting

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Discovery │───▶│  Tree-sitter     │───▶│  Hybrid Analyzer│───▶│  LibCST Modifier│
│   (pathspec +    │    │  Parser          │    │  (Rope + Jedi)  │    │  (docstring     │
│   gitignore)     │    │  (AST extraction)│    │  (usage finding)│    │   updates)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └─────────────────┘
```

### What Gets Updated

uzpy automatically adds "Used in:" sections to docstrings:

**Before:**
```python
def calculate_total(items):
    """Calculate the total price of items."""
    return sum(item.price for item in items)
```

**After:**
```python
def calculate_total(items):
    """Calculate the total price of items.

    Used in:
    - src/billing/invoice.py
    - tests/test_calculations.py
    """
    return sum(item.price for item in items)
```

## 🔧 CLI Reference

### Commands

| Command | Description |
|---------|-------------|
| `run` | Analyze and update docstrings (default behavior) |
| `test` | Run analysis in dry-run mode without modifying files |
| `clean` | Remove all "Used in:" sections from docstrings |

### Constructor Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `edit` | str/Path | Path to analyze and modify | current directory |
| `ref` | str/Path | Reference path for usage search | same as edit |
| `verbose` | bool | Enable detailed logging | False |
| `xclude_patterns` | str/list | Exclude patterns (comma-separated) | None |
| `methods_include` | bool | Include method definitions | True |
| `classes_include` | bool | Include class definitions | True |
| `functions_include` | bool | Include function definitions | True |

### Examples

```bash
# Basic usage
python -m uzpy run --edit src/

# With custom options
python -m uzpy run --edit src/ --ref . --verbose --xclude_patterns tests,migrations

# Dry run mode
python -m uzpy test --edit src/ --verbose

# Clean docstrings
python -m uzpy clean --edit src/
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/twardoch/uzpy.git
cd uzpy

# Setup with uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e .[dev,test]

# Or with pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[dev,test]
```

### Development Workflow

```bash
# Run tests
python -m pytest

# Lint and format
ruff check --fix
ruff format

# Full development pipeline
fd -e py -x autoflake {}; fd -e py -x pyupgrade --py312-plus {}; fd -e py -x ruff check --output-format=github --fix --unsafe-fixes {}; fd -e py -x ruff format --respect-gitignore --target-version py312 {}; python -m pytest;
```

### Architecture Overview

uzpy is designed with clear separation of concerns:

- **`src/uzpy/cli.py`** - Fire-based command-line interface
- **`src/uzpy/discovery.py`** - File discovery with gitignore support  
- **`src/uzpy/parser/tree_sitter_parser.py`** - Tree-sitter based Python parsing
- **`src/uzpy/analyzer/hybrid_analyzer.py`** - Hybrid reference analysis combining Rope and Jedi
- **`src/uzpy/modifier/libcst_modifier.py`** - LibCST-based safe code modification
- **`src/uzpy/pipeline.py`** - Main orchestration pipeline
- **`src/uzpy/types.py`** - Core data structures

## 📋 Requirements

### System Requirements

- **Python**: 3.10 or higher
- **Operating Systems**: Linux, macOS, Windows

### Dependencies

Core dependencies are automatically installed:

- **tree-sitter** & **tree-sitter-python** - Fast AST parsing
- **rope** - Accurate code analysis
- **jedi** - Fast symbol resolution
- **libcst** - Safe code modification
- **fire** - CLI generation
- **loguru** - Logging
- **pathspec** - Gitignore pattern matching
- **rich** - Terminal output

## ⚠️ Current Limitations

1. **Basic CLI**: Simple Fire-based interface (no fancy Rich tables)
2. **No Configuration Files**: No `.uzpy.toml` support yet
3. **No Performance Metrics**: No benchmarking data available
4. **Limited Error Context**: Some analysis failures may not provide detailed context
5. **No Watch Mode**: No real-time file monitoring

## 🚧 Future Enhancements

- **Enhanced CLI**: Rich-based terminal output with progress bars and tables
- **Configuration Support**: `.uzpy.toml` configuration files
- **Performance Optimization**: Benchmarking and optimization for large codebases
- **Watch Mode**: Real-time file monitoring and updates
- **Plugin System**: Extensible architecture for custom analyzers

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Guidelines

1. Follow the existing code style (Ruff configuration)
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Tree-sitter** for fast, error-resilient parsing
- **Rope** for accurate cross-file analysis  
- **Jedi** for fast symbol resolution
- **LibCST** for safe code modification with formatting preservation
- **Fire** for simple CLI generation
- **The Python community** for excellent tooling and libraries

