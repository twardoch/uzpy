# this_file: src/uzpy/analyzer/hybrid_analyzer.py

"""
Hybrid analyzer combining Rope and Jedi for optimal accuracy and performance.

This analyzer uses both Rope and Jedi to find construct usage, leveraging
Rope's accuracy for complex cases and Jedi's speed for straightforward ones.
"""

import time
from pathlib import Path
from typing import Any # For Any type hint

from loguru import logger

from uzpy.analyzer.jedi_analyzer import JediAnalyzer
from uzpy.analyzer.rope_analyzer import RopeAnalyzer
from uzpy.types import Construct, ConstructType, Reference


class HybridAnalyzer:
    """
    Hybrid analyzer that combines Rope and Jedi for optimal results.
    """

    def __init__(self, project_path: Path, exclude_patterns: list[str] | None = None):
        self.project_path = project_path
        self.exclude_patterns = exclude_patterns or []
        self.rope_analyzer = None
        self.jedi_analyzer = None
        self.rope_available = False
        self.jedi_available = False

        try:
            self.rope_analyzer = RopeAnalyzer(project_path, exclude_patterns)
            self.rope_available = True
        except Exception as e:
            logger.warning(f"Rope analyzer initialization failed: {e}")

        try:
            self.jedi_analyzer = JediAnalyzer(project_path)
            self.jedi_available = True
        except Exception as e:
            logger.warning(f"Jedi analyzer initialization failed: {e}")

        if not self.rope_available and not self.jedi_available:
            msg = "Neither Rope nor Jedi analyzers could be initialized"
            raise RuntimeError(msg)
        logger.info(f"Hybrid analyzer initialized (Rope: {self.rope_available}, Jedi: {self.jedi_available})")

    def find_usages(self, construct: Construct, search_paths: list[Path]) -> list[Reference]:
        jedi_results: list[Reference] = []
        rope_results: list[Reference] = []

        if self.jedi_available and self.jedi_analyzer:
            try:
                jedi_refs = self.jedi_analyzer.find_usages(construct, search_paths)
                jedi_results.extend(jedi_refs)
                logger.debug(f"Jedi found {len(jedi_refs)} references for {construct.full_name}")
            except Exception as e:
                logger.debug(f"Jedi analysis failed for {construct.full_name}: {e}")

        if self.rope_available and self.rope_analyzer:
            try:
                rope_refs = self.rope_analyzer.find_usages(construct, search_paths)
                rope_results.extend(rope_refs)
                logger.debug(f"Rope found {len(rope_refs)} references for {construct.full_name}")
            except Exception as e:
                logger.debug(f"Rope analysis failed for {construct.full_name}: {e}")

        # Deduplicate and merge based on (file_path, line_number, column_number)
        # This makes the Reference objects comparable for deduplication purposes.
        # Assuming Reference is made hashable and comparable based on these.
        # If not, use a tuple of these attributes as dict keys for deduplication.

        # Using a dictionary to store unique references based on a key tuple
        # to ensure each reference is unique by its location.
        unique_references: dict[tuple[Path, int, int], Reference] = {}

        for ref in jedi_results:
            key = (ref.file_path.resolve(), ref.line_number, ref.column_number)
            if key not in unique_references:
                unique_references[key] = ref

        for ref in rope_results: # Add Rope's, potentially overwriting Jedi's if more precise
            key = (ref.file_path.resolve(), ref.line_number, ref.column_number)
            # Simple strategy: prefer rope if both exist for the exact same spot,
            # or add if new. A more complex merge could compare context etc.
            unique_references[key] = ref

        final_references = list(unique_references.values())

        if jedi_results or rope_results: # Log only if any analyzer ran
             logger.debug(f"Merged results for {construct.full_name}: {len(final_references)} unique references.")
        else:
             logger.debug(f"No results from Jedi or Rope for {construct.full_name}.")

        return final_references

    def analyze_batch(self, constructs: list[Construct], search_paths: list[Path]) -> dict[Construct, list[Reference]]:
        logger.info(f"Starting hybrid analysis of {len(constructs)} constructs")
        start_time = time.time()

        results_by_construct: dict[Construct, list[Reference]]

        # Decide on strategy
        if len(constructs) < 50 and self.rope_available: # Magic number 50, consider making configurable
            strategy = "full_hybrid"
        elif self.jedi_available:
            strategy = "jedi_primary"
        elif self.rope_available: # Fallback if only Rope is available
            strategy = "rope_only"
        else: # Should not happen due to __init__ check, but as a safeguard
            logger.error("No underlying analyzers available for batch analysis.")
            return {c: [] for c in constructs}

        logger.debug(f"Using strategy: {strategy}")

        if strategy == "full_hybrid":
            results_by_construct = self._analyze_full_hybrid(constructs, search_paths)
        elif strategy == "jedi_primary":
            results_by_construct = self._analyze_jedi_primary(constructs, search_paths)
        else: # rope_only
            results_by_construct = self._analyze_rope_only(constructs, search_paths)

        elapsed = time.time() - start_time
        logger.info(f"Hybrid analysis completed in {elapsed:.2f}s using {strategy} strategy")
        return results_by_construct

    def _analyze_full_hybrid(self, constructs: list[Construct], search_paths: list[Path]) -> dict[Construct, list[Reference]]:
        results = {}
        for i, construct in enumerate(constructs):
            if i % 10 == 0: # Log progress every 10 constructs
                logger.debug(f"Processed {i}/{len(constructs)} constructs (full_hybrid)")
            try:
                results[construct] = self.find_usages(construct, search_paths)
            except Exception as e:
                logger.error(f"Error in full_hybrid analysis for {construct.full_name}: {e}", exc_info=True)
                results[construct] = []
        return results

    def _analyze_jedi_primary(self, constructs: list[Construct], search_paths: list[Path]) -> dict[Construct, list[Reference]]:
        if not self.jedi_analyzer: # Should not happen if jedi_available is true
            return {c:[] for c in constructs}

        # Jedi analyzer's analyze_batch should return dict[Construct, list[Reference]]
        # If it returns dict[str, ...], it needs to be adapted or results converted here.
        # Assuming jedi_analyzer.analyze_batch is adapted to return dict[Construct, list[Reference]]
        # For now, let's assume it returns dict[str(full_name), list[Reference]] as per current jedi_analyzer.py

        temp_jedi_results_by_name = self.jedi_analyzer.analyze_batch(constructs, search_paths)

        # Convert string-keyed results from jedi_analyzer to Construct-keyed
        results_by_construct: dict[Construct, list[Reference]] = {}
        construct_map_by_name = {c.full_name: c for c in constructs}
        for name, refs in temp_jedi_results_by_name.items():
            if name in construct_map_by_name:
                results_by_construct[construct_map_by_name[name]] = refs
            else:
                logger.warning(f"Jedi returned results for unknown construct name: {name}")


        candidates_for_rope_check = [
            c for c in constructs
            if c.type == ConstructType.METHOD or \
               "." in c.full_name or \
               len(results_by_construct.get(c, [])) == 0
        ]

        if candidates_for_rope_check and self.rope_available and self.rope_analyzer:
            logger.debug(f"Verifying/enhancing {len(candidates_for_rope_check)} constructs with Rope (jedi_primary)")

            for construct_candidate in candidates_for_rope_check:
                try:
                    # Get more definitive/additional results from Rope for these candidates
                    rope_refs_for_candidate = self.rope_analyzer.find_usages(construct_candidate, search_paths)

                    # Merge with existing Jedi results for this construct
                    current_refs = results_by_construct.get(construct_candidate, [])

                    # Deduplicate and merge
                    merged_map: dict[tuple[Path, int, int], Reference] = {}
                    for ref in current_refs:
                        key = (ref.file_path.resolve(), ref.line_number, ref.column_number)
                        merged_map[key] = ref
                    for ref in rope_refs_for_candidate:
                        key = (ref.file_path.resolve(), ref.line_number, ref.column_number)
                        merged_map[key] = ref # Rope might provide more accurate column or context

                    results_by_construct[construct_candidate] = list(merged_map.values())
                except Exception as e:
                    logger.error(f"Error during Rope verification for {construct_candidate.full_name}: {e}", exc_info=True)
                    # Keep existing Jedi results if Rope fails for this specific construct

        return results_by_construct

    def _analyze_rope_only(self, constructs: list[Construct], search_paths: list[Path]) -> dict[Construct, list[Reference]]:
        if not self.rope_analyzer: # Should not happen if rope_available is true
            return {c:[] for c in constructs}

        # Assuming rope_analyzer.analyze_batch returns dict[str(full_name), list[Reference]]
        temp_rope_results_by_name = self.rope_analyzer.analyze_batch(constructs, search_paths)

        results_by_construct: dict[Construct, list[Reference]] = {}
        construct_map_by_name = {c.full_name: c for c in constructs}
        for name, refs in temp_rope_results_by_name.items():
            if name in construct_map_by_name:
                results_by_construct[construct_map_by_name[name]] = refs
            else:
                logger.warning(f"Rope returned results for unknown construct name: {name}")
        return results_by_construct

    def get_analyzer_status(self) -> dict[str, Any]:
        status = {
            "rope_available": self.rope_available,
            "jedi_available": self.jedi_available,
            "project_path": str(self.project_path),
        }
        if self.rope_analyzer and hasattr(self.rope_analyzer, 'get_project_info'):
            status["rope_info"] = self.rope_analyzer.get_project_info()
        if self.jedi_analyzer and hasattr(self.jedi_analyzer, 'get_project_info'):
            status["jedi_info"] = self.jedi_analyzer.get_project_info()
        return status

    def close(self) -> None:
        if self.rope_analyzer and hasattr(self.rope_analyzer, 'close'):
            self.rope_analyzer.close()
        # Jedi doesn't typically need explicit cleanup of this type
        logger.debug("Hybrid analyzer resources (if any) closed.")

    def __del__(self):
        self.close()
