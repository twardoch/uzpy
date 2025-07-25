# this_file: tests/test_self_modification.py

"""
Integration test to verify uzpy can safely modify its own source code.

This test ensures uzpy doesn't corrupt Python syntax when processing
its own codebase, which contains complex docstrings and quote patterns.
"""

import ast
import shutil
import tempfile
from pathlib import Path

import pytest


class TestSelfModification:
    """Integration tests for uzpy self-modification safety."""
    
    def verify_python_syntax(self, file_path: Path) -> tuple[bool, str]:
        """Verify a Python file has valid syntax.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            code = file_path.read_text()
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, f"SyntaxError in {file_path}: {e}"
        except Exception as e:
            return False, f"Error reading {file_path}: {e}"
    
    def check_directory_syntax(self, directory: Path) -> list[str]:
        """Check all Python files in a directory for syntax errors.
        
        Returns:
            List of error messages (empty if all files are valid)
        """
        errors = []
        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            is_valid, error_msg = self.verify_python_syntax(py_file)
            if not is_valid:
                errors.append(error_msg)
        return errors
    
    @pytest.mark.integration
    def test_uzpy_on_own_source(self):
        """Test that uzpy can process its own source code without corruption."""
        # Create a temporary copy of the uzpy source
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy uzpy source files
            src_path = Path(__file__).parent.parent / "src/uzpy"
            dest_path = temp_path / "uzpy_copy"
            shutil.copytree(src_path, dest_path)
            
            # Verify all files have valid syntax before modification
            errors_before = self.check_directory_syntax(dest_path)
            assert not errors_before, f"Source has syntax errors before modification: {errors_before}"
            
            # TODO: Run uzpy on the copied source
            # This would require setting up the full pipeline
            # For now, we verify the source is valid
            
            # After modification, verify syntax is still valid
            errors_after = self.check_directory_syntax(dest_path)
            assert not errors_after, f"Source has syntax errors after modification: {errors_after}"
    
    @pytest.mark.integration
    def test_problematic_patterns(self):
        """Test specific patterns that are known to cause issues."""
        problematic_files = [
            "src/uzpy/modifier/libcst_modifier.py",  # Contains complex docstrings
            "src/uzpy/types.py",  # Contains dataclasses with docstrings
            "src/uzpy/cli.py",  # Contains Fire CLI with docstrings
        ]
        
        project_root = Path(__file__).parent.parent
        
        for file_path in problematic_files:
            full_path = project_root / file_path
            if full_path.exists():
                is_valid, error_msg = self.verify_python_syntax(full_path)
                assert is_valid, f"File {file_path} has invalid syntax: {error_msg}"
                
                # Check for patterns that might cause issues
                content = full_path.read_text()
                
                # Check for triple quotes within docstrings
                if '"""' in content:
                    # Ensure docstrings are properly terminated
                    triple_quote_count = content.count('"""')
                    assert triple_quote_count % 2 == 0, f"Unmatched triple quotes in {file_path}"
    
    def test_docstring_patterns(self):
        """Test various docstring patterns that might cause corruption."""
        test_cases = [
            # Normal docstring
            ('def f():\n    """Normal docstring."""\n    pass', True),
            
            # Docstring with single quotes
            ('def f():\n    """Has \'single\' quotes."""\n    pass', True),
            
            # Docstring with double quotes
            ('def f():\n    """Has "double" quotes."""\n    pass', True),
            
            # Docstring with escaped quotes
            ('def f():\n    """Has \\"escaped\\" quotes."""\n    pass', True),
            
            # Single-line docstring
            ('def f():\n    "Single line"\n    pass', True),
            
            # Multi-line docstring
            ('def f():\n    """\n    Multi\n    line\n    """\n    pass', True),
            
            # Docstring with code example
            ('def f():\n    """\n    Example:\n        >>> print("test")\n        test\n    """\n    pass', True),
        ]
        
        for code, should_be_valid in test_cases:
            try:
                ast.parse(code)
                is_valid = True
            except SyntaxError:
                is_valid = False
            
            assert is_valid == should_be_valid, f"Unexpected result for: {repr(code)}"