# TODO

Of course. Here is a detailed refactoring plan for the `uzpy` codebase, designed for a junior developer to execute.

***

## **`uzpy` Refactoring Specification**

### **1. Overview & Goals**

The current `uzpy` codebase is functional but contains several areas for improvement. The primary goal of this refactoring is to **reduce cognitive load** and **improve maintainability** by simplifying the architecture and focusing on core functionality.

We will achieve this by:
1.  **Removing "fluff":** Eliminating non-essential code, particularly the fancy `rich`-based UI elements, to focus on the core logic.
2.  **Improving Structure:** Centralizing data models and creating a clear pipeline for the analysis process.
3.  **Applying Single Responsibility Principle (SRP):** Ensuring each module and class has one, clear purpose.
4.  **Enhancing Robustness:** Strengthening error handling to ensure the tool fails gracefully on invalid or broken files.

This refactoring will **not** change the core dependencies (`tree-sitter`, `rope`, `jedi`, `libcst`) or the fundamental analysis and modification logic. All tests must pass after the refactoring is complete.

---

### **Phase 1: Project Housekeeping & Setup**

This phase involves cleaning up the project structure and preparing for larger changes.

**Task 1.1: Delete Unused File**
*   **File:** `src/uzpy/uzpy.py`
*   **Action:** Delete this file. It contains boilerplate code that is not used by the application's main entry point (`src/uzpy/cli.py`).

**Task 1.2: Create Centralized Types Module**
*   **Action:** Create a new, empty file: `src/uzpy/types.py`.
*   **Purpose:** This file will house all the core data structures (`Construct`, `Reference`, `ConstructType`) used throughout the application.

**Task 1.3: Create Core Pipeline Module**
*   **Action:** Create a new, empty file: `src/uzpy/pipeline.py`.
*   **Purpose:** This file will contain the main orchestration logic, taking the procedural code out of `cli.py`.

---

### **Phase 2: Centralize Data Models**

This phase will move all core data transfer objects to the new `types.py` module.

**Task 2.1: Move Enum and Dataclasses to `types.py`**
*   **Source File:** `src/uzpy/parser/tree_sitter_parser.py`
*   **Destination File:** `src/uzpy/types.py`
*   **Action:**
    1.  Cut the `ConstructType` enum, `Construct` dataclass, and `Reference` dataclass from `tree_sitter_parser.py`.
    2.  Paste them into `src/uzpy/types.py`.
    3.  Ensure necessary imports (e.g., `dataclass`, `Enum`, `Path`, `Node` from `tree_sitter`) are present in `types.py`. The `Node` type hint might need to be a forward reference `from typing import TYPE_CHECKING ... if TYPE_CHECKING: from tree_sitter import Node`.

**Task 2.2: Update All Imports**
*   **Action:** Go through every `.py` file in `src/` and `tests/` and update the imports for `Construct`, `Reference`, and `ConstructType`.
*   **Example:**
    *   Change `from uzpy.parser import Construct, Reference`
    *   To `from uzpy.types import Construct, Reference`
*   **Files to check (non-exhaustive list):**
    *   `src/uzpy/parser/tree_sitter_parser.py`
    *   `src/uzpy/analyzer/hybrid_analyzer.py`
    *   `src/uzpy/analyzer/jedi_analyzer.py`
    *   `src/uzpy/analyzer/rope_analyzer.py`
    *   `src/uzpy/modifier/libcst_modifier.py`
    *   `src/uzpy/cli.py`
    *   `tests/test_analyzer.py`
    *   `tests/test_modifier.py`
    *   `tests/test_parser.py`

---

### **Phase 3: Refactor the Core Pipeline**

This phase moves the main application logic from the `cli.py` into the new `pipeline.py`, separating orchestration from user interaction.

