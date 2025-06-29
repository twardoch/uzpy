# uzpy: Python Code Usage Tracker & Docstring Updater

**uzpy** (`ʌzpi`) is a powerful command-line tool and Python library that analyzes your Python codebase to discover where functions, classes, methods, and modules are used. It then automatically updates their docstrings with a clear "Used in:" section, providing valuable cross-references directly within your code.

## Part 1: User Guide

### What does `uzpy` do?

At its core, `uzpy` helps you understand and document the interconnectedness of your Python project. It:

1.  **Discovers Code Constructs:** Scans your Python files to identify definitions of functions, classes, methods, and modules.
2.  **Finds Usages:** Determines where each of these defined constructs is referenced or called throughout your specified codebase.
3.  **Updates Docstrings:** Modifies the docstrings of the defined constructs to include a list of file paths where they are used.
4.  **Cleans Docstrings:** Can also remove these automatically generated "Used in:" sections if needed.
5.  **Offers Flexibility:** Provides various analysis engines, caching, and parallel processing for efficiency.

**Example of a modified docstring:**

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

`uzpy` is for Python developers who want to:

*   **Improve Code Navigation:** Quickly see where a piece of code is utilized without manually searching or relying solely on IDE features.
*   **Enhance Code Comprehension:** Understand the impact of changes to a function or class by seeing its usage contexts.
*   **Maintain Up-to-Date Documentation:** Keep docstrings relevant by automatically linking definitions to their usage sites.
*   **Streamline Code Reviews:** Provide reviewers with immediate context on where and how a component is used.
*   **Aid Refactoring:** Identify all call sites of a function or usages of a class before making modifications.

### Why is `uzpy` useful?

*   **Automated Cross-Referencing:** Saves manual effort in tracking and documenting code usage.
*   **Living Documentation:** Docstrings evolve with your codebase, reflecting actual usage.
*   **Reduced Cognitive Load:** Makes it easier to navigate and understand complex projects.
*   **IDE Agnostic:** Provides valuable insights regardless of your development environment, though it complements IDE features well.
*   **Configurable and Performant:** Offers various analysis backends, caching, and parallel execution to suit different project sizes and needs.

### Installation

`uzpy` requires Python 3.10 or higher. You can install it using `uv pip` (or `pip`):

```bash
uv pip install uzpy
```

This installs the core package. `uzpy` also has optional dependencies for development, testing, and documentation building. You can install them as needed:

*   **For development (linters, formatters, etc.):**
    ```bash
    uv pip install uzpy[dev]
    ```
*   **For running tests:**
    ```bash
    uv pip install uzpy[test]
    ```
*   **For building documentation:**
    ```bash
    uv pip install uzpy[docs]
    ```
*   **To install all optional dependencies:**
    ```bash
    uv pip install uzpy[all]
    ```

For developing `uzpy` itself, clone the repository and install it in editable mode:

```bash
git clone https://github.com/twardoch/uzpy.git
cd uzpy
uv pip install -e .[dev,test]
```

### How to Use `uzpy`

`uzpy` can be used both as a command-line tool and programmatically within your Python scripts.

#### Command-Line Interface (CLI)

The primary CLI is accessed via the `uzpy` command (which is an alias for `uzpy-modern`).

**Core Commands:**

1.  **`run`**: Analyze the codebase and update docstrings.
    *   `--edit <path>` or `-e <path>`: Path to the file or directory whose docstrings will be modified.
    *   `--ref <path>` or `-r <path>`: Path to the file or directory to search for usages. Often this is your entire project root (e.g., `.`).
    *   `--dry-run`: Show what changes would be made without actually modifying files.
    *   `--config <file_path>` or `-c <file_path>`: Path to a custom `.uzpy.env` configuration file.
    *   `--verbose` or `-v`: Enable verbose DEBUG logging.
    *   `--log-level <LEVEL>`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    **Example:**
    ```bash
    # Analyze the 'src/' directory and update its docstrings,
    # searching for usages within the entire current project.
    uzpy run --edit src/ --ref .

    # Perform a dry run on a single file
    uzpy run --edit my_module.py --ref . --dry-run
    ```

