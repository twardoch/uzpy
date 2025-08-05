---
# this_file: src_docs/md/06-api-reference.md
---

# API Reference

This chapter provides comprehensive documentation for using uzpy programmatically as a Python library, including all public APIs, data structures, and integration patterns.

## Core API

### High-Level Pipeline API

The simplest way to use uzpy programmatically is through the pipeline API:

```python
from pathlib import Path
from uzpy.pipeline import run_analysis_and_modification
from uzpy.types import Construct, Reference

# Basic usage
usage_results = run_analysis_and_modification(
    edit_path=Path("src/"),
    ref_path=Path("."),
    exclude_patterns=["**/__pycache__/**", "*.pyc"],
    dry_run=False
)

# Process results
for construct, references in usage_results.items():
    print(f"{construct.full_name} used in {len(references)} places")
```

#### `run_analysis_and_modification`

The main entry point for programmatic usage.

**Signature:**
```python
def run_analysis_and_modification(
    edit_path: Path | list[Path],
    ref_path: Path | list[Path],
    exclude_patterns: list[str] | None = None,
    analyzer_type: str = "modern_hybrid",
    use_cache: bool = True,
    parallel: bool = False,
    safe_mode: bool = False,
    dry_run: bool = False,
    timeout: int = 30,
    **kwargs
) -> dict[Construct, list[Reference]]
```

**Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `edit_path` | `Path \| list[Path]` | Path(s) to files/directories to modify | Required |
| `ref_path` | `Path \| list[Path]` | Path(s) to search for references | Required |
| `exclude_patterns` | `list[str] \| None` | Exclusion patterns (gitignore style) | `None` |
| `analyzer_type` | `str` | Analyzer to use | `"modern_hybrid"` |
| `use_cache` | `bool` | Enable caching | `True` |
| `parallel` | `bool` | Enable parallel processing | `False` |
| `safe_mode` | `bool` | Use safe modifier | `False` |
| `dry_run` | `bool` | Don't modify files | `False` |
| `timeout` | `int` | Analysis timeout per construct (seconds) | `30` |

**Returns:**
- `dict[Construct, list[Reference]]`: Mapping of constructs to their references

**Example:**
```python
from pathlib import Path
from uzpy.pipeline import run_analysis_and_modification

# Analyze a specific module
results = run_analysis_and_modification(
    edit_path=Path("src/mymodule.py"),
    ref_path=[Path("src/"), Path("tests/")],
    exclude_patterns=["**/test_*", "**/__pycache__/**"],
    analyzer_type="jedi",
    safe_mode=True,
    dry_run=True  # Preview changes
)

# Print summary
print(f"Found {len(results)} constructs")
for construct, refs in results.items():
    if refs:
        print(f"  {construct.name}: {len(refs)} references")
```

## Data Structures

### `Construct`

Represents a code construct (function, class, method, module).

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Construct:
    name: str                    # Simple name (e.g., "myfunction")
    full_name: str              # Fully qualified name (e.g., "mymodule.myfunction")
    file_path: Path             # Path to file containing construct
    line_number: int            # Line number where construct is defined
    construct_type: str         # "function", "class", "method", "module"
    docstring: str | None       # Existing docstring content
    signature: str | None       # Function/method signature
    parent_class: str | None    # Parent class for methods
```

**Example:**
```python
from uzpy.types import Construct
from pathlib import Path

# Create a construct manually (usually done by parser)
construct = Construct(
    name="calculate_metrics",
    full_name="analytics.calculate_metrics", 
    file_path=Path("src/analytics.py"),
    line_number=42,
    construct_type="function",
    docstring="Calculate various metrics from data.",
    signature="calculate_metrics(data: dict) -> dict",
    parent_class=None
)

print(f"Construct: {construct.full_name} at {construct.file_path}:{construct.line_number}")
```

### `Reference`

Represents a usage/reference to a construct.

```python
@dataclass  
class Reference:
    file_path: Path             # File containing the reference
    line_number: int            # Line number of reference
    column_number: int | None   # Column number (if available)
    context: str | None         # Surrounding code context
    reference_type: str         # "import", "call", "attribute", etc.
```

**Example:**
```python
from uzpy.types import Reference
from pathlib import Path

# References are typically found by analyzers
reference = Reference(
    file_path=Path("src/main.py"),
    line_number=15,
    column_number=8,
    context="result = calculate_metrics(data)",
    reference_type="call"
)

