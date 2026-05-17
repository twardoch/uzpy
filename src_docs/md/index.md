# uzpy: Python Code Usage Tracker & Docstring Updater

**uzpy** (`ʌzpi`) is a command-line tool and Python library that analyzes your codebase to find where functions, classes, methods, and modules are used. It then updates their docstrings with a "Used in:" section, adding cross-references directly into your code.

## TLDR

uzpy does three things:

1. **Scans** Python files for function/class definitions  
2. **Finds** where each construct is used across the codebase  
3. **Updates** docstrings with "Used in:" sections automatically

**Quick start:**
```bash
uv pip install uzpy
uzpy run --edit src/ --ref . --safe
```

## Documentation Overview

This documentation has 9 chapters:

### User Guide

| Chapter | Topic | Description |
|---------|-------|-------------|
| **[Getting Started](01-getting-started.md)** | Quick introduction | What uzpy does, examples, and workflow |
| **[Installation](02-installation.md)** | Setup and requirements | Install uzpy and set up dependencies |
| **[Command Line Usage](03-command-line-usage.md)** | CLI reference | Commands, options, and usage patterns |
| **[Configuration](04-configuration.md)** | Settings and customization | Configure analyzers, exclusions, caching |

### Developer Guide  

| Chapter | Topic | Description |
|---------|-------|-------------|
| **[Architecture Overview](05-architecture-overview.md)** | System design | Components, data flow, design decisions |
| **[API Reference](06-api-reference.md)** | Programmatic usage | Use uzpy as a library or integrate into scripts |
| **[Extending uzpy](07-extending-uzpy.md)** | Customization and plugins | Create custom analyzers and modifiers |

### Advanced Topics

| Chapter | Topic | Description |
|---------|-------|-------------|
| **[Performance Optimization](08-performance-optimization.md)** | Speed and efficiency | Optimize analysis for large codebases |
| **[Troubleshooting](09-troubleshooting.md)** | Common issues and solutions | Debug problems and handle edge cases |

## Key Features

- **Multiple Analysis Engines**: Jedi, Rope, Pyright, ast-grep, hybrid  
- **Safe Modifications**: Prevents syntax corruption with `--safe`  
- **Intelligent Caching**: Fast re-analysis using content-aware cache  
- **Parallel Processing**: Multi-core support for large projects  
- **Flexible Configuration**: Customize via `.uzpy.env` or environment variables  
- **IDE Integration**: Works with existing tools  
- **Watch Mode**: Re-analyze on file changes

## Who Should Use uzpy?

Python developers who want to:

- Navigate code faster  
- Keep documentation in sync  
- Speed up code reviews  
- Refactor safely  
- Work with less mental overhead on complex projects

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

Ready? Start with [Getting Started](01-getting-started.md).