**Task 3.1: Create the Pipeline Function**
*   **File:** `src/uzpy/pipeline.py`
*   **Action:** Create a new function `run_analysis_and_modification`. This function will contain the logic currently in the `UzpyCLI.run` method.
*   **Signature:**
    ```python
    # src/uzpy/pipeline.py
    from pathlib import Path
    from uzpy.types import Construct

    def run_analysis_and_modification(
        edit_path: Path,
        ref_path: Path,
        exclude_patterns: list[str] | None,
        dry_run: bool,
    ) -> dict[Construct, list[Reference]]:
        """
        Orchestrates the full uzpy pipeline: discovery, parsing, analysis, and modification.
        """
        # Step 1: Discover files
        # ... logic from cli.py ...

        # Step 2: Parse constructs
        # ... logic from cli.py ...

        # Step 3: Analyze usages
        # ... logic from cli.py ...
        
        # Step 4: Modify docstrings (if not dry_run)
        # ... logic from cli.py ...

        # Return the usage_results for reporting
        return usage_results
    ```
*   **Implementation:**
    1.  Copy the entire body of the `run` method from `src/uzpy/cli.py` into this new function.
    2.  Remove all `console.print` and `rich.table` calls. The pipeline should only perform logic, not UI.
    3.  Use `loguru.logger` for all informational, debug, or error messages.
    4.  The function should accept configuration parameters (`edit_path`, `ref_path`, etc.) instead of reading them from `self`.
    5.  The function should return the final `usage_results` dictionary so the CLI can use it for reporting.

---

### **Phase 4: Simplify and Refactor the CLI**

This phase slims down the CLI to be a thin wrapper around the new pipeline.

**Task 4.1: Remove Fluff from `cli.py`**
*   **File:** `src/uzpy/cli.py`
*   **Action:**
    1.  Remove the `from rich.console import Console` and `from rich.table import Table` imports.
    2.  Delete all `_show_*_summary` and `_show_*_config` methods. We will replace these with simple log messages.
    3.  Remove the `console` attribute and its instance.

**Task 4.2: Refactor `UzpyCLI.run` Method**
*   **File:** `src/uzpy/cli.py`
*   **Action:**
    1.  Delete the entire body of the `run` method.
    2.  Replace it with a call to the new pipeline function.
    3.  Add simple `logger.info` statements before and after the pipeline call to report progress.
*   **New `run` method implementation:**
    ```python
    # src/uzpy/cli.py

    # ... imports ...
    from uzpy.pipeline import run_analysis_and_modification
    
    class UzpyCLI:
        # ... __init__ ...

        def run(self, _dry_run: bool = False) -> None:
            # Configure logging
            logger.remove()
            level = "DEBUG" if self.verbose else "INFO"
            logger.add(sys.stderr, level=level, format="<level>{level: <8}</level> | {message}")

            # Validate paths
            edit_path = Path(self.edit)
            if not edit_path.exists():
                logger.error(f"Error: Edit path '{self.edit}' does not exist")
                return
            
            ref_path = Path(self.ref) if self.ref else edit_path
            if not ref_path.exists():
                logger.error(f"Error: Reference path '{self.ref}' does not exist")
                return

            logger.info(f"Starting uzpy analysis on '{edit_path}'...")
            if _dry_run:
                logger.info("DRY RUN MODE - no files will be modified.")

            try:
                usage_results = run_analysis_and_modification(
                    edit_path=edit_path,
                    ref_path=ref_path,
                    exclude_patterns=self.xclude_patterns,
                    dry_run=_dry_run,
                )
                
                # Simple summary report
                total_constructs = len(usage_results)
                constructs_with_refs = sum(1 for refs in usage_results.values() if refs)
                logger.info(f"Analysis complete. Found usages for {constructs_with_refs}/{total_constructs} constructs.")

            except Exception as e:
                logger.error(f"A critical error occurred: {e}")
                if self.verbose:
                    logger.exception("Error details:")

    # ... keep the `clean` method, it can be refactored similarly if desired but is out of scope for now.
    ```

---

### **Phase 5: Improve Analyzer Robustness and Consistency**

This is a critical phase to ensure the analyzers are consistent and handle errors well. The current implementation where `analyzer.find_usages` returns `list[Path]` is inconsistent. We will change it to return `list[Reference]`.

