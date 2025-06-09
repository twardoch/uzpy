# this_file: src/uzpy/parser/tree_sitter_parser.py

"""
Tree-sitter based parser for extracting Python constructs.

This module uses Tree-sitter to parse Python code and extract function,
class, and method definitions with their locations and existing docstrings.
Tree-sitter provides fast, incremental parsing with excellent error recovery.

Used in:
- parser/tree_sitter_parser.py
"""

from pathlib import Path

import tree_sitter_python as tspython
from loguru import logger
from tree_sitter import Language, Node, Parser

from uzpy.types import Construct, ConstructType


class TreeSitterParser:
    """
    Tree-sitter based parser for extracting Python constructs.

    Provides fast parsing with error recovery and incremental capabilities.
    Extracts functions, classes, methods, and modules with their docstrings.

    Used in:
    - parser/__init__.py
    - parser/tree_sitter_parser.py
    - pipeline.py
    - src/uzpy/cli.py
    - src/uzpy/parser/__init__.py
    - src/uzpy/pipeline.py
    - tests/test_parser.py
    - uzpy/cli.py
    - uzpy/parser/__init__.py
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
        - pipeline.py
        - src/uzpy/cli.py
        - src/uzpy/pipeline.py
        - tests/test_parser.py
        - uzpy/cli.py
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
            # Find function name and body directly from the function_def node structure
            function_name = None
            function_body = None

            # Look for the identifier (function name) and block (function body) in the function_def children
            for child in function_def.children:
                if child.type == "identifier":
                    function_name = self._get_node_text(child, source_text)
                elif child.type == "block":
                    function_body = child

            if function_name and function_body:
                # Check if this is actually a method (inside a class)
                is_method = self._is_inside_class(function_def)

                # Only process functions that are NOT methods (methods are handled by _extract_methods)
                if not is_method:
                    # Get docstring
                    docstring = self._extract_docstring(function_body, source_text)

                    # Calculate line number (Tree-sitter uses 0-based, we want 1-based)
                    line_number = function_def.start_point[0] + 1

                    # Build full name
                    full_name = self._build_full_name(function_def, function_name, source_text)

                    construct = Construct(
                        name=function_name,
                        type=ConstructType.FUNCTION,
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

            # Find method name and body directly from the method_def node structure
            method_name = None
            method_body = None

            # Look for the identifier (method name) and block (method body) in the method_def children
            for child in method_def.children:
                if child.type == "identifier":
                    method_name = self._get_node_text(child, source_text)
                elif child.type == "block":
                    method_body = child

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

        Tree-sitter works with byte positions, but Python strings use Unicode code points.
        When the source contains non-ASCII characters, byte positions and string indices
        diverge. We need to work with the original bytes and decode the specific slice.

        Used in:
        - parser/tree_sitter_parser.py
        """
        start_byte = node.start_byte
        end_byte = node.end_byte

        # Convert source text back to bytes, slice, then decode
        # This ensures we get the exact bytes that tree-sitter identified
        source_bytes = source_text.encode("utf-8")
        node_bytes = source_bytes[start_byte:end_byte]
        return node_bytes.decode("utf-8")

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
        - tests/test_parser.py
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
