# uzpy

**A Python tool that automatically analyzes code usage patterns and updates docstrings with "Used in:" documentation.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)]()

`uzpy` scans Python codebases to find where each function, class, and method is used, then automatically updates their docstrings with comprehensive usage information. It helps developers understand code dependencies and maintain better documentation.

## ✨ Features

- **🔍 Fast Parsing**: Uses Tree-sitter for efficient, error-resilient Python parsing.
- **🎯 Flexible Analysis Strategies**:
    - **Traditional Hybrid Analysis**: Combines Rope and Jedi.
    - **Modern Hybrid Analysis**: Orchestrates Ruff, ast-grep, and Pyright for a blend of speed and precision (available via `uzpy-modern` CLI).
- **🚀 Performance Enhancements**:
    - **Caching Layer**: Utilizes `diskcache` for both parser and analyzer results to speed up subsequent runs.
    - **Parallel Processing**: Leverages multiprocessing to analyze constructs concurrently.
- **📝 Safe Modifications**: Preserves all code formatting using LibCST with lossless editing.
- **🛡️ Error Recovery**: Graceful handling of syntax errors, analysis failures, and edge cases.
- **🧹 Cleanup Support**: `clean` command to remove all "Used in:" sections.
- **🔧 Modern CLI (`uzpy-modern`)**:
    - Powered by Typer and Rich for a better user experience.
    - Configuration via `.uzpy.env` files or environment variables (using Pydantic-settings).
    - Commands for cache management (`cache clear`, `cache stats`).
    - Experimental file watching mode (`watch`) for automatic re-analysis.

## 🚀 Installation

```bash
# Install with uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e .

# Or with pip
pip install -e .
```

## 📖 Quick Start

### Using the Classic CLI (`uzpy`)

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

### Using the Modern CLI (`uzpy-modern`)

The modern CLI offers more features and configuration options.

```bash
# Install with modern CLI extras if not already done
# uv pip install -e ".[all]" # Or ensure Typer, Pydantic-settings, etc. are installed

# Basic run (uses settings from .uzpy.env or defaults)
uzpy-modern run

# Specify edit path and run in dry-run mode
uzpy-modern run --edit src/myproject/ --dry-run

# Clean docstrings
uzpy-modern clean --edit src/myproject/

# Manage cache
uzpy-modern cache clear
uzpy-modern cache stats

# Watch for file changes (experimental)
uzpy-modern watch --path src/myproject/
```
See `uzpy-modern --help` for all commands and options. You can configure `uzpy-modern` by creating a `.uzpy.env` file in your project root or by using environment variables prefixed with `UZPY_`.

Example `.uzpy.env` file:
```env
UZPY_EDIT_PATH=./src
UZPY_EXCLUDE_PATTERNS=tests,migrations/*
UZPY_ANALYZER_TYPE=modern_hybrid
UZPY_USE_CACHE=true
UZPY_USE_PARALLEL=true
UZPY_VERBOSE=false
UZPY_LOG_LEVEL=INFO
```

## 💡 Usage Examples

### Classic CLI (`uzpy`) Basic Analysis

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

## 🔧 CLI Reference (`uzpy` - Classic CLI)

The classic CLI (`python -m uzpy` or `uzpy`) is based on Python Fire.

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

`uzpy` uses a modular architecture:

- **CLI Layer**:
    - `src/uzpy/cli.py`: Classic CLI (Python Fire).
    - `src/uzpy/cli_modern.py`: Modern CLI (`uzpy-modern`, Typer, Pydantic-settings).
- **Core Pipeline (`src/uzpy/pipeline.py`)**: Orchestrates the discovery, parsing, analysis, and modification steps. Accepts configured parser and analyzer instances.
- **File Discovery (`src/uzpy/discovery.py`)**: Finds Python files, respects `.gitignore` and custom exclusions.
- **Parsing Layer**:
    - `src/uzpy/parser/tree_sitter_parser.py`: Primary parser using Tree-sitter.
    - `src/uzpy/parser/cached_parser.py`: Wraps parsers with a caching layer.
