# this_file: tests/test_modifier.py

"""
Tests for the LibCST modifier functionality.
"""

import tempfile
from pathlib import Path

import pytest

from uzpy.modifier.libcst_modifier import LibCSTModifier, DocstringModifier
from uzpy.parser import Construct, ConstructType, Reference


@pytest.fixture
def sample_python_file_with_docstrings():
    """Create a sample Python file with existing docstrings for testing."""
    content = '''"""Module docstring."""

def function_with_docstring():
    """Function with existing docstring."""
    return "hello"

def function_with_usage_info():
    """Function with existing usage info.
    
    Used in:
    - old/module.py
    - existing/file.py
    """
    return "world"

class TestClass:
    """Class with docstring."""
    
    def method_with_docstring(self):
        """Method docstring.
        
        Args:
            self: The instance
        """
        pass

def function_without_docstring():
    return 42
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        f.flush()
        yield Path(f.name)

    # Cleanup
    Path(f.name).unlink()


@pytest.fixture
def sample_constructs_and_references(sample_python_file_with_docstrings):
    """Create sample constructs and references for testing."""
    constructs = [
        Construct(
            name="function_with_docstring",
            type=ConstructType.FUNCTION,
            file_path=sample_python_file_with_docstrings,
            line_number=3,
            docstring="Function with existing docstring.",
            full_name="function_with_docstring",
        ),
        Construct(
            name="function_with_usage_info",
            type=ConstructType.FUNCTION,
            file_path=sample_python_file_with_docstrings,
            line_number=7,
            docstring="Function with existing usage info.\n    \n    Used in:\n    - old/module.py\n    - existing/file.py\n    ",
            full_name="function_with_usage_info",
        ),
        Construct(
            name="function_without_docstring",
            type=ConstructType.FUNCTION,
            file_path=sample_python_file_with_docstrings,
            line_number=24,
            docstring=None,
            full_name="function_without_docstring",
        ),
    ]

    references = [
        Reference(
            file_path=Path("src/main.py"),
            line_number=10,
            context="function_with_docstring()",
        ),
        Reference(
            file_path=Path("tests/test_module.py"),
            line_number=5,
            context="from module import function_with_docstring",
        ),
    ]

    usage_map = {
        constructs[0]: references,  # function_with_docstring gets new references
        constructs[1]: [
            Reference(  # function_with_usage_info gets additional reference
                file_path=Path("new/module.py"),
                line_number=15,
                context="function_with_usage_info()",
            )
        ],
        constructs[2]: [
            Reference(  # function_without_docstring gets first reference
                file_path=Path("src/utils.py"),
                line_number=20,
                context="function_without_docstring()",
            )
        ],
    }

    return constructs, usage_map


def test_libcst_modifier_initialization():
    """Test LibCST modifier initialization."""
    project_root = Path("/fake/project")
    modifier = LibCSTModifier(project_root)
    assert modifier.project_root == project_root


def test_docstring_modifier_initialization():
    """Test DocstringModifier initialization."""
    project_root = Path("/fake/project")
    usage_map = {}
    modifier = DocstringModifier(usage_map, project_root)
    assert modifier.project_root == project_root
    assert modifier.usage_map == usage_map


def test_extract_existing_usage_paths():
    """Test extraction of existing usage paths from docstrings."""
    modifier = DocstringModifier({}, Path("/fake"))

    # Test docstring with existing usage
    content = """Function description.
    
    Used in:
    - old/path1.py
    - old/path2.py
    """

    cleaned, paths, indent = modifier._extract_existing_usage_paths(content)

    assert "Used in:" not in cleaned
    assert "old/path1.py" in paths
    assert "old/path2.py" in paths
    assert len(paths) == 2


def test_extract_existing_usage_paths_no_usage():
    """Test extraction when no existing usage section exists."""
    modifier = DocstringModifier({}, Path("/fake"))

    content = """Function description without usage info."""

    cleaned, paths, indent = modifier._extract_existing_usage_paths(content)

    assert cleaned == content
    assert len(paths) == 0
    assert indent == ""


def test_update_docstring_content_with_existing_usage():
    """Test updating docstring content that has existing usage info."""
    modifier = DocstringModifier({}, Path("/fake/project"))

    current_docstring = '''"""Function with existing usage.
    
    Used in:
    - old/module.py
    """'''

    new_references = [
        Reference(
            file_path=Path("/fake/project/new/module.py"),
            line_number=10,
            context="call",
        )
    ]

    result = modifier._update_docstring_content(current_docstring, new_references)

    # Should contain both old and new paths
    assert "old/module.py" in result
    assert "new/module.py" in result
    assert "Used in:" in result


def test_update_docstring_content_without_existing_usage():
    """Test updating docstring content that has no existing usage info."""
    modifier = DocstringModifier({}, Path("/fake/project"))

    current_docstring = '''"""Function without existing usage."""'''

    new_references = [
        Reference(
            file_path=Path("/fake/project/src/module.py"),
            line_number=10,
            context="call",
        )
    ]

    result = modifier._update_docstring_content(current_docstring, new_references)

    # Should contain new usage section
    assert "Used in:" in result
    assert "src/module.py" in result


def test_create_new_docstring():
    """Test creating new docstring with usage information."""
    modifier = DocstringModifier({}, Path("/fake/project"))

    references = [
        Reference(
            file_path=Path("/fake/project/src/main.py"),
            line_number=5,
            context="import",
        ),
        Reference(
            file_path=Path("/fake/project/tests/test.py"),
            line_number=10,
            context="call",
        ),
    ]

    result = modifier._create_new_docstring(references)

    assert '"""' in result
    assert "Used in:" in result
    assert "src/main.py" in result
    assert "tests/test.py" in result


def test_modify_file_integration(sample_python_file_with_docstrings, sample_constructs_and_references):
    """Test full file modification integration."""
    constructs, usage_map = sample_constructs_and_references
    project_root = sample_python_file_with_docstrings.parent

    modifier = LibCSTModifier(project_root)

    # Read original content
    with open(sample_python_file_with_docstrings, "r") as f:
        original_content = f.read()

    # Modify the file
    success = modifier.modify_file(sample_python_file_with_docstrings, usage_map)

    assert success is True

    # Read modified content
    with open(sample_python_file_with_docstrings, "r") as f:
        modified_content = f.read()

    # Should have added usage information
    assert "Used in:" in modified_content
    assert "src/main.py" in modified_content
    assert "tests/test_module.py" in modified_content

    # Should preserve existing structure
    assert "def function_with_docstring():" in modified_content
    assert "class TestClass:" in modified_content


def test_modify_files_batch(sample_python_file_with_docstrings, sample_constructs_and_references):
    """Test batch file modification."""
    constructs, usage_map = sample_constructs_and_references
    project_root = sample_python_file_with_docstrings.parent

    modifier = LibCSTModifier(project_root)

    # Modify files in batch
    results = modifier.modify_files(usage_map)

    # Should report success for the test file
    file_key = str(sample_python_file_with_docstrings)
    assert file_key in results
    assert results[file_key] is True


def test_indentation_preservation():
    """Test that indentation is preserved correctly."""
    modifier = DocstringModifier({}, Path("/fake/project"))

    # Test with indented docstring
    current_docstring = '''"""
        Function with indented docstring.
        
        Args:
            param: Description
        """'''

    references = [
        Reference(
            file_path=Path("/fake/project/src/module.py"),
            line_number=10,
            context="call",
        )
    ]

    result = modifier._update_docstring_content(current_docstring, references)

    # Should preserve indentation
    assert "        Used in:" in result
    assert "        - src/module.py" in result


def test_relative_path_calculation():
    """Test that paths are calculated relative to project root."""
    project_root = Path("/fake/project")
    modifier = DocstringModifier({}, project_root)

    references = [
        Reference(
            file_path=Path("/fake/project/src/deep/nested/module.py"),
            line_number=10,
            context="call",
        ),
        Reference(
            file_path=Path("/fake/project/tests/test.py"),
            line_number=5,
            context="import",
        ),
    ]

    result = modifier._create_new_docstring(references)

    # Should use relative paths
    assert "src/deep/nested/module.py" in result
    assert "tests/test.py" in result
    # Should not contain absolute paths
    assert "/fake/project/" not in result


def test_error_handling_invalid_syntax():
    """Test error handling with invalid Python syntax."""
    content = """
def broken_function(
    # Missing closing parenthesis
    return "broken"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        f.flush()

        modifier = LibCSTModifier(Path("/fake"))
        success = modifier.modify_file(Path(f.name), {})

        # Should handle error gracefully
        assert success is False

    Path(f.name).unlink()


def test_no_changes_needed():
    """Test behavior when no changes are needed."""
    content = '''def simple_function():
    """Simple function."""
    pass
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        f.flush()

        modifier = LibCSTModifier(Path("/fake"))
        # Pass empty usage map - no changes needed
        success = modifier.modify_file(Path(f.name), {})

        # Should report no changes made
        assert success is False

    Path(f.name).unlink()
