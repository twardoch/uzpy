# this_file: src/uzpy/analyzer/hybrid_analyzer.py

"""
Hybrid analyzer combining Rope and Jedi for optimal accuracy and performance.

This analyzer uses both Rope and Jedi to find construct usage, leveraging
Rope's accuracy for complex cases and Jedi's speed for straightforward ones.

Used in:
- analyzer/hybrid_analyzer.py
"""

import time
from pathlib import Path

from loguru import logger

from uzpy.analyzer.jedi_analyzer import JediAnalyzer
from uzpy.analyzer.rope_analyzer import RopeAnalyzer
from uzpy.types import Construct, ConstructType, Reference


class HybridAnalyzer:
    """
    Hybrid analyzer that combines Rope and Jedi for optimal results.

    Uses Jedi for fast initial analysis and Rope for verification and
    complex cases. Provides confidence scoring and fallback mechanisms.

    Used in:
    - analyzer/__init__.py
    - analyzer/hybrid_analyzer.py
    - pipeline.py
    - src/uzpy/analyzer/__init__.py
    - src/uzpy/cli.py
    - src/uzpy/pipeline.py
    - tests/test_analyzer.py
    - uzpy/analyzer/__init__.py
    - uzpy/cli.py
    """

    def __init__(self, project_path: Path, exclude_patterns: list[str] | None = None):
        """
        Initialize the hybrid analyzer.

        Args:
            project_path: Root directory of the project to analyze
            exclude_patterns: Additional patterns to exclude from analysis

        Used in:
        - analyzer/hybrid_analyzer.py
        """
        self.project_path = project_path
        self.exclude_patterns = exclude_patterns or []

        # Initialize both analyzers
        try:
            self.rope_analyzer = RopeAnalyzer(project_path, exclude_patterns)
            self.rope_available = True
        except Exception as e:
            logger.warning(f"Rope analyzer initialization failed: {e}")
            self.rope_analyzer = None
            self.rope_available = False

        try:
            self.jedi_analyzer = JediAnalyzer(project_path)
            self.jedi_available = True
        except Exception as e:
            logger.warning(f"Jedi analyzer initialization failed: {e}")
            self.jedi_analyzer = None
            self.jedi_available = False

        if not self.rope_available and not self.jedi_available:
            msg = "Neither Rope nor Jedi analyzers could be initialized"
            raise RuntimeError(msg)

        logger.info(f"Hybrid analyzer initialized (Rope: {self.rope_available}, Jedi: {self.jedi_available})")

    def find_usages(self, construct: Construct, search_paths: list[Path]) -> list[Reference]:
        """
        Find all files where a construct is used using hybrid approach.

        Args:
            construct: The construct to search for
            search_paths: List of files to search within

        Returns:
            List of Reference objects where the construct is used

        Used in:
        - analyzer/hybrid_analyzer.py
        - pipeline.py
        - src/uzpy/cli.py
        - src/uzpy/pipeline.py
        - tests/test_analyzer.py
        - uzpy/cli.py
        """
        jedi_results = []
        rope_results = []

        # Try Jedi first (faster)
        if self.jedi_available:
            try:
                jedi_refs = self.jedi_analyzer.find_usages(construct, search_paths)
                jedi_results.extend(jedi_refs)
                logger.debug(f"Jedi found {len(jedi_refs)} references for {construct.full_name}")
            except Exception as e:
                logger.debug(f"Jedi analysis failed for {construct.full_name}: {e}")

        # Use Rope for verification and additional results
        if self.rope_available:
            try:
                rope_refs = self.rope_analyzer.find_usages(construct, search_paths)
                rope_results.extend(rope_refs)
                logger.debug(f"Rope found {len(rope_refs)} references for {construct.full_name}")
            except Exception as e:
                logger.debug(f"Rope analysis failed for {construct.full_name}: {e}")

        # Combine results with preference for accuracy
        # Convert to sets of file paths for deduplication
        jedi_files = {ref.file_path for ref in jedi_results}
        rope_files = {ref.file_path for ref in rope_results}

        if rope_files and jedi_files:
            # Use intersection for high confidence, union for comprehensive coverage
            intersection = rope_files & jedi_files
            union = rope_files | jedi_files

            # If intersection is substantial, prefer it (higher confidence)
            if len(intersection) >= len(union) * 0.7:
                final_files = intersection
                logger.debug(f"Using intersection of results for {construct.full_name}")
            else:
                final_files = union
                logger.debug(f"Using union of results for {construct.full_name}")
        elif rope_files:
            final_files = rope_files
            logger.debug(f"Using Rope results only for {construct.full_name}")
        elif jedi_files:
            final_files = jedi_files
            logger.debug(f"Using Jedi results only for {construct.full_name}")
        else:
            final_files = set()
            logger.debug(f"No results found for {construct.full_name}")

        # Convert back to Reference objects, preferring Rope results if available
        final_references = []
        for file_path in final_files:
            # Prefer rope reference if available, otherwise use jedi
            rope_ref = next((ref for ref in rope_results if ref.file_path == file_path), None)
            jedi_ref = next((ref for ref in jedi_results if ref.file_path == file_path), None)

            if rope_ref:
                final_references.append(rope_ref)
            elif jedi_ref:
                final_references.append(jedi_ref)
            else:
                # Fallback to basic Reference
                final_references.append(Reference(file_path=file_path, line_number=1))

        return final_references

    def analyze_batch(self, constructs: list[Construct], search_paths: list[Path]) -> dict[str, list[Reference]]:
        """
        Analyze multiple constructs using hybrid approach.

        Args:
            constructs: List of constructs to analyze
            search_paths: List of paths to search within

        Returns:
            Dictionary mapping construct full names to lists of usage references

        Used in:
        - analyzer/hybrid_analyzer.py
        - tests/test_analyzer.py
        """
        logger.info(f"Starting hybrid analysis of {len(constructs)} constructs")
        start_time = time.time()

        results = {}

        # Decide on strategy based on construct count and available analyzers
        if len(constructs) < 50 and self.rope_available:
            # For small batches, use full hybrid approach
            strategy = "full_hybrid"
        elif self.jedi_available:
            # For large batches, prefer Jedi with selective Rope verification
            strategy = "jedi_primary"
        else:
            # Fall back to Rope only
            strategy = "rope_only"

        logger.debug(f"Using strategy: {strategy}")

        if strategy == "full_hybrid":
            results = self._analyze_full_hybrid(constructs, search_paths)
        elif strategy == "jedi_primary":
            results = self._analyze_jedi_primary(constructs, search_paths)
        else:
            results = self._analyze_rope_only(constructs, search_paths)

        elapsed = time.time() - start_time
        logger.info(f"Hybrid analysis completed in {elapsed:.2f}s using {strategy} strategy")

        return results

    def _analyze_full_hybrid(self, constructs: list[Construct], search_paths: list[Path]) -> dict[str, list[Reference]]:
        """Full hybrid analysis using both analyzers for each construct.

        Used in:
        - analyzer/hybrid_analyzer.py
        """
        results = {}

        for i, construct in enumerate(constructs):
            if i % 10 == 0:
                logger.debug(f"Processed {i}/{len(constructs)} constructs")

            try:
                usage_refs = self.find_usages(construct, search_paths)
                results[construct.full_name] = usage_refs
            except Exception as e:
                logger.error(f"Error in hybrid analysis for {construct.full_name}: {e}")
                results[construct.full_name] = []

        return results

    def _analyze_jedi_primary(
        self, constructs: list[Construct], search_paths: list[Path]
    ) -> dict[str, list[Reference]]:
        """Jedi-primary analysis with selective Rope verification.

        Used in:
        - analyzer/hybrid_analyzer.py
        """
        # Use Jedi for initial analysis
        jedi_results = self.jedi_analyzer.analyze_batch(constructs, search_paths)

        # Identify constructs that might need Rope verification
        # (e.g., methods, complex inheritance cases)
        candidates_for_rope = [
            c
            for c in constructs
            if c.type == ConstructType.METHOD or "." in c.full_name or len(jedi_results.get(c.full_name, [])) == 0
        ]

        if candidates_for_rope and self.rope_available:
            logger.debug(f"Verifying {len(candidates_for_rope)} constructs with Rope")
            rope_results = self.rope_analyzer.analyze_batch(candidates_for_rope, search_paths)

            # Merge results, preferring Rope for verified constructs
            for construct in candidates_for_rope:
                rope_refs = rope_results.get(construct.full_name, [])
                jedi_refs = jedi_results.get(construct.full_name, [])

                # Use union of both results
                combined_files = {ref.file_path for ref in rope_refs} | {ref.file_path for ref in jedi_refs}
                combined_refs = []

                for file_path in combined_files:
                    # Prefer rope reference if available, otherwise use jedi
                    rope_ref = next((ref for ref in rope_refs if ref.file_path == file_path), None)
                    jedi_ref = next((ref for ref in jedi_refs if ref.file_path == file_path), None)

                    if rope_ref:
                        combined_refs.append(rope_ref)
                    elif jedi_ref:
                        combined_refs.append(jedi_ref)

                jedi_results[construct.full_name] = combined_refs

        return jedi_results

    def _analyze_rope_only(self, constructs: list[Construct], search_paths: list[Path]) -> dict[str, list[Reference]]:
        """Rope-only analysis fallback.

        Used in:
        - analyzer/hybrid_analyzer.py
        """
        if not self.rope_available:
            logger.error("Rope analyzer not available for fallback")
            return {c.full_name: [] for c in constructs}

        return self.rope_analyzer.analyze_batch(constructs, search_paths)

    def get_analyzer_status(self) -> dict[str, any]:
        """Get status information about both analyzers.

        Used in:
        - analyzer/hybrid_analyzer.py
        """
        status = {
            "rope_available": self.rope_available,
            "jedi_available": self.jedi_available,
            "project_path": str(self.project_path),
        }

        if self.rope_available:
            status["rope_info"] = self.rope_analyzer.get_project_info()

        if self.jedi_available:
            status["jedi_info"] = self.jedi_analyzer.get_project_info()

        return status

    def close(self) -> None:
        """Clean up both analyzers.

        Used in:
        - analyzer/hybrid_analyzer.py
        """
        if self.rope_analyzer:
            self.rope_analyzer.close()

        # Jedi doesn't need explicit cleanup
        logger.debug("Hybrid analyzer closed")
