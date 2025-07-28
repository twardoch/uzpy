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

import jedi
from loguru import logger

from uzpy.types import Construct, ConstructType, Reference


class JediAnalyzer:
    """
    Jedi-based analyzer for finding construct usage.

    Uses Jedi's static analysis for fast symbol resolution and reference finding.
    Provides good caching and handles large codebases efficiently.

    Used in:
    - analyzer/__init__.py
    - analyzer/hybrid_analyzer.py
    - analyzer/jedi_analyzer.py
    - src/uzpy/analyzer/__init__.py
    - src/uzpy/analyzer/hybrid_analyzer.py
    - uzpy/analyzer/__init__.py
    - uzpy/analyzer/hybrid_analyzer.py
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

    def find_usages(self, construct: Construct, search_paths: list[Path]) -> list[Reference]:
        """
        Find all files where a construct is used.

        Args:
            construct: The construct to search for
            search_paths: List of files to search within

        Returns:
            List of Reference objects where the construct is used

        Used in:
        - analyzer/hybrid_analyzer.py
        - analyzer/jedi_analyzer.py
        - src/uzpy/analyzer/hybrid_analyzer.py
        - uzpy/analyzer/hybrid_analyzer.py
        """
        usage_references = []

        # For modules, use import-based search
        if construct.type == ConstructType.MODULE:
            return self._find_module_imports(construct, search_paths)

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
                            # Create a Reference object with line number from Jedi
                            usage_ref = Reference(
                                file_path=ref_file,
                                line_number=ref.line,
                                column_number=ref.column,
                                context="",  # Can be enhanced later if needed
                            )
                            usage_references.append(usage_ref)

            except Exception as e:
                logger.debug(f"Jedi reference finding failed for {construct.full_name}: {e}")
                # Fall back to alternative method
                fallback_refs = self._fallback_search(construct, search_paths)
                usage_references.extend(fallback_refs)

        except Exception as e:
            logger.error(f"Error finding usages for {construct.full_name}: {e}")

        logger.debug(f"Found {len(usage_references)} usage references for {construct.full_name}")
        return usage_references

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
        # For modules, we can't find them by name in the source
        # Use line 1, column 0 as the module start
        if construct.type == ConstructType.MODULE:
            return (1, 0)

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

    def _find_module_imports(self, construct: Construct, search_paths: list[Path]) -> list[Reference]:
        """
        Find imports of a module across the codebase.

        Args:
            construct: The module construct to search for
            search_paths: List of paths to search within

        Returns:
            List of Reference objects where the module is imported

        Used in:
        - analyzer/jedi_analyzer.py
        """
        usage_references = []
        module_name = construct.full_name

        # Create import patterns to search for
        import_patterns = [
            f"import {module_name}",
            f"from {module_name} import",
            f"from {module_name}.",
        ]

        for search_path in search_paths:
            files_to_search = [search_path] if search_path.is_file() else list(search_path.rglob("*.py"))

            for file_path in files_to_search:
                if file_path == construct.file_path:
                    continue  # Skip the module's own file

                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Check if any import patterns appear in the file
                    if any(pattern in content for pattern in import_patterns):
                        # Create a Reference object with line number from import
                        usage_ref = Reference(
                            file_path=file_path,
                            line_number=1,  # Assuming import statements are at the top of the file
                            column_number=0,  # Assuming import statements are at the start of the file
                            context="",  # Can be enhanced later if needed
                        )
                        usage_references.append(usage_ref)

                except Exception as e:
                    logger.debug(f"Error reading {file_path} for module import search: {e}")

        return usage_references

    def _fallback_search(self, construct: Construct, search_paths: list[Path]) -> list[Reference]:
        """
        Fallback search method using simple text matching.

        Args:
            construct: The construct to search for
            search_paths: List of paths to search within

        Returns:
            List of Reference objects where the construct is used

        Used in:
        - analyzer/jedi_analyzer.py
        """
        usage_references = []

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
                        # Create a Reference object with line number from search
                        usage_ref = Reference(
                            file_path=file_path,
                            line_number=1,  # Assuming search terms are at the top of the file
                            column_number=0,  # Assuming search terms are at the start of the file
                            context="",  # Can be enhanced later if needed
                        )
                        usage_references.append(usage_ref)

                except Exception as e:
                    logger.debug(f"Error reading {file_path} for fallback search: {e}")

        return usage_references

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

    def analyze_batch(self, constructs: list[Construct], search_paths: list[Path]) -> dict[str, list[Reference]]:
        """
        Analyze multiple constructs in batch.

        Args:
            constructs: List of constructs to analyze
            search_paths: List of paths to search within

        Returns:
            Dictionary mapping construct full names to lists of usage references

        Used in:
        - analyzer/hybrid_analyzer.py
        - analyzer/jedi_analyzer.py
        - src/uzpy/analyzer/hybrid_analyzer.py
        - uzpy/analyzer/hybrid_analyzer.py
        """
        logger.info(f"Analyzing {len(constructs)} constructs with Jedi")
        start_time = time.time()

        results = {}

        for i, construct in enumerate(constructs):
            if i % 10 == 0:
                logger.debug(f"Processed {i}/{len(constructs)} constructs")

            try:
                usage_references = self.find_usages(construct, search_paths)
                results[construct.full_name] = usage_references
            except Exception as e:
                logger.error(f"Error analyzing {construct.full_name}: {e}")
                results[construct.full_name] = []

        elapsed = time.time() - start_time
        logger.info(f"Jedi analysis completed in {elapsed:.2f}s")

        return results

    def get_project_info(self) -> dict[str, any]:
        """Get information about the Jedi project.

        Used in:
        - analyzer/hybrid_analyzer.py
        - analyzer/jedi_analyzer.py
        - src/uzpy/analyzer/hybrid_analyzer.py
        - uzpy/analyzer/hybrid_analyzer.py
        """
        try:
            return {
                "project_path": str(self.project_path),
                "sys_path": self.project.sys_path,
            }
        except Exception as e:
            return {"error": str(e)}
