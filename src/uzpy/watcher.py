# this_file: src/uzpy/watcher.py

"""
File system watcher for uzpy.

This module provides the UzpyWatcher class, which uses the `watchdog`
library to monitor specified paths for file system changes (creations,
modifications, deletions). When relevant changes are detected (e.g., to .py files),
it triggers a callback function, typically to re-run analysis.
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
    A file system event handler that watches for changes in Python files
    and triggers a callback with debouncing.
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
            callback: Function to call when relevant file changes are detected.
                      It will be called with a set of modified/created/deleted relevant file paths.
            watch_paths: A list of Path objects to monitor.
            exclude_patterns: A list of glob patterns to ignore. (Handled by FileDiscovery logic)
            debounce_interval: Time in seconds to wait for more changes before triggering callback.
        """
        super().__init__()
        self.callback = callback
        self.watch_paths = [p.resolve() for p in watch_paths]  # Ensure absolute paths
        self.exclude_patterns = exclude_patterns
        self.debounce_interval = debounce_interval

        self._changed_files: Set[Path] = set()
        self._debounce_lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None

        logger.info(f"UzpyWatcher initialized. Debounce interval: {self.debounce_interval}s.")
        logger.debug(f"Watching paths: {[str(p) for p in self.watch_paths]}")

    def _is_relevant_file(self, file_path_str: str) -> bool:
        """Check if the file is a Python file and not excluded."""
        if not file_path_str:
            return False
        file_path = Path(file_path_str)
        if file_path.suffix.lower() == ".py":
            is_watched = any(
                watch_root in file_path.resolve().parents or watch_root == file_path.resolve()
                for watch_root in self.watch_paths
            )
            if is_watched:
                return True
        return False

    def _trigger_callback(self) -> None:
        """Triggers the callback with collected file paths."""
        with self._debounce_lock:
            if self._changed_files:
                logger.info(f"Debounce triggered. Processing {len(self._changed_files)} changed files.")
                try:
                    self.callback(self._changed_files.copy())
                except Exception as e:
                    logger.error(f"Error in watcher callback: {e}", exc_info=True)
                self._changed_files.clear()
            self._timer = None  # Reset timer

    def _handle_event(self, event: FileSystemEvent):
        """Generic event handler for file system events."""
        if event.is_directory:
            return

        file_path_str = getattr(event, "src_path", None)
        if not file_path_str:  # Also handle dest_path for moves
            file_path_str = getattr(event, "dest_path", None)

        if not file_path_str:
            return

        if self._is_relevant_file(file_path_str):
            logger.debug(f"Relevant file event: {event.event_type} on {file_path_str}")
            with self._debounce_lock:
                self._changed_files.add(Path(file_path_str).resolve())
                if self._timer:
                    self._timer.cancel()
                self._timer = threading.Timer(self.debounce_interval, self._trigger_callback)
                self._timer.start()
                logger.debug(f"Debounce timer (re)started for {self.debounce_interval}s.")

    def on_modified(self, event: FileSystemEvent):
        super().on_modified(event)
        self._handle_event(event)

    def on_created(self, event: FileSystemEvent):
        super().on_created(event)
        self._handle_event(event)

    def on_deleted(self, event: FileSystemEvent):
        super().on_deleted(event)
        self._handle_event(event)

    def on_moved(self, event: FileSystemEvent):
        super().on_moved(event)
        # A move involves a source (deleted) and destination (created)
        # Handle both if they are relevant Python files
        # FileSystemEvent itself doesn't make src_path/dest_path part of its direct attributes for _handle_event
        # So, we pass event and let _handle_event extract src_path or dest_path
        self._handle_event(event)


class WatcherOrchestrator:
    """
    Manages the Watchdog observer and event handler.
    """

    def __init__(
        self,
        paths_to_watch: List[Path],
        on_change_callback: Callable[[Set[Path]], None],
        exclude_patterns: List[str],
        debounce_interval: float = 1.0,
    ):
        self.paths_to_watch = paths_to_watch
        self.on_change_callback = on_change_callback
        self.exclude_patterns = exclude_patterns
        self.debounce_interval = debounce_interval
        self.observer = Observer()

    def start(self):
        """Starts the file system watcher."""
        if not self.paths_to_watch:
            logger.warning("Watcher: No paths specified to watch.")
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
            while self.observer.is_alive():
                self.observer.join(1)
        except KeyboardInterrupt:
            logger.info("Watcher interrupted by user (KeyboardInterrupt).")
        finally:
            self.stop()

    def stop(self):
        """Stops the file system watcher."""
        if self.observer.is_alive():
            self.observer.stop()
            logger.info("Watcher stopping...")
        self.observer.join()
        logger.info("File system watcher stopped.")


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    test_dir = Path("test_watch_dir")
    test_dir.mkdir(exist_ok=True)
    (test_dir / "sample1.py").write_text("print('hello')")
    (test_dir / "sample2.txt").write_text("some text")

    def my_callback(changed_files: Set[Path]):
        console = Console()
        console.print("\n[bold green]Callback triggered![/bold green] Files changed:")
        for f_path in changed_files:
            console.print(f"- {f_path} ({'exists' if f_path.exists() else 'deleted/moved'})")
        logger.info(f"Callback executed for: {changed_files}")

    logger.info(f"Starting watcher example on directory: {test_dir.resolve()}")
    orchestrator = WatcherOrchestrator(
        paths_to_watch=[test_dir], on_change_callback=my_callback, exclude_patterns=[], debounce_interval=2.0
    )
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
