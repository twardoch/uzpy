# this_file: src/uzpy/analyzer/ruff_analyzer.py

"""
Ruff-based analyzer for fast basic usage detection.

This module provides a high-performance analyzer that uses Ruff's Rust-based
AST analysis for basic usage detection. While not as comprehensive as Rope
or Jedi, it's significantly faster for common use cases.
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Union

from loguru import logger

from uzpy.types import Construct, Reference


class RuffAnalyzer:
    """
    Fast analyzer using Ruff for basic usage detection.

    This analyzer leverages Ruff's speed for quick initial analysis,
    particularly useful for finding imports and basic function calls.
    It's designed to be used as a first pass before more comprehensive
    analyzers.
    """

    def __init__(self, project_root: Path, exclude_patterns: list[str] | None = None):
        """
        Initialize Ruff analyzer.

        Args:
            project_root: Root directory of the project
            exclude_patterns: Patterns to exclude from analysis (not used by Ruff directly)
        """
        self.project_root = project_root
        self.exclude_patterns = exclude_patterns or []

        # Check if ruff is available
        try:
            result = subprocess.run(["ruff", "--version"], capture_output=True, text=True, check=False)
            logger.debug(f"Using {result.stdout.strip()}")
        except FileNotFoundError:
            logger.warning("Ruff not found in PATH, falling back to python -m ruff")
            self.ruff_cmd = ["python", "-m", "ruff"]
        else:
            self.ruff_cmd = ["ruff"]

    def find_usages(self, construct: Construct, reference_files: list[Path]) -> list[Reference]:
        """
        Find basic usages of a construct using Ruff's analysis.

        This method uses Ruff to quickly identify potential usages through
        import analysis and basic pattern matching. It's faster but less
        comprehensive than semantic analyzers.

        Args:
            construct: The construct to find usages for
            reference_files: List of files to search in

        Returns:
            List of references to the construct
        """
        references = []

        # For imports, we can use Ruff's unused import detection
        if construct.name in self._get_unused_imports(reference_files):
            # If it's unused, there are no references
            return references

        # For each file, check if it imports or uses the construct
        for ref_file in reference_files:
            if self._file_uses_construct(ref_file, construct):
                # Ruff doesn't provide exact line numbers for usage,
                # so we create a file-level reference
                references.append(
                    Reference(
                        file_path=ref_file,
                        line_number=0,  # Unknown line number
                        column=0,
                        context=f"File imports or uses {construct.name}",
                    )
                )

        return references

    def _get_unused_imports(self, files: list[Path]) -> set[str]:
        """
        Get list of unused imports across files using Ruff.

        Args:
            files: List of files to analyze

        Returns:
            Set of unused import names
        """
        unused_imports = set()

        # Run Ruff with F401 (unused imports) check
        for file_batch in self._batch_files(files, 50):  # Process in batches
            cmd = (
                self.ruff_cmd
                + [
                    "check",
                    "--select=F401",  # Only unused imports
                    "--output-format=json",
                    "--no-cache",  # Avoid cache issues
                ]
                + [str(f) for f in file_batch]
            )

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if result.stdout:
                    violations = json.loads(result.stdout)
                    for violation in violations:
                        if violation.get("code") == "F401":
                            # Extract import name from message
                            msg = violation.get("message", "")
                            if "imported but unused" in msg:
                                # Parse import name from message like "'foo' imported but unused"
                                parts = msg.split("'")
                                if len(parts) >= 2:
                                    unused_imports.add(parts[1])
            except (subprocess.SubprocessError, json.JSONDecodeError) as e:
                logger.debug(f"Ruff analysis failed for batch: {e}")

        return unused_imports

    def _file_uses_construct(self, file_path: Path, construct: Construct) -> bool:
        """
        Quick check if a file potentially uses a construct.

        This is a fast heuristic check using grep-like functionality.

        Args:
            file_path: File to check
            construct: Construct to look for

        Returns:
            True if the file likely uses the construct
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Quick checks for different construct types
            checks = [
                f"import {construct.name}",
                f"from {construct.module_path} import {construct.name}",
                f"{construct.name}(",  # Function/class call
                f"{construct.name}.",  # Attribute access
                f"class .* {construct.name}",  # Inheritance
            ]

            return any(pattern in content for pattern in checks)

        except Exception as e:
            logger.debug(f"Failed to read {file_path}: {e}")
            return False

    def _batch_files(self, files: list[Path], batch_size: int) -> list[list[Path]]:
        """
        Split files into batches for processing.

        Args:
            files: List of files
            batch_size: Size of each batch

        Returns:
            List of file batches
        """
        return [files[i : i + batch_size] for i in range(0, len(files), batch_size)]
