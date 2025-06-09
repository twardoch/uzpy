# this_file: src/uzpy/modifier/libcst_modifier.py

"""
LibCST-based modifier for updating docstrings with usage information.

This module uses LibCST to safely modify Python source code, preserving
formatting and comments while updating docstrings with where constructs are used.

Used in:
- modifier/libcst_modifier.py
"""

import re
from pathlib import Path
from typing import Optional, Union

import libcst as cst
from libcst import SimpleString
from loguru import logger

from uzpy.types import Construct, Reference


class DocstringModifier(cst.CSTTransformer):
    """
    LibCST transformer for updating docstrings with usage information.

    This transformer preserves all formatting and comments while updating
    docstrings to include information about where constructs are used.

    Used in:
    - modifier/__init__.py
    - modifier/libcst_modifier.py
    - src/uzpy/modifier/__init__.py
    - tests/test_modifier.py
    - uzpy/modifier/__init__.py
    """

    def __init__(self, usage_map: dict[Construct, list[Reference]], project_root: Path):
        """
        Initialize the docstring modifier.

        Args:
            usage_map: Mapping of constructs to their usage references
            project_root: Root directory of the project for relative paths

        Used in:
        - modifier/libcst_modifier.py
        """
        self.usage_map = usage_map
        self.project_root = project_root
        self.current_file = None

        # Build lookup map for faster access
        self.construct_lookup = {}
        for construct in usage_map:
            # Use file path as key for simpler matching
            if construct.file_path not in self.construct_lookup:
                self.construct_lookup[construct.file_path] = {}
            self.construct_lookup[construct.file_path][construct.name] = construct

        logger.debug(f"Built construct lookup for {len(usage_map)} constructs")

    def set_current_file(self, file_path: Path) -> None:
        """Set the current file being processed.

        Used in:
        - modifier/libcst_modifier.py
        """
        self.current_file = file_path

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        """Update function docstrings with usage information.

        Used in:
        - modifier/libcst_modifier.py
        """
        return self._update_construct_docstring(original_node, updated_node, "function")

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        """Update class docstrings with usage information.

        Used in:
        - modifier/libcst_modifier.py
        """
        return self._update_construct_docstring(original_node, updated_node, "class")

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Update module docstrings with usage information.

        Used in:
        - modifier/libcst_modifier.py
        """
        if not updated_node.body:
            return updated_node

        # Check if first statement is a docstring
        first_stmt = updated_node.body[0]
        if isinstance(first_stmt, cst.SimpleStatementLine) and len(first_stmt.body) == 1:
            expr = first_stmt.body[0]
            if isinstance(expr, cst.Expr) and isinstance(expr.value, cst.SimpleString):
                # This is a module docstring
                construct = self._find_construct("__init__", 1)  # Module constructs use __init__
                if construct and construct in self.usage_map:
                    references = self.usage_map[construct]
                    if references:
                        new_docstring = self._update_docstring_content(expr.value.value, references)
                        new_expr = expr.with_changes(value=cst.SimpleString(new_docstring))
                        new_stmt = first_stmt.with_changes(body=[new_expr])
                        return updated_node.with_changes(body=[new_stmt, *list(updated_node.body[1:])])

        return updated_node

    def _update_construct_docstring(self, original_node, updated_node, construct_type: str):
        """Generic method to update construct docstrings.

        Used in:
        - modifier/libcst_modifier.py
        """
        if not self.current_file:
            return updated_node

        # Get the line number and name
        line_number = self._get_node_line(original_node)
        name = original_node.name.value

        # Find the corresponding construct
        construct = self._find_construct(name, line_number)
        if not construct or construct not in self.usage_map:
            return updated_node

        references = self.usage_map[construct]
        if not references:
            return updated_node

        # Find and update the docstring
        docstring_node = self._get_docstring_node(updated_node)
        if docstring_node is None:
            # Add a new docstring if none exists
            new_docstring = self._create_new_docstring(references)
            return self._add_docstring_to_node(updated_node, new_docstring)
        # Update existing docstring
        current_content = docstring_node.value
        updated_content = self._update_docstring_content(current_content, references)
        new_docstring_node = docstring_node.with_changes(value=updated_content)
        return self._replace_docstring_in_node(updated_node, new_docstring_node)

    def _find_construct(self, name: str, line_number: int) -> Construct | None:
        """Find a construct by name and line number.

        Used in:
        - modifier/libcst_modifier.py
        """
        if not self.current_file or self.current_file not in self.construct_lookup:
            return None

        # Simple name-based lookup for now
        file_constructs = self.construct_lookup[self.current_file]
        construct = file_constructs.get(name)

        if construct:
            logger.debug(f"Found construct {name} in {self.current_file}")
        else:
            logger.debug(
                f"Construct {name} not found in {self.current_file}, available: {list(file_constructs.keys())}"
            )

        return construct

    def _get_node_line(self, node) -> int:
        """Get the line number of a node (simplified - LibCST doesn't store line numbers directly).

        Used in:
        - modifier/libcst_modifier.py
        """
        # For now, return 1. In a real implementation, we'd need to track positions.
        # This is a limitation we'll address by using the construct's stored line number.
        return 1

    def _get_docstring_node(self, node) -> SimpleString | None:
        """Extract the docstring node from a function, class, or module.

        Used in:
        - modifier/libcst_modifier.py
        """
        body = None

        if hasattr(node, "body") and isinstance(node.body, cst.IndentedBlock):
            body = node.body.body
        elif hasattr(node, "body") and isinstance(node.body, list):
            body = node.body

        if not body:
            return None

        # Check if first statement is a docstring
        first_stmt = body[0]
        if isinstance(first_stmt, cst.SimpleStatementLine) and len(first_stmt.body) == 1:
            expr = first_stmt.body[0]
            if isinstance(expr, cst.Expr) and isinstance(expr.value, cst.SimpleString):
                return expr.value

        return None

    def _update_docstring_content(self, current_docstring: str, references: list[Reference]) -> str:
        """Update docstring content with usage information.

        Used in:
        - modifier/libcst_modifier.py
        - tests/test_modifier.py
        """
        # Remove quotes from current docstring
        quote_char = '"""' if current_docstring.startswith('"""') else '"'
        content = current_docstring.strip(quote_char)

        # Detect and preserve indentation from the original docstring
        lines = content.split("\n")
        base_indent = ""
        if len(lines) > 1:
            # Find indentation from the first non-empty line after the first
            for line in lines[1:]:
                if line.strip():
                    base_indent = line[: len(line) - len(line.lstrip())]
                    break

        # Extract existing usage paths and clean content
        cleaned_content, existing_paths, original_indent = self._extract_existing_usage_paths(content)

        # Use original indent if found, otherwise use detected base_indent
        if original_indent:
            base_indent = original_indent

        # Convert new references to relative paths, excluding same-file references
        new_paths = set()
        for ref in references:
            # Skip references to the same file being modified
            if self.current_file and ref.file_path.resolve() == self.current_file.resolve():
                continue

            try:
                # Resolve both paths to ensure proper comparison
                resolved_file = ref.file_path.resolve()
                resolved_root = self.project_root.resolve()
                rel_path = resolved_file.relative_to(resolved_root)
            except ValueError:
                # If can't make relative, try with the original paths
                try:
                    rel_path = ref.file_path.relative_to(self.project_root)
                except ValueError:
                    # If still can't make relative, use the file name only
                    rel_path = ref.file_path
            new_paths.add(str(rel_path))

        # Merge existing and new paths
        all_paths = existing_paths | new_paths

        # Generate usage section with merged paths
        if all_paths:
            usage_lines = []
            for path in sorted(all_paths):
                usage_lines.append(f"{base_indent}- {path}")
            usage_section = f"{base_indent}Used in:\n" + "\n".join(usage_lines) + "\n"
        else:
            usage_section = ""

        # Combine content and usage
        updated_content = f"{cleaned_content.rstrip()}\n\n{usage_section}" if cleaned_content.strip() else usage_section

        # Add proper indentation to closing quotes for triple-quoted strings
        if quote_char == '"""' and base_indent:
            return f"{quote_char}{updated_content}{base_indent}{quote_char}"
        return f"{quote_char}{updated_content}{quote_char}"

    def _extract_existing_usage_paths(self, content: str) -> tuple[str, set[str], str]:
        """Extract existing "Used in:" paths from docstring and return cleaned content.

        Args:
            content: The docstring content

        Returns:
            Tuple of (cleaned_content, existing_paths_set, original_indent)

        Used in:
        - tests/test_modifier.py
        """
        # Pattern to match "Used in:" section with paths
        pattern = r"(\n\s*)(Used in:(?:\s*\n(?:\s*-\s*[^\n]+\n?)*)\s*)"

        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if not match:
            return content, set(), ""

        # Extract indentation from the "Used in:" line (look for immediate indentation before "Used in:")
        # Match a newline, then optionally another newline, then capture spaces/tabs before "Used in:"
        indent_match = re.search(r"\n\n?(\s*)Used in:", content)
        if indent_match:
            # Extract just the spaces/tabs, not including newlines
            original_indent = indent_match.group(1)
        else:
            original_indent = ""

        # Extract existing paths
        existing_paths = set()
        usage_section = match.group(2)

        # Find all paths in the usage section (lines starting with -)
        path_pattern = r"\s*-\s*(.+?)(?:\n|$)"
        for path_match in re.finditer(path_pattern, usage_section):
            path = path_match.group(1).strip()
            if path:
                existing_paths.add(path)

        # Remove the entire "Used in:" section from content
        cleaned_content = re.sub(pattern, "", content, flags=re.MULTILINE | re.DOTALL)

        return cleaned_content, existing_paths, original_indent

    def _create_new_docstring(self, references: list[Reference]) -> str:
        """Create a new docstring with usage information.

        Used in:
        - modifier/libcst_modifier.py
        - tests/test_modifier.py
        """
        # For new docstrings, use standard indentation (4 spaces)
        base_indent = "    "

        # Convert references to relative paths, excluding same-file references
        relative_paths = set()
        for ref in references:
            # Skip references to the same file being modified
            if self.current_file and ref.file_path.resolve() == self.current_file.resolve():
                continue

            try:
                # Resolve both paths to ensure proper comparison
                resolved_file = ref.file_path.resolve()
                resolved_root = self.project_root.resolve()
                rel_path = resolved_file.relative_to(resolved_root)
            except ValueError:
                # If can't make relative, try with the original paths
                try:
                    rel_path = ref.file_path.relative_to(self.project_root)
                except ValueError:
                    # If still can't make relative, use the file name only
                    rel_path = ref.file_path
            relative_paths.add(str(rel_path))

        # Generate usage section
        if relative_paths:
            usage_lines = []
            for path in sorted(relative_paths):
                usage_lines.append(f"{base_indent}- {path}")
            usage_section = f"{base_indent}Used in:\n" + "\n".join(usage_lines) + "\n"
        else:
            usage_section = ""

        return f'"""{usage_section}{base_indent}"""'

    def _add_docstring_to_node(self, node, docstring: str):
        """Add a docstring to a node that doesn't have one.

        Used in:
        - modifier/libcst_modifier.py
        """
        new_docstring_stmt = cst.SimpleStatementLine([cst.Expr(cst.SimpleString(docstring))])

        if hasattr(node, "body") and isinstance(node.body, cst.IndentedBlock):
            # Function or class
            old_body = node.body.body
            new_body = [new_docstring_stmt, *list(old_body)]
            return node.with_changes(body=node.body.with_changes(body=new_body))

        return node

    def _replace_docstring_in_node(self, node, new_docstring_node):
        """Replace the docstring in a node.

        Used in:
        - modifier/libcst_modifier.py
        """
        if hasattr(node, "body") and isinstance(node.body, cst.IndentedBlock):
            # Function or class
            old_body = list(node.body.body)
            if old_body and isinstance(old_body[0], cst.SimpleStatementLine):
                old_stmt = old_body[0]
                if len(old_stmt.body) == 1 and isinstance(old_stmt.body[0], cst.Expr):
                    new_expr = old_stmt.body[0].with_changes(value=new_docstring_node)
                    new_stmt = old_stmt.with_changes(body=[new_expr])
                    new_body = [new_stmt] + old_body[1:]
                    return node.with_changes(body=node.body.with_changes(body=new_body))

        return node


class LibCSTModifier:
    """
    High-level interface for modifying Python files with LibCST.

    Handles file reading, parsing, transformation, and writing while
    preserving formatting and handling errors gracefully.

    Used in:
    - modifier/__init__.py
    - modifier/libcst_modifier.py
    - pipeline.py
    - src/uzpy/cli.py
    - src/uzpy/modifier/__init__.py
    - src/uzpy/pipeline.py
    - tests/test_modifier.py
    - uzpy/cli.py
    - uzpy/modifier/__init__.py
    - uzpy/pipeline.py
    """

    def __init__(self, project_root: Path):
        """
        Initialize the LibCST modifier.

        Args:
            project_root: Root directory of the project for relative paths

        Used in:
        - modifier/libcst_modifier.py
        """
        self.project_root = project_root

    def modify_file(self, file_path: Path, usage_map: dict[Construct, list[Reference]]) -> bool:
        """
        Modify a single file's docstrings with usage information.

        Args:
            file_path: Path to the Python file to modify
            usage_map: Mapping of constructs to their usage references

        Returns:
            True if the file was successfully modified, False otherwise

        Used in:
        - modifier/libcst_modifier.py
        - tests/test_modifier.py
        """
        try:
            # Read the source code
            with open(file_path, encoding="utf-8") as f:
                source_code = f.read()

            # Parse with LibCST
            tree = cst.parse_module(source_code)

            # Transform the tree
            modifier = DocstringModifier(usage_map, self.project_root)
            modifier.set_current_file(file_path)
            modified_tree = tree.visit(modifier)

            # Check if any changes were made
            if modified_tree.code == source_code:
                logger.debug(f"No changes needed for {file_path}")
                return False

            # Write back the modified code
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_tree.code)

            logger.info(f"Updated docstrings in {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to modify {file_path}: {e}")
            return False

    def modify_files(self, usage_results: dict[Construct, list[Reference]]) -> dict[str, bool]:
        """
        Modify multiple files based on usage results.

        Args:
            usage_results: Results from reference analysis

        Returns:
            Dictionary mapping file paths to success status

        Used in:
        - modifier/libcst_modifier.py
        - pipeline.py
        - src/uzpy/cli.py
        - src/uzpy/pipeline.py
        - tests/test_modifier.py
        - uzpy/cli.py
        - uzpy/pipeline.py
        """
        # Group constructs by file
        file_constructs: dict[Path, dict[Construct, list[Reference]]] = {}

        logger.debug(f"Processing {len(usage_results)} constructs for modification")

        for construct, references in usage_results.items():
            if not references:  # Skip constructs with no references
                logger.debug(f"Skipping {construct.name} - no references")
                continue

            file_path = construct.file_path
            if file_path not in file_constructs:
                file_constructs[file_path] = {}
            file_constructs[file_path][construct] = references
            logger.debug(f"Will modify {construct.name} in {file_path} ({len(references)} references)")

        logger.info(f"Will modify {len(file_constructs)} files")

        # Modify each file
        results = {}
        for file_path, construct_map in file_constructs.items():
            logger.debug(f"Modifying {file_path} with {len(construct_map)} constructs")
            success = self.modify_file(file_path, construct_map)
            results[str(file_path)] = success

        return results


