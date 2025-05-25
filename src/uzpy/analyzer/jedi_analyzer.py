# this_file: src/uzpy/analyzer/jedi_analyzer.py

"""
Jedi-based analyzer for finding construct usage across Python codebases.

Jedi provides fast symbol resolution and reference finding, optimized
for interactive use with excellent caching mechanisms.

Used in:
- analyzer/jedi_analyzer.py
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import jedi
from jedi.api.classes import Name
from loguru import logger

from uzpy.parser import Construct, ConstructType


class JediAnalyzer:
    """
    Jedi-based analyzer for finding construct usage.

    Uses Jedi's static analysis for fast symbol resolution and reference finding.
    Provides good caching and handles large codebases efficiently.

    Used in:
    - analyzer/jedi_analyzer.py
    """

    def __init__(self, project_path: Path):
        """
        Initialize the Jedi analyzer.

        Args:
            project_path: Root directory of the project to analyze

        Used in:
        - analyzer/jedi_analyzer.py
        """
        self.project_path = project_path
        self.project = jedi.Project(str(project_path))
        logger.debug(f"Jedi analyzer initialized for {project_path}")

    def find_usages(self, construct: Construct, search_paths: list[Path]) -> list[Path]:
        """
        Find all files where a construct is used.

        Args:
            construct: The construct to search for
            search_paths: List of files to search within

        Returns:
            List of file paths where the construct is used

        Used in:
        - analyzer/jedi_analyzer.py
        """
        usage_files = set()

        try:
            # Create a Jedi script for the file containing the construct
            with open(construct.file_path, encoding="utf-8") as f:
                source_code = f.read()

            script = jedi.Script(code=source_code, path=str(construct.file_path), project=self.project)

            # Find the definition position
            definition_position = self._find_definition_position(construct, source_code)
            if not definition_position:
                logger.warning(f"Could not find definition position for {construct.full_name}")
                return []

            line, column = definition_position
            logger.debug(f"Finding references for {construct.full_name} at line {line}, column {column}")

            # Get references using Jedi
            try:
                references = script.get_references(line=line, column=column, include_builtins=False)

                for ref in references:
                    if ref.module_path:
                        ref_file = Path(ref.module_path)

                        # Only include files in our search paths
                        if any(self._is_file_in_search_path(ref_file, search_path) for search_path in search_paths):
                            usage_files.add(ref_file)

            except Exception as e:
                logger.debug(f"Jedi reference finding failed for {construct.full_name}: {e}")
                # Fall back to alternative method
                usage_files.update(self._fallback_search(construct, search_paths))

        except Exception as e:
            logger.error(f"Error finding usages for {construct.full_name}: {e}")

        logger.debug(f"Found {len(usage_files)} usage files for {construct.full_name}")
        return list(usage_files)

    def _find_definition_position(self, construct: Construct, source_code: str) -> tuple[int, int] | None:
        """
        Find the line and column position of a construct definition.

        Args:
            construct: The construct to find
            source_code: Source code of the file

        Returns:
            Tuple of (line, column) for the definition, or None if not found

        Used in:
        - analyzer/jedi_analyzer.py
        """
        lines = source_code.split("\n")

        if construct.line_number > len(lines):
            return None

        target_line = lines[construct.line_number - 1]

        # Look for the construct name in the definition
        if construct.type in (ConstructType.FUNCTION, ConstructType.METHOD):
            pattern = f"def {construct.name}"
        elif construct.type == ConstructType.CLASS:
            pattern = f"class {construct.name}"
        else:
            pattern = construct.name

        column = target_line.find(pattern)
        if column == -1:
            # Try just the name
            column = target_line.find(construct.name)
            if column == -1:
                return None

        # Adjust to point to the name itself
        if construct.type in (ConstructType.FUNCTION, ConstructType.METHOD, ConstructType.CLASS):
            name_start = target_line.find(construct.name, column)
            if name_start != -1:
                column = name_start

        return (construct.line_number, column)

    def _fallback_search(self, construct: Construct, search_paths: list[Path]) -> set[Path]:
        """
        Fallback search method using simple text matching.

        Args:
            construct: The construct to search for
            search_paths: List of paths to search within

        Returns:
            Set of file paths that potentially contain the construct

        Used in:
        - analyzer/jedi_analyzer.py
        """
        usage_files = set()

        # Simple text search as fallback
        search_terms = [
            construct.name,
            f"{construct.name}(",  # Function calls
            f".{construct.name}",  # Method calls
            f"from {construct.file_path.stem} import",  # Imports
        ]

        for search_path in search_paths:
            files_to_search = []

            files_to_search = [search_path] if search_path.is_file() else list(search_path.rglob("*.py"))

            for file_path in files_to_search:
                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Check if any search terms appear in the file
                    if any(term in content for term in search_terms):
                        usage_files.add(file_path)

                except Exception as e:
                    logger.debug(f"Error reading {file_path} for fallback search: {e}")

        return usage_files

    def _is_file_in_search_path(self, file_path: Path, search_path: Path) -> bool:
        """Check if a file is within a search path.

        Used in:
        - analyzer/jedi_analyzer.py
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
        Analyze multiple constructs in batch.

        Args:
            constructs: List of constructs to analyze
            search_paths: List of paths to search within

        Returns:
            Dictionary mapping construct full names to lists of usage files

        Used in:
        - analyzer/jedi_analyzer.py
        """
        logger.info(f"Analyzing {len(constructs)} constructs with Jedi")
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
        logger.info(f"Jedi analysis completed in {elapsed:.2f}s")

        return results

    def get_project_info(self) -> dict[str, any]:
        """Get information about the Jedi project.

        Used in:
        - analyzer/jedi_analyzer.py
        """
        try:
            return {
                "project_path": str(self.project_path),
                "sys_path": self.project.sys_path,
            }
        except Exception as e:
            return {"error": str(e)}
