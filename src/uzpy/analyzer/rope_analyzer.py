# this_file: src/uzpy/analyzer/rope_analyzer.py

"""
Rope-based analyzer for finding construct usage across Python codebases.

Rope provides excellent cross-file reference finding with proper handling
of Python's import systems, inheritance, and scoping rules.

Used in:
- analyzer/rope_analyzer.py
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger
from rope.base.exceptions import ModuleSyntaxError, ResourceNotFoundError
from rope.base.project import Project
from rope.contrib.findit import find_occurrences

from uzpy.parser import Construct, ConstructType


class RopeAnalyzer:
    """
    Rope-based analyzer for finding construct usage.

    Uses Rope's static analysis capabilities to find where functions,
    classes, and methods are used across a Python codebase.

    Used in:
    - analyzer/rope_analyzer.py
    """

    def __init__(self, root_path: Path):
        """
        Initialize the Rope analyzer.

        Args:
            root_path: Root directory of the project to analyze

        Used in:
        - analyzer/rope_analyzer.py
        """
        self.root_path = root_path
        self.project: Project | None = None
        self._init_project()

    def _init_project(self) -> None:
        """Initialize the Rope project.

        Used in:
        - analyzer/rope_analyzer.py
        """
        try:
            logger.debug(f"Initializing Rope project at {self.root_path}")
            self.project = Project(str(self.root_path))
            logger.debug("Rope project initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Rope project: {e}")
            raise

    def find_usages(self, construct: Construct, search_paths: list[Path]) -> list[Path]:
        """
        Find all files where a construct is used.

        Args:
            construct: The construct to search for
            search_paths: List of files to search within

        Returns:
            List of file paths where the construct is used

        Used in:
        - analyzer/rope_analyzer.py
        """
        if not self.project:
            logger.error("Rope project not initialized")
            return []

        usage_files = set()

        try:
            # Get the resource for the file containing the construct
            try:
                resource_path = str(construct.file_path.relative_to(self.root_path))
            except ValueError:
                # File is not relative to root_path, use absolute path
                resource_path = str(construct.file_path)

            resource = self.project.get_resource(resource_path)

            # Find the offset of the construct definition
            offset = self._find_construct_offset(construct, resource)
            if offset is None:
                logger.warning(f"Could not find offset for {construct.full_name} in {construct.file_path}")
                return []

            logger.debug(f"Finding usages of {construct.full_name} at offset {offset}")

            # Use Rope to find all occurrences
            occurrences = find_occurrences(self.project, resource, offset)

            for occurrence in occurrences:
                occurrence_file = Path(self.root_path) / occurrence.resource.path

                # Only include files that are in our search paths
                if any(self._is_file_in_search_path(occurrence_file, search_path) for search_path in search_paths):
                    usage_files.add(occurrence_file)

            logger.debug(f"Found {len(usage_files)} usage files for {construct.full_name}")

        except (ModuleSyntaxError, ResourceNotFoundError) as e:
            logger.warning(f"Rope error analyzing {construct.full_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error finding usages for {construct.full_name}: {e}")

        return list(usage_files)

    def _find_construct_offset(self, construct: Construct, resource) -> int | None:
        """
        Find the byte offset of a construct definition in a file.

        Args:
            construct: The construct to find
            resource: Rope resource representing the file

        Returns:
            Byte offset of the construct definition, or None if not found

        Used in:
        - analyzer/rope_analyzer.py
        """
        try:
            source_code = resource.read()
            lines = source_code.split("\n")

            # Find the line with the construct (1-based line numbers)
            if construct.line_number > len(lines):
                return None

            target_line = lines[construct.line_number - 1]

            # Look for the construct name in the definition line
            if construct.type in (ConstructType.FUNCTION, ConstructType.METHOD):
                pattern = f"def {construct.name}"
            elif construct.type == ConstructType.CLASS:
                pattern = f"class {construct.name}"
            else:
                # For modules, use the first occurrence of the name
                pattern = construct.name

            name_pos = target_line.find(pattern)
            if name_pos == -1:
                # Try just the name if the full pattern isn't found
                name_pos = target_line.find(construct.name)
                if name_pos == -1:
                    return None

            # Calculate byte offset
            offset = 0
            for i in range(construct.line_number - 1):
                offset += len(lines[i]) + 1  # +1 for newline
            offset += name_pos + len(pattern.split()[-1]) // 2  # Position within the name

            return offset

        except Exception as e:
            logger.debug(f"Error finding offset for {construct.name}: {e}")
            return None

    def _is_file_in_search_path(self, file_path: Path, search_path: Path) -> bool:
        """
        Check if a file is within a search path.

        Args:
            file_path: File to check
            search_path: Directory or file to search within

        Returns:
            True if the file is within the search path

        Used in:
        - analyzer/rope_analyzer.py
        """
        try:
            if search_path.is_file():
                return file_path.resolve() == search_path.resolve()
            # Check if file is under the directory
            return search_path.resolve() in file_path.resolve().parents or file_path.resolve() == search_path.resolve()
        except Exception:
            return False

    def analyze_batch(self, constructs: list[Construct], search_paths: list[Path]) -> dict[str, list[Path]]:
        """
        Analyze multiple constructs in batch for efficiency.

        Args:
            constructs: List of constructs to analyze
            search_paths: List of paths to search within

        Returns:
            Dictionary mapping construct full names to lists of usage files

        Used in:
        - analyzer/rope_analyzer.py
        """
        logger.info(f"Analyzing {len(constructs)} constructs with Rope")
        start_time = time.time()

        results = {}

        for i, construct in enumerate(constructs):
            if i % 10 == 0:
                logger.debug(f"Processed {i}/{len(constructs)} constructs")

            try:
                usage_files = self.find_usages(construct, search_paths)
                results[construct.full_name] = usage_files
            except Exception as e:
                logger.error(f"Error analyzing {construct.full_name}: {e}")
                results[construct.full_name] = []

        elapsed = time.time() - start_time
        logger.info(f"Rope analysis completed in {elapsed:.2f}s")

        return results

    def get_project_info(self) -> dict[str, any]:
        """Get information about the Rope project.

        Used in:
        - analyzer/rope_analyzer.py
        """
        if not self.project:
            return {}

        try:
            # Get basic project info
            all_resources = list(self.project.get_files())
            python_files = [r for r in all_resources if r.path.endswith(".py")]

            return {
                "root_path": str(self.root_path),
                "total_files": len(all_resources),
                "python_files": len(python_files),
                "project_name": self.project.root.path,
            }
        except Exception as e:
            logger.debug(f"Error getting project info: {e}")
            return {"error": str(e)}

    def close(self) -> None:
        """Clean up the Rope project.

        Used in:
        - analyzer/rope_analyzer.py
        """
        if self.project:
            try:
                self.project.close()
                logger.debug("Rope project closed")
            except Exception as e:
                logger.debug(f"Error closing Rope project: {e}")