print(f"Reference: {reference.file_path}:{reference.line_number}")
```

## Component APIs

### Discovery API

Find Python files for analysis.

```python
from uzpy.discovery import FileDiscovery
from pathlib import Path

# Create discovery instance
discovery = FileDiscovery(
    exclude_patterns=["**/__pycache__/**", "*.pyc"]
)

# Find Python files
edit_files = discovery.discover_python_files([Path("src/")])
ref_files = discovery.discover_python_files([Path(".")])

print(f"Found {len(edit_files)} files to edit")
print(f"Found {len(ref_files)} files to search")
```

#### `FileDiscovery`

**Constructor:**
```python
def __init__(
    self,
    exclude_patterns: list[str] | None = None,
    follow_symlinks: bool = False
)
```

**Methods:**

**`discover_python_files`**
```python
def discover_python_files(self, paths: list[Path]) -> list[Path]:
    """Discover Python files in given paths."""
```

**`is_python_file`**
```python
def is_python_file(self, file_path: Path) -> bool:
    """Check if file is a Python file."""
```

### Parser API

Extract constructs from Python files.

```python
from uzpy.parser import TreeSitterParser, CachedParser
from pathlib import Path

# Basic parser
parser = TreeSitterParser()
constructs = parser.parse_file(Path("src/mymodule.py"))

# Cached parser (recommended)
cached_parser = CachedParser(
    base_parser=TreeSitterParser(),
    cache_size=1000
)
constructs = cached_parser.parse_file(Path("src/mymodule.py"))

for construct in constructs:
    print(f"{construct.construct_type}: {construct.full_name}")
```

#### `TreeSitterParser`

**Constructor:**
```python  
def __init__(self, language: str = "python")
```

**Methods:**

**`parse_file`**
```python
def parse_file(self, file_path: Path) -> list[Construct]:
    """Parse file and extract constructs."""
```

**`parse_content`**
```python
def parse_content(self, content: str, file_path: Path) -> list[Construct]:
    """Parse content string and extract constructs."""
```

#### `CachedParser`

Wraps any parser with caching capability.

**Constructor:**
```python
def __init__(
    self,
    base_parser: BaseParser,
    cache_size: int = 1000,
    cache_ttl: int = 3600
)
```

### Analyzer API

Find references to constructs.

```python
from uzpy.analyzer import (
    ModernHybridAnalyzer,
    HybridAnalyzer, 
    JediAnalyzer,
    RopeAnalyzer,
    PyrightAnalyzer
)
from pathlib import Path

# Choose analyzer
analyzer = ModernHybridAnalyzer()

# Find references
references = analyzer.find_references(
    construct=my_construct,
    search_paths=[Path("src/"), Path("tests/")]
)

print(f"Found {len(references)} references")
for ref in references:
    print(f"  {ref.file_path}:{ref.line_number}")
```

#### Base Analyzer Interface

All analyzers implement this interface:

```python
from abc import ABC, abstractmethod

class BaseAnalyzer(ABC):
    @abstractmethod
    def find_references(
        self, 
        construct: Construct, 
        search_paths: list[Path]
    ) -> list[Reference]:
        """Find all references to construct in search paths."""
```

#### Specific Analyzers

**`ModernHybridAnalyzer`** (recommended)
```python
def __init__(
    self,
    ruff_threshold: int = 100,
    astgrep_threshold: int = 50, 
    pyright_threshold: int = 10,
    short_circuit: bool = True
)
```

**`HybridAnalyzer`**
```python
def __init__(
    self,
    jedi_threshold: int = 200,
    rope_threshold: int = 100,
    prefer_jedi: bool = True
)
```

**`JediAnalyzer`**
```python
def __init__(
    self,
    follow_imports: bool = True,
    auto_import_modules: bool = True
)
```

**`RopeAnalyzer`**
```python
def __init__(
    self,
    project_root: Path | None = None,
    ignore_syntax_errors: bool = True
)
```

### Modifier API

Update docstrings with usage information.

```python
from uzpy.modifier import LibCSTModifier, SafeModifier
from pathlib import Path

# Basic modifier
modifier = LibCSTModifier()

# Safe modifier (recommended for production)
safe_modifier = SafeModifier(
    base_modifier=LibCSTModifier(),
    validate_syntax=True,
    preserve_quotes=True
)

# Update docstring
success = modifier.update_docstring(
    file_path=Path("src/mymodule.py"),
    construct=my_construct,
    references=references,
    dry_run=False
)

