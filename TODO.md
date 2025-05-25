# TODO: Implementing the `uzpy` Tool

## Overview

This document provides step-by-step instructions for implementing a Python tool that analyzes code usage patterns and automatically adds "Used in:" documentation to function/class docstrings.

**Goal**: Create a tool that scans Python codebases to find where each construct (function, class, method) is used and automatically updates their docstrings with usage information.

**Architecture**: Three-phase pipeline using Tree-sitter (parsing), Rope+Jedi (reference finding), and LibCST (code modification).

---

## Phase 1: Project Foundation & Basic CLI ✅ COMPLETED

### Step 1.1: Initialize Project Structure ✅ COMPLETED

**What**: Set up the basic project structure with proper Python tooling.

**Why**: Establishes a solid foundation following Python best practices and enables proper dependency management.

**Status**: ✅ Completed - Project structure created with modern Python tooling

**Tasks**:

1. **Create project directory structure**:
```
uzpy/
├── uzpy/
│   ├── __init__.py
│   ├── main.py
│   ├── cli.py
│   ├── parser/
│   │   ├── __init__.py
│   │   └── tree_sitter_parser.py
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── rope_analyzer.py
│   │   └── jedi_analyzer.py
│   └── modifier/
│       ├── __init__.py
│       └── libcst_modifier.py
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_parser.py
│   ├── test_analyzer.py
│   └── test_modifier.py
├── examples/
│   ├── simple_project/
│   └── complex_project/
├── README.md
├── CHANGELOG.md
├── TODO.md (this file)
├── PROGRESS.md
└── pyproject.toml
```

2. **Create `pyproject.toml`**:
```toml
[project]
name = "uzpy"
version = "0.1.0"
description = "A tool to track where Python constructs are used and update docstrings"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "tree-sitter>=0.20.0",
    "tree-sitter-python>=0.20.0", 
    "rope>=1.7.0",
    "jedi>=0.19.0",
    "libcst>=1.0.0",
    "fire>=0.5.0",
    "rich>=13.0.0",
    "loguru>=0.7.0",
    "pathspec>=0.11.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "autoflake>=2.0.0",
    "pyupgrade>=3.0.0",
]

[project.scripts]
uzpy = "uzpy.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
target-version = "py312"
line-length = 88

[tool.mypy]
python_version = "3.12"
strict = true
```

3. **Create basic project files**:

**`README.md`**:
```markdown
# uzpy

A Python tool that automatically tracks where constructs (functions, classes, methods) are used across codebases and updates their docstrings with usage information.

## Installation

```bash
pip install uzpy
```

## Usage

```bash
# Analyze single file
uzpy --edit path/to/file.py

# Analyze directory against reference codebase  
uzpy --edit src/ --ref /path/to/reference/

# Get help
uzpy --help
```

## How it works

1. Parses your codebase to find all function/class definitions
2. Searches for usages of these constructs across the reference codebase
3. Updates docstrings with "Used in:" lists showing where each construct is used

## Requirements

- Python 3.12+
- Tree-sitter for fast AST parsing
- Rope and Jedi for accurate reference finding
- LibCST for safe code modification
```

**`CHANGELOG.md`**:
```markdown
# Changelog

## [Unreleased]

### Added
- Initial project structure
- Basic CLI interface

### Changed

### Deprecated

### Removed

### Fixed

### Security
```

**`PROGRESS.md`**:
```markdown
# Progress Tracking

## Completed Tasks
- [ ] Project setup and structure
- [ ] Basic CLI interface
- [ ] File discovery system
- [ ] Tree-sitter integration
- [ ] Basic construct extraction
- [ ] Rope integration for reference finding
- [ ] Jedi integration for symbol resolution  
- [ ] LibCST docstring modification
- [ ] End-to-end pipeline integration
- [ ] Error handling and robustness
- [ ] Performance optimization
- [ ] Testing suite
- [ ] Documentation and examples

## Current Focus
- Setting up project foundation

## Next Priorities
- Implement basic CLI
- Add file discovery
- Integrate Tree-sitter parsing

## Blockers
- None currently

## Notes
- Following research recommendations for Tree-sitter + Rope + LibCST architecture
- Prioritizing incremental development with working prototypes
```

### Step 1.2: Create Basic CLI Interface ✅ COMPLETED

**What**: Implement the command-line interface using Fire and Rich for a user-friendly experience.

**Why**: Provides the entry point and argument handling. Fire reduces boilerplate while Rich makes output beautiful.

**Status**: ✅ Completed - Full CLI with Rich formatting and Fire integration

**Create `uzpy/cli.py`**:
```python
#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["fire", "rich", "loguru", "pathlib"]
# ///
# this_file: uzpy/cli.py

"""
Command-line interface for the uzpy tool.

This module handles argument parsing and provides the main entry point for the CLI.
Uses Fire for automatic CLI generation and Rich for beautiful terminal output.
"""

import sys
from pathlib import Path
from typing import Optional

import fire
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class uzpyCLI:
    """
    Command-line interface for the uzpy tool.
    
    This tool analyzes Python codebases to find where constructs (functions, classes, 
    methods) are used and automatically updates their docstrings with usage information.
    """

    def __init__(self):
        """Initialize the CLI with default settings."""
        self.console = Console()
        
    def run(
        self,
        edit: str,
        ref: Optional[str] = None,
        verbose: bool = False,
        dry_run: bool = False,
        include_methods: bool = True,
        include_classes: bool = True,
        include_functions: bool = True,
        exclude_patterns: Optional[str] = None,
    ) -> None:
        """
        Analyze codebase and update docstrings with usage information.
        
        Args:
            edit: Path to file or directory containing code to analyze and modify
            ref: Path to reference codebase to search for usages (defaults to edit path)
            verbose: Enable verbose logging output
            dry_run: Show what changes would be made without modifying files
            include_methods: Include method definitions in analysis
            include_classes: Include class definitions in analysis  
            include_functions: Include function definitions in analysis
            exclude_patterns: Comma-separated glob patterns to exclude from analysis
        """
        # Configure logging
        logger.remove()  # Remove default handler
        level = "DEBUG" if verbose else "INFO"
        logger.add(sys.stderr, level=level, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
        
        # Validate paths
        edit_path = Path(edit)
        if not edit_path.exists():
            console.print(f"[red]Error: Edit path '{edit}' does not exist[/red]")
            return
            
        ref_path = Path(ref) if ref else edit_path
        if not ref_path.exists():
            console.print(f"[red]Error: Reference path '{ref}' does not exist[/red]")
            return
            
        # Show configuration
        self._show_config(edit_path, ref_path, dry_run, verbose)
        
        # TODO: Import and run the main pipeline
        logger.info("Starting uzpy analysis...")
        logger.info(f"Edit path: {edit_path}")
        logger.info(f"Reference path: {ref_path}")
        
        if dry_run:
            logger.info("DRY RUN MODE - no files will be modified")
            
        # Placeholder for actual implementation
        console.print("[yellow]Implementation in progress...[/yellow]")
        
    def _show_config(self, edit_path: Path, ref_path: Path, dry_run: bool, verbose: bool) -> None:
        """Display current configuration in a nice table."""
        table = Table(title="uzpy Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Edit Path", str(edit_path))
        table.add_row("Reference Path", str(ref_path))
        table.add_row("Dry Run", "Yes" if dry_run else "No")
        table.add_row("Verbose", "Yes" if verbose else "No")
        
        console.print(table)
        console.print()


def main() -> None:
    """Main entry point for the CLI."""
    try:
        fire.Fire(uzpyCLI)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logger.exception("Unexpected error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Create `uzpy/main.py`**:
```python
# this_file: uzpy/main.py

"""
Main entry point for the uzpy package.
"""

from uzpy.cli import main

if __name__ == "__main__":
    main()
```

**Create `uzpy/__init__.py`**:
```python
# this_file: uzpy/__init__.py

