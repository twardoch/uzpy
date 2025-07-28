# this_file: src/uzpy/watcher.py

"""
File system watcher for uzpy.

This module provides real-time monitoring of Python files and automatic
re-analysis when changes are detected.

"""

import sys  # Added for __main__ example
import time
from pathlib import Path
from typing import Callable, Set, List, Optional  # Added List, Optional for type hints
import threading  # Added for Timer

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from loguru import logger
from rich.console import Console  # Added for __main__ example


class UzpyWatcher(FileSystemEventHandler):
    """
    File system event handler for watching Python files.

    This class monitors changes to Python files and triggers re-analysis
    when modifications are detected.

    """

    def __init__(
        self,
        callback: Callable[[Set[Path]], None],
        watch_paths: List[Path],  # Corrected type hint
        exclude_patterns: List[str],  # Corrected type hint
        debounce_interval: float = 1.0,
    ):
        """
        Initialize the UzpyWatcher.

        Args:
            edit_path: Path to watch for changes
            ref_path: Reference path for analysis
            exclude_patterns: Patterns to exclude from watching
            console: Rich console for output

        """
        self.edit_path = edit_path
        self.ref_path = ref_path
        self.exclude_patterns = exclude_patterns or []
        self.console = console or Console()
        self.last_analysis_time = 0
        self.pending_files = set()
        self.analysis_count = 0

    def on_modified(self, event):
        """Handle file modification events.

"""
        if event.is_directory:
            return

        file_path_str = getattr(event, "src_path", None)
        if not file_path_str:  # Also handle dest_path for moves
            file_path_str = getattr(event, "dest_path", None)

        if not file_path_str:
            return

        # Check if file matches exclude patterns
        if self._is_excluded(file_path):
            return

        logger.debug(f"File modified: {file_path}")
        self.pending_files.add(file_path)

        # Debounce - wait a bit before analyzing
        current_time = time.time()
        if current_time - self.last_analysis_time > 1.0:  # 1 second debounce
            self._trigger_analysis()

    def _is_excluded(self, file_path: Path) -> bool:
        """Check if a file matches any exclude pattern.

"""
        from pathspec import PathSpec

        if self.exclude_patterns:
            spec = PathSpec.from_lines("gitwildmatch", self.exclude_patterns)
            return spec.match_file(str(file_path))
        return False

    def _trigger_analysis(self):
        """Trigger re-analysis of the codebase.

"""
        if not self.pending_files:
            return

        event_handler = UzpyWatcher(
            callback=self.on_change_callback,
            watch_paths=self.paths_to_watch,
            exclude_patterns=self.exclude_patterns,
            debounce_interval=self.debounce_interval,
        )

        for path in self.paths_to_watch:
            if path.exists():
                self.observer.schedule(event_handler, str(path.resolve()), recursive=path.is_dir())
                logger.info(f"Watcher scheduled for path: {path.resolve()} (recursive: {path.is_dir()})")
            else:
                logger.warning(f"Watcher: Path does not exist, cannot watch: {path}")
        if not self.observer.emitters:
            logger.error("Watcher: No valid paths found to watch. Observer not started.")
            return

        self.observer.start()
        logger.info("File system watcher started.")
        try:
            # Run analysis
            start_time = time.time()
            usage_results = run_analysis_and_modification(
                edit_path=self.edit_path,
                ref_path=self.ref_path,
                exclude_patterns=self.exclude_patterns,
                dry_run=False,
            )

            elapsed = time.time() - start_time

            # Show results
            total_constructs = len(usage_results)
            constructs_with_refs = sum(1 for refs in usage_results.values() if refs)

            self.console.print(
                f"[green]✅ Analysis complete in {elapsed:.2f}s. "
                f"Found usages for {constructs_with_refs}/{total_constructs} constructs.[/green]"
            )

        except Exception as e:
            self.console.print(f"[red]❌ Analysis failed: {e}[/red]")
            logger.exception("Analysis error in watch mode")


def create_watch_status_table(path: Path, ref_path: Path, exclude_patterns: list[str], analysis_count: int) -> Table:
    """Create a status table for watch mode display.

"""
    table = Table(title="uzpy Watch Mode", box=None)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Watching", str(path))
    table.add_row("Reference Path", str(ref_path))
    if exclude_patterns:
        table.add_row("Exclude Patterns", ", ".join(exclude_patterns))
    table.add_row("Analyses Run", str(analysis_count))
    table.add_row("Status", "[yellow]Watching for changes...[/yellow]")

    return table


def watch_directory(
    edit_path: Path,
    ref_path: Path,
    exclude_patterns: list[str] | None = None,
) -> None:
    """
    Watch a directory for changes and automatically re-run analysis.

    Args:
        edit_path: Path to watch
        ref_path: Reference path for analysis
        exclude_patterns: Patterns to exclude from watching

    Used in:
    - src/uzpy/cli_modern.py
    """
    console = Console()

    # Create event handler and observer
    event_handler = UzpyWatcher(edit_path, ref_path, exclude_patterns, console)
    observer = Observer()

    # Schedule the observer
    observer.schedule(event_handler, str(edit_path), recursive=True)

    console.print("\n[bold blue]uzpy Watch Mode[/bold blue]")
    console.print("Press Ctrl+C to stop watching\n")

    # Start watching
    observer.start()

    try:
        orchestrator.start()
    except Exception as e:
        logger.error(f"Error in watcher example: {e}")
    finally:
        logger.info("Watcher example finished.")
        # import shutil # Not used if rmtree is commented
        # shutil.rmtree(test_dir)
        # logger.info(f"Cleaned up {test_dir}")
        # Commenting out cleanup to allow inspection if needed
