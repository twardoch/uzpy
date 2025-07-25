# this_file: src/uzpy/modifier/safe_modifier.py

"""
Safe docstring modifier that prevents Python syntax corruption.

This module provides enhanced safety features compared to the standard
LibCST modifier, including proper quote handling and syntax validation.
"""

import ast
import re
import shutil
from pathlib import Path

import libcst as cst
from libcst import SimpleString
from loguru import logger

from uzpy.types import Construct, Reference


class SafeDocstringModifier(cst.CSTTransformer):
    """
    Enhanced docstring modifier with corruption prevention.
    
    This transformer includes additional safety checks to ensure
    that docstring modifications don't result in invalid Python syntax.
    """
    
    def __init__(self, usage_map: dict[Construct, list[Reference]], project_root: Path):
        """Initialize the safe docstring modifier."""
        self.usage_map = usage_map
        self.project_root = project_root
        self.current_file = None
        
        # Build lookup map
        self.construct_lookup = {}
        for construct in usage_map:
            if construct.file_path not in self.construct_lookup:
                self.construct_lookup[construct.file_path] = {}
            self.construct_lookup[construct.file_path][construct.name] = construct
            
    def set_current_file(self, file_path: Path) -> None:
        """Set the current file being processed."""
        self.current_file = file_path
        
    def _safe_create_docstring(self, content: str, original_quotes: str = None) -> str:
        """
        Create a safe docstring that won't cause syntax errors.
        
        Args:
            content: The docstring content (without quotes)
            original_quotes: The original quote style used (optional)
            
        Returns:
            A properly quoted docstring
        """
        # Determine the best quote style to use
        if original_quotes:
            # Check if we can safely use the original quote style
            if original_quotes == '"""' and '"""' not in content:
                return f'"""{content}"""'
            elif original_quotes == "'''" and "'''" not in content:
                return f"'''{content}'''"
            elif original_quotes == '"' and '"' not in content and '\n' not in content:
                return f'"{content}"'
            elif original_quotes == "'" and "'" not in content and '\n' not in content:
                return f"'{content}'"
        
        # Choose the safest quote style based on content
        if '"""' not in content and "'''" not in content:
            # Prefer triple double quotes for multi-line
            if '\n' in content:
                return f'"""{content}"""'
            # For single line, use single quotes if possible
            elif '"' not in content:
                return f'"{content}"'
            elif "'" not in content:
                return f"'{content}'"
            else:
                # Escape quotes and use double quotes
                escaped_content = content.replace('"', '\\"')
                return f'"{escaped_content}"'
        elif '"""' not in content:
            return f'"""{content}"""'
        elif "'''" not in content:
            return f"'''{content}'''"
        else:
            # Complex case: both triple quote styles present
            # Use raw string or escape the quotes
            if '\\' not in content:
                # Can use raw string
                if '"""' in content and "'''" not in content:
                    return f"r'''{content}'''"
                elif "'''" in content and '"""' not in content:
                    return f'r"""{content}"""'
            
            # Last resort: escape the less common quote style
            if content.count('"""') <= content.count("'''"):
                escaped_content = content.replace('"""', '\\"\\"\\"')
                return f'"""{escaped_content}"""'
            else:
                escaped_content = content.replace("'''", "\\'\\'\\'")
                return f"'''{escaped_content}'''"
    
    def _extract_docstring_info(self, docstring_node: SimpleString) -> tuple[str, str]:
        """
        Extract content and quote style from a docstring node.
        
        Returns:
            Tuple of (content, quote_style)
        """
        raw_value = docstring_node.value
        
        # Determine quote style
        if raw_value.startswith('"""'):
            quote_style = '"""'
            content = raw_value[3:-3]
        elif raw_value.startswith("'''"):
            quote_style = "'''"
            content = raw_value[3:-3]
        elif raw_value.startswith('"'):
            quote_style = '"'
            content = raw_value[1:-1]
        elif raw_value.startswith("'"):
            quote_style = "'"
            content = raw_value[1:-1]
        else:
            # Fallback
            quote_style = '"""'
            content = raw_value
            
        return content, quote_style
    
    def _update_docstring_content(self, current_docstring: str, references: list[Reference]) -> str:
        """Update docstring content with usage information safely."""
        # Extract content and quote style
        content, quote_style = self._extract_docstring_info(
            cst.SimpleString(current_docstring)
        )
        
        # Extract existing usage paths and clean content
        cleaned_content, existing_paths, original_indent = self._extract_existing_usage_paths(content)
        
        # Detect base indentation
        lines = content.split("\n")
        base_indent = ""
        if len(lines) > 1:
            for line in lines[1:]:
                if line.strip():
                    base_indent = line[: len(line) - len(line.lstrip())]
                    break
        
        if original_indent:
            base_indent = original_indent
        
        # Convert references to relative paths
        new_paths = set()
        for ref in references:
            if self.current_file and ref.file_path.resolve() == self.current_file.resolve():
                continue
            try:
                resolved_file = ref.file_path.resolve()
                resolved_root = self.project_root.resolve()
                rel_path = resolved_file.relative_to(resolved_root)
            except ValueError:
                try:
                    rel_path = ref.file_path.relative_to(self.project_root)
                except ValueError:
                    rel_path = ref.file_path
            new_paths.add(str(rel_path))
        
        # Merge paths
        all_paths = existing_paths | new_paths
        
        # Generate usage section
        if all_paths:
            usage_lines = []
            for path in sorted(all_paths):
                usage_lines.append(f"{base_indent}- {path}")
            usage_section = f"{base_indent}Used in:\n" + "\n".join(usage_lines)
        else:
            usage_section = ""
        
        # Combine content
        if cleaned_content.strip():
            if usage_section:
                updated_content = f"{cleaned_content.rstrip()}\n\n{usage_section}"
            else:
                updated_content = cleaned_content
        else:
            updated_content = usage_section
        
        # Add proper indentation for closing quotes
        if quote_style == '"""' and base_indent and '\n' in updated_content:
            updated_content = f"{updated_content}\n{base_indent}"
        
        # Create safe docstring
        return self._safe_create_docstring(updated_content, quote_style)
    
    def _extract_existing_usage_paths(self, content: str) -> tuple[str, set[str], str]:
        """Extract existing 'Used in:' paths from docstring."""
        pattern = r"(\n\s*)(Used in:(?:\s*\n(?:\s*-\s*[^\n]+\n?)*)\s*)"
        
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if not match:
            return content, set(), ""
        
        # Extract indentation
        indent_match = re.search(r"\n\n?(\s*)Used in:", content)
        original_indent = indent_match.group(1) if indent_match else ""
        
        # Extract paths
        existing_paths = set()
        usage_section = match.group(2)
        path_pattern = r"\s*-\s*(.+?)(?:\n|$)"
        for path_match in re.finditer(path_pattern, usage_section):
            path = path_match.group(1).strip()
            if path:
                existing_paths.add(path)
        
        # Remove usage section
        cleaned_content = re.sub(pattern, "", content, flags=re.MULTILINE | re.DOTALL)
        
        return cleaned_content, existing_paths, original_indent
    
    def _validate_syntax(self, code: str) -> bool:
        """Validate that code has valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    def _find_construct(self, name: str) -> Construct | None:
        """Find a construct by name in the current file."""
        if not self.current_file or self.current_file not in self.construct_lookup:
            return None
        
        file_constructs = self.construct_lookup[self.current_file]
        return file_constructs.get(name)
    
    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        """Update function docstrings safely."""
        return self._update_construct_docstring(original_node, updated_node, "function")
    
    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        """Update class docstrings safely."""
        return self._update_construct_docstring(original_node, updated_node, "class")
    
    def _update_construct_docstring(self, original_node, updated_node, construct_type: str):
        """Update a construct's docstring with safety checks."""
        # Get construct name
        name = original_node.name.value
        
        # Find construct in usage map
        construct = self._find_construct(name)
        if not construct:
            return updated_node
        
        # Get references
        references = self.usage_map.get(construct, [])
        if not references:
            return updated_node
        
        # Get existing docstring
        docstring_node = self._get_docstring_node(updated_node)
        
        if docstring_node:
            # Update existing docstring
            new_docstring = self._update_docstring_content(docstring_node.value, references)
            
            # Validate the new docstring won't cause syntax errors
            test_code = f"def test():\n    {new_docstring}\n    pass"
            if not self._validate_syntax(test_code):
                logger.warning(f"Skipping docstring update for {name} - would create invalid syntax")
                return updated_node
            
            # Create new docstring node
            new_docstring_node = cst.SimpleString(new_docstring)
            return self._replace_docstring_in_node(updated_node, new_docstring_node)
        else:
            # Add new docstring
            new_docstring = self._create_new_docstring(references)
            
            # Validate
            test_code = f"def test():\n    {new_docstring}\n    pass"
            if not self._validate_syntax(test_code):
                logger.warning(f"Skipping docstring creation for {name} - would create invalid syntax")
                return updated_node
            
            return self._add_docstring_to_node(updated_node, new_docstring)
    
    def _get_docstring_node(self, node) -> SimpleString | None:
        """Extract the docstring node from a function or class."""
        body = None
        
        if hasattr(node, "body") and isinstance(node.body, cst.IndentedBlock):
            body = node.body.body
        elif hasattr(node, "body") and isinstance(node.body, list):
            body = node.body
        
        if not body:
            return None
        
        first_stmt = body[0]
        if isinstance(first_stmt, cst.SimpleStatementLine) and len(first_stmt.body) == 1:
            expr = first_stmt.body[0]
            if isinstance(expr, cst.Expr) and isinstance(expr.value, cst.SimpleString):
                return expr.value
        
        return None
    
    def _create_new_docstring(self, references: list[Reference]) -> str:
        """Create a new docstring with usage information."""
        base_indent = "    "
        
        relative_paths = set()
        for ref in references:
            if self.current_file and ref.file_path.resolve() == self.current_file.resolve():
                continue
            try:
                resolved_file = ref.file_path.resolve()
                resolved_root = self.project_root.resolve()
                rel_path = resolved_file.relative_to(resolved_root)
            except ValueError:
                try:
                    rel_path = ref.file_path.relative_to(self.project_root)
                except ValueError:
                    rel_path = ref.file_path
            relative_paths.add(str(rel_path))
        
        if relative_paths:
            usage_lines = []
            for path in sorted(relative_paths):
                usage_lines.append(f"{base_indent}- {path}")
            usage_section = f"Used in:\n" + "\n".join(usage_lines)
            return self._safe_create_docstring(usage_section)
        
        return '""""""'
    
    def _add_docstring_to_node(self, node, docstring: str):
        """Add a docstring to a node that doesn't have one."""
        new_docstring_stmt = cst.SimpleStatementLine([cst.Expr(cst.SimpleString(docstring))])
        
        if hasattr(node, "body") and isinstance(node.body, cst.IndentedBlock):
            old_body = node.body.body
            new_body = [new_docstring_stmt, *list(old_body)]
            return node.with_changes(body=node.body.with_changes(body=new_body))
        
        return node
    
    def _replace_docstring_in_node(self, node, new_docstring_node):
        """Replace the docstring in a node."""
        if hasattr(node, "body") and isinstance(node.body, cst.IndentedBlock):
            old_body = list(node.body.body)
            if old_body and isinstance(old_body[0], cst.SimpleStatementLine):
                old_stmt = old_body[0]
                if len(old_stmt.body) == 1 and isinstance(old_stmt.body[0], cst.Expr):
                    new_expr = old_stmt.body[0].with_changes(value=new_docstring_node)
                    new_stmt = old_stmt.with_changes(body=[new_expr])
                    new_body = [new_stmt, *old_body[1:]]
                    return node.with_changes(body=node.body.with_changes(body=new_body))
        
        return node


