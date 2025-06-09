# this_file: src/uzpy/watcher.py

"""
File watching functionality for uzpy.

This module provides real-time monitoring of Python files and automatic
re-analysis when changes are detected.
"""

import time
from pathlib import Path
from typing import Optional

from loguru import logger
from rich.console import Console
from rich.live import Live
from rich.table import Table
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from uzpy.pipeline import run_analysis_and_modification


class UzpyWatcher(FileSystemEventHandler):
    """
    File system event handler for watching Python files.
    
    This class monitors changes to Python files and triggers re-analysis
    when modifications are detected.
    """
    
    def __init__(
        self,
        edit_path: Path,
        ref_path: Path,
        exclude_patterns: Optional[list[str]] = None,
        console: Optional[Console] = None,
    ):
        """
        Initialize the file watcher.
        
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
        """Handle file modification events."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only watch Python files
        if file_path.suffix != ".py":
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
        """Check if a file matches any exclude pattern."""
        from pathspec import PathSpec
        
        if self.exclude_patterns:
            spec = PathSpec.from_lines("gitwildmatch", self.exclude_patterns)
            return spec.match_file(str(file_path))
        return False
    
    def _trigger_analysis(self):
        """Trigger re-analysis of the codebase."""
        if not self.pending_files:
            return
            
        self.analysis_count += 1
        self.console.print(
            f"\n[yellow]Changes detected in {len(self.pending_files)} files. "
            f"Running analysis #{self.analysis_count}...[/yellow]"
        )
        
        # Clear pending files
        modified_files = list(self.pending_files)
        self.pending_files.clear()
        self.last_analysis_time = time.time()
        
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


def create_watch_status_table(
    path: Path,
    ref_path: Path,
    exclude_patterns: list[str],
    analysis_count: int
) -> Table:
    """Create a status table for watch mode display."""
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
    exclude_patterns: Optional[list[str]] = None,
) -> None:
    """
    Watch a directory for changes and automatically re-run analysis.
    
    Args:
        edit_path: Path to watch
        ref_path: Reference path for analysis
        exclude_patterns: Patterns to exclude from watching
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
        # Run initial analysis
        console.print("[yellow]Running initial analysis...[/yellow]")
        run_analysis_and_modification(
            edit_path=edit_path,
            ref_path=ref_path,
            exclude_patterns=exclude_patterns,
            dry_run=False,
        )
        event_handler.analysis_count = 1
        console.print("[green]✅ Initial analysis complete[/green]\n")
        
        # Keep the program running
        with Live(
            create_watch_status_table(
                edit_path, ref_path, exclude_patterns or [], 
                event_handler.analysis_count
            ),
            console=console,
            refresh_per_second=1,
        ) as live:
            while True:
                time.sleep(1)
                # Update the status table
                live.update(
                    create_watch_status_table(
                        edit_path, ref_path, exclude_patterns or [],
                        event_handler.analysis_count
                    )
                )
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping watch mode...[/yellow]")
    finally:
        observer.stop()
        observer.join()
        console.print("[green]Watch mode stopped.[/green]")