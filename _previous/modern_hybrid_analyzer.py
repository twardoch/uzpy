# this_file: src/uzpy/analyzer/modern_hybrid_analyzer.py

"""
Modern hybrid analyzer that combines multiple fast analyzers.

This module provides a high-performance analyzer that uses multiple
modern tools (Ruff, Pyright, ast-grep) in combination for comprehensive
and fast usage detection.
"""

from pathlib import Path
from typing import Optional, Union

from loguru import logger

from uzpy.analyzer.astgrep_analyzer import AstGrepAnalyzer
from uzpy.analyzer.pyright_analyzer import PyrightAnalyzer
from uzpy.analyzer.ruff_analyzer import RuffAnalyzer
from uzpy.types import Construct, Reference


class ModernHybridAnalyzer:
    """
    Modern hybrid analyzer combining multiple fast analysis tools.

    This analyzer uses a tiered approach:
    1. Ruff for quick basic detection
    2. ast-grep for structural pattern matching
    3. Pyright for accurate type-based analysis
    4. Falls back to traditional analyzers if needed

    Each tier adds more accuracy but takes more time, so we can
    short-circuit when we have enough confidence.
    """

    def __init__(
        self,
        project_root: Path,
        exclude_patterns: list[str] | None = None,
        use_fallback: bool = True,
    ):
        """
        Initialize modern hybrid analyzer.

        Args:
            project_root: Root directory of the project
            exclude_patterns: Patterns to exclude from analysis
            use_fallback: Whether to fall back to traditional analyzers
        """
        self.project_root = project_root
        self.exclude_patterns = exclude_patterns or []
        self.use_fallback = use_fallback

        # Initialize modern analyzers
        self.ruff_analyzer = RuffAnalyzer(project_root, exclude_patterns)
        self.astgrep_analyzer = AstGrepAnalyzer(project_root, exclude_patterns)
        self.pyright_analyzer = PyrightAnalyzer(project_root, exclude_patterns)

        # Initialize fallback analyzer if needed
        if use_fallback:
            from uzpy.analyzer.hybrid_analyzer import HybridAnalyzer

            self.fallback_analyzer = HybridAnalyzer(project_root, exclude_patterns)
        else:
            self.fallback_analyzer = None

        logger.debug("Initialized modern hybrid analyzer")

    def find_usages(
        self,
        construct: Construct,
        reference_files: list[Path],
    ) -> list[Reference]:
        """
        Find usages using a tiered approach with multiple analyzers.

        Args:
            construct: The construct to find usages for
            reference_files: List of files to search in

        Returns:
            List of references to the construct
        """
        all_references = {}

        # Tier 1: Ruff for quick basic detection
        try:
            logger.debug(f"Running Ruff analysis for {construct.name}")
            ruff_refs = self.ruff_analyzer.find_usages(construct, reference_files)
            for ref in ruff_refs:
                key = (ref.file_path, ref.line_number)
                all_references[key] = ref
            logger.debug(f"Ruff found {len(ruff_refs)} references")
        except Exception as e:
            logger.debug(f"Ruff analysis failed: {e}")

        # Tier 2: ast-grep for structural patterns
        try:
            logger.debug(f"Running ast-grep analysis for {construct.name}")
            astgrep_refs = self.astgrep_analyzer.find_usages(construct, reference_files)
            for ref in astgrep_refs:
                key = (ref.file_path, ref.line_number)
                # ast-grep provides more accurate line numbers
                if key not in all_references or ref.line_number > 0:
                    all_references[key] = ref
            logger.debug(f"ast-grep found {len(astgrep_refs)} references")
        except Exception as e:
            logger.debug(f"ast-grep analysis failed: {e}")

        # Tier 3: Pyright for type-based analysis (selective)
        # Only use Pyright for complex cases or when we have few results
        if len(all_references) < 5 or construct.type.value in ["class", "method"]:
            try:
                logger.debug(f"Running Pyright analysis for {construct.name}")
                pyright_refs = self.pyright_analyzer.find_usages(construct, reference_files)
                for ref in pyright_refs:
                    key = (ref.file_path, ref.line_number)
                    if key not in all_references:
                        all_references[key] = ref
                logger.debug(f"Pyright found {len(pyright_refs)} references")
            except Exception as e:
                logger.debug(f"Pyright analysis failed: {e}")

        # Tier 4: Fallback to traditional analyzers if enabled and needed
        if self.use_fallback and len(all_references) == 0:
            try:
                logger.debug(f"Falling back to traditional analysis for {construct.name}")
                fallback_refs = self.fallback_analyzer.find_usages(construct, reference_files)
                for ref in fallback_refs:
                    key = (ref.file_path, ref.line_number)
                    all_references[key] = ref
                logger.debug(f"Traditional analyzer found {len(fallback_refs)} references")
            except Exception as e:
                logger.warning(f"Fallback analysis failed: {e}")

        # Return deduplicated references
        return list(all_references.values())