2.  **`clean`**: Remove "Used in:" sections from docstrings.
    *   `--edit <path>` or `-e <path>`: Path to the file or directory to clean.
    *   `--dry-run`: Show what files would be cleaned without modifying them.

    **Example:**
    ```bash
    uzpy clean --edit src/
    ```

3.  **`cache`**: Manage the analysis cache.
    *   `uzpy cache clear`: Clears the parser and analyzer caches.
    *   `uzpy cache stats`: Shows statistics about the cache (item count, disk usage).

4.  **`watch`**: (Experimental) Monitor files for changes and re-run analysis automatically.
    *   `--path <path>` or `-p <path>`: Directory/file to watch (overrides configured `edit_path`).

    **Example:**
    ```bash
    uzpy watch --path src/
    ```

**Configuration:**

`uzpy` can be configured using a `.uzpy.env` file in the directory where you run the command, or by specifying a custom config file path with `--config`. Environment variables prefixed with `UZPY_` can also be used.

Key configuration options (settable in `.uzpy.env` or as environment variables):

*   `UZPY_EDIT_PATH`: Default path to analyze/modify.
*   `UZPY_REF_PATH`: Default reference path for usage search.
*   `UZPY_EXCLUDE_PATTERNS`: Comma-separated list of glob patterns to exclude (e.g., `__pycache__/*,*.tmp`).
*   `UZPY_USE_CACHE`: `true` or `false` to enable/disable caching.
*   `UZPY_ANALYZER_TYPE`: Choose the analysis engine (e.g., `modern_hybrid`, `hybrid`, `jedi`, `rope`).
*   `UZPY_LOG_LEVEL`: Default logging level.
*   `UZPY_VERBOSE`: `true` or `false` for verbose logging.
*   ... and more for fine-tuning analyzer behavior (see `src/uzpy/cli_modern.py` `UzpySettings` for all options).

#### Programmatic Usage

You can integrate `uzpy`'s core functionality into your own Python scripts. The main entry point for this is the `run_analysis_and_modification` function.

```python
from pathlib import Path
from uzpy.pipeline import run_analysis_and_modification
from uzpy.types import Construct, Reference # For inspecting results

# Define paths
project_root = Path(".")
edit_directory = project_root / "src"
reference_directory = project_root # Search the whole project

# Define exclusion patterns (optional)
exclude_patterns = ["**/__pycache__/**", "*.pyc", "build/", "dist/"]

# Run the analysis and modification
# Set dry_run=True to see what would change without modifying files
usage_results: dict[Construct, list[Reference]] = run_analysis_and_modification(
    edit_path=edit_directory,
    ref_path=reference_directory,
    exclude_patterns=exclude_patterns,
    dry_run=False # Set to True for a dry run
)

# Process results (optional)
if usage_results:
    print(f"Analysis complete. Found usages for {len(usage_results)} constructs.")
    for construct, references in usage_results.items():
        if references:
            print(f"Construct {construct.full_name} in {construct.file_path} is used in:")
            for ref in references:
                print(f"  - {ref.file_path} (Line: {ref.line_number})")
else:
    print("No constructs found or no usages identified.")

```

You can also use individual components like parsers or analyzers directly. See the modules in `src/uzpy/parser/` and `src/uzpy/analyzer/` for more details.

## Part 2: Technical Details & Contribution Guide

### How `uzpy` Works

`uzpy` follows a multi-stage process:

1.  **File Discovery (`src/uzpy/discovery.py`):**
    *   The `FileDiscovery` class scans the specified `edit_path` and `ref_path`.
    *   It identifies all Python files (`.py` or files with Python shebangs).
    *   It respects default exclude patterns (e.g., `.git`, `__pycache__`, `venv`) and user-defined exclusions. Patterns are `.gitignore` style.

2.  **Parsing (`src/uzpy/parser/`):**
    *   The primary parser is `TreeSitterParser`, which uses the `tree-sitter` library for fast and robust parsing of Python code into an Abstract Syntax Tree (AST).
    *   It extracts code constructs (modules, classes, functions, methods) along with their names, line numbers, existing docstrings, and fully qualified names. These are stored as `Construct` objects (see `src/uzpy/types.py`).
    *   A `CachedParser` wraps the `TreeSitterParser` to cache parsing results using `diskcache`. Cache keys are based on file content and modification time to ensure freshness.