- **Analysis Layer (`src/uzpy/analyzer/`)**:
    - **Traditional**: `JediAnalyzer`, `RopeAnalyzer`, `HybridAnalyzer`.
    - **Modern**: `RuffAnalyzer`, `AstGrepAnalyzer`, `PyrightAnalyzer`, `ModernHybridAnalyzer`.
    - **Enhancements**: `CachedAnalyzer` (for caching analysis results), `ParallelAnalyzer` (for parallel execution).
- **Modification Layer (`src/uzpy/modifier/libcst_modifier.py`)**: Safely updates docstrings using LibCST.
- **Type Definitions (`src/uzpy/types.py`)**: Core data structures like `Construct` and `Reference`.
- **Watcher (`src/uzpy/watcher.py`)**: File system monitoring for `uzpy-modern watch` mode.


### Modern CLI (`uzpy-modern`) Reference

The `uzpy-modern` CLI provides enhanced features and configuration. Access it via the `uzpy-modern` command after installation.

**Configuration:**
- Create a `.uzpy.env` file in your project root (see example in "Quick Start").
- Or, use environment variables prefixed with `UZPY_` (e.g., `UZPY_VERBOSE=true`).
- Command-line options override environment/file settings.

**Key Commands (`uzpy-modern --help` for full details):**
- `run`: Analyzes and updates docstrings.
  - Options: `--edit`, `--ref`, `--dry-run`.
- `clean`: Removes "Used in:" sections from docstrings.
  - Options: `--edit`, `--dry-run`.
- `cache <action>`: Manages caches.
  - `clear`: Clears parser and analyzer caches.
  - `stats`: Shows cache statistics.
- `watch`: Monitors files for changes and re-runs analysis (experimental).
  - Options: `--path`.

**Global Options for `uzpy-modern`:**
- `--config / -c FILE_PATH`: Path to a custom `.env` configuration file.
- `--verbose / -v`: Enable verbose DEBUG logging.
- `--log-level LEVEL`: Set logging level (DEBUG, INFO, etc.).


## 📋 Requirements

### System Requirements

- **Python**: 3.10 or higher
- **Operating Systems**: Linux, macOS, Windows

### Dependencies

Core dependencies are automatically installed:

- **tree-sitter** & **tree-sitter-python**: Core parsing.
- **rope**, **jedi**: Traditional analysis.
- **libcst**: Code modification.
- **fire**: Classic CLI.
- **loguru**: Logging.
- **pathspec**: Files discovery.
- **rich**: Used by Typer for enhanced CLI output.
- **New in `uzpy-modern` and core enhancements**:
    - `typer`, `pydantic-settings`: Modern CLI and configuration.
    - `diskcache`: Caching for performance.
    - `multiprocessing-logging`: For parallel analysis logging.
    - `ast-grep-py`: Structural code search for `AstGrepAnalyzer`.
    - `watchdog`: File monitoring for `watch` mode.
- **Note**: `ruff` and `pyright` are utilized as command-line tools and are expected to be in your environment for full `ModernHybridAnalyzer` functionality.

## ⚠️ Current Limitations

1. **Classic CLI (`uzpy`)**: Remains a simple Fire-based interface. For advanced features and configuration, use `uzpy-modern`.
2. **Performance Metrics**: No formal benchmarking data published yet, though significant improvements are expected with caching/parallelism.
3. **Modern Analyzer Precision**: The new analyzers (`RuffAnalyzer`, `PyrightAnalyzer`) rely on CLI tool output, which might have limitations for precise reference finding compared to deep programmatic integration (e.g., Pyright via LSP). `AstGrepAnalyzer` depends on the quality of its patterns.
4. **Watch Mode**: The `watch` mode in `uzpy-modern` is experimental and currently re-analyzes the full configured scope on change.

## 🚧 Future Enhancements

- **Refined Incremental Analysis**: Improve `watch` mode to only re-analyze affected parts of the codebase.
- **LSP Integration**: Deeper integration with Pyright or other language servers for more precise analysis.
- **Advanced Analytics**: Implement planned `duckdb`/`sqlalchemy` based usage analytics.
- **Plugin System**: Develop a plugin system for custom analyzers or docstring formatters.
- **Comprehensive Testing**: Expand test suite to cover all new analyzers and features in depth.

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

