# this_file: tests/test_cli.py

"""
Tests for the CLI module.
"""

import tempfile
from pathlib import Path

import pytest

from uzpy.cli import UzpyCLI


@pytest.fixture
def sample_project():
    """Create a sample project for testing CLI."""
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


def test_cli_init():
    """Test CLI initialization."""
    cli = UzpyCLI()
    assert cli.edit is not None


def test_cli_with_nonexistent_path(capsys):
    """Test CLI with non-existent path."""
    cli = UzpyCLI(edit="/nonexistent/path")
    cli.run()
    captured = capsys.readouterr()
    assert "does not exist" in captured.err


def test_cli_dry_run(sample_project, capsys):
    """Test CLI dry run functionality."""
    cli = UzpyCLI(edit=str(sample_project), verbose=True)
    cli.test()  # test() method calls run with dry_run=True
    captured = capsys.readouterr()

    # Should show analysis results without modifying files
    assert "Starting uzpy analysis" in captured.err


def test_cli_single_file(sample_project, capsys):
    """Test CLI with single file."""
    sample_file = sample_project / "sample.py"
    cli = UzpyCLI(edit=str(sample_file))
    cli.test()
    captured = capsys.readouterr()

    # Should process the single file
    assert "Starting uzpy analysis" in captured.err


def test_cli_verbose_output(sample_project, capsys):
    """Test CLI verbose output."""
    cli = UzpyCLI(edit=str(sample_project), verbose=True)
    cli.test()
    captured = capsys.readouterr()

    # Verbose mode should show detailed information
    assert len(captured.err) > 0
    # Should show analysis phases
    assert "Starting uzpy analysis" in captured.err


def test_cli_with_exclude_patterns(sample_project, capsys):
    """Test CLI with exclude patterns."""
    # Create additional files to exclude
    (sample_project / "test_file.py").write_text("# Test file")
    (sample_project / "__pycache__").mkdir()
    (sample_project / "__pycache__" / "cache.pyc").write_text("cache")

    cli = UzpyCLI(edit=str(sample_project), xclude_patterns="test_*,__pycache__/*")
    cli.test()
    captured = capsys.readouterr()

    # Should process successfully with exclusions
    assert "Starting uzpy analysis" in captured.err


def test_cli_error_handling_invalid_args():
    """Test CLI error handling with invalid arguments."""
    cli = UzpyCLI(edit="/nonexistent/path")

    # Test with invalid path - should not raise SystemExit but should log error
    cli.run()  # Should handle gracefully


def test_cli_methods_include_flag(sample_project, capsys):
    """Test CLI with methods include flag."""
    cli = UzpyCLI(edit=str(sample_project), methods_include=True, verbose=True)
    cli.test()
    captured = capsys.readouterr()

    # Should include methods in analysis
    assert "Starting uzpy analysis" in captured.err


def test_cli_classes_include_flag(sample_project, capsys):
    """Test CLI with classes include flag."""
    cli = UzpyCLI(edit=str(sample_project), classes_include=True, verbose=True)
    cli.test()
    captured = capsys.readouterr()

    # Should include classes in analysis
    assert "Starting uzpy analysis" in captured.err


def test_cli_functions_include_flag(sample_project, capsys):
    """Test CLI with functions include flag."""
    cli = UzpyCLI(edit=str(sample_project), functions_include=True, verbose=True)
    cli.test()
    captured = capsys.readouterr()

    # Should include functions in analysis
    assert "Starting uzpy analysis" in captured.err


def test_cli_ref_path_different_from_edit(sample_project, capsys):
    """Test CLI with different reference path."""
    # Create a separate reference directory
    ref_dir = sample_project / "ref"
    ref_dir.mkdir()
    (ref_dir / "reference.py").write_text("""
from sample import hello_world
hello_world()
""")

    cli = UzpyCLI(edit=str(sample_project / "sample.py"), ref=str(sample_project), verbose=True)
    cli.test()
    captured = capsys.readouterr()

    # Should analyze with separate reference path
    assert "Starting uzpy analysis" in captured.err


def test_cli_statistics_reporting(sample_project, capsys):
    """Test that CLI reports statistics."""
    cli = UzpyCLI(edit=str(sample_project), verbose=True)
    cli.test()
    captured = capsys.readouterr()

    # Should show statistics in output
    assert any(keyword in captured.err for keyword in ["Found", "constructs", "files"])
