# this_file: src/uzpy/analyzer/modern_hybrid_analyzer.py

"""
Modern Hybrid Analyzer for uzpy.

This analyzer orchestrates a suite of modern analysis tools including
Ruff, ast-grep, and Pyright. It aims for a balance of speed and accuracy
by using faster tools for initial sweeps and more comprehensive tools
for deeper analysis or when initial results are insufficient.
"""

from pathlib import Path
from typing import Any  # Optional removed

from loguru import logger

from uzpy.analyzer.astgrep_analyzer import AstGrepAnalyzer
from uzpy.analyzer.pyright_analyzer import PyrightAnalyzer
from uzpy.analyzer.ruff_analyzer import RuffAnalyzer
from uzpy.types import Construct, Reference

# Importing existing analyzers for potential fallback or comparison


class ModernHybridAnalyzer:
    """
    Orchestrates modern analyzers (Ruff, ast-grep, Pyright) with a tiered strategy.
    Can also incorporate traditional analyzers (Jedi, Rope) as fallbacks or for comparison.
    """

    def __init__(
        self,
        project_root: Path,
        python_executable: str | None = None,  # For Pyright
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize the ModernHybridAnalyzer.

        Args:
            project_root: The root directory of the project.
            python_executable: Path to the python executable for Pyright.
            config: Configuration dictionary for analyzer behavior.
                    Example: {"use_ruff": True, "use_astgrep": True, "use_pyright": True,
                              "short_circuit_threshold": 5}
        """
        self.project_root = project_root
        self.config = config if config is not None else {}

        # Initialize individual analyzers
        # These could be conditionally initialized based on config
        if self.config.get("use_ruff", True):  # Default to True if not specified
            self.ruff_analyzer = RuffAnalyzer(project_root)
        else:
            self.ruff_analyzer = None

        if self.config.get("use_astgrep", True):
            self.ast_grep_analyzer = AstGrepAnalyzer(project_root)
        else:
            self.ast_grep_analyzer = None

        if self.config.get("use_pyright", True):
            self.pyright_analyzer = PyrightAnalyzer(project_root, python_executable)
        else:
            self.pyright_analyzer = None

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

        The process can short-circuit if a sufficient number of references are found by earlier stages.
        Results from different analyzers are merged and deduplicated.
        """
        all_references: dict[tuple[Path, int, int], Reference] = {}  # Use (path, line, col) as key for deduplication

        def _add_references(new_refs: list[Reference]):
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

        # Stage 2: ast-grep Analyzer
        if self.ast_grep_analyzer:
            logger.debug(f"Running AstGrepAnalyzer for {construct.full_name}...")
            try:
                ast_grep_refs = self.ast_grep_analyzer.find_usages(construct, search_paths)
                _add_references(ast_grep_refs)
                if self.short_circuit_threshold > 0 and len(all_references) >= self.short_circuit_threshold:
                    logger.info(
                        f"Short-circuiting after AstGrepAnalyzer for {construct.full_name}. "
                        f"Found {len(all_references)} references."
                    )
                    return list(all_references.values())
            except Exception as e:
                logger.error(f"Error during AstGrepAnalyzer execution for {construct.full_name}: {e}")

        # Stage 3: Pyright Analyzer
        if self.pyright_analyzer:
            logger.debug(f"Running PyrightAnalyzer for {construct.full_name}...")
            try:
                pyright_refs = self.pyright_analyzer.find_usages(construct, search_paths)
                _add_references(pyright_refs)
                # No short-circuit check here as it's the last main stage
            except Exception as e:
                logger.error(f"Error during PyrightAnalyzer execution for {construct.full_name}: {e}")

        final_references_list = list(all_references.values())
        logger.info(
            f"ModernHybridAnalyzer found {len(final_references_list)} unique references for {construct.full_name}."
        )
        return final_references_list

    def analyze_batch(self, constructs: list[Construct], search_paths: list[Path]) -> dict[Construct, list[Reference]]:
        """
        Analyze a batch of constructs using the tiered strategy for each.
        This method currently iterates and calls `find_usages` for each construct.
        True batching capabilities would depend on the underlying analyzers.
        """
        logger.info(f"ModernHybridAnalyzer starting batch analysis of {len(constructs)} constructs.")
        results = {}
        for i, construct in enumerate(constructs):
            logger.debug(f"Batch processing construct {i + 1}/{len(constructs)}: {construct.full_name}")
            results[construct] = self.find_usages(construct, search_paths)

        logger.info(f"ModernHybridAnalyzer batch analysis completed for {len(constructs)} constructs.")
        return results

    def close(self) -> None:
        """Close any resources held by the underlying analyzers."""
        if self.ruff_analyzer and hasattr(self.ruff_analyzer, "close"):
            self.ruff_analyzer.close()
        if self.ast_grep_analyzer and hasattr(self.ast_grep_analyzer, "close"):
            self.ast_grep_analyzer.close()
        if self.pyright_analyzer and hasattr(self.pyright_analyzer, "close"):
            self.pyright_analyzer.close()
        logger.info("ModernHybridAnalyzer and its components closed.")

    def __del__(self) -> None:
        self.close()

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to specific analyzers if the attribute
        is not found on ModernHybridAnalyzer itself. This could be useful
        for accessing specific methods of underlying analyzers if needed,
        though direct interaction is generally discouraged in favor of
        the hybrid methods.
        """
        # Example: try to delegate to Pyright first, then others.
        if self.pyright_analyzer and hasattr(self.pyright_analyzer, name):
            return getattr(self.pyright_analyzer, name)
        if self.ast_grep_analyzer and hasattr(self.ast_grep_analyzer, name):
            return getattr(self.ast_grep_analyzer, name)
        if self.ruff_analyzer and hasattr(self.ruff_analyzer, name):
            return getattr(self.ruff_analyzer, name)

        msg = (
            f"'{type(self).__name__}' object has no attribute '{name}', "
            "and it was not found in its configured sub-analyzers."
        )
        raise AttributeError(msg)
