---
# this_file: src_docs/md/index.md
---

# uzpy: Python Code Usage Tracker & Docstring Updater

**uzpy** (`ʌzpi`) is a powerful command-line tool and Python library that analyzes your Python codebase to discover where functions, classes, methods, and modules are used. It then automatically updates their docstrings with a clear "Used in:" section, providing valuable cross-references directly within your code.

## TLDR

uzpy helps you understand and document code relationships by:

1. **Scanning** your Python files to find function/class definitions
2. **Analyzing** where each construct is used throughout your codebase  
3. **Updating** docstrings with "Used in:" sections automatically
4. **Providing** fast, cached analysis with multiple analyzer backends

**Quick start:**
```bash
uv pip install uzpy
uzpy run --edit src/ --ref . --safe
```

## Documentation Overview

This documentation is organized into 9 comprehensive chapters:

### User Guide

| Chapter | Topic | Description |
|---------|-------|-------------|
| **[Getting Started](01-getting-started.md)** | Quick introduction | Learn what uzpy does, see examples, and understand the workflow |
| **[Installation](02-installation.md)** | Setup and requirements | Install uzpy, configure dependencies, and set up your environment |
| **[Command Line Usage](03-command-line-usage.md)** | CLI reference | Complete guide to all commands, options, and usage patterns |
| **[Configuration](04-configuration.md)** | Settings and customization | Configure analyzers, exclusion patterns, caching, and more |

### Developer Guide  

| Chapter | Topic | Description |
|---------|-------|-------------|
| **[Architecture Overview](05-architecture-overview.md)** | System design | Understand uzpy's components, data flow, and design decisions |
| **[API Reference](06-api-reference.md)** | Programmatic usage | Use uzpy as a library, integrate into scripts, and access internals |
| **[Extending uzpy](07-extending-uzpy.md)** | Customization and plugins | Create custom analyzers, modifiers, and extend functionality |

### Advanced Topics

| Chapter | Topic | Description |
|---------|-------|-------------|
| **[Performance Optimization](08-performance-optimization.md)** | Speed and efficiency | Optimize analysis for large codebases, caching strategies, and parallelization |
| **[Troubleshooting](09-troubleshooting.md)** | Common issues and solutions | Debug problems, handle edge cases, and resolve analysis failures |

## Key Features

- **Multiple Analysis Engines**: Choose from Jedi, Rope, Pyright, ast-grep, and hybrid approaches
- **Safe Modifications**: Prevents syntax corruption with the `--safe` modifier  
- **Intelligent Caching**: Fast re-analysis using content-aware disk caching
- **Parallel Processing**: Multi-core analysis for large codebases
- **Flexible Configuration**: Extensive customization via `.uzpy.env` files and environment variables
- **IDE Integration**: Works alongside your existing development tools
- **Watch Mode**: Automatic re-analysis on file changes

## Who Should Use uzpy?

uzpy is designed for Python developers who want to:

- **Improve code navigation** and understand component relationships
- **Maintain living documentation** that evolves with the codebase  
- **Streamline code reviews** by providing usage context
- **Aid refactoring efforts** by identifying all usage sites
- **Reduce cognitive load** when working with complex projects

## Project Information

- **Repository**: [github.com/twardoch/uzpy](https://github.com/twardoch/uzpy)
- **PyPI Package**: [pypi.org/project/uzpy](https://pypi.org/project/uzpy/)
- **License**: MIT
- **Python Version**: 3.10+
- **Author**: Adam Twardoch

## Quick Example

Before uzpy:
```python
def calculate_metrics(data):
    """Calculate various metrics from data."""
    # implementation...
```

After uzpy:
```python
def calculate_metrics(data):
    """
    Calculate various metrics from data.
    
    Used in:
    - src/reports/generator.py
    - src/analysis/dashboard.py  
    - tests/test_metrics.py
    """
    # implementation...
```

Ready to get started? Head to [Getting Started](01-getting-started.md) for your first uzpy workflow!