3.  **Usage Analysis (`src/uzpy/analyzer/`):**
    *   This is the most complex stage, with multiple analyzer implementations available. The goal is to find all `Reference`s to each `Construct`.
    *   **`ModernHybridAnalyzer`**: This is often the default and recommended analyzer. It combines several modern tools in a tiered approach:
        *   **`RuffAnalyzer`**: Uses `ruff` (a fast linter) for very basic checks. Its ability to find references is limited but can quickly identify non-usage in some cases.
        *   **`AstGrepAnalyzer`**: Uses `ast-grep` for structural pattern matching based on predefined rules for calls and imports.
        *   **`PyrightAnalyzer`**: Leverages `pyright` (Microsoft's static type checker). While Pyright's CLI is not primarily designed for "find references" like its LSP, `uzpy` attempts to use its analysis output. This is more accurate for type-aware reference finding.
    *   **`HybridAnalyzer`**: A traditional hybrid approach combining:
        *   **`JediAnalyzer`**: Uses `jedi` for fast symbol resolution and reference finding.
        *   **`RopeAnalyzer`**: Uses `rope` for more robust, deeper static analysis, especially for complex cases.
    *   Analyzers can be wrapped with:
        *   **`CachedAnalyzer`**: Caches analysis results (the list of `Reference`s for a `Construct`). Cache keys depend on the construct itself and a hash of all files in the `search_paths` to ensure that changes in referenced code invalidate the cache.
        *   **`ParallelAnalyzer`**: Uses `multiprocessing` to run analysis for multiple constructs concurrently, speeding up the process on multi-core machines.
    *   The choice of analyzer and its configuration (e.g., short-circuit thresholds in `ModernHybridAnalyzer`) can be set via the `.uzpy.env` file or environment variables.

4.  **Docstring Modification (`src/uzpy/modifier/libcst_modifier.py`):**
    *   Once usages are found, `LibCSTModifier` is used to update the docstrings in the files from `edit_path`.
    *   LibCST (Concrete Syntax Tree) is used because it preserves all formatting, comments, and whitespace in the original code.
    *   The `DocstringModifier` (a LibCST transformer) visits relevant nodes (functions, classes, modules) in the AST.
    *   It extracts the existing docstring (if any).
    *   It generates a "Used in:" section, listing relative file paths of all references.
        *   References from the same file being modified are excluded from this list.
        *   If a "Used in:" section already exists, new references are merged with existing ones, and duplicates are avoided. Old, valid references are preserved.
    *   The modified docstring is then written back into the CST, and the entire file is re-serialized.
    *   `LibCSTCleaner` and `DocstringCleaner` use a similar process to remove these "Used in:" sections.

5.  **CLI and Orchestration (`src/uzpy/cli_modern.py`, `src/uzpy/pipeline.py`):**
    *   `cli_modern.py` uses `Typer` to provide the command-line interface. It handles argument parsing, loads settings (from `.uzpy.env` or environment variables via Pydantic's `BaseSettings`), and sets up `loguru` for logging.
    *   `pipeline.py`'s `run_analysis_and_modification` function orchestrates the discovery, parsing, analysis, and modification steps.

### Coding and Contribution Rules

We welcome contributions to `uzpy`! Please follow these guidelines:

**General Principles (from `AGENT.md`/`CLAUDE.md`):**

*   **Iterate Gradually:** Make small, incremental changes. Avoid major refactors in single commits.
*   **Preserve Structure:** Maintain the existing code structure unless a change is well-justified.
*   **Readability:** Write clear, descriptive names for variables and functions. Keep code simple and explicit (PEP 20).
*   **Comments & Docstrings:**
    *   Write explanatory docstrings for all public modules, classes, functions, and methods (PEP 257). Docstrings should be imperative (e.g., "Do this," not "Does this.").
    *   Use comments to explain *why* certain complex or non-obvious code exists.
    *   Ensure docstrings and comments are kept up-to-date with code changes.
*   **`this_file` Record:** For Python source files within `src/uzpy/`, include a comment near the top like `# this_file: src/uzpy/module_name.py` indicating its path relative to the project root.
*   **Error Handling:** Handle potential errors gracefully. Use `try-except` blocks where appropriate and log errors effectively.
*   **Modularity:** Encapsulate repeated logic into concise, single-purpose functions.

**Python Specifics:**

*   **Formatting:**
    *   Follow PEP 8 guidelines.
    *   Use `ruff format` for consistent code formatting. Line length is generally 120 characters.
    *   Use `ruff check` for linting. Configurations are in `pyproject.toml`.
*   **Type Hints:**
    *   Use type hints for all function signatures and variables where practical (PEP 484).
    *   Use simple forms (e.g., `list[int]`, `dict[str, bool]`, `str | None`).
*   **Imports:**
    *   Organize imports according to PEP 8. `ruff` (with `isort` integration) will handle this.
    *   Relative imports within the `src/uzpy` package are banned; use absolute imports (e.g., `from uzpy.parser import TreeSitterParser`).
*   **Logging:**
    *   Use `loguru` for logging. Add `logger.debug()`, `logger.info()`, etc. where appropriate.
    *   Ensure CLI commands have options for verbosity (`-v`) and log level selection.
*   **CLI Scripts:** For new CLI scripts (if any, though `cli_modern.py` is the main one), consider using `Typer` and `Rich` as established in the project.
*   **Dependencies:** Use `uv pip` for managing dependencies (e.g., `uv pip install <package>`, `uv pip uninstall <package>`).

**Development Workflow:**

1.  **Set up Environment:**
    *   Ensure you have Python 3.10+ and `uv` installed.
    *   Clone the repository.
    *   Create and activate a virtual environment:
        ```bash
        python -m venv .venv
        source .venv/bin/activate # or .venv\Scripts\activate on Windows
        ```
    *   Install dependencies: `uv pip install -e .[dev,test]`
    *   (Alternatively, use `hatch env create` and `hatch shell` if you prefer Hatch for environment management.)

2.  **Pre-commit Hooks:**
    *   Install pre-commit hooks to ensure code quality before committing:
        ```bash
        pre-commit install
        ```
    *   These hooks will automatically run tools like `ruff` on your changed files.

3.  **Making Changes:**
    *   Create a new branch for your feature or bugfix.
    *   Write code following the guidelines above.
    *   Add or update tests for your changes in the `tests/` directory.
    *   Ensure all tests pass: `pytest` or `hatch run test:test`.
    *   Run linters and formatters: `hatch run lint:all` or run `ruff format .` and `ruff check . --fix`.
    *   Run type checks: `mypy src/uzpy tests` or `hatch run lint:typing`.

4.  **Updating Documentation (`AGENT.md`/`CLAUDE.md` workflow):**
    *   If you make significant changes, consider if `PLAN.md`, `TODO.md`, or `CHANGELOG.md` need updates.
    *   This `README.md` should be updated if your changes affect user-facing functionality, installation, or technical workings.

5.  **Submitting Changes:**
    *   Commit your changes with clear and descriptive commit messages.
    *   Push your branch to your fork and open a Pull Request against the main `uzpy` repository.

**Running Linters/Formatters/Tests (as per `CLAUDE.md`):**
After making Python changes, you can run the full suite of checks:
```bash
fd -e py -x autoflake --in-place --remove-all-unused-imports {} \; \
fd -e py -x pyupgrade --py311-plus {} \; \
fd -e py -x ruff check --fix --unsafe-fixes {} \; \
fd -e py -x ruff format --respect-gitignore --target-version py311 {} \; \
python -m pytest
```
(Note: `pyupgrade --py311-plus` means Python 3.11+ syntax. `uzpy` targets 3.10+, so adjust if needed, though `ruff` often handles modern syntax upgrades well.)
Many of these are also covered by `hatch` scripts (e.g., `hatch run lint:fix`, `hatch run test:test`).

By following these guidelines, you'll help maintain the quality and consistency of the `uzpy` codebase.
