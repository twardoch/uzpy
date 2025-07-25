# this_file: src/uzpy/cli_modern.py

"""
Modern Command-Line Interface for uzpy using Typer.

This module provides a new CLI experience for uzpy, leveraging Typer for
command parsing, Rich for enhanced terminal output, and Pydantic-settings
for configuration management.
"""

import sys
from pathlib import Path
# from typing import List, Optional # Removed by autoflake/manual cleanup

import typer
from loguru import logger
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console

from uzpy.analyzer import (
    CachedAnalyzer,
    # For fallback or direct use:
    HybridAnalyzer,
    JediAnalyzer,
    ModernHybridAnalyzer,
    ParallelAnalyzer,
    RopeAnalyzer,
    # TreeSitterParser, # Removed from here, will be imported from uzpy.parser
)
from uzpy.discovery import FileDiscovery
from uzpy.modifier import LibCSTCleaner
from uzpy.parser import TreeSitterParser, CachedParser  # Ensure CachedParser is also imported

# Assuming other necessary uzpy components will be imported as needed
from uzpy.pipeline import run_analysis_and_modification

# Placeholder for watcher, will be implemented in a later step
# from uzpy.watcher import UzpyWatcher


# --- Settings Model ---
class UzpySettings(BaseSettings):
    """Configuration settings for uzpy with environment variable support.

"""


    class Config:
        """    """
        env_prefix = "UZPY_"
        env_file = ".uzpy.env"

# --- Helper Functions ---
def setup_logging(log_level: str, verbose: bool):
    """Configures Loguru logger based on verbosity and level."""
    if verbose and log_level == "INFO":  # If verbose is true, default to DEBUG
        final_log_level = "DEBUG"
    else:
        final_log_level = log_level.upper()

def configure_logging(verbose: bool) -> None:
    """Configure logging with appropriate level and format.

"""
    logger.remove()
    logger.add(
        sys.stderr,
        level=final_log_level,
        format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    logger.info(f"Logging initialized at level: {final_log_level}")


def get_settings(config_file: Path | None = None) -> UzpySettings:
    """Loads settings, optionally from a specified config file."""
    env_file_path = config_file if config_file else UzpySettings.model_config.get("env_file")
    try:
        settings = UzpySettings(_env_file=env_file_path)
        logger.debug(f"Loaded settings. Edit path: {settings.edit_path}, Analyzer: {settings.analyzer_type}")
        logger.debug(
            f"Effective .env path: {env_file_path if Path(env_file_path).exists() else 'Not found or default'}"
        )
        return settings
    except ValidationError as e:
        console.print("[bold red]Error loading configuration:[/bold red]")
        console.print(e)
        raise typer.Exit(code=1)


def _get_analyzer_stack(settings: UzpySettings):
    """Constructs the analyzer stack based on settings."""
    # Base parser
    parser = TreeSitterParser()
    if settings.use_cache:
        parser = CachedParser(parser, settings.cache_dir, settings.parser_cache_name)
        logger.debug("Parser caching enabled.")

    # Base analyzer
    if settings.analyzer_type == "modern_hybrid":
        analyzer = ModernHybridAnalyzer(
            project_root=settings.get_effective_ref_path().parent,  # Assuming project root is parent of ref_path
            config={
                "use_ruff": settings.mha_use_ruff,
                "use_astgrep": settings.mha_use_astgrep,
                "use_pyright": settings.mha_use_pyright,
                "short_circuit_threshold": settings.mha_short_circuit_threshold,
            },
        )
    elif settings.analyzer_type == "hybrid":
        analyzer = HybridAnalyzer(
            project_path=settings.get_effective_ref_path().parent, exclude_patterns=settings.exclude_patterns
        )
    elif settings.analyzer_type == "rope":
        analyzer = RopeAnalyzer(
            root_path=settings.get_effective_ref_path().parent, exclude_patterns=settings.exclude_patterns
        )
    elif settings.analyzer_type == "jedi":
        analyzer = JediAnalyzer(project_path=settings.get_effective_ref_path().parent)
    else:
        logger.error(f"Unknown analyzer type: {settings.analyzer_type}. Defaulting to Hybrid.")
        analyzer = HybridAnalyzer(
            project_path=settings.get_effective_ref_path().parent, exclude_patterns=settings.exclude_patterns
        )
    logger.debug(f"Using base analyzer: {type(analyzer).__name__}")

    if settings.use_cache:
        analyzer = CachedAnalyzer(analyzer, settings.cache_dir, settings.analyzer_cache_name)
        logger.debug("Analyzer caching enabled.")

    if settings.use_parallel and settings.num_workers != 0:  # num_workers=0 could mean disable parallel
        analyzer = ParallelAnalyzer(analyzer, num_workers=settings.num_workers)
        logger.debug("Analyzer parallelism enabled.")

    return parser, analyzer


# --- Typer Commands ---


@app.callback()
def main_callback(
    ctx: typer.Context,
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to a custom .env configuration file.",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose DEBUG logging."),
    log_level: str = typer.Option(
        "INFO", "--log-level", help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."
    ),
):
    """
    🚀 Analyze Python code and update docstrings with usage information.

    This command finds where your functions, classes, and methods are used
    across your codebase and automatically updates their docstrings with
    'Used in:' sections.

    """
    settings = get_settings(config_file=config)
    # Override verbose and log_level from CLI if provided
    if verbose:  # CLI --verbose overrides .env
        settings.verbose = True
    if ctx.params.get("log_level") and ctx.params["log_level"] != "INFO":  # if log_level is explicitly set via CLI
        settings.log_level = ctx.params["log_level"]

    setup_logging(settings.log_level, settings.verbose)
    ctx.meta["settings"] = settings
    logger.debug("Typer context initialized with settings.")