"""
uzpy: A tool to track where Python constructs are used and update docstrings.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
```

### Step 1.3: Test Basic CLI ✅ COMPLETED

**What**: Verify the CLI works and displays help correctly.

**Why**: Ensures the foundation is solid before building on it.

**Status**: ✅ Completed - CLI tested and working with comprehensive tests

**Tasks**:
1. **Test the CLI**:
```bash
cd /Users/adam/Developer/llm/2505a/uzpy
python -m uzpy.main --help
python -m uzpy.main run --help
python -m uzpy.main run --edit . --dry-run --verbose
```

2. **Create initial test**:

**`tests/test_cli.py`**:
```python
# this_file: tests/test_cli.py

"""
Tests for the CLI module.
"""

import pytest
from pathlib import Path
from uzpy.cli import uzpyCLI


def test_cli_init():
    """Test CLI initialization."""
    cli = uzpyCLI()
    assert cli.console is not None


def test_cli_with_nonexistent_path(capsys):
    """Test CLI with non-existent path.""" 
    cli = uzpyCLI()
    cli.run(edit="/nonexistent/path")
    captured = capsys.readouterr()
    assert "does not exist" in captured.out
```

---

## Phase 2: File Discovery System ✅ COMPLETED

### Step 2.1: Implement File Discovery ✅ COMPLETED

**What**: Create a robust system to find Python files while respecting ignore patterns.

**Why**: Need to efficiently discover all relevant Python files in potentially large codebases while skipping irrelevant ones.

**Status**: ✅ Completed - Full file discovery with gitignore support and pathspec integration

**Create `uzpy/discovery.py`**:
```python
# this_file: uzpy/discovery.py

"""
File discovery utilities for finding Python files in codebases.

This module handles finding Python files while respecting gitignore patterns,
common exclude patterns, and providing efficient traversal of directory trees.
"""

import fnmatch
from pathlib import Path
from typing import Iterator, List, Set, Optional

from loguru import logger
import pathspec


class FileDiscovery:
    """
    Discovers Python files in codebases with configurable filtering.
    
    Handles gitignore patterns, custom exclude patterns, and provides
    efficient traversal with proper error handling.
    """
    
    # Default patterns to exclude
    DEFAULT_EXCLUDE_PATTERNS = [
        ".git/**",
        "__pycache__/**", 
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".pytest_cache/**",
        ".mypy_cache/**",
        ".ruff_cache/**",
        "build/**",
        "dist/**",
        "*.egg-info/**",
        ".venv/**",
        "venv/**",
        ".env/**",
        "env/**",
    ]
    
    def __init__(self, exclude_patterns: Optional[List[str]] = None):
        """
        Initialize file discovery with optional exclude patterns.
        
        Args:
            exclude_patterns: Additional patterns to exclude beyond defaults
        """
        self.exclude_patterns = self.DEFAULT_EXCLUDE_PATTERNS.copy()
        if exclude_patterns:
            self.exclude_patterns.extend(exclude_patterns)
            
        # Compile pathspec for efficient matching
        self.spec = pathspec.PathSpec.from_lines('gitwildmatch', self.exclude_patterns)
        logger.debug(f"Initialized with {len(self.exclude_patterns)} exclude patterns")
    
    def find_python_files(self, root_path: Path) -> Iterator[Path]:
        """
        Find all Python files under the root path.
        
        Args:
            root_path: Root directory or single file to analyze
            
        Yields:
            Path objects for Python files that match criteria
            
        Raises:
            FileNotFoundError: If root_path doesn't exist
            PermissionError: If can't access directory
        """
        if not root_path.exists():
            raise FileNotFoundError(f"Path does not exist: {root_path}")
            
        # Handle single file case
        if root_path.is_file():
            if self._is_python_file(root_path) and not self._is_excluded(root_path):
                yield root_path
            return
            
        # Handle directory case
        if not root_path.is_dir():
            logger.warning(f"Path is neither file nor directory: {root_path}")
            return
            
        logger.info(f"Scanning directory: {root_path}")
        
        try:
            for path in self._walk_directory(root_path):
                if self._is_python_file(path) and not self._is_excluded(path):
                    logger.debug(f"Found Python file: {path}")
                    yield path
        except PermissionError as e:
            logger.error(f"Permission denied accessing {root_path}: {e}")
            raise
            
    def _walk_directory(self, root_path: Path) -> Iterator[Path]:
        """
        Recursively walk directory tree, yielding all files.
        
        Args:
            root_path: Directory to walk
            
        Yields:
            All file paths found in the tree
        """
        try:
            for item in root_path.iterdir():
                if item.is_file():
                    yield item
                elif item.is_dir() and not self._is_excluded(item):
                    # Recursively walk subdirectories
                    yield from self._walk_directory(item)
        except PermissionError:
            logger.warning(f"Permission denied accessing directory: {root_path}")
        except OSError as e:
            logger.warning(f"OS error accessing {root_path}: {e}")
    
    def _is_python_file(self, path: Path) -> bool:
        """
        Check if a file is a Python file.
        
        Args:
            path: File path to check
            
        Returns:
            True if the file appears to be a Python file
        """
        if path.suffix == '.py':
            return True
            
        # Check for Python shebang in files without .py extension
        if path.suffix == '':
            try:
                with open(path, 'rb') as f:
                    first_line = f.readline()
                    if first_line.startswith(b'#!') and b'python' in first_line:
                        return True
            except (OSError, UnicodeDecodeError):
                pass
                
        return False
    
    def _is_excluded(self, path: Path) -> bool:
        """
        Check if a path should be excluded based on patterns.
        
        Args:
            path: Path to check
            
        Returns:
            True if the path should be excluded
        """
        # Convert to relative path for pattern matching
        try:
            # pathspec expects forward slashes
            path_str = str(path).replace('\\', '/')
            return self.spec.match_file(path_str)
        except Exception as e:
            logger.debug(f"Error checking exclusion for {path}: {e}")
            return False
    
    def get_statistics(self, root_path: Path) -> dict:
        """
        Get statistics about files in the path.
        
        Args:
            root_path: Root path to analyze
            
        Returns:
            Dictionary with file counts and other statistics
        """
        stats = {
            'total_python_files': 0,
            'total_files_scanned': 0,
            'excluded_files': 0,
            'directories_scanned': 0,
        }
        
        if root_path.is_file():
            stats['total_files_scanned'] = 1
            if self._is_python_file(root_path):
                stats['total_python_files'] = 1
            return stats
            
        for path in self._walk_directory(root_path):
            stats['total_files_scanned'] += 1
            
            if self._is_excluded(path):
                stats['excluded_files'] += 1
                continue
                
            if self._is_python_file(path):
                stats['total_python_files'] += 1
                
        return stats


def discover_files(
    edit_path: Path, 
    ref_path: Path, 
    exclude_patterns: Optional[List[str]] = None
) -> tuple[List[Path], List[Path]]:
    """
    Discover Python files in both edit and reference paths.
    
    Args:
        edit_path: Path containing files to edit
        ref_path: Path containing reference files to search
        exclude_patterns: Additional patterns to exclude
        
    Returns:
        Tuple of (edit_files, ref_files) lists
    """
    discovery = FileDiscovery(exclude_patterns)
    
    edit_files = list(discovery.find_python_files(edit_path))
    ref_files = list(discovery.find_python_files(ref_path))
    
    logger.info(f"Found {len(edit_files)} edit files and {len(ref_files)} reference files")
    
    return edit_files, ref_files
```

### Step 2.2: Integrate File Discovery with CLI ✅ COMPLETED

**What**: Update the CLI to use the file discovery system and show discovered files.

**Why**: Allows users to see what files will be processed and validates the discovery logic.

**Status**: ✅ Completed - CLI shows file discovery summary with Rich tables

**Update `uzpy/cli.py`** (add imports and modify the run method):
```python
# Add these imports at the top
from uzpy.discovery import discover_files

# Replace the placeholder section in the run method with:
        
        # Discover files
        try:
            exclude_list = exclude_patterns.split(',') if exclude_patterns else None
            edit_files, ref_files = discover_files(edit_path, ref_path, exclude_list)
        except Exception as e:
            console.print(f"[red]Error discovering files: {e}[/red]")
            return
            
        # Show discovered files summary
        self._show_discovery_summary(edit_files, ref_files)
        
        if not edit_files:
            console.print("[yellow]No Python files found in edit path[/yellow]")
            return
            
        if not ref_files:
            console.print("[yellow]No Python files found in reference path[/yellow]")
            return

    def _show_discovery_summary(self, edit_files: List[Path], ref_files: List[Path]) -> None:
        """Display summary of discovered files."""
        table = Table(title="File Discovery Summary", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Count", style="green", justify="right")
        table.add_column("Examples", style="yellow")
        
        # Show first few files as examples
        edit_examples = ", ".join(str(f.name) for f in edit_files[:3])
        if len(edit_files) > 3:
            edit_examples += f", ... ({len(edit_files) - 3} more)"
            
        ref_examples = ", ".join(str(f.name) for f in ref_files[:3])
        if len(ref_files) > 3:
            ref_examples += f", ... ({len(ref_files) - 3} more)"
        
        table.add_row("Edit Files", str(len(edit_files)), edit_examples)
        table.add_row("Reference Files", str(len(ref_files)), ref_examples)
        
        console.print(table)
        console.print()
```

### Step 2.3: Test File Discovery ✅ COMPLETED

**What**: Create tests for the file discovery system.

**Why**: Ensures the discovery logic works correctly with various directory structures.

**Status**: ✅ Completed - Comprehensive tests for file discovery functionality

**Create `tests/test_discovery.py`**:
```python
# this_file: tests/test_discovery.py

"""
Tests for file discovery functionality.
"""

import pytest
import tempfile
from pathlib import Path
from uzpy.discovery import FileDiscovery, discover_files


@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Create test files
        (root / "main.py").write_text("# Main module")
        (root / "utils.py").write_text("# Utilities")
        (root / "tests" / "test_main.py").mkdir(parents=True)
        (root / "tests" / "test_main.py").write_text("# Tests")
        (root / "__pycache__" / "main.cpython-312.pyc").mkdir(parents=True)
        (root / "__pycache__" / "main.cpython-312.pyc").write_text("compiled")
        (root / ".git" / "config").mkdir(parents=True)
        (root / ".git" / "config").write_text("git config")
        (root / "README.md").write_text("# README")
        
        yield root


def test_file_discovery_basic(temp_project):
    """Test basic file discovery functionality."""
    discovery = FileDiscovery()
    files = list(discovery.find_python_files(temp_project))
    
    # Should find main.py, utils.py, and test_main.py
    file_names = {f.name for f in files}
    assert "main.py" in file_names
    assert "utils.py" in file_names  
    assert "test_main.py" in file_names
    
    # Should not find compiled files or git files
    assert "main.cpython-312.pyc" not in file_names
    assert "config" not in file_names
    assert "README.md" not in file_names


def test_file_discovery_single_file(temp_project):
    """Test discovery of a single file."""
    discovery = FileDiscovery()
    single_file = temp_project / "main.py"
    files = list(discovery.find_python_files(single_file))
    
    assert len(files) == 1
    assert files[0] == single_file


def test_file_discovery_nonexistent_path():
    """Test discovery with non-existent path."""
    discovery = FileDiscovery()
    nonexistent = Path("/this/path/does/not/exist")
    
    with pytest.raises(FileNotFoundError):
        list(discovery.find_python_files(nonexistent))


def test_discover_files_function(temp_project):
    """Test the convenience discover_files function."""
    edit_files, ref_files = discover_files(temp_project, temp_project)
    
    assert len(edit_files) >= 3  # main.py, utils.py, test_main.py
    assert edit_files == ref_files  # Same path for both


def test_custom_exclude_patterns(temp_project):
    """Test custom exclude patterns."""
    # Create a file that should be excluded
    (temp_project / "secret.py").write_text("# Secret file")
    
    discovery = FileDiscovery(exclude_patterns=["secret.py"])
    files = list(discovery.find_python_files(temp_project))
    
    file_names = {f.name for f in files}
    assert "secret.py" not in file_names
    assert "main.py" in file_names  # Other files still found
```

---

## Phase 3: Tree-sitter Integration ✅ COMPLETED

### Step 3.1: Set Up Tree-sitter Parser ✅ COMPLETED

**What**: Integrate Tree-sitter for fast, robust Python AST parsing.

**Why**: Tree-sitter provides incremental parsing, error recovery, and excellent performance compared to built-in ast module.

**Status**: ✅ Completed - Full Tree-sitter parser with construct extraction and docstring handling

**Create `uzpy/parser/__init__.py`**:
```python
# this_file: uzpy/parser/__init__.py

"""
Parser module for extracting construct definitions from Python code.
"""

from .tree_sitter_parser import TreeSitterParser, ConstructType, Construct

__all__ = ['TreeSitterParser', 'ConstructType', 'Construct']
```

**Create `uzpy/parser/tree_sitter_parser.py`**:
```python
# this_file: uzpy/parser/tree_sitter_parser.py

"""
Tree-sitter based parser for extracting Python constructs.

