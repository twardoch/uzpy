#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["fire", "rich", "loguru", "pathlib"]
# ///
# this_file: src/uzpy/cli.py

"""
Command-line interface for the uzpy tool.

This module handles argument parsing and provides the main entry point for the CLI.
Uses Fire for automatic CLI generation and Rich for beautiful terminal output.
"""

import sys
from pathlib import Path
from typing import List, Optional

import fire
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from uzpy.discovery import discover_files
from uzpy.parser import TreeSitterParser

console = Console()


class UzpyCLI:
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
        ref: str | None = None,
        verbose: bool = False,
        dry_run: bool = False,
        include_methods: bool = True,
        include_classes: bool = True,
        include_functions: bool = True,
        exclude_patterns: str | None = None,
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
        logger.add(
            sys.stderr, level=level, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}"
        )

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

        # Discover files
        try:
            exclude_list = exclude_patterns.split(",") if exclude_patterns else None
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

        logger.info("Starting uzpy analysis...")

        if dry_run:
            logger.info("DRY RUN MODE - no files will be modified")

        # TODO: Continue with reference finding and modification
        console.print("[yellow]Analyzer implementation in progress...[/yellow]")

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

    def _show_discovery_summary(self, edit_files: list[Path], ref_files: list[Path]) -> None:
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

    def _show_parsing_summary(self, constructs: list) -> None:
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
            with_docs = sum(1 for c in constructs if c.type.value == construct_type and c.docstring)

            table.add_row(construct_type.title(), str(count), f"{with_docs}/{count}" if count > 0 else "0/0")

        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{len(constructs)}[/bold]",
            f"[bold]{sum(1 for c in constructs if c.docstring)}/{len(constructs)}[/bold]",
        )

        console.print(table)
        console.print()


def cli() -> None:
    cli = UzpyCLI()
    """Main entry point for the CLI."""
    fire.Fire(cli.run)