class DocstringCleaner(cst.CSTTransformer):
    """
    LibCST transformer for removing 'Used in:' sections from docstrings.

    This transformer preserves all formatting and comments while removing
    any 'Used in:' sections from docstrings.

    Used in:
    - modifier/__init__.py
    - src/uzpy/modifier/__init__.py
    - uzpy/modifier/__init__.py
    """

    def __init__(self):
        """Initialize the docstring cleaner."""

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        """Clean function docstrings by removing usage information."""
        return self._clean_construct_docstring(updated_node)

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        """Clean class docstrings by removing usage information."""
        return self._clean_construct_docstring(updated_node)

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Clean module docstrings by removing usage information."""
        if not updated_node.body:
            return updated_node

        # Check if first statement is a docstring
        first_stmt = updated_node.body[0]
        if isinstance(first_stmt, cst.SimpleStatementLine) and len(first_stmt.body) == 1:
            expr = first_stmt.body[0]
            if isinstance(expr, cst.Expr) and isinstance(expr.value, cst.SimpleString):
                # This is a module docstring
                cleaned_content = self._clean_docstring_content(expr.value.value)
                if cleaned_content != expr.value.value:
                    new_expr = expr.with_changes(value=cst.SimpleString(cleaned_content))
                    new_stmt = first_stmt.with_changes(body=[new_expr])
                    return updated_node.with_changes(body=[new_stmt, *list(updated_node.body[1:])])

        return updated_node

    def _clean_construct_docstring(self, updated_node):
        """Generic method to clean construct docstrings."""
        # Find and clean the docstring
        docstring_node = self._get_docstring_node(updated_node)
        if docstring_node is None:
            return updated_node

        # Clean existing docstring
        current_content = docstring_node.value
        cleaned_content = self._clean_docstring_content(current_content)

        if cleaned_content != current_content:
            new_docstring_node = docstring_node.with_changes(value=cleaned_content)
            return self._replace_docstring_in_node(updated_node, new_docstring_node)

        return updated_node

    def _get_docstring_node(self, node) -> SimpleString | None:
        """Extract the docstring node from a function, class, or module."""
        body = None

        if hasattr(node, "body") and isinstance(node.body, cst.IndentedBlock):
            body = node.body.body
        elif hasattr(node, "body") and isinstance(node.body, list):
            body = node.body

        if not body:
            return None

        # Check if first statement is a docstring
        first_stmt = body[0]
        if isinstance(first_stmt, cst.SimpleStatementLine) and len(first_stmt.body) == 1:
            expr = first_stmt.body[0]
            if isinstance(expr, cst.Expr) and isinstance(expr.value, cst.SimpleString):
                return expr.value

        return None

    def _clean_docstring_content(self, current_docstring: str) -> str:
        """Remove 'Used in:' sections from docstring content."""
        # Remove quotes from current docstring
        quote_char = '"""' if current_docstring.startswith('"""') else '"'
        content = current_docstring.strip(quote_char)

        # Use the same pattern as in DocstringModifier to remove "Used in:" sections
        pattern = r"(\n\s*)(Used in:(?:\s*\n(?:\s*-\s*[^\n]+\n?)*)\s*)"
        cleaned_content = re.sub(pattern, "", content, flags=re.MULTILINE | re.DOTALL)

        # Clean up any trailing whitespace
        cleaned_content = cleaned_content.rstrip()

        # Add back quotes
        return f"{quote_char}{cleaned_content}{quote_char}"

    def _replace_docstring_in_node(self, node, new_docstring_node):
        """Replace the docstring in a node."""
        if hasattr(node, "body") and isinstance(node.body, cst.IndentedBlock):
            # Function or class
            old_body = list(node.body.body)
            if old_body and isinstance(old_body[0], cst.SimpleStatementLine):
                old_stmt = old_body[0]
                if len(old_stmt.body) == 1 and isinstance(old_stmt.body[0], cst.Expr):
                    new_expr = old_stmt.body[0].with_changes(value=new_docstring_node)
                    new_stmt = old_stmt.with_changes(body=[new_expr])
                    new_body = [new_stmt] + old_body[1:]
                    return node.with_changes(body=node.body.with_changes(body=new_body))

        return node


class LibCSTCleaner:
    """
    High-level interface for cleaning 'Used in:' sections from Python files.

    Handles file reading, parsing, transformation, and writing while
    preserving formatting and handling errors gracefully.

    Used in:
    - cli.py
    - modifier/__init__.py
    - src/uzpy/cli.py
    - src/uzpy/modifier/__init__.py
    - uzpy/cli.py
    - uzpy/modifier/__init__.py
    """

    def __init__(self, project_root: Path):
        """
        Initialize the LibCST cleaner.

        Args:
            project_root: Root directory of the project

        """
        self.project_root = project_root

    def clean_file(self, file_path: Path) -> bool:
        """
        Clean a single file by removing 'Used in:' sections from docstrings.

        Args:
            file_path: Path to the Python file to clean

        Returns:
            True if the file was successfully cleaned, False otherwise

        """
        try:
            # Read the source code
            with open(file_path, encoding="utf-8") as f:
                source_code = f.read()

            # Parse with LibCST
            tree = cst.parse_module(source_code)

            # Transform the tree
            cleaner = DocstringCleaner()
            cleaned_tree = tree.visit(cleaner)

            # Check if any changes were made
            if cleaned_tree.code == source_code:
                logger.debug(f"No cleaning needed for {file_path}")
                return False

            # Write back the cleaned code
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(cleaned_tree.code)

            logger.info(f"Cleaned 'Used in:' sections from {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to clean {file_path}: {e}")
            return False

    def clean_files(self, file_paths: list[Path]) -> dict[str, bool]:
        """
        Clean multiple files by removing 'Used in:' sections.

        Args:
            file_paths: List of file paths to clean

        Returns:
            Dictionary mapping file paths to success status

        Used in:
        - cli.py
        - src/uzpy/cli.py
        - uzpy/cli.py
        """
        logger.info(f"Cleaning 'Used in:' sections from {len(file_paths)} files")

        results = {}
        for file_path in file_paths:
            logger.debug(f"Cleaning {file_path}")
            success = self.clean_file(file_path)
            results[str(file_path)] = success

        return results
