# this_file: tests/test_parser.py

"""
Tests for the Tree-sitter parser functionality.
"""

import tempfile
from pathlib import Path

import pytest

from uzpy.parser import ConstructType, TreeSitterParser


@pytest.fixture
def sample_python_file():
    """Create a sample Python file for testing."""
    content = '''"""Module docstring for testing."""

def standalone_function():
    """A standalone function."""
    return "hello"

class TestClass:
    """A test class."""

    def method_one(self):
        """First method."""
        pass

    def method_two(self):
        # No docstring
        return 42

class AnotherClass:
    # Class with no docstring

    def __init__(self):
        """Constructor."""
        self.value = 0

def another_function():
    # Function with no docstring
    pass
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        f.flush()
        yield Path(f.name)

    # Cleanup
    Path(f.name).unlink()


def test_parser_initialization():
    """Test that the parser initializes correctly."""
    parser = TreeSitterParser()
    assert parser.language is not None
    assert parser.parser is not None


def test_parse_file_basic(sample_python_file):
    """Test basic file parsing functionality."""
    parser = TreeSitterParser()
    constructs = parser.parse_file(sample_python_file)

    # Should find module, classes, and functions/methods
    assert len(constructs) > 0

    # Check we have different types
    types_found = {c.type for c in constructs}
    assert ConstructType.MODULE in types_found
    assert ConstructType.CLASS in types_found
    assert ConstructType.FUNCTION in types_found
    assert ConstructType.METHOD in types_found


def test_construct_extraction(sample_python_file):
    """Test detailed construct extraction."""
    parser = TreeSitterParser()
    constructs = parser.parse_file(sample_python_file)

    # Build a map by name for easier testing
    by_name = {c.name: c for c in constructs}

    # Test module
    assert sample_python_file.stem in by_name
    module = by_name[sample_python_file.stem]
    assert module.type == ConstructType.MODULE
    assert module.docstring == "Module docstring for testing."

    # Test standalone function
    assert "standalone_function" in by_name
    func = by_name["standalone_function"]
    assert func.type == ConstructType.FUNCTION
    assert func.docstring == "A standalone function."
    assert func.full_name == "standalone_function"

    # Test class
    assert "TestClass" in by_name
    cls = by_name["TestClass"]
    assert cls.type == ConstructType.CLASS
    assert cls.docstring == "A test class."

    # Test method with docstring
    assert "method_one" in by_name
    method = by_name["method_one"]
    assert method.type == ConstructType.METHOD
    assert method.docstring == "First method."
    assert method.full_name == "TestClass.method_one"

    # Test method without docstring
    assert "method_two" in by_name
    method2 = by_name["method_two"]
    assert method2.type == ConstructType.METHOD
    assert method2.docstring is None

    # Test function without docstring
    assert "another_function" in by_name
    func2 = by_name["another_function"]
    assert func2.type == ConstructType.FUNCTION
    assert func2.docstring is None


def test_line_numbers(sample_python_file):
    """Test that line numbers are correctly extracted."""
    parser = TreeSitterParser()
    constructs = parser.parse_file(sample_python_file)

    by_name = {c.name: c for c in constructs}

    # Module should start at line 1
    module = by_name[sample_python_file.stem]
    assert module.line_number == 1

    # Function should be after module docstring
    func = by_name["standalone_function"]
    assert func.line_number > 1

    # All line numbers should be positive
    for construct in constructs:
        assert construct.line_number > 0


def test_parser_statistics(sample_python_file):
    """Test parser statistics functionality."""
    parser = TreeSitterParser()
    stats = parser.get_statistics(sample_python_file)

    assert stats["total_constructs"] > 0
    assert stats["functions"] >= 2  # standalone_function, another_function
    assert stats["methods"] >= 3  # method_one, method_two, __init__
    assert stats["classes"] >= 2  # TestClass, AnotherClass
    assert stats["modules"] == 1  # The module itself
    assert stats["with_docstrings"] > 0
    assert stats["without_docstrings"] > 0


def test_parser_with_syntax_error():
    """Test parser behavior with syntax errors."""
    content = '''
def broken_function(
    # Missing closing parenthesis
    return "this should still be parsed"

def good_function():
    """This should work fine."""
    return 42
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        f.flush()

        parser = TreeSitterParser()
        constructs = parser.parse_file(Path(f.name))

        # Should still find some constructs despite syntax error
        assert len(constructs) > 0

        # Should find the good function
        names = {c.name for c in constructs}
        assert "good_function" in names

    Path(f.name).unlink()


def test_parser_empty_file():
    """Test parser with empty file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        f.flush()

        parser = TreeSitterParser()
        constructs = parser.parse_file(Path(f.name))

        # Should at least find the module construct
        assert len(constructs) >= 1
        assert any(c.type == ConstructType.MODULE for c in constructs)

    Path(f.name).unlink()


def test_parser_nonexistent_file():
    """Test parser with non-existent file."""
    parser = TreeSitterParser()

    with pytest.raises(FileNotFoundError):
        parser.parse_file(Path("/this/file/does/not/exist.py"))
