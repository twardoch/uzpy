# this_file: src/uzpy/discovery.py

"""
File discovery utilities for finding Python files in codebases.

This module handles finding Python files while respecting gitignore patterns,
common exclude patterns, and providing efficient traversal of directory trees.

Used in:
- discovery.py
"""

from collections.abc import Iterator
from pathlib import Path

import pathspec
from loguru import logger


class FileDiscovery:
    """
    Discovers Python files in codebases with configurable filtering.

    Handles gitignore patterns, custom exclude patterns, and provides
    efficient traversal with proper error handling.

    Used in:
    - discovery.py
    - uzpy/cli.py
    """

    # Default patterns to exclude
    DEFAULT_EXCLUDE_PATTERNS = [
        ".git/**",
        "__pycache__/**",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".pytest_cache/**",
        ".mypy_cache/**",
        ".ruff_cache/**",
        "build/**",
        "dist/**",
        "*.egg-info/**",
        ".venv/**",
        "venv/**",
        ".env/**",
        "env/**",
    ]

    def __init__(self, exclude_patterns: list[str] | None = None):
        """
        Initialize file discovery with optional exclude patterns.

        Args:
            exclude_patterns: Additional patterns to exclude beyond defaults

        Used in:
        - discovery.py
        """
        self.exclude_patterns = self.DEFAULT_EXCLUDE_PATTERNS.copy()
        if exclude_patterns:
            self.exclude_patterns.extend(exclude_patterns)

        # Compile pathspec for efficient matching
        self.spec = pathspec.PathSpec.from_lines("gitwildmatch", self.exclude_patterns)
        logger.debug(f"Initialized with {len(self.exclude_patterns)} exclude patterns")

    def find_python_files(self, root_path: Path) -> Iterator[Path]:
        """
        Find all Python files under the root path.

        Args:
            root_path: Root directory or single file to analyze

        Yields:
            Path objects for Python files that match criteria

        Raises:
            FileNotFoundError: If root_path doesn't exist
            PermissionError: If can't access directory

        Used in:
        - discovery.py
        - uzpy/cli.py
        """
        if not root_path.exists():
            msg = f"Path does not exist: {root_path}"
            raise FileNotFoundError(msg)

        # Handle single file case
        if root_path.is_file():
            if self._is_python_file(root_path) and not self._is_excluded(root_path):
                yield root_path
            return

        # Handle directory case
        if not root_path.is_dir():
            logger.warning(f"Path is neither file nor directory: {root_path}")
            return

        logger.info(f"Scanning directory: {root_path}")

        try:
            for path in self._walk_directory(root_path):
                if self._is_python_file(path) and not self._is_excluded(path):
                    logger.debug(f"Found Python file: {path}")
                    yield path
        except PermissionError as e:
            logger.error(f"Permission denied accessing {root_path}: {e}")
            raise

    def _walk_directory(self, root_path: Path) -> Iterator[Path]:
        """
        Recursively walk directory tree, yielding all files.

        Args:
            root_path: Directory to walk

        Yields:
            All file paths found in the tree

        Used in:
        - discovery.py
        """
        try:
            for item in root_path.iterdir():
                if item.is_file():
                    yield item
                elif item.is_dir() and not self._is_excluded(item):
                    # Recursively walk subdirectories
                    yield from self._walk_directory(item)
        except PermissionError:
            logger.warning(f"Permission denied accessing directory: {root_path}")
        except OSError as e:
            logger.warning(f"OS error accessing {root_path}: {e}")

    def _is_python_file(self, path: Path) -> bool:
        """
        Check if a file is a Python file.

        Args:
            path: File path to check

        Returns:
            True if the file appears to be a Python file

        Used in:
        - discovery.py
        """
        if path.suffix == ".py":
            return True

        # Check for Python shebang in files without .py extension
        if path.suffix == "":
            try:
                with open(path, "rb") as f:
                    first_line = f.readline()
                    if first_line.startswith(b"#!") and b"python" in first_line:
                        return True
            except (OSError, UnicodeDecodeError):
                pass

        return False

    def _is_excluded(self, path: Path) -> bool:
        """
        Check if a path should be excluded based on patterns.

        Args:
            path: Path to check

        Returns:
            True if the path should be excluded

        Used in:
        - discovery.py
        """
        # Convert to relative path for pattern matching
        try:
            # pathspec expects forward slashes
            path_str = str(path).replace("\\", "/")
            return self.spec.match_file(path_str)
        except Exception as e:
            logger.debug(f"Error checking exclusion for {path}: {e}")
            return False

    def get_statistics(self, root_path: Path) -> dict:
        """
        Get statistics about files in the path.

        Args:
            root_path: Root path to analyze

        Returns:
            Dictionary with file counts and other statistics

        Used in:
        - discovery.py
        """
        stats = {
            "total_python_files": 0,
            "total_files_scanned": 0,
            "excluded_files": 0,
            "directories_scanned": 0,
        }

        if root_path.is_file():
            stats["total_files_scanned"] = 1
            if self._is_python_file(root_path):
                stats["total_python_files"] = 1
            return stats

        for path in self._walk_directory(root_path):
            stats["total_files_scanned"] += 1

            if self._is_excluded(path):
                stats["excluded_files"] += 1
                continue

            if self._is_python_file(path):
                stats["total_python_files"] += 1

        return stats


def discover_files(
    edit_path: Path, ref_path: Path, exclude_patterns: list[str] | None = None
) -> tuple[list[Path], list[Path]]:
    """
    Discover Python files in both edit and reference paths.

    Args:
        edit_path: Path containing files to edit
        ref_path: Path containing reference files to search
        exclude_patterns: Additional patterns to exclude

    Returns:
        Tuple of (edit_files, ref_files) lists

    Used in:
    - discovery.py
    - uzpy/cli.py
    """
    discovery = FileDiscovery(exclude_patterns)

    edit_files = list(discovery.find_python_files(edit_path))
    ref_files = list(discovery.find_python_files(ref_path))

    logger.info(f"Found {len(edit_files)} edit files and {len(ref_files)} reference files")

    return edit_files, ref_files
