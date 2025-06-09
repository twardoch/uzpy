# this_file: src/uzpy/pipeline.py

"""
Core pipeline for uzpy analysis and modification.

This module contains the main orchestration logic, taking procedural code
out of cli.py to separate user interaction from core functionality.
"""

from pathlib import Path

from loguru import logger

from uzpy.analyzer import HybridAnalyzer
from uzpy.discovery import FileDiscovery, discover_files
from uzpy.modifier import LibCSTModifier
from uzpy.parser import TreeSitterParser
from uzpy.types import Construct, Reference


def run_analysis_and_modification(
    edit_path: Path,
    ref_path: Path,
    exclude_patterns: list[str] | None,
    dry_run: bool,
) -> dict[Construct, list[Reference]]:
    """
    Orchestrates the full uzpy pipeline: discovery, parsing, analysis,
    and modification.

    Args:
        edit_path: Path containing files to edit
        ref_path: Path containing reference files to search
        exclude_patterns: Additional patterns to exclude from analysis
        dry_run: Show what changes would be made without modifying files

    Returns:
        Dictionary mapping constructs to their usage references

    Used in:
    - cli.py
    - pipeline.py
    - src/uzpy/cli.py
    """
    # Step 1: Discover files
    logger.info("Discovering files...")
    try:
        edit_files, ref_files = discover_files(edit_path, ref_path, exclude_patterns)
    except Exception as e:
        logger.error(f"Error discovering files: {e}")
        raise

    if not edit_files:
        logger.warning("No Python files found in edit path")
        return {}

    if not ref_files:
        logger.warning("No Python files found in reference path")
        return {}

    logger.info(f"Found {len(edit_files)} edit files and {len(ref_files)} reference files")

    # Step 2: Parse constructs
    logger.info("Parsing edit files for constructs...")
    parser = TreeSitterParser()
    all_constructs = []

    for edit_file in edit_files:
        try:
            constructs = parser.parse_file(edit_file)
            all_constructs.extend(constructs)
            logger.debug(f"Found {len(constructs)} constructs in {edit_file}")
        except Exception as e:
            logger.error(f"Failed to parse {edit_file}: {e}")
            continue

    if not all_constructs:
        logger.warning("No constructs found in edit files")
        return {}

    logger.info(f"Found {len(all_constructs)} total constructs")

    # Step 3: Analyze usages
    logger.info("Finding references...")
    try:
        analyzer = HybridAnalyzer(ref_path, exclude_patterns)
        logger.debug("Initialized hybrid analyzer")
    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {e}")
        raise

    usage_results = {}

    # Get all reference files for analysis
    file_discovery = FileDiscovery(exclude_patterns)
    ref_files = list(file_discovery.find_python_files(ref_path))

    total_constructs = len(all_constructs)
    for i, construct in enumerate(all_constructs, 1):
        logger.debug(f"Analyzing {construct.name} ({i}/{total_constructs})")

        try:
            # Find where this construct is used (already returns Reference objects)
            references = analyzer.find_usages(construct, ref_files)
            usage_results[construct] = references

            if references:
                logger.debug(f"Found {len(references)} references for {construct.name}")

        except Exception as e:
            logger.warning(f"Error analyzing {construct.name}: {e}")
            usage_results[construct] = []

    # Summary of analysis results
    constructs_with_refs = sum(1 for refs in usage_results.values() if refs)
    total_references = sum(len(refs) for refs in usage_results.values())
    logger.info(f"Found usages for {constructs_with_refs}/{total_constructs} constructs")
    logger.info(f"Total references found: {total_references}")

    # Step 4: Modify docstrings (if not dry_run)
    if not dry_run:
        logger.info("Updating docstrings...")
        try:
            project_root = ref_path.parent if ref_path.is_file() else ref_path
            modifier = LibCSTModifier(project_root)
            modification_results = modifier.modify_files(usage_results)

            # Show modification summary
            successful_modifications = sum(1 for success in modification_results.values() if success)
            total_files = len(modification_results)

            if successful_modifications > 0:
                logger.info(f"Successfully updated {successful_modifications}/{total_files} files")
            else:
                logger.info("No files needed modification")

        except Exception as e:
            logger.error(f"Failed to apply modifications: {e}")
            raise
    else:
        logger.info("Dry run mode - no files modified")

    return usage_results
