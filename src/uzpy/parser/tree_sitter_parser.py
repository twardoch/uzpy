# this_file: src/uzpy/parser/tree_sitter_parser.py

"""
Tree-sitter based parser for extracting Python constructs.

This module uses Tree-sitter to parse Python code and extract function,
class, and method definitions with their locations and existing docstrings.
Tree-sitter provides fast, incremental parsing with excellent error recovery.

Used in:
- parser/tree_sitter_parser.py
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import tree_sitter_python as tspython
from loguru import logger
from tree_sitter import Language, Node, Parser


class ConstructType(Enum):
    """Types of Python constructs we can analyze.

    Used in:
    - parser/tree_sitter_parser.py
    """

    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    MODULE = "module"


@dataclass
class Construct:
    """
    Represents a Python construct (function, class, method, module) with metadata.

    Attributes:
        name: The name of the construct
        type: The type of construct (function, class, method, module)
        file_path: Path to the file containing this construct
        line_number: Line number where the construct is defined (1-based)
        docstring: Existing docstring content (None if no docstring)
        full_name: Fully qualified name including class/module context
        node: The Tree-sitter node (for internal use)

    Used in:
    - parser/tree_sitter_parser.py
    """

    name: str
    type: ConstructType
    file_path: Path
    line_number: int
    docstring: str | None
    full_name: str
    node: Node | None = None  # Keep reference to tree-sitter node

    def __post_init__(self):
        """Clean up docstring formatting after initialization.

        Used in:
        - parser/tree_sitter_parser.py
        """
        if self.docstring:
            self.docstring = self._clean_docstring(self.docstring)

    def _clean_docstring(self, docstring: str) -> str:
        """
        Clean and normalize docstring formatting.

        Removes extra indentation and normalizes quotes while preserving content.

        Used in:
        - parser/tree_sitter_parser.py
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
        """Make Construct hashable based on its unique identifying attributes.

        Used in:
        - parser/tree_sitter_parser.py
        """
        return hash((self.name, self.type, str(self.file_path), self.line_number, self.full_name))

    def __eq__(self, other) -> bool:
        """Compare constructs based on their unique identifying attributes.

        Used in:
        - parser/tree_sitter_parser.py
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
    - parser/tree_sitter_parser.py
    """

    file_path: Path
    line_number: int
    column_number: int = 0
    context: str = ""


