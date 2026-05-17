# uzpy: Python Code Usage Tracker & Docstring Updater

**uzpy** (`ʌzpi`) analyzes your Python codebase to find where functions, classes, methods, and modules are used. It then automatically updates their docstrings with a "Used in:" section for easy cross-referencing.

## Part 1: User Guide

### What does `uzpy` do?

`uzpy` scans Python files to:

1. **Discover code constructs** – functions, classes, methods, modules
2. **Find usages** – where each construct is referenced or called
3. **Update docstrings** – adds "Used in:" sections with file paths
4. **Clean docstrings** – removes generated "Used in:" sections when needed
5. **Scale efficiently** – supports multiple analysis engines, caching, and parallel processing

**Example output:**
```python
def my_utility_function(data):
    """
    This function processes data in a specific way.

    Used in:
    - src/feature_a/core.py
    - tests/unit/test_processing.py
    """
    # ... implementation ...
    pass
```

### Who is `uzpy` for?

Python developers who need to:
* Navigate code quickly without manual searches
* Understand impact of changes across the codebase
* Keep documentation synchronized with actual usage
* Review code with immediate context on dependencies
* Refactor safely by identifying all call sites

### Why use `uzpy`?

* **Automated tracking** – No more manual documentation updates
* **Living docs** – Usage information updates with your code
* **Simplified navigation** – See dependencies at a glance
* **IDE-agnostic** – Works regardless of your development environment
* **Configurable performance** – Choose analysis backend, enable caching, run in parallel

### Installation

Requires Python 3.10+. Install with `uv pip` (or regular `pip`):

```bash
uv pip install uzpy
```

Optional dependencies:
* **Development tools:** `uv pip install uzpy[dev]`
* **Testing:** `uv pip install uzpy[test]`
* **Documentation:** `uv pip install uzpy[docs]`
* **Everything:** `uv pip install uzpy[all]`

For development:
```bash
git clone https://github.com/twardoch/uzpy.git
cd uzpy
uv pip install -e .[dev,test]
```

### Usage

Access via `uzpy` command (alias for `uzpy-modern`).

#### Core Commands

1. **`run`** – Analyze and update docstrings
    * `--edit <path>` or `-e <path>`: Files/directories to modify
    * `--ref <path>` or `-r <path>`: Files/directories to search for usages
    * `--dry-run`: Preview changes without modifying files
    * `--safe`: Prevent syntax corruption in complex cases
    * `--config <file>` or `-c <file>`: Custom configuration file
    * `--verbose` or `-v`: Enable DEBUG logging
    * `--log-level <LEVEL>`: Set logging level

    **Examples:**
    ```bash
    # Update docstrings in src/, searching entire project
    uzpy run --edit src/ --ref .

    # Preview changes to single file
    uzpy run --edit my_module.py --ref . --dry-run

    # Safe mode for complex codebases
    uzpy run --edit src/ --ref . --safe
    ```

2. **`clean`** – Remove "Used in:" sections
    * `--edit <path>` or `-e <path>`: Files/directories to clean
    * `--dry-run`: Preview files that would be cleaned

    **Example:**
    ```bash
    uzpy clean --edit src/
    ```

3. **`cache`** – Manage analysis cache
    * `uzpy cache clear`: Clear parser and analyzer caches
    * `uzpy cache stats`: Show cache statistics

4. **`watch`** – (Experimental) Auto-reanalyze on file changes
    * `--path <path>` or `-p <path>`: Directory/file to monitor

    **Example:**
    ```bash
    uzpy watch --path src/
    ```

#### Configuration

Use `.uzpy.env` file in working directory, or specify with `--config`. Environment variables use `UZPY_` prefix.

Key options:
* `UZPY_EDIT_PATH`: Default path to analyze/modify
* `UZPY_REF_PATH`: Default reference search path
* `UZPY_EXCLUDE_PATTERNS`: Comma-separated glob patterns to exclude
* `UZPY_USE_CACHE`: Enable/disable caching (`true`/`false`)
* `UZPY_ANALYZER_TYPE`: Analysis engine (`modern_hybrid`, `hybrid`, `jedi`, `rope`)
* `UZPY_LOG_LEVEL`: Default logging level
* `UZPY_VERBOSE`: Enable verbose logging (`true`/`false`)

See `src/uzpy/cli_modern.py` `UzpySettings` for complete options.

#### Programmatic Usage