@app.command()
def run(
    ctx: typer.Context,
    edit_path_override: Path | None = typer.Option(
        None, "--edit", "-e", help="Path to analyze/modify (overrides config).", resolve_path=True
    ),
    ref_path_override: Path | None = typer.Option(
        None, "--ref", "-r", help="Reference path for usage search (overrides config).", resolve_path=True
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show changes without modifying files."),
    safe_mode: bool = typer.Option(False, "--safe", help="Use safe modifier to prevent syntax corruption."),
):
    """
    Analyze codebase and update docstrings with usage information.
    """
    settings: UzpySettings = ctx.meta["settings"]

    # Override paths from CLI if provided
    current_edit_path = edit_path_override if edit_path_override else settings.edit_path
    current_ref_path = ref_path_override if ref_path_override else settings.get_effective_ref_path()

    if not current_edit_path.exists():
        console.print(f"[bold red]Error:[/bold red] Edit path '{current_edit_path}' does not exist.")
        raise typer.Exit(code=1)
    if not current_ref_path.exists():
        console.print(f"[bold red]Error:[/bold red] Reference path '{current_ref_path}' does not exist.")
        raise typer.Exit(code=1)

    console.print(f"Starting uzpy analysis on '[cyan]{current_edit_path}[/cyan]'...")
    if dry_run:
        console.print("[yellow]DRY RUN MODE[/yellow] - no files will be modified.")

    _parser, analyzer = _get_analyzer_stack(settings)  # Parser is used inside pipeline

    try:
        # Note: The `run_analysis_and_modification` function in `pipeline.py`
        # needs to be updated to accept the configured parser and analyzer,
        # or this CLI needs to replicate/adapt that pipeline logic.
        # For now, assuming pipeline.py is flexible or will be adapted.
        # This is a key integration point.
        logger.info(f"Using analyzer stack ending with: {type(analyzer).__name__}")
        logger.info(f"Exclusion patterns: {settings.exclude_patterns}")

        usage_results = run_analysis_and_modification(
            edit_path=current_edit_path,
            ref_path=current_ref_path,
            exclude_patterns=settings.exclude_patterns,
            dry_run=dry_run,
            safe_mode=safe_mode,
            # We might need to pass the configured analyzer and parser instances here
            # For example: parser_instance=_parser, analyzer_instance=analyzer
            # This requires run_analysis_and_modification to be adapted.
        )
        total_constructs = len(usage_results)
        constructs_with_refs = sum(1 for refs in usage_results.values() if refs)
        console.print(
            f"Analysis complete. Found usages for [green]{constructs_with_refs}/{total_constructs}[/green] constructs."
        )

    except Exception as e:
        logger.error(f"A critical error occurred during 'run': {e}", exc_info=settings.verbose)
        console.print(f"[bold red]Error during analysis:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def clean(
    ctx: typer.Context,
    edit_path_override: Path | None = typer.Option(
        None, "--edit", "-e", help="Path to clean (overrides config).", resolve_path=True
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show files that would be cleaned."),
):
    """
    🧹 Clean all 'Used in:' sections from docstrings.

    This command removes all automatically generated usage information
    from docstrings in the specified path.

    """
    settings: UzpySettings = ctx.meta["settings"]
    current_edit_path = edit_path_override if edit_path_override else settings.edit_path

    if not current_edit_path.exists():
        console.print(f"[bold red]Error:[/bold red] Edit path '{current_edit_path}' does not exist.")
        raise typer.Exit(code=1)

    console.print(f"Starting uzpy cleaning on '[cyan]{current_edit_path}[/cyan]'...")
    if dry_run:
        console.print("[yellow]DRY RUN MODE[/yellow] - no files will be modified.")

    try:
        file_discovery = FileDiscovery(settings.exclude_patterns)
        files_to_clean = list(file_discovery.find_python_files(current_edit_path))

        if not files_to_clean:
            console.print("[yellow]No Python files found to clean.[/yellow]")
            raise typer.Exit

        console.print(f"Found {len(files_to_clean)} Python files to potentially clean.")

        if not dry_run:
            project_root_for_cleaner = current_edit_path.parent if current_edit_path.is_file() else current_edit_path
            cleaner = LibCSTCleaner(project_root_for_cleaner)
            clean_results = cleaner.clean_files(files_to_clean)

            successful_cleanings = sum(1 for success in clean_results.values() if success)
            console.print(f"Successfully cleaned [green]{successful_cleanings}/{len(files_to_clean)}[/green] files.")
        else:
            console.print("Dry run: Would attempt to clean the files listed above.")

    except Exception as e:
        logger.error(f"A critical error occurred during 'clean': {e}", exc_info=settings.verbose)
        console.print(f"[bold red]Error during cleaning:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("cache")
def cache_management(
    ctx: typer.Context,
    action: str = typer.Argument(..., help="Cache action: 'clear' or 'stats'."),
):
    """
    💾 Manage the analysis cache.

    The cache stores parsed constructs and analysis results to speed up
    subsequent runs.

    """
    settings: UzpySettings = ctx.meta["settings"]

    # Initialize dummy/representative instances to access cache controls
    # This is a bit clunky; ideally cache management would be more direct.
    # Or, cache objects could be globally accessible or passed via context.
    # For now, instantiate them as configured.

    _parser_instance, _analyzer_instance = _get_analyzer_stack(settings)

    parser_cache = None
    if hasattr(_parser_instance, "cache"):  # If it's a CachedParser instance
        parser_cache = _parser_instance.cache
    elif hasattr(_parser_instance, "parser") and hasattr(
        _parser_instance.parser, "cache"
    ):  # If wrapped again e.g. by Parallel
        parser_cache = _parser_instance.parser.cache

    analyzer_cache = None
    if hasattr(_analyzer_instance, "cache"):  # If it's a CachedAnalyzer instance
        analyzer_cache = _analyzer_instance.cache
    elif hasattr(_analyzer_instance, "analyzer") and hasattr(_analyzer_instance.analyzer, "cache"):  # If wrapped again
        analyzer_cache = _analyzer_instance.analyzer.cache

    if action.lower() == "clear":
        if parser_cache:
            console.print(f"Clearing parser cache at [cyan]{settings.cache_dir / settings.parser_cache_name}[/cyan]...")
            parser_cache.clear()
            console.print("[green]Parser cache cleared.[/green]")
        else:
            console.print("[yellow]Parser cache not active or not accessible directly.[/yellow]")

        if analyzer_cache:
            console.print(
                f"Clearing analyzer cache at [cyan]{settings.cache_dir / settings.analyzer_cache_name}[/cyan]..."
            )
            analyzer_cache.clear()
            console.print("[green]Analyzer cache cleared.[/green]")
        else:
            console.print("[yellow]Analyzer cache not active or not accessible directly.[/yellow]")

    elif action.lower() == "stats":
        if parser_cache:
            stats = parser_cache.stats()
            console.print(f"\n[bold]Parser Cache Stats ({settings.cache_dir / settings.parser_cache_name}):[/bold]")
            console.print(f"  Items: {stats.get('item_count', 'N/A')}")
            console.print(f"  Size: {stats.get('disk_usage_bytes', 'N/A')} bytes")
        else:
            console.print("[yellow]Parser cache not active or not accessible directly for stats.[/yellow]")

        if analyzer_cache:
            stats = analyzer_cache.stats()
            console.print(f"\n[bold]Analyzer Cache Stats ({settings.cache_dir / settings.analyzer_cache_name}):[/bold]")
            console.print(f"  Items: {stats.get('item_count', 'N/A')}")
            console.print(f"  Size: {stats.get('disk_usage_bytes', 'N/A')} bytes")
        else:
            console.print("[yellow]Analyzer cache not active or not accessible directly for stats.[/yellow]")

    else:
        console.print(f"[bold red]Error:[/bold red] Unknown cache action '{action}'. Choose 'clear' or 'stats'.")
        raise typer.Exit(code=1)

def display_results_summary(usage_results: dict) -> None:
    """Display a formatted summary of analysis results.

"""
    total_constructs = len(usage_results)
    constructs_with_refs = sum(1 for refs in usage_results.values() if refs)
    total_references = sum(len(refs) for refs in usage_results.values())

@app.command()
def watch(
    ctx: typer.Context,
    path_override: Path | None = typer.Option(
        None, "--path", "-p", help="Directory/file to watch (overrides config edit_path).", resolve_path=True
    ),
):
    """
    Watch for file changes and re-run analysis automatically. (Experimental)
    """
    settings: UzpySettings = ctx.meta["settings"]
    watch_path = path_override if path_override else settings.edit_path

    if not watch_path.exists():
        console.print(f"[bold red]Error:[/bold red] Path to watch '{watch_path}' does not exist.")
        raise typer.Exit(code=1)

    console.print(f"Starting watcher on '[cyan]{watch_path}[/cyan]'... Press Ctrl+C to exit.")
    logger.info(f"Watcher mode enabled for path: {watch_path}")

    # This is where the Watchdog integration would go.
    from typing import Set  # For type hinting the callback argument

    from uzpy.watcher import WatcherOrchestrator  # Assuming this will be created

    def _on_files_changed_callback(changed_files: set[Path]):
        console.print("\n[bold magenta]File change detected for:[/bold magenta]")
        for f_path in changed_files:
            console.print(f"- {f_path}")
        console.print("Re-running analysis (full project for now)...")
        logger.info(f"Watch event: Files changed: {changed_files}. Triggering re-analysis.")

        # For simplicity, re-trigger the 'run' command logic.
        # A more optimized approach would analyze only affected files/dependencies.
        # Current 'run' command needs ctx, which we have.
        # We also need to decide if it should be dry_run or not. For watch mode, usually not dry_run.
        try:
            # Use settings from the context for consistency
            # We are calling the 'run' command's core logic here.
            # This assumes `run` can be called programmatically.
            # We need to ensure the settings are correctly propagated.
            # The `run` command itself handles `_get_analyzer_stack` and `run_analysis_and_modification`.

            # To call the Typer command programmatically, it's tricky.
            # Instead, let's replicate the core logic of `run` here or refactor `run`
            # to be callable with specific parameters.

            # Replicating core run logic for now:
            current_edit_path = settings.edit_path  # Use the original configured edit path for full re-scan
            current_ref_path = settings.get_effective_ref_path()

    This command monitors Python files for changes and automatically
    updates docstrings whenever a file is modified.

    """
    configure_logging(verbose)

            usage_results = run_analysis_and_modification(
                edit_path=current_edit_path,
                ref_path=current_ref_path,
                exclude_patterns=settings.exclude_patterns,
                dry_run=False,  # Watch mode typically applies changes
                # parser_instance=_parser, # If pipeline supports this
                # analyzer_instance=analyzer # If pipeline supports this
            )
            total_constructs = len(usage_results)
            constructs_with_refs = sum(1 for refs in usage_results.values() if refs)
            console.print(
                f"Re-analysis complete. Found usages for [green]{constructs_with_refs}/{total_constructs}[/green] constructs."
            )
            console.print(f"Watching for next change on '[cyan]{watch_path}[/cyan]'... Press Ctrl+C to exit.")

        except Exception as e:
            logger.error(f"Error during automatic re-analysis in watch mode: {e}", exc_info=settings.verbose)
            console.print(f"[bold red]Error during re-analysis:[/bold red] {e}")

    orchestrator = WatcherOrchestrator(
        paths_to_watch=[watch_path],
        on_change_callback=_on_files_changed_callback,
        exclude_patterns=settings.exclude_patterns,  # Pass excludes to watcher too
        debounce_interval=settings.watch_debounce_seconds,
    )

    orchestrator.start()  # This blocks until Ctrl+C or observer stops

def cli() -> None:
    """Main entry point for the modern CLI.

Used in:
- src/uzpy/__main__.py
- src/uzpy/cli.py
"""
    app()


if __name__ == "__main__":
    app()
