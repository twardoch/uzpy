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

from uzpy.discovery import discover_files, FileDiscovery
from uzpy.parser import TreeSitterParser, Reference
from uzpy.analyzer import HybridAnalyzer
from uzpy.modifier import LibCSTModifier

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
        methods_include: bool = True,
        classes_include: bool = True,
        functions_include: bool = True,
        xclude_patterns: str | None = None,
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
            xclude_patterns: Comma-separated glob patterns to exclude from analysis
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
            exclude_list = xclude_patterns.split(",") if xclude_patterns else None
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

        # Initialize analyzer for reference finding
        try:
            analyzer = HybridAnalyzer(ref_path)
            logger.info("Initialized hybrid analyzer")
        except Exception as e:
            console.print(f"[red]Failed to initialize analyzer: {e}[/red]")
            if verbose:
                logger.exception("Analyzer initialization failed")
            return

        # Find references for each construct
        console.print("[blue]Finding references...[/blue]")
        usage_results = {}
        total_constructs = len(all_constructs)
        
        # Get all reference files for analysis
        file_discovery = FileDiscovery()
        ref_files = list(file_discovery.find_python_files(ref_path))
        
        for i, construct in enumerate(all_constructs, 1):
            if verbose:
                console.print(f"[dim]Analyzing {construct.name} ({i}/{total_constructs})[/dim]")
            
            try:
                # Find where this construct is used
                usage_files = analyzer.find_usages(construct, ref_files)
                
                # Convert file paths to Reference objects for consistency
                references = [
                    Reference(file_path=file_path, line_number=1)  
                    for file_path in usage_files
                ]
                usage_results[construct] = references
                
                if verbose and references:
                    console.print(f"[green]  Found {len(references)} references in {len(usage_files)} files[/green]")
                elif verbose:
                    console.print(f"[yellow]  No references found[/yellow]")
                    
            except Exception as e:
                console.print(f"[red]Error analyzing {construct.name}: {e}[/red]")
                if verbose:
                    logger.exception(f"Failed to analyze construct {construct.name}")
                usage_results[construct] = []

        # Show analysis summary
        self._show_analysis_summary(usage_results)

        if not dry_run:
            # Apply docstring modifications
            console.print("[blue]Updating docstrings...[/blue]")
            try:
                modifier = LibCSTModifier(edit_path.parent if edit_path.is_file() else edit_path)
                modification_results = modifier.modify_files(usage_results)
                
                # Show modification summary
                successful_modifications = sum(1 for success in modification_results.values() if success)
                total_files = len(modification_results)
                
                if successful_modifications > 0:
                    console.print(f"[green]Successfully updated {successful_modifications}/{total_files} files[/green]")
                else:
                    console.print("[yellow]No files needed modification[/yellow]")
                    
                if verbose:
                    for file_path, success in modification_results.items():
                        status = "[green]✓[/green]" if success else "[red]✗[/red]"
                        console.print(f"  {status} {file_path}")
                        
            except Exception as e:
                console.print(f"[red]Failed to apply modifications: {e}[/red]")
                if verbose:
                    logger.exception("Modification failed")
        else:
            console.print("[green]Analysis complete - dry run mode[/green]")

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

    def _show_analysis_summary(self, usage_results: dict) -> None:
        """Display summary of reference analysis results."""
        if not usage_results:
            console.print("[yellow]No analysis results to display[/yellow]")
            return

        # Create summary statistics
        total_constructs = len(usage_results)
        constructs_with_refs = sum(1 for refs in usage_results.values() if refs)
        total_references = sum(len(refs) for refs in usage_results.values())
        
        # Count by construct type
        from collections import defaultdict
        type_stats = defaultdict(lambda: {"total": 0, "with_refs": 0, "ref_count": 0})
        
        for construct, references in usage_results.items():
            construct_type = construct.type.value
            type_stats[construct_type]["total"] += 1
            if references:
                type_stats[construct_type]["with_refs"] += 1
                type_stats[construct_type]["ref_count"] += len(references)

        # Display summary table
        table = Table(title="Reference Analysis Summary", show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Total", style="blue", justify="right")
        table.add_column("With References", style="green", justify="right")
        table.add_column("Total References", style="yellow", justify="right")

        for construct_type in ["module", "class", "function", "method"]:
            if construct_type in type_stats:
                stats = type_stats[construct_type]
                table.add_row(
                    construct_type.title(),
                    str(stats["total"]),
                    str(stats["with_refs"]),
                    str(stats["ref_count"])
                )

        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{total_constructs}[/bold]",
            f"[bold]{constructs_with_refs}[/bold]",
            f"[bold]{total_references}[/bold]"
        )

        console.print(table)
        
        # Show detailed results for constructs with many references
        high_usage_constructs = [
            (construct, refs) for construct, refs in usage_results.items() 
            if len(refs) >= 3
        ]
        
        if high_usage_constructs:
            console.print()
            console.print("[bold blue]Most Referenced Constructs:[/bold blue]")
            
            detail_table = Table(show_header=True, header_style="bold cyan")
            detail_table.add_column("Construct", style="green")
            detail_table.add_column("Type", style="blue")
            detail_table.add_column("References", style="yellow", justify="right")
            detail_table.add_column("Files", style="magenta", justify="right")
            
            # Sort by reference count, show top 10
            high_usage_constructs.sort(key=lambda x: len(x[1]), reverse=True)
            for construct, refs in high_usage_constructs[:10]:
                ref_files = {ref.file_path for ref in refs}
                detail_table.add_row(
                    construct.name,
                    construct.type.value,
                    str(len(refs)),
                    str(len(ref_files))
                )
            
            console.print(detail_table)
        
        console.print()


def cli() -> None:
    cli = UzpyCLI()
    """Main entry point for the CLI."""
    fire.Fire(cli.run)
