# this_file: tests/test_cli.py

"""
Tests for the modern CLI module.
"""

import tempfile
from pathlib import Path

import pytest

from uzpy.pipeline import run_analysis_and_modification


@pytest.fixture
def sample_project():
    """Create a sample project for testing CLI.

"""
    project_dir = Path(tempfile.mkdtemp())

    # Create a simple Python file
    content = '''"""Sample module."""

def hello_world():
    """Print hello world."""
    print("Hello, World!")

class SampleClass:
    """A sample class."""

    def method(self):
        """Sample method."""
        return "sample"
'''

    (project_dir / "sample.py").write_text(content)

    yield project_dir

    # Cleanup
    import shutil

    shutil.rmtree(project_dir)


def test_modern_cli_analysis(sample_project):
    """Test modern CLI analysis functionality.

"""
    edit_path = sample_project
    ref_path = sample_project
    exclude_patterns = []
    dry_run = True
    
    # Should run without errors
    result = run_analysis_and_modification(edit_path, ref_path, exclude_patterns, dry_run)
    assert isinstance(result, dict)


def test_modern_cli_single_file(sample_project):
    """Test modern CLI with single file.

"""
    sample_file = sample_project / "sample.py"
    edit_path = sample_file
    ref_path = sample_file
    exclude_patterns = []
    dry_run = True
    
    # Should run without errors
    result = run_analysis_and_modification(edit_path, ref_path, exclude_patterns, dry_run)
    assert isinstance(result, dict)


def test_modern_cli_with_exclusions(sample_project):
    """Test modern CLI with exclude patterns.

"""
    # Create additional files to exclude
    (sample_project / "test_file.py").write_text("# Test file")
    (sample_project / "__pycache__").mkdir()
    (sample_project / "__pycache__" / "cache.pyc").write_text("cache")

    edit_path = sample_project
    ref_path = sample_project
    exclude_patterns = ["test_*", "__pycache__/*"]
    dry_run = True
    
    # Should run without errors
    result = run_analysis_and_modification(edit_path, ref_path, exclude_patterns, dry_run)
    assert isinstance(result, dict)


def test_modern_cli_with_reference_files(sample_project):
    """Test modern CLI with different reference path.

"""
    # Create a separate reference directory
    ref_dir = sample_project / "ref"
    ref_dir.mkdir()
    (ref_dir / "reference.py").write_text(
        """
from sample import hello_world
hello_world()
"""
    )

    edit_path = sample_project / "sample.py"
    ref_path = sample_project
    exclude_patterns = []
    dry_run = True
    
    # Should run without errors
    result = run_analysis_and_modification(edit_path, ref_path, exclude_patterns, dry_run)
    assert isinstance(result, dict)