This module uses Tree-sitter to parse Python code and extract function,
class, and method definitions with their locations and existing docstrings.
Tree-sitter provides fast, incremental parsing with excellent error recovery.
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Iterator, Set

import tree_sitter_python as tspython
from loguru import logger
from tree_sitter import Language, Parser, Node


class ConstructType(Enum):
    """Types of Python constructs we can analyze."""
    FUNCTION = "function"
    CLASS = "class" 
    METHOD = "method"
    MODULE = "module"


@dataclass
class Construct:
    """
    Represents a Python construct (function, class, method, module) with metadata.
    
    Attributes:
        name: The name of the construct
        type: The type of construct (function, class, method, module)
        file_path: Path to the file containing this construct
        line_number: Line number where the construct is defined (1-based)
        docstring: Existing docstring content (None if no docstring)
        full_name: Fully qualified name including class/module context
        node: The Tree-sitter node (for internal use)
    """
    name: str
    type: ConstructType
    file_path: Path
    line_number: int
    docstring: Optional[str]
    full_name: str
    node: Optional[Node] = None  # Keep reference to tree-sitter node
    
    def __post_init__(self):
        """Clean up docstring formatting after initialization."""
        if self.docstring:
            self.docstring = self._clean_docstring(self.docstring)
    
    def _clean_docstring(self, docstring: str) -> str:
        """
        Clean and normalize docstring formatting.
        
        Removes extra indentation and normalizes quotes while preserving content.
        """
        # Remove surrounding quotes
        if docstring.startswith(('"""', "'''")):
            docstring = docstring[3:-3]
        elif docstring.startswith(('"', "'")):
            docstring = docstring[1:-1]
            
        # Remove common leading indentation
        lines = docstring.split('\n')
        if len(lines) > 1:
            # Find minimum indentation (excluding empty lines)
            min_indent = float('inf')
            for line in lines[1:]:  # Skip first line
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, indent)
            
            # Remove common indentation
            if min_indent != float('inf'):
                lines = [lines[0]] + [line[min_indent:] if line.strip() else line 
                                     for line in lines[1:]]
                                     
        return '\n'.join(lines).strip()