class TreeSitterParser:
    """
    Tree-sitter based parser for extracting Python constructs.

    Provides fast parsing with error recovery and incremental capabilities.
    Extracts functions, classes, methods, and modules with their docstrings.

    Used in:
    - parser/tree_sitter_parser.py
    """

    def __init__(self):
        """Initialize the Tree-sitter parser for Python.

        Used in:
        - parser/tree_sitter_parser.py
        """
        # tspython.language() returns a PyCapsule that needs to be wrapped
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)

        # Queries for finding different construct types
        self._init_queries()

        logger.debug("Tree-sitter parser initialized")

    def _init_queries(self) -> None:
        """Initialize Tree-sitter queries for finding constructs.

        Used in:
        - parser/tree_sitter_parser.py
        """
        # Query for function definitions
        self.function_query = self.language.query("""
        (function_definition
          name: (identifier) @function_name
          body: (block) @function_body) @function_def
        """)

        # Query for class definitions
        self.class_query = self.language.query("""
        (class_definition
          name: (identifier) @class_name
          body: (block) @class_body) @class_def
        """)

        # Query for method definitions (functions inside classes)
        self.method_query = self.language.query("""
        (class_definition
          body: (block
            (function_definition
              name: (identifier) @method_name
              body: (block) @method_body) @method_def)) @class_def
        """)

        # Query for docstrings (string expressions at start of blocks)
        self.docstring_query = self.language.query("""
        (block
          (expression_statement
            (string) @docstring) @doc_stmt) @block
        """)

    def parse_file(self, file_path: Path) -> list[Construct]:
        """
        Parse a Python file and extract all constructs.

        Args:
            file_path: Path to the Python file to parse

        Returns:
            List of Construct objects found in the file

        Raises:
            FileNotFoundError: If the file doesn't exist
            UnicodeDecodeError: If the file can't be decoded as UTF-8

        Used in:
        - parser/tree_sitter_parser.py
        """
        logger.debug(f"Parsing file: {file_path}")

        try:
            with open(file_path, "rb") as f:
                source_code = f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error in {file_path}: {e}")
            raise

        # Parse with Tree-sitter
        tree = self.parser.parse(source_code)

        if tree.root_node.has_error:
            logger.warning(f"Parse errors in {file_path}, continuing with partial parse")

        # Extract constructs
        constructs = []

        # Get source code as string for node text extraction
        source_text = source_code.decode("utf-8")

        # Extract module-level constructs
        constructs.extend(self._extract_functions(tree.root_node, file_path, source_text))
        constructs.extend(self._extract_classes(tree.root_node, file_path, source_text))
        constructs.extend(self._extract_methods(tree.root_node, file_path, source_text))

        # Add module construct
        module_construct = self._create_module_construct(file_path, tree.root_node, source_text)
        if module_construct:
            constructs.append(module_construct)

        logger.debug(f"Found {len(constructs)} constructs in {file_path}")
        return constructs

    def _extract_functions(self, root_node: Node, file_path: Path, source_text: str) -> list[Construct]:
        """Extract function definitions from the AST.

        Used in:
        - parser/tree_sitter_parser.py
        """
        functions = []

        captures = self.function_query.captures(root_node)

        # Process function definitions
        for function_def in captures.get("function_def", []):
            # Get captures for this specific function
            func_captures = self.function_query.captures(function_def)

            function_name = None
            function_body = None

            # Extract name and body
            if "function_name" in func_captures:
                function_name = self._get_node_text(func_captures["function_name"][0], source_text)
            if "function_body" in func_captures:
                function_body = func_captures["function_body"][0]

            if function_name and function_body:
                # Check if this is actually a method (inside a class)
                is_method = self._is_inside_class(function_def)
                construct_type = ConstructType.METHOD if is_method else ConstructType.FUNCTION

                # Get docstring
                docstring = self._extract_docstring(function_body, source_text)

                # Calculate line number (Tree-sitter uses 0-based, we want 1-based)
                line_number = function_def.start_point[0] + 1

                # Build full name
                full_name = self._build_full_name(function_def, function_name, source_text)

                construct = Construct(
                    name=function_name,
                    type=construct_type,
                    file_path=file_path,
                    line_number=line_number,
                    docstring=docstring,
                    full_name=full_name,
                    node=function_def,
                )

                functions.append(construct)

        return functions

    def _extract_classes(self, root_node: Node, file_path: Path, source_text: str) -> list[Construct]:
        """Extract class definitions from the AST.

        Used in:
        - parser/tree_sitter_parser.py
        """
        classes = []

        captures = self.class_query.captures(root_node)

        # Process class definitions
        for class_def in captures.get("class_def", []):
            # Get captures for this specific class
            class_captures = self.class_query.captures(class_def)

            class_name = None
            class_body = None

            # Extract name and body
            if "class_name" in class_captures:
                class_name = self._get_node_text(class_captures["class_name"][0], source_text)
            if "class_body" in class_captures:
                class_body = class_captures["class_body"][0]

            if class_name and class_body:
                # Get docstring
                docstring = self._extract_docstring(class_body, source_text)

                # Calculate line number
                line_number = class_def.start_point[0] + 1

                # Build full name
                full_name = self._build_full_name(class_def, class_name, source_text)

                construct = Construct(
                    name=class_name,
                    type=ConstructType.CLASS,
                    file_path=file_path,
                    line_number=line_number,
                    docstring=docstring,
                    full_name=full_name,
                    node=class_def,
                )

                classes.append(construct)

        return classes

    def _extract_methods(self, root_node: Node, file_path: Path, source_text: str) -> list[Construct]:
        """Extract method definitions from classes.

        Used in:
        - parser/tree_sitter_parser.py
        """
        methods = []

        captures = self.method_query.captures(root_node)

        # Process method definitions
        for method_def in captures.get("method_def", []):
            # Get the containing class
            class_def = captures.get("class_def", [None])[0]
            if not class_def:
                continue

            # Get captures for this specific method
            method_captures = self.method_query.captures(method_def)

            method_name = None
            method_body = None

            # Extract name and body
            if "method_name" in method_captures:
                method_name = self._get_node_text(method_captures["method_name"][0], source_text)
            if "method_body" in method_captures:
                method_body = method_captures["method_body"][0]

            if method_name and method_body:
                # Get docstring
                docstring = self._extract_docstring(method_body, source_text)

                # Calculate line number
                line_number = method_def.start_point[0] + 1

                # Build full name (including class)
                full_name = self._build_full_name(method_def, method_name, source_text)

                construct = Construct(
                    name=method_name,
                    type=ConstructType.METHOD,
                    file_path=file_path,
                    line_number=line_number,
                    docstring=docstring,
                    full_name=full_name,
                    node=method_def,
                )

                methods.append(construct)

        return methods

    def _create_module_construct(self, file_path: Path, root_node: Node, source_text: str) -> Construct | None:
        """Create a construct representing the module itself.

        Used in:
        - parser/tree_sitter_parser.py
        """
        # Look for module-level docstring (first statement is a string)
        docstring = None

        # Check first statement
        for child in root_node.children:
            if child.type == "expression_statement":
                for grandchild in child.children:
                    if grandchild.type == "string":
                        docstring = self._get_node_text(grandchild, source_text)
                        break
                break

        module_name = file_path.stem
        full_name = str(file_path.relative_to(file_path.anchor)).replace("/", ".").replace("\\", ".")
        if full_name.endswith(".py"):
            full_name = full_name[:-3]

        return Construct(
            name=module_name,
            type=ConstructType.MODULE,
            file_path=file_path,
            line_number=1,
            docstring=docstring,
            full_name=full_name,
            node=root_node,
        )

    def _extract_docstring(self, body_node: Node, source_text: str) -> str | None:
        """Extract docstring from a function or class body.

        Used in:
        - parser/tree_sitter_parser.py
        """
        # Look for the first expression statement that contains a string
        for child in body_node.children:
            if child.type == "expression_statement":
                for grandchild in child.children:
                    if grandchild.type == "string":
                        return self._get_node_text(grandchild, source_text)
        return None

    def _get_node_text(self, node: Node, source_text: str) -> str:
        """Get the text content of a Tree-sitter node.

        Used in:
        - parser/tree_sitter_parser.py
        """
        start_byte = node.start_byte
        end_byte = node.end_byte
        return source_text[start_byte:end_byte]

    def _is_inside_class(self, node: Node) -> bool:
        """Check if a node is inside a class definition.

        Used in:
        - parser/tree_sitter_parser.py
        """
        parent = node.parent
        while parent:
            if parent.type == "class_definition":
                return True
            parent = parent.parent
        return False

    def _build_full_name(self, node: Node, name: str, source_text: str) -> str:
        """Build the fully qualified name for a construct.

        Used in:
        - parser/tree_sitter_parser.py
        """
        parts = [name]

        # Walk up the tree to find containing classes
        parent = node.parent
        while parent:
            if parent.type == "class_definition":
                # Find the class name
                for child in parent.children:
                    if child.type == "identifier":
                        class_name = self._get_node_text(child, source_text)
                        parts.insert(0, class_name)
                        break
            parent = parent.parent

        return ".".join(parts)

    def get_statistics(self, file_path: Path) -> dict[str, int]:
        """Get parsing statistics for a file.

        Used in:
        - parser/tree_sitter_parser.py
        """
        constructs = self.parse_file(file_path)

        return {
            "total_constructs": len(constructs),
            "functions": sum(1 for c in constructs if c.type == ConstructType.FUNCTION),
            "methods": sum(1 for c in constructs if c.type == ConstructType.METHOD),
            "classes": sum(1 for c in constructs if c.type == ConstructType.CLASS),
            "modules": sum(1 for c in constructs if c.type == ConstructType.MODULE),
            "with_docstrings": sum(1 for c in constructs if c.docstring),
            "without_docstrings": sum(1 for c in constructs if not c.docstring),
        }
