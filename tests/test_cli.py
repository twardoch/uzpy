# this_file: tests/test_cli.py

"""
Tests for the CLI module.
"""

from uzpy.cli import UzpyCLI


def test_cli_init():
    """Test CLI initialization."""
    cli = UzpyCLI()
    assert cli.console is not None


def test_cli_with_nonexistent_path(capsys):
    """Test CLI with non-existent path."""
    cli = UzpyCLI()
    cli.run(edit="/nonexistent/path")
    captured = capsys.readouterr()
    assert "does not exist" in captured.out
