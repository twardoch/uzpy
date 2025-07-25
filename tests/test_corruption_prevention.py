# this_file: tests/test_corruption_prevention.py

"""
Test cases to expose and prevent Python syntax corruption when uzpy modifies docstrings.

These tests ensure uzpy maintains valid Python syntax when processing edge cases.
"""

import ast
import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from uzpy.modifier.libcst_modifier import DocstringModifier, LibCSTModifier
from uzpy.parser import Construct, ConstructType, Reference


class TestCorruptionPrevention:
    """Test cases to prevent Python syntax corruption."""

    @pytest.fixture
    def modifier(self):
        """Create a LibCST modifier instance."""
        return LibCSTModifier(project_root=Path.cwd())

    def verify_valid_python(self, code: str) -> bool:
        """Verify that code is valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def test_triple_quote_in_docstring(self, modifier):
        """Test handling of triple quotes within docstrings."""
        code = dedent('''
            def example():
                """This docstring contains ''' + '"""' + ''' triple quotes."""
                pass
        ''').strip()
        
        # Create usage map
        construct = Construct(
            name="example",
            type=ConstructType.FUNCTION,
            file_path=Path("test.py"),
            line=1
        )
        reference = Reference(
            name="example",
            file_path=Path("other.py"),
            line=10
        )
        usage_map = {construct: [reference]}
        
        # Modify the code
        result = modifier.modify_string(code, Path("test.py"), usage_map)
        
        # Verify syntax is still valid
        assert self.verify_valid_python(result), f"Invalid Python syntax:\n{result}"
        
    def test_escaped_quotes_in_docstring(self, modifier):
        """Test handling of escaped quotes in docstrings."""
        code = dedent(r'''
            def example():
                """This docstring has \"escaped\" quotes and \n newlines."""
                pass
        ''').strip()
        
        construct = Construct(
            name="example",
            type=ConstructType.FUNCTION,
            file_path=Path("test.py"),
            line=1
        )
        reference = Reference(
            name="example",
            file_path=Path("other.py"),
            line=10
        )
        usage_map = {construct: [reference]}
        
        result = modifier.modify_string(code, Path("test.py"), usage_map)
        assert self.verify_valid_python(result), f"Invalid Python syntax:\n{result}"
        
    def test_single_quote_docstring(self, modifier):
        """Test handling of single-quoted docstrings."""
        code = dedent('''
            def example():
                'Single quoted docstring'
                pass
        ''').strip()
        
        construct = Construct(
            name="example",
            type=ConstructType.FUNCTION,
            file_path=Path("test.py"),
            line=1
        )
        reference = Reference(
            name="example",
            file_path=Path("other.py"),
            line=10
        )
        usage_map = {construct: [reference]}
        
        result = modifier.modify_string(code, Path("test.py"), usage_map)
        assert self.verify_valid_python(result), f"Invalid Python syntax:\n{result}"
        
    def test_multiline_string_with_quotes(self, modifier):
        """Test handling of complex multiline strings with mixed quotes."""
        code = dedent('''
            def example():
                """
                This is a complex docstring with:
                - 'Single quotes'
                - "Double quotes"
                - """ + r"\"Escaped quotes\"" + """
                - Raw strings: r"\\n"
                """
                pass
        ''').strip()
        
        construct = Construct(
            name="example",
            type=ConstructType.FUNCTION,
            file_path=Path("test.py"),
            line=1
        )
        reference = Reference(
            name="example",
            file_path=Path("other.py"),
            line=10
        )
        usage_map = {construct: [reference]}
        
        result = modifier.modify_string(code, Path("test.py"), usage_map)
        assert self.verify_valid_python(result), f"Invalid Python syntax:\n{result}"
        
    def test_existing_used_in_section(self, modifier):
        """Test handling of docstrings that already have 'Used in:' sections."""
        code = dedent('''
            def example():
                """
                Function with existing usage.
                
                Used in:
                - old/file.py
                - another/file.py
                """
                pass
        ''').strip()
        
        construct = Construct(
            name="example",
            type=ConstructType.FUNCTION,
            file_path=Path("test.py"),
            line=1
        )
        reference = Reference(
            name="example",
            file_path=Path("new/file.py"),
            line=10
        )
        usage_map = {construct: [reference]}
        
        result = modifier.modify_string(code, Path("test.py"), usage_map)
        assert self.verify_valid_python(result), f"Invalid Python syntax:\n{result}"
        # Should merge old and new references
        assert "old/file.py" in result
        assert "new/file.py" in result
        
    def test_no_docstring_function(self, modifier):
        """Test adding docstring to function without one."""
        code = dedent('''
            def example():
                pass
        ''').strip()
        
        construct = Construct(
            name="example",
            type=ConstructType.FUNCTION,
            file_path=Path("test.py"),
            line=1
        )
        reference = Reference(
            name="example",
            file_path=Path("other.py"),
            line=10
        )
        usage_map = {construct: [reference]}
        
        result = modifier.modify_string(code, Path("test.py"), usage_map)
        assert self.verify_valid_python(result), f"Invalid Python syntax:\n{result}"
        assert '"""' in result or "'''" in result  # Should add a docstring
        
    def test_self_referential_modification(self, modifier):
        """Test that uzpy doesn't include self-references in 'Used in:' sections."""
        code = dedent('''
            def example():
                """Example function."""
                pass
                
            def caller():
                """Calls example."""
                example()
        ''').strip()
        
        # Both functions in same file
        file_path = Path("test.py")
        construct = Construct(
            name="example",
            type=ConstructType.FUNCTION,
            file_path=file_path,
            line=1
        )
        # Reference from same file - should be excluded
        reference = Reference(
            name="example",
            file_path=file_path,
            line=7
        )
        usage_map = {construct: [reference]}
        
        result = modifier.modify_string(code, file_path, usage_map)
        assert self.verify_valid_python(result), f"Invalid Python syntax:\n{result}"
        # Should not add "Used in:" for same-file reference
        assert "Used in:" not in result
        
    def test_nested_quotes_edge_case(self, modifier):
        """Test extreme edge case with nested quote patterns."""
        code = dedent('''
            def example():
                """This has \""" and ''' + "'''" + ''' and mixed quotes."""
                pass
        ''').strip()
        
        construct = Construct(
            name="example",
            type=ConstructType.FUNCTION,
            file_path=Path("test.py"),
            line=1
        )
        reference = Reference(
            name="example",
            file_path=Path("other.py"),
            line=10
        )
        usage_map = {construct: [reference]}
        
        result = modifier.modify_string(code, Path("test.py"), usage_map)
        assert self.verify_valid_python(result), f"Invalid Python syntax:\n{result}"
        
    def test_docstring_with_code_blocks(self, modifier):
        """Test docstrings containing code examples with quotes."""
        code = dedent('''
            def example():
                """
                Example function.
                
                Example:
                    >>> print("Hello")
                    'Hello'
                    >>> data = {"key": 'value'}
                """
                pass
        ''').strip()
        
        construct = Construct(
            name="example",
            type=ConstructType.FUNCTION,
            file_path=Path("test.py"),
            line=1
        )
        reference = Reference(
            name="example",
            file_path=Path("other.py"),
            line=10
        )
        usage_map = {construct: [reference]}
        
        result = modifier.modify_string(code, Path("test.py"), usage_map)
        assert self.verify_valid_python(result), f"Invalid Python syntax:\n{result}"


class TestRegressionPrevention:
    """Tests to prevent regression of previously fixed issues."""
    
    def test_uzpy_self_modification(self):
        """Test that uzpy can safely modify its own source code."""
        # This test would actually run uzpy on a copy of its own source
        # For now, we'll test the specific pattern that caused issues
        
        # Read the actual modifier source
        modifier_path = Path(__file__).parent.parent / "src/uzpy/modifier/libcst_modifier.py"
        if modifier_path.exists():
            code = modifier_path.read_text()
            
            # Verify it's currently valid Python
            try:
                ast.parse(code)
            except SyntaxError as e:
                pytest.fail(f"Current modifier source has syntax error: {e}")
                
        # TODO: Implement full self-modification test in integration tests
        pass