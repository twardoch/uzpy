# this_file: src/uzpy/analyzer/astgrep_analyzer.py

"""
ast-grep based analyzer for structural pattern matching.

This module provides an analyzer that uses ast-grep for intuitive and fast
structural pattern matching across Python codebases.
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Union

from loguru import logger

from uzpy.types import Construct, ConstructType, Reference


class AstGrepAnalyzer:
    """
    Structural pattern matching analyzer using ast-grep.

    This analyzer leverages ast-grep's powerful pattern matching capabilities
    to find complex usage patterns that other analyzers might miss.
    """

    def __init__(self, project_root: Path, exclude_patterns: list[str] | None = None):
        """
        Initialize ast-grep analyzer.

        Args:
            project_root: Root directory of the project
            exclude_patterns: Patterns to exclude from analysis
        """
        self.project_root = project_root
        self.exclude_patterns = exclude_patterns or []

        # Check if ast-grep is available
        try:
            result = subprocess.run(["ast-grep", "--version"], capture_output=True, text=True, check=False)
            logger.debug(f"Using ast-grep {result.stdout.strip()}")
            self.astgrep_cmd = ["ast-grep"]
        except FileNotFoundError:
            # Try the Python bindings
            logger.info("ast-grep CLI not found, using Python bindings")
            self.astgrep_cmd = ["python", "-m", "ast_grep_py"]

    def find_usages(self, construct: Construct, reference_files: list[Path]) -> list[Reference]:
        """
        Find usages of a construct using ast-grep pattern matching.

        Args:
            construct: The construct to find usages for
            reference_files: List of files to search in

        Returns:
            List of references to the construct
        """
        references = []

        # Generate patterns based on construct type
        patterns = self._generate_patterns(construct)

        for pattern in patterns:
            # Run ast-grep for each pattern
            matches = self._search_pattern(pattern, reference_files)
            references.extend(matches)

        # Deduplicate references
        unique_refs = {}
        for ref in references:
            key = (ref.file_path, ref.line_number, ref.column)
            if key not in unique_refs:
                unique_refs[key] = ref

        return list(unique_refs.values())

    def _generate_patterns(self, construct: Construct) -> list[str]:
        """
        Generate ast-grep patterns for different construct types and usage patterns.

        Args:
            construct: The construct to generate patterns for

        Returns:
            List of ast-grep pattern strings
        """
        patterns = []
        name = construct.name

        # Import patterns
        patterns.extend(
            [
                f"import {name}",
                f"import $M, {name}",
                f"from $M import {name}",
                f"from $M import {name}, $$$",
                f"from $M import $A as {name}",
            ]
        )

        if construct.type == ConstructType.FUNCTION:
            # Function call patterns
            patterns.extend(
                [
                    f"{name}($$$)",  # Direct call
                    f"$A.{name}($$$)",  # Method call
                    f"$A = {name}($$$)",  # Assignment
                    f"return {name}($$$)",  # Return
                    f"yield {name}($$$)",  # Yield
                    f"await {name}($$$)",  # Async call
                ]
            )

            # Function reference patterns
            patterns.extend(
                [
                    f"$A = {name}",  # Assignment without call
                    f"callback={name}",  # As callback
                    f"func={name}",  # As parameter
                ]
            )

        elif construct.type == ConstructType.CLASS:
            # Class instantiation patterns
            patterns.extend(
                [
                    f"{name}($$$)",  # Instantiation
                    f"$A = {name}($$$)",  # Assignment
                    f"return {name}($$$)",  # Return instance
                ]
            )

            # Inheritance patterns
            patterns.extend(
                [
                    f"class $A({name})",  # Direct inheritance
                    f"class $A({name}, $$$)",  # Multiple inheritance
                    f"class $A($$$, {name})",  # Multiple inheritance
                ]
            )

            # Type annotation patterns
            patterns.extend(
                [
                    f"$A: {name}",  # Variable annotation
                    f"-> {name}",  # Return annotation
                    f"$A: list[{name}]",  # Generic annotation
                    f"$A: Optional[{name}]",  # Optional annotation
                ]
            )

        elif construct.type == ConstructType.METHOD:
            # Method call patterns
            patterns.extend(
                [
                    f"$A.{name}($$$)",  # Method call
                    f"self.{name}($$$)",  # Self method call
                    f"super().{name}($$$)",  # Super call
                ]
            )

        elif construct.type == ConstructType.VARIABLE:
            # Variable usage patterns
            patterns.extend(
                [
                    f"{name}",  # Direct usage
                    f"{name}.$A",  # Attribute access
                    f"{name}[$A]",  # Subscript
                    f"$A = {name}",  # Assignment from
                    f"{name} = $A",  # Assignment to
                ]
            )

        return patterns

    def _search_pattern(self, pattern: str, files: list[Path]) -> list[Reference]:
        """
        Search for a pattern across files using ast-grep.

        Args:
            pattern: ast-grep pattern to search for
            files: List of files to search in

        Returns:
            List of references found
        """
        references = []

        # Process files in batches to avoid command line length limits
        for file_batch in self._batch_files(files, 50):
            cmd = (
                self.astgrep_cmd
                + [
                    "--lang",
                    "python",
                    "--pattern",
                    pattern,
                    "--json",
                ]
                + [str(f) for f in file_batch]
            )

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if result.stdout:
                    matches = self._parse_astgrep_output(result.stdout)
                    references.extend(matches)
            except subprocess.SubprocessError as e:
                logger.debug(f"ast-grep search failed for pattern '{pattern}': {e}")

        return references

    def _parse_astgrep_output(self, output: str) -> list[Reference]:
        """
        Parse ast-grep JSON output to extract references.

        Args:
            output: ast-grep JSON output

        Returns:
            List of references
        """
        references = []

        try:
            # ast-grep outputs one JSON object per line
            for line in output.strip().split("\n"):
                if not line:
                    continue

                match = json.loads(line)

                # Extract file path and location
                file_path = Path(match.get("file", ""))

                # Get match location
                range_info = match.get("range", {})
                start = range_info.get("start", {})
                line = start.get("line", 0) + 1  # ast-grep uses 0-based lines
                column = start.get("column", 0)

                # Get matched text as context
                text = match.get("text", "")

                if file_path and line > 0:
                    references.append(
                        Reference(
                            file_path=file_path,
                            line_number=line,
                            column=column,
                            context=text[:100],  # Limit context length
                        )
                    )

        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse ast-grep output: {e}")

        return references

    def _batch_files(self, files: list[Path], batch_size: int) -> list[list[Path]]:
        """
        Split files into batches for processing.

        Args:
            files: List of files
            batch_size: Size of each batch

        Returns:
            List of file batches
        """
        return [files[i : i + batch_size] for i in range(0, len(files), batch_size)]
