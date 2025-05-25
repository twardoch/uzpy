# this_file: src/uzpy/modifier/libcst_modifier.py

"""
LibCST-based modifier for updating docstrings with usage information.

This module uses LibCST to safely modify Python source code, preserving
formatting and comments while updating docstrings with where constructs are used.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set

import libcst as cst
from libcst import matchers as m
from loguru import logger

from uzpy.parser import Construct, Reference


class DocstringModifier(cst.CSTTransformer):
    """
    LibCST transformer for updating docstrings with usage information.

    This transformer preserves all formatting and comments while updating
    docstrings to include information about where constructs are used.
    """

    def __init__(self, usage_map: Dict[Construct, List[Reference]], project_root: Path):
        """
        Initialize the docstring modifier.

        Args:
            usage_map: Mapping of constructs to their usage references
            project_root: Root directory of the project for relative paths
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
        """Set the current file being processed."""
        self.current_file = file_path

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        """Update function docstrings with usage information."""
        return self._update_construct_docstring(original_node, updated_node, "function")

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        """Update class docstrings with usage information."""
        return self._update_construct_docstring(original_node, updated_node, "class")

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Update module docstrings with usage information."""
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
                        return updated_node.with_changes(body=[new_stmt] + list(updated_node.body[1:]))

        return updated_node

    def _update_construct_docstring(self, original_node, updated_node, construct_type: str):
        """Generic method to update construct docstrings."""
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
        else:
            # Update existing docstring
            current_content = docstring_node.value
            updated_content = self._update_docstring_content(current_content, references)
            new_docstring_node = docstring_node.with_changes(value=updated_content)
            return self._replace_docstring_in_node(updated_node, new_docstring_node)

    def _find_construct(self, name: str, line_number: int) -> Optional[Construct]:
        """Find a construct by name and line number."""
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
        """Get the line number of a node (simplified - LibCST doesn't store line numbers directly)."""
        # For now, return 1. In a real implementation, we'd need to track positions.
        # This is a limitation we'll address by using the construct's stored line number.
        return 1

    def _get_docstring_node(self, node) -> Optional[cst.SimpleString]:
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

    def _update_docstring_content(self, current_docstring: str, references: List[Reference]) -> str:
        """Update docstring content with usage information."""
        # Remove quotes from current docstring
        quote_char = '"""' if current_docstring.startswith('"""') else '"'
        content = current_docstring.strip(quote_char)

        # Detect and preserve indentation from the original docstring
        lines = content.split('\n')
        base_indent = ""
        if len(lines) > 1:
            # Find indentation from the first non-empty line after the first
            for line in lines[1:]:
                if line.strip():
                    base_indent = line[:len(line) - len(line.lstrip())]
                    break

        # Remove existing usage information if present
        content = self._remove_existing_usage_info(content)

        # Generate usage section with proper indentation
        usage_section = self._generate_usage_section_with_indent(references, base_indent)

        # Combine content and usage
        if content.strip():
            updated_content = f"{content.rstrip()}\n\n{usage_section}"
        else:
            updated_content = usage_section

        return f"{quote_char}{updated_content}{quote_char}"

    def _remove_existing_usage_info(self, content: str) -> str:
        """Remove existing usage information from docstring."""
        # Look for existing usage sections and remove them
        patterns = [
            r"\n\s*Used in:.*?(?=\n\s*\w|\n\s*$|\Z)",
            r"\n\s*Usage:.*?(?=\n\s*\w|\n\s*$|\Z)",
            r"\n\s*References:.*?(?=\n\s*\w|\n\s*$|\Z)",
        ]

        for pattern in patterns:
            content = re.sub(pattern, "", content, flags=re.DOTALL | re.MULTILINE)

        return content

    def _generate_usage_section(self, references: List[Reference]) -> str:
        """Generate the usage section text."""
        if not references:
            return ""

        # Convert to relative paths and deduplicate
        relative_paths = set()
        for ref in references:
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
            relative_paths.add(rel_path)

        # Generate usage lines
        usage_lines = []
        for rel_path in sorted(relative_paths):
            usage_lines.append(f"- {rel_path}")

        # Add one extra newline at the end of the "Used in" list
        return f"Used in:\n" + "\n".join(usage_lines) + "\n"

    def _generate_usage_section_with_indent(self, references: List[Reference], base_indent: str) -> str:
        """Generate the usage section text with proper indentation."""
        if not references:
            return ""

        # Group references by file and convert to relative paths immediately
        relative_paths = set()
        for ref in references:
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
            relative_paths.add(rel_path)

        # Generate usage lines with indentation
        usage_lines = []
        for rel_path in sorted(relative_paths):
            usage_lines.append(f"{base_indent}- {rel_path}")

        # Format with proper indentation and extra newline at the end
        return f"{base_indent}Used in:\n" + "\n".join(usage_lines) + "\n"

    def _create_new_docstring(self, references: List[Reference]) -> str:
        """Create a new docstring with usage information."""
        usage_section = self._generate_usage_section(references)
        return f'"""{usage_section}"""'

    def _add_docstring_to_node(self, node, docstring: str):
        """Add a docstring to a node that doesn't have one."""
        new_docstring_stmt = cst.SimpleStatementLine([cst.Expr(cst.SimpleString(docstring))])

        if hasattr(node, "body") and isinstance(node.body, cst.IndentedBlock):
            # Function or class
            old_body = node.body.body
            new_body = [new_docstring_stmt] + list(old_body)
            return node.with_changes(body=node.body.with_changes(body=new_body))

        return node

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


class LibCSTModifier:
    """
    High-level interface for modifying Python files with LibCST.

    Handles file reading, parsing, transformation, and writing while
    preserving formatting and handling errors gracefully.
    """

    def __init__(self, project_root: Path):
        """
        Initialize the LibCST modifier.

        Args:
            project_root: Root directory of the project for relative paths
        """
        self.project_root = project_root

    def modify_file(self, file_path: Path, usage_map: Dict[Construct, List[Reference]]) -> bool:
        """
        Modify a single file's docstrings with usage information.

        Args:
            file_path: Path to the Python file to modify
            usage_map: Mapping of constructs to their usage references

        Returns:
            True if the file was successfully modified, False otherwise
        """
        try:
            # Read the source code
            with open(file_path, "r", encoding="utf-8") as f:
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

    def modify_files(self, usage_results: Dict[Construct, List[Reference]]) -> Dict[str, bool]:
        """
        Modify multiple files based on usage results.

        Args:
            usage_results: Results from reference analysis

        Returns:
            Dictionary mapping file paths to success status
        """
        # Group constructs by file
        file_constructs: Dict[Path, Dict[Construct, List[Reference]]] = {}

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