**Task 5.1: Update Analyzer `find_usages` Signatures**
*   **Files:** `src/uzpy/analyzer/rope_analyzer.py`, `src/uzpy/analyzer/jedi_analyzer.py`, `src/uzpy/analyzer/hybrid_analyzer.py`
*   **Action:** Change the return type annotation for all `find_usages` methods from `-> list[Path]` to `-> list[Reference]`.

**Task 5.2: Refactor `rope_analyzer.find_usages`**
*   **File:** `src/uzpy/analyzer/rope_analyzer.py`
*   **Action:** Modify the `find_usages` method to create and return `Reference` objects.
*   **Implementation:**
    *   Inside the `for occurrence in occurrences:` loop:
    *   Instead of just adding the file path to a set, create a `Reference` object.
    *   The `rope.contrib.findit.Occurrence` object has a `lineno` attribute. Use it.
    *   You can extract a context snippet from the `occurrence.resource.read()`.
    *   **Example Code:**
        ```python
        # Inside the loop in rope_analyzer.py
        occurrence_file = Path(self.root_path) / occurrence.resource.path
        if any(...): # your existing check
            # Create a Reference object instead of just the path
            ref = Reference(
                file_path=occurrence_file,
                line_number=occurrence.lineno,
                # context can be added here if desired, but is optional for now
            )
            usage_references.add(ref) # change usage_files to usage_references
        ```

**Task 5.3: Refactor `pipeline.py` to use new analyzer output**
*   **File:** `src/uzpy/pipeline.py`
*   **Action:** The logic that converts file paths to `Reference` objects is now redundant. Remove it.
*   **Implementation:**
    ```python
    # Inside the loop in pipeline.py
    # OLD CODE (to be removed):
    # usage_files = analyzer.find_usages(construct, ref_files)
    # references = [Reference(file_path=file_path, line_number=1) for file_path in usage_files]
    # usage_results[construct] = references
    
    # NEW CODE:
    references = analyzer.find_usages(construct, ref_files)
    usage_results[construct] = references
    ```

**Task 5.4: Enhance Graceful Failure in Parsers and Analyzers**
*   **Files:** `tree_sitter_parser.py`, `rope_analyzer.py`, `jedi_analyzer.py`
*   **Action:** Review all `try...except` blocks.
    1.  Ensure that when a specific file fails to parse (e.g., `UnicodeDecodeError`, `tree_sitter` error), the process logs a warning and continues to the next file, rather than stopping the entire run. The current implementation is already good, but double-check this behavior.
    2.  Ensure that when analysis for a *single construct* fails, it logs a warning and continues to the next construct.

---

### **6. Post-Refactoring Checklist**

1.  **Run all tests:** Execute `python -m pytest` and ensure all tests pass.
2.  **Run linter/formatter:** Execute `ruff format .` and `ruff check --fix .` to ensure code quality.
3.  **Perform manual End-to-End test (Dry Run):**
    *   Run `python -m uzpy --edit src/ --dry-run --verbose` on its own codebase.
    *   Verify that the log output is clean and shows the tool discovering, parsing, and analyzing constructs correctly.
4.  **Perform manual End-to-End test (Actual Run):**
    *   Create a small, temporary test project or use a copy of a safe project.
    *   Run `python -m uzpy --edit .` within that project.
    *   Inspect the modified files to confirm that "Used in:" sections were added correctly and that code formatting was preserved.
5.  **Test the `clean` command:**
    *   Run `python -m uzpy clean` on the project you modified in the previous step.
    *   Verify that the "Used in:" sections are removed correctly.

# Task

Analyze the codebase of `uzpy`. 

Prepare a refactoring plan that will: 

- remove fluff: keep only code that's relevant to the core functionality, remove "decorational" code like custom fancy logging etc. 
- reduce the cognitive load
- itemize the code so that the functions, classes, modules are focused on a single task, and are well-structured
- ensure that the actual core functionality remains and does not break
- ensure that the code fails gracefully on files that don't comply

Make the plan very very specific, like a detailed spec for a junior dev who will actually perform the refactoring. 

Write the plan in a file called `PLAN.md`. 