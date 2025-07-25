# this_file: src/uzpy/pipeline.py

"""
Core pipeline for uzpy analysis and modification.

This module contains the main orchestration logic, taking procedural code
out of cli.py to separate user interaction from core functionality.
"""

from pathlib import Path
from typing import Any  # Optional removed

from loguru import logger

from uzpy.analyzer import CachedAnalyzer, ModernHybridAnalyzer, ParallelAnalyzer
from uzpy.discovery import FileDiscovery, discover_files
from uzpy.modifier import LibCSTModifier, SafeLibCSTModifier

# Import base implementations for default fallback
from uzpy.parser import TreeSitterParser
from uzpy.types import Construct, Reference


def run_analysis_and_modification(
    edit_path: Path,
    ref_path: Path,
    exclude_patterns: list[str] | None,
    dry_run: bool,
    safe_mode: bool = False,
) -> dict[Construct, list[Reference]]:
    """
    Orchestrates the full uzpy pipeline: discovery, parsing, analysis,
    and modification.

    Args:
        edit_path: Path containing files to edit.
        ref_path: Path containing reference files to search.
        exclude_patterns: Additional patterns to exclude from analysis.
        dry_run: Show what changes would be made without modifying files.
        safe_mode: Use SafeLibCSTModifier to prevent syntax corruption.
        parser_instance: Optional pre-configured parser instance.
                         If None, a default TreeSitterParser is used.
        analyzer_instance: Optional pre-configured analyzer instance.
                           If None, a default HybridAnalyzer is used.

    Returns:
        Dictionary mapping constructs to their usage references

    Used in:
    - cli.py
    - pipeline.py
    - src/uzpy/cli.py
    - src/uzpy/cli_modern.py
    - src/uzpy/watcher.py
    - tests/test_cli.py
    - uzpy/cli.py
    """
    # Step 1: Discover files
    logger.info("Discovering files...")
    try:
        edit_files, ref_files_paths = discover_files(edit_path, ref_path, exclude_patterns)
    except Exception as e:
        logger.error(f"Error discovering files: {e}")
        raise

    if not edit_files:
        logger.warning("No Python files found in edit path.")
        return {}

    if not ref_files_paths:  # Note: discover_files returns list of Paths
        logger.warning("No Python files found in reference path.")
        return {}

    logger.info(f"Found {len(edit_files)} edit files and {len(ref_files_paths)} reference files.")

    # Step 2: Parse constructs
    logger.info("Parsing edit files for constructs...")

    # Use provided parser instance or default to TreeSitterParser
    parser = parser_instance if parser_instance else TreeSitterParser()
    logger.debug(f"Using parser: {type(parser).__name__}")

    all_constructs: list[Construct] = []
    for i, edit_file_path in enumerate(edit_files):
        logger.debug(f"Parsing file {i + 1}/{len(edit_files)}: {edit_file_path}")
        try:
            constructs_in_file = parser.parse_file(edit_file_path)
            all_constructs.extend(constructs_in_file)
            logger.debug(f"Found {len(constructs_in_file)} constructs in {edit_file_path}")
        except Exception as e:
            logger.error(f"Failed to parse {edit_file_path}: {e}", exc_info=True)
            continue  # Continue with other files

    if not all_constructs:
        logger.warning("No constructs found in edit files after parsing.")
        return {}

    logger.info(f"Successfully parsed {len(all_constructs)} total constructs from {len(edit_files)} files.")

    # Step 3: Analyze usages
    logger.info("Finding references...")
    try:
        # Use modern analyzer stack
        base_analyzer = ModernHybridAnalyzer(ref_path, exclude_patterns)
        cached_analyzer = CachedAnalyzer(base_analyzer)
        analyzer = ParallelAnalyzer(cached_analyzer)
        logger.debug("Initialized modern parallel cached analyzer")
    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {e}")
        raise

    # Get all reference files for analysis
    file_discovery = FileDiscovery(exclude_patterns)
    ref_files = list(file_discovery.find_python_files(ref_path))

    # Use parallel batch processing for better performance
    def progress_callback(completed, total):
        """    """
        logger.info(f"Progress: {completed}/{total} constructs analyzed")

    usage_results = analyzer.find_usages_batch(all_constructs, ref_files, progress_callback=progress_callback)

    # Summary of analysis results
    constructs_with_refs = sum(1 for refs in usage_results.values() if refs)
    total_references_found = sum(len(refs) for refs in usage_results.values())
    logger.info(f"Analysis complete. Found usages for {constructs_with_refs}/{len(all_constructs)} constructs.")
    logger.info(f"Total references found: {total_references_found}.")

    # Step 4: Modify docstrings (if not dry_run)
    if not dry_run:
        logger.info("Updating docstrings with found references...")
        try:
            # Determine project_root for LibCSTModifier for relative path generation in docstrings
            # This should be the common ancestor or the main project directory being analyzed.
            # Using ref_path's parent (if file) or itself (if dir) is a common heuristic.
            project_root_for_modifier = ref_path.parent if ref_path.is_file() else ref_path
            
            # Use safe modifier if requested
            if safe_mode:
                logger.info("Using SafeLibCSTModifier to prevent syntax corruption")
                modifier = SafeLibCSTModifier(project_root_for_modifier)
            else:
                modifier = LibCSTModifier(project_root_for_modifier)

            modification_results = modifier.modify_files(usage_results)

            successful_modifications = sum(1 for success in modification_results.values() if success)
            total_files_processed_for_modification = len(modification_results)

            if successful_modifications > 0:
                logger.info(
                    f"Successfully updated {successful_modifications}/{total_files_processed_for_modification} files."
                )
            elif total_files_processed_for_modification > 0:  # Files were processed but none needed changes
                logger.info(
                    f"{total_files_processed_for_modification} files processed, but no docstring updates were necessary."
                )
            else:  # No files were relevant for modification based on usage_results
                logger.info("No files identified for docstring modification.")

        except Exception as e:
            logger.error(f"Failed to apply modifications to docstrings: {e}", exc_info=True)
            # Decide if this should re-raise or just log. For now, just log.
    else:
        logger.info("Dry run mode active - no files were modified.")

    # Close parser and analyzer if they have close methods (e.g., for releasing resources)
    if hasattr(parser, "close") and callable(parser.close):
        try:
            parser.close()
        except Exception as e:
            logger.warning(f"Error closing parser {type(parser).__name__}: {e}")

    if hasattr(analyzer, "close") and callable(analyzer.close):
        try:
            analyzer.close()
        except Exception as e:
            logger.warning(f"Error closing analyzer {type(analyzer).__name__}: {e}")

    return usage_results