class SafeLibCSTModifier:
    """
    Safe high-level interface for modifying Python files with LibCST.
    
    This version includes additional safety features to prevent
    corruption of Python source files.
    """
    
    def __init__(self, project_root: Path):
        """Initialize the safe modifier."""
        self.project_root = project_root
    
    def modify_file(self, file_path: Path, usage_map: dict[Construct, list[Reference]], 
                    dry_run: bool = False, backup: bool = True) -> bool:
        """
        Safely modify a file's docstrings with usage information.
        
        Args:
            file_path: Path to the Python file to modify
            usage_map: Mapping of constructs to their usage references
            dry_run: If True, don't actually write changes
            backup: If True, create a backup before modifying
            
        Returns:
            True if the file was successfully modified, False otherwise
        """
        try:
            # Read the source code
            with open(file_path, encoding="utf-8") as f:
                source_code = f.read()
            
            # Validate original syntax
            if not self._validate_syntax(source_code):
                logger.error(f"Original file {file_path} has syntax errors - skipping")
                return False
            
            # Create backup if requested
            if backup and not dry_run:
                backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                shutil.copy2(file_path, backup_path)
            
            # Parse with LibCST
            tree = cst.parse_module(source_code)
            
            # Create and run transformer
            transformer = SafeDocstringModifier(usage_map, self.project_root)
            transformer.set_current_file(file_path)
            modified_tree = tree.visit(transformer)
            
            # Generate modified code
            modified_code = modified_tree.code
            
            # Validate modified syntax
            if not self._validate_syntax(modified_code):
                logger.error(f"Modified code for {file_path} has syntax errors - skipping")
                if backup and not dry_run:
                    # Restore from backup
                    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                    if backup_path.exists():
                        shutil.move(backup_path, file_path)
                return False
            
            # Write changes if not dry run
            if not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(modified_code)
                
                # Remove backup if successful
                if backup:
                    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                    if backup_path.exists():
                        backup_path.unlink()
            
            logger.info(f"Successfully modified {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error modifying {file_path}: {e}")
            # Restore from backup if exists
            if backup and not dry_run:
                backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                if backup_path.exists():
                    shutil.move(backup_path, file_path)
            return False
    
    def _validate_syntax(self, code: str) -> bool:
        """Validate that code has valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False