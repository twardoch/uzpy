# uzpy

**A production-ready Python tool that automatically analyzes code usage patterns and updates docstrings with "Used in:" documentation.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Production Ready](https://img.shields.io/badge/status-production%20ready-green.svg)]()

uzpy scans Python codebases to find where each function, class, and method is used, then automatically updates their docstrings with comprehensive usage information. This helps developers understand code dependencies and maintain better documentation.

## ✨ Features

- **🔍 Smart Analysis**: Uses Tree-sitter for fast, error-resilient Python parsing
- **🎯 Accurate References**: Combines Rope and Jedi for comprehensive usage detection  
- **📝 Safe Modifications**: Preserves code formatting using LibCST with lossless editing
- **⚡ High Performance**: Optimized for large codebases with hybrid analysis strategies
- **🎨 Beautiful Output**: Rich terminal interface with progress indicators and summaries
- **🛡️ Error Recovery**: Graceful handling of syntax errors and edge cases
- **🏗️ Production Ready**: Complete implementation with comprehensive error handling

## 🚀 Installation

```bash
# Install dependencies with uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e .

# Or with pip
pip install tree-sitter tree-sitter-python rope jedi libcst fire rich loguru pathspec
pip install -e .
```

## 📖 Quick Start

```bash
# Analyze and update docstrings in a project
python -m uzpy -e src/myproject/

# Preview changes without modification  
python -m uzpy -e src/myproject/ --dry-run --verbose

# Analyze a single file
python -m uzpy -e src/myproject/module.py --dry-run

# Get help
python -m uzpy --help
```

## 💡 Usage Examples

### Basic Analysis

```bash
# Analyze and update docstrings in a project directory
python -m uzpy -e src/myproject/

# Analyze a single file
python -m uzpy -e src/myproject/utils.py
```

### Preview Mode

```bash
# See what would change without modifying files
python -m uzpy -e src/myproject/ --dry-run --verbose

# Get detailed analysis information
python -m uzpy -e src/myproject/ --dry-run --verbose
```

### Real-World Examples

```bash
# Analyze your entire src directory
python -m uzpy -e src/ --verbose

# Check a specific module before refactoring
python -m uzpy -e src/core/database.py --dry-run

# Update documentation for API modules
python -m uzpy -e src/api/ --verbose
```

## 🔧 How It Works

uzpy uses a sophisticated four-phase pipeline:

1. **🔍 Discovery Phase**: Finds all Python files while respecting gitignore patterns
2. **📊 Parsing Phase**: Uses Tree-sitter to extract functions, classes, and methods with their docstrings
3. **🔗 Analysis Phase**: Employs a hybrid approach combining Rope and Jedi to find usage patterns
4. **📝 Modification Phase**: Uses LibCST to safely update docstrings while preserving formatting

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Discovery │───▶│  Tree-sitter     │───▶│  Hybrid Analyzer│───▶│  LibCST Modifier│
│   (gitignore +   │    │  Parser          │    │  (Rope + Jedi)  │    │  (docstring     │
│   pathspec)      │    │  (AST + constructs)│   │  (usage finding)│    │   updates)      │
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
    - src/main.py
    - src/billing/invoice.py
    - tests/test_calculations.py"""
    return sum(item.price for item in items)
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

## 🔧 CLI Reference

### Main Command

```bash
python -m uzpy [OPTIONS]
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--edit` | `-e` | Path to analyze and modify | Required |
| `--ref` | `-r` | Reference path to search for usage | Same as edit |
| `--verbose` | `-v` | Enable detailed logging | `False` |
| `--dry-run` | | Show changes without modifying files | `False` |
| `--methods-include` | | Include method definitions | `True` |
| `--classes-include` | | Include class definitions | `True` |
| `--functions-include` | | Include function definitions | `True` |
| `--exclude-patterns` | Comma-separated glob patterns to exclude | None |

## 🛠️ Development

uzpy is built with modern Python practices and comprehensive testing.

### Setup Development Environment

```bash
# Clone the repository  
git clone https://github.com/yourusername/uzpy.git
cd uzpy

# Setup with uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e .

# Or with pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### Development Workflow

```bash
# Run tests
python -m pytest

# Lint and format code
ruff check --fix
ruff format

# Full development pipeline (from CLAUDE.md)
fd -e py -x autoflake {}; fd -e py -x pyupgrade --py311-plus {}; fd -e py -x ruff check --output-format=github --fix --unsafe-fixes {}; fd -e py -x ruff format --respect-gitignore --target-version py311 {}; python -m pytest;
```

### Architecture Overview

uzpy is designed with modularity and extensibility in mind:

- **`src/uzpy/cli.py`** - Command-line interface using Fire and Rich
- **`src/uzpy/discovery.py`** - File discovery with gitignore support  
- **`src/uzpy/parser/`** - Tree-sitter based Python parsing
- **`src/uzpy/analyzer/`** - Hybrid reference analysis (Rope + Jedi)
- **`src/uzpy/modifier/`** - LibCST-based safe code modification

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Tree-sitter** for fast, error-resilient parsing
- **Rope** for accurate cross-file analysis  
- **Jedi** for fast symbol resolution
- **LibCST** for safe code modification
- **Rich** for beautiful terminal output