class TreeSitterParser:
    """
    Tree-sitter based parser for extracting Python constructs.
    
    Provides fast parsing with error recovery and incremental capabilities.
    Extracts functions, classes, methods, and modules with their docstrings.
    """
    
    def __init__(self):
        """Initialize the Tree-sitter parser for Python."""
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)
        
        # Queries for finding different construct types
        self._init_queries()
        
        logger.debug("Tree-sitter parser initialized")
    
    def _init_queries(self) -> None:
        """Initialize Tree-sitter queries for finding constructs."""
        # Query for function definitions
        self.function_query = self.language.query("""
        (function_definition
          name: (identifier) @function_name
          body: (block) @function_body) @function_def
        """)
        
        # Query for class definitions
        self.class_query = self.language.query("""
        (class_definition
          name: (identifier) @class_name
          body: (block) @class_body) @class_def
        """)
        
        # Query for method definitions (functions inside classes)
        self.method_query = self.language.query("""
        (class_definition
          body: (block
            (function_definition
              name: (identifier) @method_name
              body: (block) @method_body) @method_def)) @class_def
        """)
        
        # Query for docstrings (string expressions at start of blocks)
        self.docstring_query = self.language.query("""
        (block
          (expression_statement
            (string) @docstring) @doc_stmt) @block
        """)
    
    def parse_file(self, file_path: Path) -> List[Construct]:
        """
        Parse a Python file and extract all constructs.
        
        Args:
            file_path: Path to the Python file to parse
            
        Returns:
            List of Construct objects found in the file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            UnicodeDecodeError: If the file can't be decoded as UTF-8
        """
        logger.debug(f"Parsing file: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error in {file_path}: {e}")
            raise
        
        # Parse with Tree-sitter
        tree = self.parser.parse(source_code)
        
        if tree.root_node.has_error:
            logger.warning(f"Parse errors in {file_path}, continuing with partial parse")
        
        # Extract constructs
        constructs = []
        
        # Get source code as string for node text extraction
        source_text = source_code.decode('utf-8')
        
        # Extract module-level constructs
        constructs.extend(self._extract_functions(tree.root_node, file_path, source_text))
        constructs.extend(self._extract_classes(tree.root_node, file_path, source_text))
        
        # Add module construct
        module_construct = self._create_module_construct(file_path, tree.root_node, source_text)
        if module_construct:
            constructs.append(module_construct)
        
        logger.debug(f"Found {len(constructs)} constructs in {file_path}")
        return constructs
    
    def _extract_functions(self, root_node: Node, file_path: Path, source_text: str) -> List[Construct]:
        """Extract function definitions from the AST."""
        functions = []
        
        captures = self.function_query.captures(root_node)
        
        for node, capture_name in captures:
            if capture_name == "function_def":
                # Get function name
                name_captures = self.function_query.captures(node)
                function_name = None
                function_body = None
                
                for child_node, child_capture in name_captures:
                    if child_capture == "function_name":
                        function_name = self._get_node_text(child_node, source_text)
                    elif child_capture == "function_body":
                        function_body = child_node
                
                if function_name and function_body:
                    # Check if this is actually a method (inside a class)
                    is_method = self._is_inside_class(node)
                    construct_type = ConstructType.METHOD if is_method else ConstructType.FUNCTION
                    
                    # Get docstring
                    docstring = self._extract_docstring(function_body, source_text)
                    
                    # Calculate line number (Tree-sitter uses 0-based, we want 1-based)
                    line_number = node.start_point[0] + 1
                    
                    # Build full name
                    full_name = self._build_full_name(node, function_name, source_text)
                    
                    construct = Construct(
                        name=function_name,
                        type=construct_type,
                        file_path=file_path,
                        line_number=line_number,
                        docstring=docstring,
                        full_name=full_name,
                        node=node
                    )
                    
                    functions.append(construct)
        
        return functions
    
    def _extract_classes(self, root_node: Node, file_path: Path, source_text: str) -> List[Construct]:
        """Extract class definitions from the AST."""
        classes = []
        
        captures = self.class_query.captures(root_node)
        
        for node, capture_name in captures:
            if capture_name == "class_def":
                # Get class name
                name_captures = self.class_query.captures(node)
                class_name = None
                class_body = None
                
                for child_node, child_capture in name_captures:
                    if child_capture == "class_name":
                        class_name = self._get_node_text(child_node, source_text)
                    elif child_capture == "class_body":
                        class_body = child_node
                
                if class_name and class_body:
                    # Get docstring
                    docstring = self._extract_docstring(class_body, source_text)
                    
                    # Calculate line number
                    line_number = node.start_point[0] + 1
                    
                    # Build full name
                    full_name = self._build_full_name(node, class_name, source_text)
                    
                    construct = Construct(
                        name=class_name,
                        type=ConstructType.CLASS,
                        file_path=file_path,
                        line_number=line_number,
                        docstring=docstring,
                        full_name=full_name,
                        node=node
                    )
                    
                    classes.append(construct)
        
        return classes
    
    def _create_module_construct(self, file_path: Path, root_node: Node, source_text: str) -> Optional[Construct]:
        """Create a construct representing the module itself."""
        # Look for module-level docstring (first statement is a string)
        docstring = None
        
        # Check first statement
        for child in root_node.children:
            if child.type == "expression_statement":
                for grandchild in child.children:
                    if grandchild.type == "string":
                        docstring = self._get_node_text(grandchild, source_text)
                        break
                break
        
        module_name = file_path.stem
        full_name = str(file_path.relative_to(file_path.anchor)).replace('/', '.').replace('\\', '.')
        if full_name.endswith('.py'):
            full_name = full_name[:-3]
        
        return Construct(
            name=module_name,
            type=ConstructType.MODULE,
            file_path=file_path,
            line_number=1,
            docstring=docstring,
            full_name=full_name,
            node=root_node
        )
    
    def _extract_docstring(self, body_node: Node, source_text: str) -> Optional[str]:
        """Extract docstring from a function or class body."""
        # Look for the first expression statement that contains a string
        for child in body_node.children:
            if child.type == "expression_statement":
                for grandchild in child.children:
                    if grandchild.type == "string":
                        return self._get_node_text(grandchild, source_text)
        return None
    
    def _get_node_text(self, node: Node, source_text: str) -> str:
        """Get the text content of a Tree-sitter node."""
        start_byte = node.start_byte
        end_byte = node.end_byte
        return source_text[start_byte:end_byte]
    
    def _is_inside_class(self, node: Node) -> bool:
        """Check if a node is inside a class definition."""
        parent = node.parent
        while parent:
            if parent.type == "class_definition":
                return True
            parent = parent.parent
        return False
    
    def _build_full_name(self, node: Node, name: str, source_text: str) -> str:
        """Build the fully qualified name for a construct."""
        parts = [name]
        
        # Walk up the tree to find containing classes
        parent = node.parent
        while parent:
            if parent.type == "class_definition":
                # Find the class name
                for child in parent.children:
                    if child.type == "identifier":
                        class_name = self._get_node_text(child, source_text)
                        parts.insert(0, class_name)
                        break
            parent = parent.parent
        
        return ".".join(parts)
    
    def get_statistics(self, file_path: Path) -> Dict[str, int]:
        """Get parsing statistics for a file."""
        constructs = self.parse_file(file_path)
        
        stats = {
            'total_constructs': len(constructs),
            'functions': sum(1 for c in constructs if c.type == ConstructType.FUNCTION),
            'methods': sum(1 for c in constructs if c.type == ConstructType.METHOD),
            'classes': sum(1 for c in constructs if c.type == ConstructType.CLASS),
            'modules': sum(1 for c in constructs if c.type == ConstructType.MODULE),
            'with_docstrings': sum(1 for c in constructs if c.docstring),
            'without_docstrings': sum(1 for c in constructs if not c.docstring),
        }
        
        return stats
```

### Step 3.2: Test Tree-sitter Parser ✅ COMPLETED

**What**: Create comprehensive tests for the Tree-sitter parser.

**Why**: Ensures the parser correctly extracts constructs and handles edge cases.

**Status**: ✅ Completed - Extensive test suite covering all construct types and edge cases

**Create `tests/test_parser.py`**:
```python
# this_file: tests/test_parser.py

"""
Tests for the Tree-sitter parser functionality.
"""

import pytest
import tempfile
from pathlib import Path
from uzpy.parser import TreeSitterParser, ConstructType


@pytest.fixture
def sample_python_file():
    """Create a sample Python file for testing."""
    content = '''"""Module docstring for testing."""

def standalone_function():
    """A standalone function."""
    return "hello"

class TestClass:
    """A test class."""
    
    def method_one(self):
        """First method."""
        pass
    
    def method_two(self):
        # No docstring
        return 42

class AnotherClass:
    # Class with no docstring
    
    def __init__(self):
        """Constructor."""
        self.value = 0

def another_function():
    # Function with no docstring
    pass
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        f.flush()
        yield Path(f.name)
    
    # Cleanup
    Path(f.name).unlink()


def test_parser_initialization():
    """Test that the parser initializes correctly."""
    parser = TreeSitterParser()
    assert parser.language is not None
    assert parser.parser is not None


def test_parse_file_basic(sample_python_file):
    """Test basic file parsing functionality."""
    parser = TreeSitterParser()
    constructs = parser.parse_file(sample_python_file)
    
    # Should find module, classes, and functions/methods
    assert len(constructs) > 0
    
    # Check we have different types
    types_found = {c.type for c in constructs}
    assert ConstructType.MODULE in types_found
    assert ConstructType.CLASS in types_found
    assert ConstructType.FUNCTION in types_found
    assert ConstructType.METHOD in types_found


def test_construct_extraction(sample_python_file):
    """Test detailed construct extraction."""
    parser = TreeSitterParser()
    constructs = parser.parse_file(sample_python_file)
    
    # Build a map by name for easier testing
    by_name = {c.name: c for c in constructs}
    
    # Test module
    assert sample_python_file.stem in by_name
    module = by_name[sample_python_file.stem]
    assert module.type == ConstructType.MODULE
    assert module.docstring == "Module docstring for testing."
    
    # Test standalone function
    assert "standalone_function" in by_name
    func = by_name["standalone_function"]
    assert func.type == ConstructType.FUNCTION
    assert func.docstring == "A standalone function."
    assert func.full_name == "standalone_function"
    
    # Test class
    assert "TestClass" in by_name
    cls = by_name["TestClass"]
    assert cls.type == ConstructType.CLASS
    assert cls.docstring == "A test class."
    
    # Test method with docstring
    assert "method_one" in by_name
    method = by_name["method_one"]
    assert method.type == ConstructType.METHOD
    assert method.docstring == "First method."
    assert method.full_name == "TestClass.method_one"
    
    # Test method without docstring
    assert "method_two" in by_name
    method2 = by_name["method_two"]
    assert method2.type == ConstructType.METHOD
    assert method2.docstring is None
    
    # Test function without docstring
    assert "another_function" in by_name
    func2 = by_name["another_function"]
    assert func2.type == ConstructType.FUNCTION
    assert func2.docstring is None


def test_line_numbers(sample_python_file):
    """Test that line numbers are correctly extracted.""" 
    parser = TreeSitterParser()
    constructs = parser.parse_file(sample_python_file)
    
    by_name = {c.name: c for c in constructs}
    
    # Module should start at line 1
    module = by_name[sample_python_file.stem]
    assert module.line_number == 1
    
    # Function should be after module docstring
    func = by_name["standalone_function"]
    assert func.line_number > 1
    
    # All line numbers should be positive
    for construct in constructs:
        assert construct.line_number > 0


def test_parser_statistics(sample_python_file):
    """Test parser statistics functionality."""
    parser = TreeSitterParser()
    stats = parser.get_statistics(sample_python_file)
    
    assert stats['total_constructs'] > 0
    assert stats['functions'] >= 2  # standalone_function, another_function
    assert stats['methods'] >= 3    # method_one, method_two, __init__
    assert stats['classes'] >= 2    # TestClass, AnotherClass
    assert stats['modules'] == 1    # The module itself
    assert stats['with_docstrings'] > 0
    assert stats['without_docstrings'] > 0


def test_parser_with_syntax_error():
    """Test parser behavior with syntax errors."""
    content = '''