print(f"Update {'successful' if success else 'failed'}")
```

#### `LibCSTModifier`

**Constructor:**
```python
def __init__(
    self,
    usage_section_title: str = "Used in:",
    relative_paths: bool = True,
    sort_paths: bool = True
)
```

**Methods:**

**`update_docstring`**
```python
def update_docstring(
    self,
    file_path: Path,
    construct: Construct, 
    references: list[Reference],
    dry_run: bool = False
) -> bool:
    """Update construct's docstring with reference information."""
```

**`clean_docstring`**
```python
def clean_docstring(
    self,
    file_path: Path,
    construct: Construct,
    dry_run: bool = False
) -> bool:
    """Remove usage section from construct's docstring."""
```

#### `SafeModifier`

Wraps any modifier with additional safety checks.

**Constructor:**
```python
def __init__(
    self,
    base_modifier: BaseModifier,
    validate_syntax: bool = True,
    preserve_quotes: bool = True,
    backup_enabled: bool = False
)
```

## Configuration API

Manage uzpy settings programmatically.

```python
from uzpy.settings import UzpySettings
from pathlib import Path

# Load settings from environment/config file
settings = UzpySettings()

# Create settings programmatically
settings = UzpySettings(
    edit_path=[Path("src/")],
    ref_path=[Path(".")],
    analyzer_type="modern_hybrid",
    use_cache=True,
    safe_mode=True,
    log_level="INFO"
)

# Use settings with pipeline
results = run_analysis_and_modification(
    edit_path=settings.edit_path,
    ref_path=settings.ref_path,
    analyzer_type=settings.analyzer_type,
    use_cache=settings.use_cache,
    safe_mode=settings.safe_mode
)
```

### `UzpySettings`

Pydantic-based settings class.

**Key Fields:**
```python
class UzpySettings(BaseSettings):
    edit_path: list[Path]
    ref_path: list[Path] 
    exclude_patterns: list[str] = field(default_factory=list)
    analyzer_type: str = "modern_hybrid"
    use_cache: bool = True
    safe_mode: bool = False
    parallel_enabled: bool = False
    timeout: int = 30
    log_level: str = "INFO"
    verbose: bool = False
```

## Advanced Usage Patterns

### Custom Analysis Workflow

Create a custom analysis workflow with fine-grained control:

```python
from pathlib import Path
from uzpy.discovery import FileDiscovery
from uzpy.parser import CachedParser, TreeSitterParser
from uzpy.analyzer import ModernHybridAnalyzer
from uzpy.modifier import SafeModifier, LibCSTModifier

# Step 1: Discover files
discovery = FileDiscovery(exclude_patterns=["**/__pycache__/**"])
edit_files = discovery.discover_python_files([Path("src/")])
ref_files = discovery.discover_python_files([Path(".")])

# Step 2: Parse constructs
parser = CachedParser(TreeSitterParser())
all_constructs = []
for file_path in edit_files:
    constructs = parser.parse_file(file_path)
    all_constructs.extend(constructs)

print(f"Found {len(all_constructs)} constructs")

# Step 3: Analyze references
analyzer = ModernHybridAnalyzer()
results = {}
for construct in all_constructs:
    references = analyzer.find_references(construct, ref_files)
    if references:
        results[construct] = references

print(f"Found references for {len(results)} constructs")

# Step 4: Update docstrings
modifier = SafeModifier(LibCSTModifier())
for construct, references in results.items():
    success = modifier.update_docstring(
        file_path=construct.file_path,
        construct=construct,
        references=references,
        dry_run=False
    )
    if success:
        print(f"Updated {construct.full_name}")
```

### Batch Processing

Process multiple projects or configurations:

```python
from pathlib import Path
from uzpy.pipeline import run_analysis_and_modification

# Define projects
projects = [
    {
        "name": "core",
        "edit_path": Path("packages/core/src/"),
        "ref_path": Path("packages/core/")
    },
    {
        "name": "utils", 
        "edit_path": Path("packages/utils/src/"),
        "ref_path": Path("packages/")
    },
    {
        "name": "api",
        "edit_path": Path("packages/api/src/"),
        "ref_path": Path("packages/")
    }
]

# Process each project
for project in projects:
    print(f"Processing {project['name']}...")
    
    results = run_analysis_and_modification(
        edit_path=project["edit_path"],
        ref_path=project["ref_path"],
        analyzer_type="modern_hybrid",
        safe_mode=True
    )
    
    constructs_updated = len([c for c, refs in results.items() if refs])
    print(f"  Updated {constructs_updated} constructs")