```python
from pathlib import Path
from uzpy.pipeline import run_analysis_and_modification
from uzpy.types import Construct, Reference

# Define paths
project_root = Path(".")
edit_directory = project_root / "src"
reference_directory = project_root

# Define exclusions
exclude_patterns = ["**/__pycache__/**", "*.pyc", "build/", "dist/"]

# Run analysis
usage_results: dict[Construct, list[Reference]] = run_analysis_and_modification(
    edit_path=edit_directory,
    ref_path=reference_directory,
    exclude_patterns=exclude_patterns,
    dry_run=False
)

# Process results
if usage_results:
    print(f"Found usages for {len(usage_results)} constructs.")
    for construct, references in usage_results.items():
        if references:
            print(f"{construct.full_name} used in:")
            for ref in references:
                print(f"  - {ref.file_path} (Line: {ref.line_number})")
else:
    print("No constructs found or no usages identified.")
```

See `src/uzpy/parser/` and `src/uzpy/analyzer/` for direct component access.

## Part 2: Technical Details & Contribution Guide

### How `uzpy` Works

Multi-stage process:

1. **File Discovery (`src/uzpy/discovery.py`)**
    * `FileDiscovery` scans `edit_path` and `ref_path`
    * Identifies Python files (`.py` or with Python shebangs)
    * Respects `.gitignore`-style exclude patterns

2. **Parsing (`src/uzpy/parser/`)**
    * `TreeSitterParser` uses tree-sitter for fast AST parsing
    * Extracts constructs with names, line numbers, docstrings, and qualified names
    * `CachedParser` wraps primary parser with diskcache integration

3. **Usage Analysis (`src/uzpy/analyzer/`)**
    * **`ModernHybridAnalyzer`** (default):
        * `RuffAnalyzer` – Basic checks with ruff
        * `AstGrepAnalyzer` – Structural pattern matching
        * `PyrightAnalyzer` – Type-aware reference finding
    * **`HybridAnalyzer`** – Traditional approach:
        * `JediAnalyzer` – Fast symbol resolution
        * `RopeAnalyzer` – Deep static analysis
    * Wrappers:
        * `CachedAnalyzer` – Cache results based on construct and file hashes
        * `ParallelAnalyzer` – Multiprocessing for speed

4. **Docstring Modification (`src/uzpy/modifier/libcst_modifier.py`)**
    * `LibCSTModifier` updates docstrings using Concrete Syntax Trees
    * Preserves formatting, comments, whitespace
    * `DocstringModifier` transformer visits relevant AST nodes
    * Generates "Used in:" section with relative file paths
    * Excludes self-references, merges with existing sections, removes duplicates
    * `LibCSTCleaner`/`DocstringCleaner` remove generated sections

5. **CLI and Orchestration (`src/uzpy/cli_modern.py`, `src/uzpy/pipeline.py`)**
    * `cli_modern.py` uses Typer for CLI interface
    * Loads settings via Pydantic `BaseSettings`
    * Uses loguru for logging
    * `pipeline.py` orchestrates discovery, parsing, analysis, modification

### Contribution Guidelines

**General Principles:**
* Make small, incremental changes
* Preserve existing structure unless justified
* Write clear, descriptive names (PEP 20)
* Document public interfaces imperatively (PEP 257)
* Comment complex logic with reasoning
* Include `# this_file: src/uzpy/module_name.py` in source files
* Handle errors gracefully with appropriate logging
* Encapsulate repeated logic in single-purpose functions

**Python Standards:**
* Follow PEP 8
* Use `ruff format` (120 character line limit)
* Add type hints (PEP 484) with simple forms (`list[int]`, `str | None`)
* Use absolute imports within `src/uzpy/`
* Log with `loguru` where appropriate

**Development Workflow:**
1. **Environment setup:**
    * Python 3.10+, uv installed
    * Clone repository
    * Create virtual environment: `python -m venv .venv`
    * Activate: `source .venv/bin/activate`
    * Install dependencies: `uv pip install -e .[dev,test]`

2. **Pre-commit hooks:**
    * Install: `pre-commit install`
    * Runs ruff and other tools automatically

3. **Making changes:**
    * Branch from main
    * Follow coding guidelines
    * Add/update tests in `tests/`
    * Verify tests pass: `pytest` or `hatch run test:test`
    * Run linters: `hatch run lint:all` or `ruff format .` + `ruff check . --fix`
    * Run type checks: `mypy src/uzpy tests` or `hatch run lint:typing`

4. **Documentation:**
    * Update `README.md` for user-facing changes
    * Update `TASKS.md`, `TODO.md`, `CHANGELOG.md` as needed

5. **Submit changes:**
    * Commit with clear messages
    * Push branch and create Pull Request

**Quality Checks:**
```bash
fd -e py -x autoflake --in-place --remove-all-unused-imports {} \;
fd -e py -x pyupgrade --py311-plus {} \;
fd -e py -x ruff check --fix --unsafe-fixes {} \;
fd -e py -x ruff format --respect-gitignore --target-version py311 {} \;
python -m pytest
```

Many checks available through hatch: `hatch run lint:fix`, `hatch run test:test`