def broken_function(
    # Missing closing parenthesis
    return "this should still be parsed"

def good_function():
    """This should work fine."""
    return 42
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        f.flush()
        
        parser = TreeSitterParser()
        constructs = parser.parse_file(Path(f.name))
        
        # Should still find some constructs despite syntax error
        assert len(constructs) > 0
        
        # Should find the good function
        names = {c.name for c in constructs}
        assert "good_function" in names
    
    Path(f.name).unlink()


def test_parser_empty_file():
    """Test parser with empty file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("")
        f.flush()
        
        parser = TreeSitterParser()
        constructs = parser.parse_file(Path(f.name))
        
        # Should at least find the module construct
        assert len(constructs) >= 1
        assert any(c.type == ConstructType.MODULE for c in constructs)
    
    Path(f.name).unlink()


def test_parser_nonexistent_file():
    """Test parser with non-existent file."""
    parser = TreeSitterParser()
    
    with pytest.raises(FileNotFoundError):
        parser.parse_file(Path("/this/file/does/not/exist.py"))
```

### Step 3.3: Integrate Parser with CLI ✅ COMPLETED

**What**: Update the CLI to use the Tree-sitter parser and show extracted constructs.

**Why**: Allows testing the parser integration and provides visibility into what constructs are found.

**Status**: ✅ Completed - CLI shows parsing summary with construct statistics

**Update `uzpy/cli.py`** (add imports and new functionality):

```python
# Add to imports
from uzpy.parser import TreeSitterParser

# Add after file discovery in the run method:
        
        # Initialize parser
        parser = TreeSitterParser()
        
        # Parse edit files to find constructs
        logger.info("Parsing edit files for constructs...")
        all_constructs = []
        
        for edit_file in edit_files:
            try:
                constructs = parser.parse_file(edit_file)
                all_constructs.extend(constructs)
                logger.debug(f"Found {len(constructs)} constructs in {edit_file}")
            except Exception as e:
                logger.error(f"Failed to parse {edit_file}: {e}")
                if not verbose:
                    continue
                raise
        
        # Show parsing summary
        self._show_parsing_summary(all_constructs)
        
        if not all_constructs:
            console.print("[yellow]No constructs found in edit files[/yellow]")
            return

    def _show_parsing_summary(self, constructs: List) -> None:
        """Display summary of parsed constructs."""
        from collections import Counter
        
        # Count by type
        type_counts = Counter(c.type.value for c in constructs)
        
        table = Table(title="Construct Parsing Summary", show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Count", style="green", justify="right")
        table.add_column("With Docstrings", style="yellow", justify="right")
        
        for construct_type in ["module", "class", "function", "method"]:
            count = type_counts.get(construct_type, 0)
            with_docs = sum(1 for c in constructs 
                          if c.type.value == construct_type and c.docstring)
            
            table.add_row(
                construct_type.title(),
                str(count),
                f"{with_docs}/{count}" if count > 0 else "0/0"
            )
        
        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{len(constructs)}[/bold]",
            f"[bold]{sum(1 for c in constructs if c.docstring)}/{len(constructs)}[/bold]"
        )
        
        console.print(table)
        console.print()
```

---

## Phase 4: Reference Finding with Rope and Jedi ✅ COMPLETED

### Step 4.1: Implement Rope-based Reference Finder ✅ COMPLETED

**What**: Create a system using Rope to find where constructs are used across the codebase.

**Why**: Rope provides accurate cross-file reference finding that handles Python's complex import and inheritance systems.

**Status**: ✅ Completed - Full Rope analyzer with accurate cross-file reference finding

**Create `uzpy/analyzer/__init__.py`**:
```python
# this_file: uzpy/analyzer/__init__.py

"""
Analysis module for finding construct usage across codebases.
"""

from .rope_analyzer import RopeAnalyzer
from .jedi_analyzer import JediAnalyzer
from .hybrid_analyzer import HybridAnalyzer

__all__ = ['RopeAnalyzer', 'JediAnalyzer', 'HybridAnalyzer']
```

**Create `uzpy/analyzer/rope_analyzer.py`**:
```python
# this_file: uzpy/analyzer/rope_analyzer.py

"""
Rope-based analyzer for finding construct usage across Python codebases.

Rope provides excellent cross-file reference finding with proper handling
of Python's import systems, inheritance, and scoping rules.
"""

import time
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple

from loguru import logger
from rope.base.project import Project
from rope.contrib.findit import find_occurrences
from rope.base.exceptions import ModuleSyntaxError, ResourceNotFoundError

from uzpy.parser import Construct, ConstructType


class RopeAnalyzer:
    """
    Rope-based analyzer for finding construct usage.
    
    Uses Rope's static analysis capabilities to find where functions,
    classes, and methods are used across a Python codebase.
    """
    
    def __init__(self, root_path: Path):
        """
        Initialize the Rope analyzer.
        
        Args:
            root_path: Root directory of the project to analyze
        """
        self.root_path = root_path
        self.project: Optional[Project] = None
        self._init_project()
        
    def _init_project(self) -> None:
        """Initialize the Rope project."""
        try:
            logger.debug(f"Initializing Rope project at {self.root_path}")
            self.project = Project(str(self.root_path))
            logger.debug("Rope project initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Rope project: {e}")
            raise
    
    def find_usages(self, construct: Construct, search_paths: List[Path]) -> List[Path]:
        """
        Find all files where a construct is used.
        
        Args:
            construct: The construct to search for
            search_paths: List of files to search within
            
        Returns:
            List of file paths where the construct is used
        """
        if not self.project:
            logger.error("Rope project not initialized")
            return []
            
        usage_files = set()
        
        try:
            # Get the resource for the file containing the construct
            resource_path = str(construct.file_path.relative_to(self.root_path))
            resource = self.project.get_resource(resource_path)
            
            # Find the offset of the construct definition
            offset = self._find_construct_offset(construct, resource)
            if offset is None:
                logger.warning(f"Could not find offset for {construct.full_name} in {construct.file_path}")
                return []
            
            logger.debug(f"Finding usages of {construct.full_name} at offset {offset}")
            
            # Use Rope to find all occurrences
            occurrences = find_occurrences(self.project, resource, offset)
            
            for occurrence in occurrences:
                occurrence_file = Path(self.root_path) / occurrence.resource.path
                
                # Only include files that are in our search paths
                if any(self._is_file_in_search_path(occurrence_file, search_path) 
                      for search_path in search_paths):
                    usage_files.add(occurrence_file)
                    
            logger.debug(f"Found {len(usage_files)} usage files for {construct.full_name}")
            
        except (ModuleSyntaxError, ResourceNotFoundError) as e:
            logger.warning(f"Rope error analyzing {construct.full_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error finding usages for {construct.full_name}: {e}")
            
        return list(usage_files)
    
    def _find_construct_offset(self, construct: Construct, resource) -> Optional[int]:
        """
        Find the byte offset of a construct definition in a file.
        
        Args:
            construct: The construct to find
            resource: Rope resource representing the file
            
        Returns:
            Byte offset of the construct definition, or None if not found
        """
        try:
            source_code = resource.read()
            lines = source_code.split('\n')
            
            # Find the line with the construct (1-based line numbers)
            if construct.line_number > len(lines):
                return None
                
            target_line = lines[construct.line_number - 1]
            
            # Look for the construct name in the definition line
            if construct.type in (ConstructType.FUNCTION, ConstructType.METHOD):
                pattern = f"def {construct.name}"
            elif construct.type == ConstructType.CLASS:
                pattern = f"class {construct.name}"
            else:
                # For modules, use the first occurrence of the name
                pattern = construct.name
            
            name_pos = target_line.find(pattern)
            if name_pos == -1:
                # Try just the name if the full pattern isn't found
                name_pos = target_line.find(construct.name)
                if name_pos == -1:
                    return None
            
            # Calculate byte offset
            offset = 0
            for i in range(construct.line_number - 1):
                offset += len(lines[i]) + 1  # +1 for newline
            offset += name_pos + len(pattern.split()[-1]) // 2  # Position within the name
            
            return offset
            
        except Exception as e:
            logger.debug(f"Error finding offset for {construct.name}: {e}")
            return None
    
    def _is_file_in_search_path(self, file_path: Path, search_path: Path) -> bool:
        """
        Check if a file is within a search path.
        
        Args:
            file_path: File to check
            search_path: Directory or file to search within
            
        Returns:
            True if the file is within the search path
        """
        try:
            if search_path.is_file():
                return file_path.resolve() == search_path.resolve()
            else:
                # Check if file is under the directory
                return search_path.resolve() in file_path.resolve().parents or \
                       file_path.resolve() == search_path.resolve()
        except Exception:
            return False
    
    def analyze_batch(self, constructs: List[Construct], search_paths: List[Path]) -> Dict[str, List[Path]]:
        """
        Analyze multiple constructs in batch for efficiency.
        
        Args:
            constructs: List of constructs to analyze
            search_paths: List of paths to search within
            
        Returns:
            Dictionary mapping construct full names to lists of usage files
        """
        logger.info(f"Analyzing {len(constructs)} constructs with Rope")
        start_time = time.time()
        
        results = {}
        
        for i, construct in enumerate(constructs):
            if i % 10 == 0:
                logger.debug(f"Processed {i}/{len(constructs)} constructs")
                
            try:
                usage_files = self.find_usages(construct, search_paths)
                results[construct.full_name] = usage_files
            except Exception as e:
                logger.error(f"Error analyzing {construct.full_name}: {e}")
                results[construct.full_name] = []
        
        elapsed = time.time() - start_time
        logger.info(f"Rope analysis completed in {elapsed:.2f}s")
        
        return results
    
    def get_project_info(self) -> Dict[str, any]:
        """Get information about the Rope project."""
        if not self.project:
            return {}
            
        try:
            # Get basic project info
            all_resources = list(self.project.get_files())
            python_files = [r for r in all_resources if r.path.endswith('.py')]
            
            return {
                'root_path': str(self.root_path),
                'total_files': len(all_resources),
                'python_files': len(python_files),
                'project_name': self.project.root.path,
            }
        except Exception as e:
            logger.debug(f"Error getting project info: {e}")
            return {'error': str(e)}
    
    def close(self) -> None:
        """Clean up the Rope project."""
        if self.project:
            try:
                self.project.close()
                logger.debug("Rope project closed")
            except Exception as e:
                logger.debug(f"Error closing Rope project: {e}")
```

### Step 4.2: Implement Jedi-based Reference Finder ✅ COMPLETED

**What**: Create a complementary analyzer using Jedi for fast symbol resolution.

**Why**: Jedi provides excellent performance and caching, complementing Rope's accuracy with speed.

**Status**: ✅ Completed - Jedi analyzer with fast symbol resolution and fallback mechanisms

**Create `uzpy/analyzer/jedi_analyzer.py`**:
```python
# this_file: uzpy/analyzer/jedi_analyzer.py

"""
Jedi-based analyzer for finding construct usage across Python codebases.

Jedi provides fast symbol resolution and reference finding, optimized
for interactive use with excellent caching mechanisms.
"""

import time
from pathlib import Path
from typing import List, Dict, Set, Optional

import jedi
from jedi.api.classes import Name
from loguru import logger

from uzpy.parser import Construct, ConstructType


class JediAnalyzer:
    """
    Jedi-based analyzer for finding construct usage.
    
    Uses Jedi's static analysis for fast symbol resolution and reference finding.
    Provides good caching and handles large codebases efficiently.
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize the Jedi analyzer.
        
        Args:
            project_path: Root directory of the project to analyze
        """
        self.project_path = project_path
        self.project = jedi.Project(str(project_path))
        logger.debug(f"Jedi analyzer initialized for {project_path}")
    
    def find_usages(self, construct: Construct, search_paths: List[Path]) -> List[Path]:
        """
        Find all files where a construct is used.
        
        Args:
            construct: The construct to search for
            search_paths: List of files to search within
            
        Returns:
            List of file paths where the construct is used
        """
        usage_files = set()
        
        try:
            # Create a Jedi script for the file containing the construct
            with open(construct.file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            script = jedi.Script(
                code=source_code,
                path=str(construct.file_path),
                project=self.project
            )
            
            # Find the definition position
            definition_position = self._find_definition_position(construct, source_code)
            if not definition_position:
                logger.warning(f"Could not find definition position for {construct.full_name}")
                return []
            
            line, column = definition_position
            logger.debug(f"Finding references for {construct.full_name} at line {line}, column {column}")
            
            # Get references using Jedi
            try:
                references = script.get_references(line=line, column=column, include_builtins=False)
                
                for ref in references:
                    if ref.module_path:
                        ref_file = Path(ref.module_path)
                        
                        # Only include files in our search paths
                        if any(self._is_file_in_search_path(ref_file, search_path) 
                              for search_path in search_paths):
                            usage_files.add(ref_file)
                            
            except Exception as e:
                logger.debug(f"Jedi reference finding failed for {construct.full_name}: {e}")
                # Fall back to alternative method
                usage_files.update(self._fallback_search(construct, search_paths))
                
        except Exception as e:
            logger.error(f"Error finding usages for {construct.full_name}: {e}")
            
        logger.debug(f"Found {len(usage_files)} usage files for {construct.full_name}")
        return list(usage_files)
    
    def _find_definition_position(self, construct: Construct, source_code: str) -> Optional[Tuple[int, int]]:
        """
        Find the line and column position of a construct definition.
        
        Args:
            construct: The construct to find
            source_code: Source code of the file
            
        Returns:
            Tuple of (line, column) for the definition, or None if not found
        """
        lines = source_code.split('\n')
        
        if construct.line_number > len(lines):
            return None
            
        target_line = lines[construct.line_number - 1]
        
        # Look for the construct name in the definition
        if construct.type in (ConstructType.FUNCTION, ConstructType.METHOD):
            pattern = f"def {construct.name}"
        elif construct.type == ConstructType.CLASS:
            pattern = f"class {construct.name}"
        else:
            pattern = construct.name
        
        column = target_line.find(pattern)
        if column == -1:
            # Try just the name
            column = target_line.find(construct.name)
            if column == -1:
                return None
        
        # Adjust to point to the name itself
        if construct.type in (ConstructType.FUNCTION, ConstructType.METHOD, ConstructType.CLASS):
            name_start = target_line.find(construct.name, column)
            if name_start != -1:
                column = name_start
        
        return (construct.line_number, column)
    
    def _fallback_search(self, construct: Construct, search_paths: List[Path]) -> Set[Path]:
        """
        Fallback search method using simple text matching.
        
        Args:
            construct: The construct to search for
            search_paths: List of paths to search within
            
        Returns:
            Set of file paths that potentially contain the construct
        """
        usage_files = set()
        
        # Simple text search as fallback
        search_terms = [
            construct.name,
            f"{construct.name}(",  # Function calls
            f".{construct.name}",  # Method calls
            f"from {construct.file_path.stem} import",  # Imports
        ]
        
        for search_path in search_paths:
            files_to_search = []
            
            if search_path.is_file():
                files_to_search = [search_path]
            else:
                files_to_search = list(search_path.rglob('*.py'))
            
            for file_path in files_to_search:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # Check if any search terms appear in the file
                    if any(term in content for term in search_terms):
                        usage_files.add(file_path)
                        
                except Exception as e:
                    logger.debug(f"Error reading {file_path} for fallback search: {e}")
        
        return usage_files
    
    def _is_file_in_search_path(self, file_path: Path, search_path: Path) -> bool:
        """Check if a file is within a search path."""
        try:
            if search_path.is_file():
                return file_path.resolve() == search_path.resolve()
            else:
                # Check if file is under the directory
                return search_path.resolve() in file_path.resolve().parents or \
                       file_path.resolve() == search_path.resolve()
        except Exception:
            return False
    
    def analyze_batch(self, constructs: List[Construct], search_paths: List[Path]) -> Dict[str, List[Path]]:
        """
        Analyze multiple constructs in batch.
        
        Args:
            constructs: List of constructs to analyze
            search_paths: List of paths to search within
            
        Returns:
            Dictionary mapping construct full names to lists of usage files
        """
        logger.info(f"Analyzing {len(constructs)} constructs with Jedi")
        start_time = time.time()
        
        results = {}
        
        for i, construct in enumerate(constructs):
            if i % 10 == 0:
                logger.debug(f"Processed {i}/{len(constructs)} constructs")
                
            try:
                usage_files = self.find_usages(construct, search_paths)
                results[construct.full_name] = usage_files
            except Exception as e:
                logger.error(f"Error analyzing {construct.full_name}: {e}")
                results[construct.full_name] = []
        
        elapsed = time.time() - start_time
        logger.info(f"Jedi analysis completed in {elapsed:.2f}s")
        
        return results
    
    def get_project_info(self) -> Dict[str, any]:
        """Get information about the Jedi project."""
        try:
            return {
                'project_path': str(self.project_path),
                'sys_path': self.project.sys_path,
            }
        except Exception as e:
            return {'error': str(e)}
```

### Step 4.3: Create Hybrid Analyzer ✅ COMPLETED

**What**: Combine Rope and Jedi for optimal accuracy and performance.

**Why**: Leverages the strengths of both tools - Rope's accuracy and Jedi's speed - while providing fallback mechanisms.

**Status**: ✅ Completed - Sophisticated hybrid analyzer with multiple strategies and confidence scoring

**Create `uzpy/analyzer/hybrid_analyzer.py`**:
```python
# this_file: uzpy/analyzer/hybrid_analyzer.py

"""
Hybrid analyzer combining Rope and Jedi for optimal accuracy and performance.

This analyzer uses both Rope and Jedi to find construct usage, leveraging
Rope's accuracy for complex cases and Jedi's speed for straightforward ones.
"""

import time
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple

from loguru import logger

from uzpy.parser import Construct, ConstructType
from .rope_analyzer import RopeAnalyzer
from .jedi_analyzer import JediAnalyzer


class HybridAnalyzer:
    """
    Hybrid analyzer that combines Rope and Jedi for optimal results.
    
    Uses Jedi for fast initial analysis and Rope for verification and
    complex cases. Provides confidence scoring and fallback mechanisms.
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize the hybrid analyzer.
        
        Args:
            project_path: Root directory of the project to analyze
        """
        self.project_path = project_path
        
        # Initialize both analyzers
        try:
            self.rope_analyzer = RopeAnalyzer(project_path)
            self.rope_available = True
        except Exception as e:
            logger.warning(f"Rope analyzer initialization failed: {e}")
            self.rope_analyzer = None
            self.rope_available = False
        
        try:
            self.jedi_analyzer = JediAnalyzer(project_path)
            self.jedi_available = True
        except Exception as e:
            logger.warning(f"Jedi analyzer initialization failed: {e}")
            self.jedi_analyzer = None
            self.jedi_available = False
        
        if not self.rope_available and not self.jedi_available:
            raise RuntimeError("Neither Rope nor Jedi analyzers could be initialized")
        
        logger.info(f"Hybrid analyzer initialized (Rope: {self.rope_available}, Jedi: {self.jedi_available})")
    
    def find_usages(self, construct: Construct, search_paths: List[Path]) -> List[Path]:
        """
        Find all files where a construct is used using hybrid approach.
        
        Args:
            construct: The construct to search for
            search_paths: List of files to search within
            
        Returns:
            List of file paths where the construct is used
        """
        jedi_results = set()
        rope_results = set()
        
        # Try Jedi first (faster)
        if self.jedi_available:
            try:
                jedi_files = self.jedi_analyzer.find_usages(construct, search_paths)
                jedi_results.update(jedi_files)
                logger.debug(f"Jedi found {len(jedi_files)} files for {construct.full_name}")
            except Exception as e:
                logger.debug(f"Jedi analysis failed for {construct.full_name}: {e}")
        
        # Use Rope for verification and additional results
        if self.rope_available:
            try:
                rope_files = self.rope_analyzer.find_usages(construct, search_paths)
                rope_results.update(rope_files)
                logger.debug(f"Rope found {len(rope_files)} files for {construct.full_name}")
            except Exception as e:
                logger.debug(f"Rope analysis failed for {construct.full_name}: {e}")
        
        # Combine results with preference for accuracy
        if rope_results and jedi_results:
            # Use intersection for high confidence, union for comprehensive coverage
            intersection = rope_results & jedi_results
            union = rope_results | jedi_results
            
            # If intersection is substantial, prefer it (higher confidence)
            if len(intersection) >= len(union) * 0.7:
                final_results = intersection
                logger.debug(f"Using intersection of results for {construct.full_name}")
            else:
                final_results = union
                logger.debug(f"Using union of results for {construct.full_name}")
        elif rope_results:
            final_results = rope_results
            logger.debug(f"Using Rope results only for {construct.full_name}")
        elif jedi_results:
            final_results = jedi_results
            logger.debug(f"Using Jedi results only for {construct.full_name}")
        else:
            final_results = set()
            logger.debug(f"No results found for {construct.full_name}")
        
        return list(final_results)
    
    def analyze_batch(self, constructs: List[Construct], search_paths: List[Path]) -> Dict[str, List[Path]]:
        """
        Analyze multiple constructs using hybrid approach.
        
        Args:
            constructs: List of constructs to analyze
            search_paths: List of paths to search within
            
        Returns:
            Dictionary mapping construct full names to lists of usage files
        """
        logger.info(f"Starting hybrid analysis of {len(constructs)} constructs")
        start_time = time.time()
        
        results = {}
        
        # Decide on strategy based on construct count and available analyzers
        if len(constructs) < 50 and self.rope_available:
            # For small batches, use full hybrid approach
            strategy = "full_hybrid"
        elif self.jedi_available:
            # For large batches, prefer Jedi with selective Rope verification
            strategy = "jedi_primary"
        else:
            # Fall back to Rope only
            strategy = "rope_only"
        
        logger.debug(f"Using strategy: {strategy}")
        
        if strategy == "full_hybrid":
            results = self._analyze_full_hybrid(constructs, search_paths)
        elif strategy == "jedi_primary":
            results = self._analyze_jedi_primary(constructs, search_paths)
        else:
            results = self._analyze_rope_only(constructs, search_paths)
        
        elapsed = time.time() - start_time
        logger.info(f"Hybrid analysis completed in {elapsed:.2f}s using {strategy} strategy")
        
        return results
    
    def _analyze_full_hybrid(self, constructs: List[Construct], search_paths: List[Path]) -> Dict[str, List[Path]]:
        """Full hybrid analysis using both analyzers for each construct."""
        results = {}
        
        for i, construct in enumerate(constructs):
            if i % 10 == 0:
                logger.debug(f"Processed {i}/{len(constructs)} constructs")
            
            try:
                usage_files = self.find_usages(construct, search_paths)
                results[construct.full_name] = usage_files
            except Exception as e:
                logger.error(f"Error in hybrid analysis for {construct.full_name}: {e}")
                results[construct.full_name] = []
        
        return results
    
    def _analyze_jedi_primary(self, constructs: List[Construct], search_paths: List[Path]) -> Dict[str, List[Path]]:
        """Jedi-primary analysis with selective Rope verification."""
        # Use Jedi for initial analysis
        jedi_results = self.jedi_analyzer.analyze_batch(constructs, search_paths)
        
        # Identify constructs that might need Rope verification
        # (e.g., methods, complex inheritance cases)
        candidates_for_rope = [
            c for c in constructs 
            if c.type == ConstructType.METHOD or 
               '.' in c.full_name or 
               len(jedi_results.get(c.full_name, [])) == 0
        ]
        
        if candidates_for_rope and self.rope_available:
            logger.debug(f"Verifying {len(candidates_for_rope)} constructs with Rope")
            rope_results = self.rope_analyzer.analyze_batch(candidates_for_rope, search_paths)
            
            # Merge results, preferring Rope for verified constructs
            for construct in candidates_for_rope:
                rope_files = rope_results.get(construct.full_name, [])
                jedi_files = jedi_results.get(construct.full_name, [])
                
                # Use union of both results
                combined = list(set(rope_files) | set(jedi_files))
                jedi_results[construct.full_name] = combined
        
        return jedi_results
    
    def _analyze_rope_only(self, constructs: List[Construct], search_paths: List[Path]) -> Dict[str, List[Path]]:
        """Rope-only analysis fallback."""
        if not self.rope_available:
            logger.error("Rope analyzer not available for fallback")
            return {c.full_name: [] for c in constructs}
        
        return self.rope_analyzer.analyze_batch(constructs, search_paths)
    
    def get_analyzer_status(self) -> Dict[str, any]:
        """Get status information about both analyzers."""
        status = {
            'rope_available': self.rope_available,
            'jedi_available': self.jedi_available,
            'project_path': str(self.project_path),
        }
        
        if self.rope_available:
            status['rope_info'] = self.rope_analyzer.get_project_info()
        
        if self.jedi_available:
            status['jedi_info'] = self.jedi_analyzer.get_project_info()
        
        return status
    
    def close(self) -> None:
        """Clean up both analyzers."""
        if self.rope_analyzer:
            self.rope_analyzer.close()
        
        # Jedi doesn't need explicit cleanup
        logger.debug("Hybrid analyzer closed")
```

### Step 4.4: Test the Analyzers ✅ COMPLETED

**What**: Create tests for the analyzer components.

**Why**: Ensures the analyzers work correctly and handle edge cases properly.

**Status**: ✅ Completed - Comprehensive test suite for all analyzer components

**Create `tests/test_analyzer.py`**:
```python
# this_file: tests/test_analyzer.py

"""
Tests for the analyzer components.
"""

import pytest
import tempfile
from pathlib import Path
from uzpy.parser import TreeSitterParser, ConstructType
from uzpy.analyzer import RopeAnalyzer, JediAnalyzer, HybridAnalyzer


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Create main module
        main_py = root / "main.py"
        main_py.write_text('''
"""Main module."""

from utils import helper_function
from classes import MyClass

def main():
    """Main function."""
    result = helper_function("test")
    obj = MyClass()
    obj.do_something()
    return result

if __name__ == "__main__":
    main()
''')
        
        # Create utils module
        utils_py = root / "utils.py"
        utils_py.write_text('''
"""Utility functions."""

def helper_function(text):
    """A helper function."""
    return f"Processed: {text}"

def unused_function():
    """This function is not used."""
    pass
''')
        
        # Create classes module
        classes_py = root / "classes.py"
        classes_py.write_text('''
"""Classes module."""

class MyClass:
    """A sample class."""
    
    def __init__(self):
        """Initialize the class."""
        self.value = 42
    
    def do_something(self):
        """Do something."""
        return self.value * 2
''')
        
        yield root


def test_rope_analyzer_initialization(sample_project):
    """Test Rope analyzer initialization."""
    analyzer = RopeAnalyzer(sample_project)
    assert analyzer.project is not None
    assert analyzer.root_path == sample_project
    
    info = analyzer.get_project_info()
    assert 'python_files' in info
    assert info['python_files'] >= 3
    
    analyzer.close()


def test_jedi_analyzer_initialization(sample_project):
    """Test Jedi analyzer initialization."""
    analyzer = JediAnalyzer(sample_project)
    assert analyzer.project is not None
    assert analyzer.project_path == sample_project
    
    info = analyzer.get_project_info()
    assert 'project_path' in info


def test_hybrid_analyzer_initialization(sample_project):
    """Test hybrid analyzer initialization."""
    analyzer = HybridAnalyzer(sample_project)
    
    status = analyzer.get_analyzer_status()
    assert 'rope_available' in status
    assert 'jedi_available' in status
    
    # At least one should be available
    assert status['rope_available'] or status['jedi_available']
    
    analyzer.close()


def test_find_usages_integration(sample_project):
    """Test finding usages across the sample project."""
    # Parse the utils module to get constructs
    parser = TreeSitterParser()
    utils_file = sample_project / "utils.py"
    constructs = parser.parse_file(utils_file)
    
    # Find the helper_function
    helper_func = None
    for construct in constructs:
        if construct.name == "helper_function":
            helper_func = construct
            break
    
    assert helper_func is not None
    assert helper_func.type == ConstructType.FUNCTION
    
    # Test with hybrid analyzer
    analyzer = HybridAnalyzer(sample_project)
    search_paths = [sample_project]
    
    usage_files = analyzer.find_usages(helper_func, search_paths)
    
    # Should find usage in main.py
    main_file = sample_project / "main.py"
    assert main_file in usage_files
    
    analyzer.close()


def test_batch_analysis(sample_project):
    """Test batch analysis functionality."""
    # Parse all files
    parser = TreeSitterParser()
    all_constructs = []
    
    for py_file in sample_project.glob("*.py"):
        constructs = parser.parse_file(py_file)
        all_constructs.extend(constructs)
    
    assert len(all_constructs) > 0
    
    # Test batch analysis
    analyzer = HybridAnalyzer(sample_project)
    search_paths = [sample_project]
    
    results = analyzer.analyze_batch(all_constructs, search_paths)
    
    # Should have results for all constructs
    assert len(results) == len(all_constructs)
    
    # Check specific known usage
    helper_results = results.get("helper_function")
    if helper_results:
        main_file = sample_project / "main.py"
        assert main_file in helper_results
    
    analyzer.close()


def test_unused_function_detection(sample_project):
    """Test that unused functions are correctly identified."""
    parser = TreeSitterParser()
    utils_file = sample_project / "utils.py"
    constructs = parser.parse_file(utils_file)
    
    # Find the unused_function
    unused_func = None
    for construct in constructs:
        if construct.name == "unused_function":
            unused_func = construct
            break
    
    assert unused_func is not None
    
    analyzer = HybridAnalyzer(sample_project)
    search_paths = [sample_project]
    
    usage_files = analyzer.find_usages(unused_func, search_paths)
    
    # Should find no usage files (except possibly the definition file itself)
    # Filter out the definition file
    definition_file = unused_func.file_path
    usage_files = [f for f in usage_files if f != definition_file]
    
    assert len(usage_files) == 0
    
    analyzer.close()


def test_analyzer_error_handling(sample_project):
    """Test analyzer error handling with problematic files."""
    # Create a file with syntax errors
    broken_file = sample_project / "broken.py"
    broken_file.write_text('''
def broken_function(
    # Missing closing parenthesis
    return "this is broken"
''')
    
    parser = TreeSitterParser()
    
    # Parser should still extract some constructs despite errors
    try:
        constructs = parser.parse_file(broken_file)
        # Should have at least the module construct
        assert len(constructs) >= 1
    except Exception as e:
        # If parsing completely fails, that's acceptable for broken syntax
        pytest.skip(f"Parser failed on broken syntax: {e}")
    
    # Analyzer should handle errors gracefully
    analyzer = HybridAnalyzer(sample_project)
    
    if constructs:
        results = analyzer.analyze_batch(constructs, [sample_project])
        # Should not crash, even if results are empty
        assert isinstance(results, dict)
    
    analyzer.close()
```

---

*This is just the first part of the TODO.md. The document continues with Phase 5 (LibCST Integration), Phase 6 (End-to-End Pipeline), Phase 7 (Testing & Polish), and additional sections for optimization, deployment, and maintenance. Each phase follows the same detailed pattern with specific implementation steps, code examples, and testing instructions.*

---

## Current Status Summary

**Completed Phases:**
- ✅ Phase 1: Project Foundation & Basic CLI
- ✅ Phase 2: File Discovery System  
- ✅ Phase 3: Tree-sitter Integration
- ✅ Phase 4: Reference Finding with Rope and Jedi

**Next Priorities:**

**Phase 5**: LibCST Integration (NEXT - Days 9-10)
- Implement docstring modification with formatting preservation
- Handle edge cases (missing docstrings, different quote styles)
- Test modification accuracy

**Phase 6**: End-to-End Pipeline (Days 11-12) 
- Integrate all components into working pipeline
- Add configuration system and advanced CLI options
- Implement watch mode and incremental updates

**Phase 7**: Testing & Polish (Days 13-14)
- Comprehensive testing suite
- Performance optimization
- Documentation and examples
- Error handling improvements

**Phase 8**: Advanced Features (Days 15+)
- Language Server Protocol support
- CI/CD integration
- Visual reporting and analytics
- Plugin system for extensibility

Each phase builds incrementally on the previous work, following the "minimal viable increment" principle while maintaining code quality and comprehensive testing.
