#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["typer", "rich", "pydantic-settings", "loguru", "pathlib"]
# ///
# this_file: src/uzpy/cli_modern.py

"""
Modern command-line interface for the uzpy tool using Typer and Rich.

This module provides an enhanced CLI experience with better help text,
progress tracking, and configuration management.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from uzpy.modifier import LibCSTCleaner
from uzpy.pipeline import run_analysis_and_modification
from uzpy.watcher import watch_directory

# Initialize Typer app and Rich console
app = typer.Typer(
    name="uzpy",
    help="🔍 Modern Python usage tracker - Find where your code is used and update docstrings automatically",
    add_completion=True,
    rich_markup_mode="rich",
)
console = Console()


class UzpySettings(BaseSettings):
    """Configuration settings for uzpy with environment variable support."""
    
    edit_path: Path = Field(default_factory=Path.cwd, description="Path to analyze and edit")
    ref_path: Optional[Path] = Field(None, description="Reference path for usage search")
    exclude_patterns: list[str] = Field(default_factory=list, description="Patterns to exclude")
    cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".uzpy" / "cache",
        description="Cache directory"
    )
    parallel_workers: int = Field(4, description="Number of parallel workers")
    verbose: bool = Field(False, description="Enable verbose logging")
    
    class Config:
        env_prefix = "UZPY_"
        env_file = ".uzpy.env"


def configure_logging(verbose: bool) -> None:
    """Configure logging with appropriate level and format."""
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        level=level,
        format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> | {message}",
        colorize=True,
    )


@app.command()
def run(
    edit: Path = typer.Argument(
        Path.cwd(),
        help="Path to file or directory to analyze and modify",
        exists=True,
    ),
    ref: Optional[Path] = typer.Option(
        None,
        "--ref", "-r",
        help="Reference path to search for usages (defaults to edit path)",
        exists=True,
    ),
    exclude: Optional[list[str]] = typer.Option(
        None,
        "--exclude", "-e",
        help="Glob patterns to exclude from analysis",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-n",
        help="Show what would be changed without modifying files",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose logging",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="Path to configuration file",
        exists=True,
    ),
    workers: int = typer.Option(
        4,
        "--workers", "-j",
        help="Number of parallel workers for analysis",
        min=1,
        max=32,
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable caching for this run",
    ),
):
    """
    🚀 Analyze Python code and update docstrings with usage information.
    
    This command finds where your functions, classes, and methods are used
    across your codebase and automatically updates their docstrings with
    'Used in:' sections.
    """
    # Load settings
    settings = UzpySettings(_env_file=config) if config else UzpySettings()
    
    # Override with CLI arguments
    if edit != Path.cwd():
        settings.edit_path = edit
    if ref:
        settings.ref_path = ref
    if exclude:
        settings.exclude_patterns = exclude
    if verbose:
        settings.verbose = verbose
    settings.parallel_workers = workers
    
    configure_logging(settings.verbose)
    
    # Display configuration
    console.print("\n[bold blue]uzpy[/bold blue] - Modern Python Usage Tracker")
    console.print(f"Edit path: [cyan]{settings.edit_path}[/cyan]")
    console.print(f"Reference path: [cyan]{settings.ref_path or settings.edit_path}[/cyan]")
    if settings.exclude_patterns:
        console.print(f"Exclude patterns: [yellow]{', '.join(settings.exclude_patterns)}[/yellow]")
    console.print(f"Workers: [green]{settings.parallel_workers}[/green]")
    console.print(f"Cache: [{'red]disabled' if no_cache else 'green]enabled'}[/]")
    
    if dry_run:
        console.print("\n[yellow]DRY RUN MODE - No files will be modified[/yellow]")
    
    console.print()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing codebase...", total=None)
            
            usage_results = run_analysis_and_modification(
                edit_path=settings.edit_path,
                ref_path=settings.ref_path or settings.edit_path,
                exclude_patterns=settings.exclude_patterns,
                dry_run=dry_run,
            )
            
            progress.update(task, completed=True)
        
        # Display results summary
        display_results_summary(usage_results)
        
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if settings.verbose:
            logger.exception("Detailed error:")
        raise typer.Exit(1)


@app.command()
def clean(
    path: Path = typer.Argument(
        Path.cwd(),
        help="Path to clean 'Used in:' sections from",
        exists=True,
    ),
    exclude: Optional[list[str]] = typer.Option(
        None,
        "--exclude", "-e",
        help="Glob patterns to exclude from cleaning",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-n",
        help="Show what would be cleaned without modifying files",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose logging",
    ),
):
    """
    🧹 Clean all 'Used in:' sections from docstrings.
    
    This command removes all automatically generated usage information
    from docstrings in the specified path.
    """
    configure_logging(verbose)
    
    console.print("\n[bold blue]uzpy clean[/bold blue] - Remove usage information")
    console.print(f"Path: [cyan]{path}[/cyan]")
    if exclude:
        console.print(f"Exclude patterns: [yellow]{', '.join(exclude)}[/yellow]")
    
    if dry_run:
        console.print("\n[yellow]DRY RUN MODE - No files will be modified[/yellow]")
    
    console.print()
    
    try:
        # Discover files
        from uzpy.discovery import FileDiscovery
        
        file_discovery = FileDiscovery(exclude)
        files_to_clean = list(file_discovery.find_python_files(path))
        
        if not files_to_clean:
            console.print("[yellow]No Python files found to clean[/yellow]")
            return
        
        console.print(f"Found [green]{len(files_to_clean)}[/green] Python files")
        
        if not dry_run:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Cleaning docstrings...", total=None)
                
                cleaner = LibCSTCleaner(path.parent if path.is_file() else path)
                clean_results = cleaner.clean_files(files_to_clean)
                
                progress.update(task, completed=True)
            
            # Display results
            successful = sum(1 for success in clean_results.values() if success)
            if successful > 0:
                console.print(f"\n✅ Successfully cleaned [green]{successful}[/green] files")
            else:
                console.print("\n[yellow]No 'Used in:' sections found to clean[/yellow]")
        else:
            console.print(f"\n[yellow]Would clean {len(files_to_clean)} files in dry-run mode[/yellow]")
            
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if verbose:
            logger.exception("Detailed error:")
        raise typer.Exit(1)


@app.command()
def cache(
    action: str = typer.Argument(
        ...,
        help="Cache action: 'clear' to clear cache, 'stats' to show statistics",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose logging",
    ),
):
    """
    💾 Manage the analysis cache.
    
    The cache stores parsed constructs and analysis results to speed up
    subsequent runs.
    """
    configure_logging(verbose)
    
    settings = UzpySettings()
    
    if action == "clear":
        console.print("\n[bold blue]Clearing cache...[/bold blue]")
        try:
            import shutil
            if settings.cache_dir.exists():
                shutil.rmtree(settings.cache_dir)
                console.print(f"✅ Cache cleared at [cyan]{settings.cache_dir}[/cyan]")
            else:
                console.print("[yellow]No cache found[/yellow]")
        except Exception as e:
            console.print(f"[red]Error clearing cache:[/red] {e}")
            raise typer.Exit(1)
            
    elif action == "stats":
        console.print("\n[bold blue]Cache Statistics[/bold blue]")
        try:
            from uzpy.analyzer.cached_analyzer import CachedAnalyzer
            from uzpy.analyzer.hybrid_analyzer import HybridAnalyzer
            
            # Create a cached analyzer to get stats
            analyzer = CachedAnalyzer(
                HybridAnalyzer(Path.cwd()),
                cache_dir=settings.cache_dir
            )
            stats = analyzer.get_cache_stats()
            
            # Display stats in a table
            table = Table(title="Cache Information")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Cache Directory", str(settings.cache_dir))
            table.add_row("Total Entries", str(stats.get("size", 0)))
            table.add_row("Cache Size", f"{stats.get('volume', 0) / 1024 / 1024:.2f} MB")
            table.add_row("Cache Hits", str(stats.get("hits", 0)))
            table.add_row("Cache Misses", str(stats.get("misses", 0)))
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error getting cache stats:[/red] {e}")
            raise typer.Exit(1)
    else:
        console.print(f"[red]Unknown cache action:[/red] {action}")
        console.print("Valid actions: 'clear', 'stats'")
        raise typer.Exit(1)


def display_results_summary(usage_results: dict) -> None:
    """Display a formatted summary of analysis results."""
    total_constructs = len(usage_results)
    constructs_with_refs = sum(1 for refs in usage_results.values() if refs)
    total_references = sum(len(refs) for refs in usage_results.values())
    
    # Create summary table
    table = Table(title="Analysis Summary")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    table.add_row("Total Constructs", str(total_constructs))
    table.add_row("Constructs with Usages", str(constructs_with_refs))
    table.add_row("Total References Found", str(total_references))
    
    if total_constructs > 0:
        coverage = (constructs_with_refs / total_constructs) * 100
        table.add_row("Usage Coverage", f"{coverage:.1f}%")
    
    console.print("\n")
    console.print(table)
    
    # Show top used constructs
    if constructs_with_refs > 0:
        sorted_constructs = sorted(
            usage_results.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:5]
        
        if sorted_constructs:
            top_table = Table(title="\nTop Used Constructs")
            top_table.add_column("Construct", style="cyan")
            top_table.add_column("Type", style="yellow")
            top_table.add_column("References", style="green")
            
            for construct, refs in sorted_constructs:
                if refs:  # Only show constructs with references
                    top_table.add_row(
                        construct.name,
                        construct.type.value,
                        str(len(refs))
                    )
            
            console.print(top_table)


@app.command()
def watch(
    edit: Path = typer.Argument(
        Path.cwd(),
        help="Path to watch for changes",
        exists=True,
    ),
    ref: Optional[Path] = typer.Option(
        None,
        "--ref", "-r",
        help="Reference path to search for usages (defaults to edit path)",
        exists=True,
    ),
    exclude: Optional[list[str]] = typer.Option(
        None,
        "--exclude", "-e",
        help="Glob patterns to exclude from watching",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose logging",
    ),
):
    """
    👁️ Watch for file changes and automatically re-run analysis.
    
    This command monitors Python files for changes and automatically
    updates docstrings whenever a file is modified.
    """
    configure_logging(verbose)
    
    settings = UzpySettings()
    settings.edit_path = edit
    settings.ref_path = ref or edit
    if exclude:
        settings.exclude_patterns = exclude
    
    try:
        watch_directory(
            edit_path=settings.edit_path,
            ref_path=settings.ref_path,
            exclude_patterns=settings.exclude_patterns,
        )
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if verbose:
            logger.exception("Detailed error:")
        raise typer.Exit(1)


def cli() -> None:
    """Main entry point for the modern CLI."""
    app()


if __name__ == "__main__":
    cli()