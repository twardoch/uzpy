# this_file: src/uzpy/types.py

"""
Core data types and structures for uzpy.

This module contains all the core data transfer objects used throughout
the application.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING  # Optional removed

if TYPE_CHECKING:
    from tree_sitter import Node


class ConstructType(Enum):
    """Types of Python constructs we can analyze.

    Used in:
    - analyzer/hybrid_analyzer.py
    - analyzer/jedi_analyzer.py
    - analyzer/rope_analyzer.py
    - parser/__init__.py
    - parser/tree_sitter_parser.py
    - src/uzpy/analyzer/hybrid_analyzer.py
    - src/uzpy/analyzer/jedi_analyzer.py
    - src/uzpy/analyzer/rope_analyzer.py
    - src/uzpy/parser/__init__.py
    - src/uzpy/parser/tree_sitter_parser.py
    - tests/test_analyzer.py
    - tests/test_modifier.py
    - tests/test_parser.py
    - types.py
    - uzpy/analyzer/hybrid_analyzer.py
    - uzpy/analyzer/jedi_analyzer.py
    - uzpy/analyzer/rope_analyzer.py
    - uzpy/parser/__init__.py
    - uzpy/parser/tree_sitter_parser.py
    """

    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    MODULE = "module"


@dataclass
class Construct:
    """
    Represents a Python construct (function, class, method, module) with
    metadata.

    Attributes:
        name: The name of the construct
        type: The type of construct (function, class, method, module)
        file_path: Path to the file containing this construct
        line_number: Line number where the construct is defined (1-based)
        docstring: Existing docstring content (None if no docstring)
        full_name: Fully qualified name including class/module context
        node: The Tree-sitter node (for internal use)

    Used in:
    - analyzer/hybrid_analyzer.py
    - analyzer/jedi_analyzer.py
    - analyzer/rope_analyzer.py
    - modifier/libcst_modifier.py
    - parser/__init__.py
    - parser/tree_sitter_parser.py
    - pipeline.py
    - src/uzpy/analyzer/hybrid_analyzer.py
    - src/uzpy/analyzer/jedi_analyzer.py
    - src/uzpy/analyzer/rope_analyzer.py
    - src/uzpy/modifier/libcst_modifier.py
    - src/uzpy/parser/__init__.py
    - src/uzpy/parser/tree_sitter_parser.py
    - src/uzpy/pipeline.py
    - tests/test_analyzer.py
    - tests/test_modifier.py
    - types.py
    - uzpy/analyzer/hybrid_analyzer.py
    - uzpy/analyzer/jedi_analyzer.py
    - uzpy/analyzer/rope_analyzer.py
    - uzpy/modifier/libcst_modifier.py
    - uzpy/parser/__init__.py
    - uzpy/parser/tree_sitter_parser.py
    - uzpy/pipeline.py
    """

    name: str
    type: ConstructType
    file_path: Path
    line_number: int
    docstring: str | None
    full_name: str
    node: "Node | None" = None  # Keep reference to tree-sitter node

    def __post_init__(self):
        """Clean up docstring formatting after initialization.

        Used in:
        - types.py
        """
        if self.docstring:
            self.docstring = self._clean_docstring(self.docstring)

    def _clean_docstring(self, docstring: str) -> str:
        """
        Clean and normalize docstring formatting.

        Removes extra indentation and normalizes quotes while preserving
        content.

        Used in:
        - types.py
        """
        # Remove surrounding quotes
        if docstring.startswith(('"""', "'''")):
            docstring = docstring[3:-3]
        elif docstring.startswith(('"', "'")):
            docstring = docstring[1:-1]

        # Remove common leading indentation
        lines = docstring.split("\n")
        if len(lines) > 1:
            # Find minimum indentation (excluding empty lines)
            min_indent = float("inf")
            for line in lines[1:]:  # Skip first line
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, indent)

            # Remove common indentation
            if min_indent != float("inf"):
                lines = [lines[0]] + [line[min_indent:] if line.strip() else line for line in lines[1:]]

        return "\n".join(lines).strip()

    def __hash__(self) -> int:
        """Make Construct hashable based on unique identifying attributes.

        Used in:
        - types.py
        """
        return hash((self.name, self.type, str(self.file_path), self.line_number, self.full_name))

    def __eq__(self, other) -> bool:
        """Compare constructs based on unique identifying attributes.

        Used in:
        - types.py
        """
        if not isinstance(other, Construct):
            return False
        return (
            self.name == other.name
            and self.type == other.type
            and self.file_path == other.file_path
            and self.line_number == other.line_number
            and self.full_name == other.full_name
        )


@dataclass
class Reference:
    """
    Represents a reference to a construct found in the codebase.

    Attributes:
        file_path: Path to the file containing the reference
        line_number: Line number of the reference (1-based)
        column_number: Column number of the reference (0-based)
        context: Surrounding code context for the reference

    Used in:
    - analyzer/hybrid_analyzer.py
    - analyzer/jedi_analyzer.py
    - analyzer/rope_analyzer.py
    - modifier/libcst_modifier.py
    - parser/__init__.py
    - pipeline.py
    - src/uzpy/analyzer/hybrid_analyzer.py
    - src/uzpy/analyzer/jedi_analyzer.py
    - src/uzpy/analyzer/rope_analyzer.py
    - src/uzpy/modifier/libcst_modifier.py
    - src/uzpy/parser/__init__.py
    - src/uzpy/pipeline.py
    - tests/test_modifier.py
    - types.py
    - uzpy/analyzer/hybrid_analyzer.py
    - uzpy/analyzer/jedi_analyzer.py
    - uzpy/analyzer/rope_analyzer.py
    - uzpy/modifier/libcst_modifier.py
    - uzpy/parser/__init__.py
    - uzpy/pipeline.py
    """

    file_path: Path
    line_number: int
    column_number: int = 0
    context: str = ""
