# this_file: src/uzpy/analyzer/modern_hybrid_analyzer.py

"""
Modern Hybrid Analyzer for uzpy.

This module provides a high-performance analyzer that uses multiple
modern tools (Ruff, Pyright, ast-grep) in combination for comprehensive
and fast usage detection.

"""

from pathlib import Path
from typing import Any

from loguru import logger

from uzpy.analyzer.astgrep_analyzer import AstGrepAnalyzer
from uzpy.analyzer.pyright_analyzer import PyrightAnalyzer
from uzpy.analyzer.ruff_analyzer import RuffAnalyzer
from uzpy.types import Construct, Reference

# Importing existing analyzers for potential fallback or comparison


class ModernHybridAnalyzer:
    """
    Modern hybrid analyzer combining multiple fast analysis tools.

    This analyzer uses a tiered approach:
    1. Ruff for quick basic detection
    2. ast-grep for structural pattern matching
    3. Pyright for accurate type-based analysis
    4. Traditional analyzers (Rope/Jedi) as smart fallbacks

    Each tier adds more accuracy but takes more time. The traditional
    analyzers serve as reliable fallbacks when modern tools fail,
    ensuring comprehensive coverage.

    Used in:
    - src/uzpy/analyzer/__init__.py
    - src/uzpy/pipeline.py
    """

    def __init__(
        self,
        project_root: Path,
        exclude_patterns: list[str] | None = None,
        config: dict[str, Any] | None = None,
        python_executable: str | None = None,  # For Pyright
    ):
        """
        Initialize the ModernHybridAnalyzer.

        Args:
            project_root: Root directory of the project
            exclude_patterns: Patterns to exclude from analysis (used by the
                optional traditional-analyzer fallback)
            config: Feature toggles (use_ruff, use_astgrep, use_pyright,
                use_fallback, short_circuit_threshold)
            python_executable: Python interpreter for the Pyright backend

        """
        self.project_root = project_root
        self.exclude_patterns = exclude_patterns or []
        self.config = config if config is not None else {}

        # Initialize individual analyzers, each toggleable via config.
        self.ruff_analyzer: RuffAnalyzer | None
        if self.config.get("use_ruff", True):
            self.ruff_analyzer = RuffAnalyzer(project_root)
        else:
            self.ruff_analyzer = None

        self.ast_grep_analyzer: AstGrepAnalyzer | None
        if self.config.get("use_astgrep", True):
            self.ast_grep_analyzer = AstGrepAnalyzer(project_root)
        else:
            self.ast_grep_analyzer = None

        self.pyright_analyzer: PyrightAnalyzer | None
        if self.config.get("use_pyright", True):
            self.pyright_analyzer = PyrightAnalyzer(project_root, python_executable)
        else:
            self.pyright_analyzer = None

        # Optionally fall back to the traditional (jedi/rope) analyzer stack.
        self.use_fallback = self.config.get("use_fallback", False)
        self.fallback_analyzer = None
        if self.use_fallback:
            try:
                from uzpy.analyzer.hybrid_analyzer import HybridAnalyzer

                self.fallback_analyzer = HybridAnalyzer(project_root, self.exclude_patterns)
                logger.debug("Initialized traditional analyzer fallback")
            except Exception as e:
                logger.warning(f"Failed to initialize fallback analyzer: {e}")
                self.use_fallback = False

        # Threshold for short-circuiting (if enough references are found)
        self.short_circuit_threshold = self.config.get("short_circuit_threshold", 0)  # 0 means no short-circuit

        logger.info("ModernHybridAnalyzer initialized.")
        logger.debug(
            f"Configuration: Ruff={'enabled' if self.ruff_analyzer else 'disabled'}, "
            f"ast-grep={'enabled' if self.ast_grep_analyzer else 'disabled'}, "
            f"Pyright={'enabled' if self.pyright_analyzer else 'disabled'}."
        )
        if self.short_circuit_threshold > 0:
            logger.debug(f"Short-circuit threshold set to: {self.short_circuit_threshold} references.")

    def find_usages(self, construct: Construct, search_paths: list[Path]) -> list[Reference]:
        """
        Find usages for a single construct using a tiered approach.

        Strategy:
        1. Ruff (if enabled): Quick, less precise, good for obvious non-usage or basic imports.
        2. ast-grep (if enabled): Structural patterns, more precise than text, faster than full type analysis.
        3. Pyright (if enabled): Deep type analysis, most accurate, potentially slower.

        Returns:
            List of references to the construct

        Used in:
        - src/uzpy/analyzer/cached_analyzer.py
        """
        all_references: dict[tuple[Path, int, int], Reference] = {}  # Use (path, line, col) as key for deduplication

        def _add_references(new_refs: list[Reference]) -> None:
            for ref in new_refs:
                key = (ref.file_path.resolve(), ref.line_number, ref.column_number)
                if key not in all_references:  # Add only if not already present
                    all_references[key] = ref
            logger.debug(f"Added {len(new_refs)} new refs. Total unique refs: {len(all_references)}.")

        # Stage 1: Ruff Analyzer (very limited for reference finding as implemented)
        if self.ruff_analyzer:
            logger.debug(f"Running RuffAnalyzer for {construct.full_name}...")
            try:
                ruff_refs = self.ruff_analyzer.find_usages(construct, search_paths)
                _add_references(ruff_refs)
                if self.short_circuit_threshold > 0 and len(all_references) >= self.short_circuit_threshold:
                    logger.info(
                        f"Short-circuiting after RuffAnalyzer for {construct.full_name}. "
                        f"Found {len(all_references)} references."
                    )
                    return list(all_references.values())
            except Exception as e:
                logger.error(f"Error during RuffAnalyzer execution for {construct.full_name}: {e}")

        # Tier 4: Fallback to traditional analyzers if needed and enabled
        if self.use_fallback and self.fallback_analyzer and len(all_references) == 0:
            try:
                logger.debug(f"Using traditional analyzer fallback for {construct.name}")
                fallback_refs = self.fallback_analyzer.find_usages(construct, search_paths)
                for ref in fallback_refs:
                    key = (ref.file_path.resolve(), ref.line_number, ref.column_number)
                    all_references[key] = ref
                logger.debug(f"Traditional fallback found {len(fallback_refs)} references")
            except Exception as e:
                logger.debug(f"Traditional fallback failed: {e}")

        # Return deduplicated references
        return list(all_references.values())
