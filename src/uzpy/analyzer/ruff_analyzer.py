# this_file: src/uzpy/analyzer/ruff_analyzer.py

"""
Ruff-based analyzer for uzpy.

This module provides a high-performance analyzer that uses Ruff's Rust-based
AST analysis for basic usage detection. While not as comprehensive as Rope
or Jedi, it's significantly faster for common use cases.

"""

import json
import subprocess
from pathlib import Path
from typing import Any

from loguru import logger

from uzpy.types import Construct, ConstructType, Reference


class RuffAnalyzer:
    """
    Fast analyzer using Ruff for basic usage detection.

    This analyzer leverages Ruff's speed for quick initial analysis,
    particularly useful for finding imports and basic function calls.
    It's designed to be used as a first pass before more comprehensive
    analyzers.

    Used in:
    - src/uzpy/analyzer/__init__.py
    - src/uzpy/analyzer/modern_hybrid_analyzer.py
    """

    def __init__(self, project_root: Path):
        """
        Initialize the RuffAnalyzer.

        Args:
            project_root: Root directory of the project
            exclude_patterns: Patterns to exclude from analysis (not used by Ruff directly)

        """
        # Handle case where project_root is a file instead of directory
        if project_root.is_file():
            self.project_root = project_root.parent
        else:
            self.project_root = project_root
        self.exclude_patterns = exclude_patterns or []

    def _run_ruff(self, target_path: Path, select_rules: str = "F401,F811") -> list[dict[str, Any]]:
        """
        Run Ruff as a subprocess and parse its JSON output.

        Args:
            target_path: The file or directory to analyze with Ruff.
            select_rules: Comma-separated list of Ruff rules to check.

        Returns:
            List of references to the construct

        Used in:
        - src/uzpy/analyzer/modern_hybrid_analyzer.py
        """
        try:
            # It's often better to run ruff on individual files if we're analyzing specific file contexts
            # or on the project root if we're looking for project-wide issues like F401.
            # For finding references *within* specific files (search_paths), running ruff per file might be needed.
            command = [
                "ruff",
                "check",
                "--select",
                select_rules,
                "--output-format",
                "json",
                "--force-exclude",  # Ensures .gitignore is respected but we can still target specific files
                str(target_path),
            ]
            logger.debug(f"Running Ruff command: {' '.join(command)}")
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.project_root,  # Run ruff from the project root
                check=False,  # Don't raise exception for non-zero exit code (ruff exits 1 if issues found)
            )

            if process.stderr:
                logger.warning(f"Ruff stderr for {target_path}:\n{process.stderr}")

            if process.stdout:
                try:
                    return json.loads(process.stdout)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Ruff JSON output for {target_path}: {e}\nOutput:\n{process.stdout}")
                    return []
            return []
        except FileNotFoundError:
            logger.error("Ruff command not found. Please ensure Ruff is installed and in PATH.")
            return []
        except Exception as e:
            logger.error(f"Error running Ruff for {target_path}: {e}")
            return []

    def find_usages(self, construct: Construct, search_paths: list[Path]) -> list[Reference]:
        """
        Uses Ruff to find potential indications of usage for a construct.
        This is an indirect way of finding references. For example, if a module
        is imported (no F401 for it in the importing file), it's "used".

        Args:
            construct: The construct to find usages for.
            search_paths: List of Python files to search within.

        Returns:
            Set of unused import names

        """
        logger.debug(f"RuffAnalyzer looking for usages of {construct.full_name} ({construct.type}).")
        references: list[Reference] = []

        # Ruff's F401 (unused import) can tell us if a module or name from a module is imported.
        # If F401 is *not* reported for `construct.name` in a file in `search_paths`,
        # it implies `construct.name` is used or at least imported. This is very indirect.

        # This approach is more about "is this construct potentially NOT unused in these files?"
        # rather than "find all specific usages".

        if construct.type == ConstructType.MODULE:
            # For a module construct, check if it's imported in search_paths files.
            # We'd look for absence of F401 related to this module.
            # This is complex to do accurately with just F401, as F401 applies to specific names.
            # A simpler proxy: if a file imports anything from this module's file without ruff complaining,
            # it's a potential usage.
            # This is a placeholder for a more robust strategy.
            logger.warning(
                "RuffAnalyzer's find_usages for Module constructs is highly experimental and may not be accurate."
            )
            # For now, returning empty as a reliable implementation is non-trivial with Ruff alone.
            return []

        # For functions, classes, methods:
        # Ruff doesn't directly find references. We might try to infer usage by seeing if ruff
        # *doesn't* complain about an import of this construct in the search_paths.
        # This is still very indirect. A more direct (but still limited) approach could be:
        # If we are looking for `my_function` from `my_module.py`:
        # In `another_file.py`:
        #   `from my_module import my_function` -> if no F401 for my_function, it's used.
        #   `import my_module; my_module.my_function()` -> harder to detect with ruff alone.

        # Given the limitations, this method will likely be a very rough heuristic or might
        # be better suited for tasks like "find potentially unused constructs".
        # For now, let's assume a very basic check: run ruff on each search_path file
        # and if the construct's name appears and Ruff doesn't flag it as part of an unused import,
        # consider it a potential reference. This is still not ideal.

        for file_path in search_paths:
            if not file_path.is_file():
                logger.warning(f"Skipping non-file path in search_paths: {file_path}")
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                # Simple text search for the construct name.
                # This is a very naive way and will have many false positives.
                if construct.name in content:
                    # This doesn't confirm usage, just presence.
                    # A true Ruff-based usage would need to parse Ruff's output more intelligently.
                    # For example, if 'from module import construct_name' exists and F401 is NOT raised
                    # for 'construct_name' at that line.

                    # To make this slightly more meaningful with Ruff:
                    # Check if the file *imports* the construct and Ruff doesn't flag that import as unused.
                    # This is still limited.

                    # Let's try to find if construct.name is part of an import statement.
                    # And then check ruff output for that file.

                    # This simplified version just adds a reference if the name is present.
                    # This is a placeholder for a more sophisticated Ruff-based analysis if feasible.
                    logger.debug(f"Construct name '{construct.name}' found in {file_path}. (Naive check)")

                    # A more ruff-centric (but still limited) approach:
                    # diagnostics = self._run_ruff(file_path, "F401") # Check for unused imports
                    # is_imported_and_used = True # Assume true, try to falsify
                    # for diag in diagnostics:
                    #     if construct.name in diag.get("message",""): # very rough
                    #         is_imported_and_used = False
                    #         break
                    # if is_imported_and_used:
                    #    references.append(Reference(file_path=file_path, line_number=1)) # Line number unknown

                    # For now, sticking to the PLAN's F401,F811 idea, though its application to "find_usages" is tricky.
                    # The current implementation is a placeholder.
                    # A full implementation would require parsing Ruff's output to identify
                    # specific lines where `construct.name` is imported and NOT flagged as F401,
                    # or where it's defined/redefined (F811) which isn't usage by others.

                    # Given the difficulty, returning an empty list to signify that RuffAnalyzer,
                    # in this configuration, is not a reliable reference finder.

            except Exception as e:
                logger.error(f"Error processing file {file_path} with RuffAnalyzer: {e}")

        if not references:
            logger.debug(
                f"RuffAnalyzer did not find direct usages for {construct.full_name}. This is expected due to Ruff's nature as a linter."
            )

        return references

        Returns:
            True if the file likely uses the construct

        """
        Analyze a batch of constructs.
        For Ruff, this will call find_usages for each construct as batch processing
        with Ruff for this specific task (finding references) isn't straightforward.
        """
        results = {}
        for construct in constructs:
            results[construct] = self.find_usages(construct, search_paths)
        return results

    def __del__(self) -> None:
        logger.debug("RuffAnalyzer instance being deleted.")

        Returns:
            List of file batches

        """
        return [files[i : i + batch_size] for i in range(0, len(files), batch_size)]
