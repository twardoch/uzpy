# this_file: tests/test_discovery.py

"""
Tests for file discovery functionality.
"""

import tempfile
from pathlib import Path

import pytest

from uzpy.discovery import FileDiscovery, discover_files


@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # Create test files
        (root / "main.py").write_text("# Main module")
        (root / "utils.py").write_text("# Utilities")
        (root / "tests").mkdir()
        (root / "tests" / "test_main.py").write_text("# Tests")
        (root / "__pycache__").mkdir()
        (root / "__pycache__" / "main.cpython-312.pyc").write_text("compiled")
        (root / ".git").mkdir()
        (root / ".git" / "config").write_text("git config")
        (root / "README.md").write_text("# README")

        yield root


def test_file_discovery_basic(temp_project):
    """Test basic file discovery functionality."""
    discovery = FileDiscovery()
    files = list(discovery.find_python_files(temp_project))

    # Should find main.py, utils.py, and test_main.py
    file_names = {f.name for f in files}
    assert "main.py" in file_names
    assert "utils.py" in file_names
    assert "test_main.py" in file_names

    # Should not find compiled files or git files
    assert "main.cpython-312.pyc" not in file_names
    assert "config" not in file_names
    assert "README.md" not in file_names


def test_file_discovery_single_file(temp_project):
    """Test discovery of a single file."""
    discovery = FileDiscovery()
    single_file = temp_project / "main.py"
    files = list(discovery.find_python_files(single_file))

    assert len(files) == 1
    assert files[0] == single_file


def test_file_discovery_nonexistent_path():
    """Test discovery with non-existent path."""
    discovery = FileDiscovery()
    nonexistent = Path("/this/path/does/not/exist")

    with pytest.raises(FileNotFoundError):
        list(discovery.find_python_files(nonexistent))


def test_discover_files_function(temp_project):
    """Test the convenience discover_files function."""
    edit_files, ref_files = discover_files(temp_project, temp_project)

    assert len(edit_files) >= 3  # main.py, utils.py, test_main.py
    assert edit_files == ref_files  # Same path for both


def test_custom_exclude_patterns(temp_project):
    """Test custom exclude patterns."""
    # Create a file that should be excluded
    (temp_project / "secret.py").write_text("# Secret file")

    discovery = FileDiscovery(exclude_patterns=["secret.py"])
    files = list(discovery.find_python_files(temp_project))

    file_names = {f.name for f in files}
    assert "secret.py" not in file_names
    assert "main.py" in file_names  # Other files still found
