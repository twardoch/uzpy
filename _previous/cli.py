#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["fire", "loguru", "pathlib"]
# ///
# this_file: src/uzpy/cli.py

"""
Command-line interface for the uzpy tool.

This module handles argument parsing and provides the main entry point for the CLI.
Uses Fire for automatic CLI generation and simple logger for output.

Used in:
- cli.py
"""

import sys
from pathlib import Path
from typing import Optional, Union

import fire
from loguru import logger

from uzpy.modifier import LibCSTCleaner
from uzpy.pipeline import run_analysis_and_modification


class UzpyCLI:
    """
    Command-line interface for the uzpy tool.

    This tool analyzes Python codebases to find where constructs (functions, classes,
    methods) are used and automatically updates their docstrings with usage information.

    Used in:
    - cli.py
    - tests/test_cli.py
    """

    def __init__(
        self,
        edit: str | Path | None = None,
        ref: str | Path | None = None,
        xclude_patterns: str | list | None = None,
        methods_include: bool = True,
        classes_include: bool = True,
        functions_include: bool = True,
        verbose: bool = False,
    ) -> None:
        """Initialize the CLI with default settings.

        Args:
            edit: Path to file or directory containing code to analyze and modify
            ref: Path to reference codebase to search for usages (defaults to edit path)
            verbose: Enable verbose logging output
            include_methods: Include method definitions in analysis
            include_classes: Include class definitions in analysis
            include_functions: Include function definitions in analysis
            xclude_patterns: Comma-separated glob patterns to exclude from analysis

        Used in:
        - cli.py
        """
        self.edit = Path(edit) if edit else Path.cwd()
        self.ref = Path(ref) if ref else self.edit
        self.xclude_patterns = None
        if hasattr(xclude_patterns, "split"):
            self.xclude_patterns = xclude_patterns.split(",")
        elif isinstance(xclude_patterns, list):
            self.xclude_patterns = xclude_patterns
        elif xclude_patterns:
            self.xclude_patterns = [xclude_patterns]

        self.methods_include = bool(methods_include)
        self.classes_include = bool(classes_include)
        self.functions_include = bool(functions_include)
        self.verbose = bool(verbose)

    def test(self) -> None:
        """Run analysis in dry-run mode for testing."""
        self.run(_dry_run=True)

    def run(self, _dry_run: bool = False) -> None:
        """
        Analyze codebase and update docstrings with usage information.

        Used in:
        - cli.py
        - tests/test_cli.py
        """
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

    def clean(self, _dry_run: bool = False) -> None:
        """
        Clean all 'Used in:' sections from docstrings in the codebase.

        Args:
            _dry_run: Show what files would be cleaned without modifying them

        """
        # Configure logging
        logger.remove()
        level = "DEBUG" if self.verbose else "INFO"
        logger.add(sys.stderr, level=level, format="<level>{level: <8}</level> | {message}")

        # Validate paths
        edit_path = Path(self.edit)
        if not edit_path.exists():
            logger.error(f"Error: Edit path '{self.edit}' does not exist")
            return

        logger.info(f"Starting uzpy cleaning on '{edit_path}'...")

        if _dry_run:
            logger.info("DRY RUN MODE - no files will be modified")

        # Discover files to clean
        try:
            from uzpy.discovery import FileDiscovery

            exclude_list = self.xclude_patterns
            file_discovery = FileDiscovery(exclude_list)
            files_to_clean = list(file_discovery.find_python_files(edit_path))
        except Exception as e:
            logger.error(f"Error discovering files: {e}")
            return

        if not files_to_clean:
            logger.warning("No Python files found to clean")
            return

        logger.info(f"Found {len(files_to_clean)} Python files to clean")

        if not _dry_run:
            # Apply cleaning
            logger.info("Cleaning docstrings...")
            try:
                cleaner = LibCSTCleaner(edit_path.parent if edit_path.is_file() else edit_path)
                clean_results = cleaner.clean_files(files_to_clean)

                # Show cleaning summary
                successful_cleanings = sum(1 for success in clean_results.values() if success)
                total_files = len(clean_results)

                if successful_cleanings > 0:
                    logger.info(f"Successfully cleaned {successful_cleanings}/{total_files} files")
                else:
                    logger.info("No 'Used in:' sections found to clean")

            except Exception as e:
                logger.error(f"Failed to apply cleaning: {e}")
                if self.verbose:
                    logger.exception("Cleaning failed")
        else:
            logger.info("Cleaning analysis complete - dry run mode")
            logger.info(f"Would clean {len(files_to_clean)} Python files")


def cli() -> None:
    """Main entry point for the CLI.

    Used in:
    - __main__.py
    - src/uzpy/__main__.py
    - uzpy/__main__.py
    """
    import os

    # Check if modern CLI is requested via environment variable
    if os.environ.get("UZPY_MODERN_CLI", "").lower() in ("1", "true", "yes"):
        from uzpy.cli_modern import cli as modern_cli

        modern_cli()
    else:
        # Use traditional Fire CLI for backwards compatibility
        fire.Fire(UzpyCLI)
