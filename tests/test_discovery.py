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
    """Create a temporary project structure for testing.

"""
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
    """Test basic file discovery functionality.

"""
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
    """Test discovery of a single file.

"""
    discovery = FileDiscovery()
    single_file = temp_project / "main.py"
    files = list(discovery.find_python_files(single_file))

    assert len(files) == 1
    assert files[0] == single_file


def test_file_discovery_nonexistent_path():
    """Test discovery with non-existent path.

"""
    discovery = FileDiscovery()
    nonexistent = Path("/this/path/does/not/exist")

    with pytest.raises(FileNotFoundError):
        list(discovery.find_python_files(nonexistent))


def test_discover_files_function(temp_project):
    """Test the convenience discover_files function.

"""
    edit_files, ref_files = discover_files(temp_project, temp_project)

    assert len(edit_files) >= 3  # main.py, utils.py, test_main.py
    assert edit_files == ref_files  # Same path for both


def test_custom_exclude_patterns(temp_project):
    """Test custom exclude patterns.

"""
    # Create a file that should be excluded
    (temp_project / "secret.py").write_text("# Secret file")

    discovery = FileDiscovery(exclude_patterns=["secret.py"])
    files = list(discovery.find_python_files(temp_project))

    file_names = {f.name for f in files}
    assert "secret.py" not in file_names
    assert "main.py" in file_names  # Other files still found


def test_private_folder_exclusion(temp_project):
    """Test that _private folder exclusion works correctly.

"""
    # Create _private folder with files
    private_dir = temp_project / "_private"
    private_dir.mkdir()
    (private_dir / "secret.py").write_text("# Private secret file")
    (private_dir / "config.py").write_text("# Private config file")

    # Create a normal file
    (temp_project / "public.py").write_text("# Public file")

    # Test with _private pattern
    discovery = FileDiscovery(exclude_patterns=["_private"])
    files = list(discovery.find_python_files(temp_project))

    file_names = {f.name for f in files}
    relative_paths = {f.relative_to(temp_project) for f in files}

    # Should not find files in _private folder
    assert "secret.py" not in file_names
    assert "config.py" not in file_names

    # Should find normal files
    assert "public.py" in file_names
    assert "main.py" in file_names

    # Check no paths start with _private
    for path in relative_paths:
        assert not str(path).startswith("_private")


def test_private_folder_exclusion_glob_pattern(temp_project):
    """Test that _private/** folder exclusion works correctly.

"""
    # Create _private folder with files
    private_dir = temp_project / "_private"
    private_dir.mkdir()
    (private_dir / "secret.py").write_text("# Private secret file")

    # Create subfolder in _private
    private_subdir = private_dir / "subdir"
    private_subdir.mkdir()
    (private_subdir / "deep_secret.py").write_text("# Deep private file")

    # Create a normal file
    (temp_project / "public.py").write_text("# Public file")

    # Test with _private/** pattern
    discovery = FileDiscovery(exclude_patterns=["_private/**"])
    files = list(discovery.find_python_files(temp_project))

    file_names = {f.name for f in files}
    relative_paths = {f.relative_to(temp_project) for f in files}

    # Should not find files in _private folder
    assert "secret.py" not in file_names
    assert "deep_secret.py" not in file_names

    # Should find normal files
    assert "public.py" in file_names
    assert "main.py" in file_names

    # Check no paths start with _private
    for path in relative_paths:
        assert not str(path).startswith("_private")
