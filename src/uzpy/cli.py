#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["typer", "rich", "loguru"]
# ///
# this_file: src/uzpy/cli.py

"""
Modern CLI for uzpy using Typer and Rich.

This module provides the main command-line interface for uzpy using modern
Python CLI tools with beautiful output and progress tracking.
"""

from uzpy.cli_modern import cli