```

### Integration with CI/CD

Integrate uzpy into automated workflows:

```python
import sys
from pathlib import Path
from uzpy.pipeline import run_analysis_and_modification

def ci_analysis(base_branch: str = "main") -> int:
    """Run uzpy analysis for CI/CD pipeline."""
    
    # Get changed files (would integrate with git)
    changed_files = get_changed_python_files(base_branch)
    
    if not changed_files:
        print("No Python files changed")
        return 0
    
    # Run analysis on changed files only
    results = run_analysis_and_modification(
        edit_path=changed_files,
        ref_path=Path("."),
        safe_mode=True,
        dry_run=True  # Don't modify in CI
    )
    
    # Check if docstrings would be updated
    needs_update = [c for c, refs in results.items() if refs]
    
    if needs_update:
        print("The following constructs need docstring updates:")
        for construct in needs_update:
            print(f"  {construct.file_path}:{construct.line_number} - {construct.full_name}")
        return 1  # Fail CI if updates needed
    
    print("All docstrings are up to date")
    return 0

if __name__ == "__main__":
    sys.exit(ci_analysis())
```

### Custom Analyzer

Create a custom analyzer for specific needs:

```python
from uzpy.analyzer.base import BaseAnalyzer
from uzpy.types import Construct, Reference
from pathlib import Path
import re

class RegexAnalyzer(BaseAnalyzer):
    """Simple regex-based analyzer for demonstration."""
    
    def find_references(
        self, 
        construct: Construct, 
        search_paths: list[Path]
    ) -> list[Reference]:
        references = []
        
        # Create regex pattern for construct name
        pattern = re.compile(rf'\b{re.escape(construct.name)}\b')
        
        for path in search_paths:
            if path.is_file() and path.suffix == '.py':
                try:
                    content = path.read_text()
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if pattern.search(line):
                            references.append(Reference(
                                file_path=path,
                                line_number=line_num,
                                column_number=None,
                                context=line.strip(),
                                reference_type="regex_match"
                            ))
                except Exception as e:
                    print(f"Error reading {path}: {e}")
        
        return references

# Use custom analyzer
analyzer = RegexAnalyzer()
results = run_analysis_and_modification(
    edit_path=Path("src/"),
    ref_path=Path("."),
    analyzer=analyzer,  # Pass custom analyzer
    dry_run=True
)
```

## Error Handling

Handle errors gracefully in your applications:

```python
from pathlib import Path
from uzpy.pipeline import run_analysis_and_modification
from uzpy.exceptions import (
    UzpyError,
    ParseError, 
    AnalysisError,
    ModificationError
)

try:
    results = run_analysis_and_modification(
        edit_path=Path("src/"),
        ref_path=Path("."),
        timeout=60
    )
    
except ParseError as e:
    print(f"Failed to parse file: {e}")
    # Handle parse errors (syntax issues, etc.)
    
except AnalysisError as e:
    print(f"Analysis failed: {e}")
    # Handle analyzer failures (timeouts, tool errors)
    
except ModificationError as e:
    print(f"Failed to modify file: {e}")
    # Handle modification failures (permissions, syntax errors)
    
except UzpyError as e:
    print(f"General uzpy error: {e}")
    # Handle other uzpy-specific errors
    
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle unexpected errors
```

## Performance Monitoring

Monitor performance in your applications:

```python
import time
from pathlib import Path
from uzpy.pipeline import run_analysis_and_modification

def timed_analysis(edit_path: Path, ref_path: Path) -> dict:
    """Run analysis with timing information."""
    
    start_time = time.time()
    
    results = run_analysis_and_modification(
        edit_path=edit_path,
        ref_path=ref_path,
        use_cache=True
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    stats = {
        "duration_seconds": duration,
        "constructs_found": len(results),
        "constructs_with_references": len([c for c, refs in results.items() if refs]),
        "total_references": sum(len(refs) for refs in results.values())
    }
    
    print(f"Analysis completed in {duration:.2f} seconds")
    print(f"Found {stats['constructs_found']} constructs")
    print(f"{stats['constructs_with_references']} have references")
    print(f"Total {stats['total_references']} references found")
    
    return stats

# Usage
stats = timed_analysis(Path("src/"), Path("."))
```

## Next Steps

With the API reference in hand, you can:

1. **[Extend uzpy](07-extending-uzpy.md)** with custom components
2. **[Optimize performance](08-performance-optimization.md)** for your specific use case
3. **[Troubleshoot issues](09-troubleshooting.md)** when things go wrong

The next chapter covers creating custom analyzers, modifiers, and other extensions.