# this_file: src/uzpy/analyzer/parallel_analyzer.py

"""
Parallel analyzer for uzpy.

This module provides a parallel processing wrapper that can be applied to any
analyzer to analyze multiple constructs concurrently using multiprocessing,
significantly improving performance for large codebases.

"""

import concurrent.futures
import multiprocessing
from pathlib import Path
from typing import Any  # Optional removed

import multiprocessing_logging
from loguru import logger

from uzpy.types import Construct, Reference

# It's important to call install_mp_handler() early, ideally at the start of your main script or module.
# If this module is imported by other modules that might also use multiprocessing,
# ensure this is called only once or in a controlled manner.
# For library code, it's often better to let the application install the handler.
# However, for this specific class designed for parallelism, installing it here
# ensures it's active when ParallelAnalyzer is used.
try:
    multiprocessing_logging.install_mp_handler()
    logger.debug("multiprocessing_logging handler installed by ParallelAnalyzer module.")
except Exception as e:
    logger.warning(
        f"Could not install multiprocessing_logging handler: {e}. Logs from child processes might not be properly captured."
    )


# Helper function to be executed in parallel.
# It needs to be a top-level function for pickling by multiprocessing.
def _analyze_construct_worker(
    analyzer_instance_config: dict, construct: Construct, search_paths: list[Path]
) -> tuple[Construct, list[Reference]]:
    """
    Worker function to analyze a single construct.
    analyzer_instance_config is a dict that allows recreating or configuring the analyzer in the child process.
    This avoids pickling complex analyzer objects.
    """
    # This is a simplified example. In a real scenario, analyzer_instance_config
    # would contain info to recreate/get an analyzer instance.
    # For now, assuming the passed 'analyzer_instance' in ParallelAnalyzer is simple enough or
    # that this worker function gets a picklable 'analyzer_instance'.
    # The direct passing of analyzer_instance as done in the ProcessPoolExecutor submit
    # implies it must be picklable. If not, this worker needs to reconstruct it.

    # For this example, we assume analyzer_instance_config is the actual analyzer instance
    # if it's passed directly and is picklable.
    analyzer_instance = analyzer_instance_config

    try:
        # Logs from here should be handled by multiprocessing_logging
        logger.debug(f"Worker (PID {multiprocessing.current_process().pid}): Analyzing {construct.full_name}")
        references = analyzer_instance.find_usages(construct, search_paths)
        logger.debug(
            f"Worker (PID {multiprocessing.current_process().pid}): Found {len(references)} refs for {construct.full_name}"
        )
        return construct, references
    except Exception as e:
        logger.error(
            f"Worker (PID {multiprocessing.current_process().pid}): Error analyzing {construct.full_name}: {e}"
        )
        return construct, []


class ParallelAnalyzer:
    """
    A wrapper class that parallelizes the analysis of constructs using an underlying analyzer.

    This class wraps an existing analyzer and adds multiprocessing support
    to analyze multiple constructs concurrently, significantly improving
    performance for large numbers of constructs.

    Used in:
    - src/uzpy/analyzer/__init__.py
    - src/uzpy/pipeline.py
    """

    def __init__(self, analyzer: Any, num_workers: int | None = None):
        """
        Initialize the ParallelAnalyzer.

        Args:
            analyzer: The underlying analyzer to wrap
            max_workers: Maximum number of worker processes (defaults to CPU count)

        """
        self.analyzer = analyzer
        self.num_workers = num_workers if num_workers is not None else multiprocessing.cpu_count()
        # Ensure num_workers is at least 1
        if self.num_workers < 1:
            logger.warning(f"num_workers corrected from {self.num_workers} to 1.")
            self.num_workers = 1

        This method is provided for compatibility with the standard analyzer
        interface. For parallel processing, use find_usages_batch instead.

        Args:
            construct: The construct to find usages for
            reference_files: List of files to search in

        Returns:
            List of references to the construct

        """
        return self.analyzer.find_usages(construct, reference_files)

    def analyze_batch(self, constructs: list[Construct], search_paths: list[Path]) -> dict[Construct, list[Reference]]:
        """
        Analyze a batch of constructs in parallel.

        Args:
            constructs: A list of constructs to analyze.
            search_paths: A list of paths to search for references.

        Returns:
            Dictionary mapping constructs to their references

        Used in:
        - src/uzpy/pipeline.py
        """
        if not constructs:
            logger.debug("analyze_batch called with no constructs.")
            return {}

        # If only one construct or one worker, use sequential processing
        if len(constructs) == 1 or self.max_workers == 1:
            results = {}
            for i, construct in enumerate(constructs):
                results[construct] = self.analyzer.find_usages(construct, reference_files)
                if progress_callback:
                    progress_callback(i + 1, len(constructs))
            return results

        logger.info(f"Analyzing {len(constructs)} constructs in parallel with {self.max_workers} workers")

        # Create a pool of workers
        with mp.Pool(processes=self.max_workers) as pool:
            # Create partial function with fixed reference_files
            analyze_func = partial(self._analyze_construct, reference_files=reference_files)

            # Submit all tasks (create serializable constructs without tree-sitter nodes)
            async_results = []
            for construct in constructs:
                # Create serializable construct without the unpickleable Node object
                serializable_construct = Construct(
                    name=construct.name,
                    type=construct.type,
                    file_path=construct.file_path,
                    line_number=construct.line_number,
                    docstring=construct.docstring,
                    full_name=construct.full_name,
                    node=None,  # Remove unpickleable Node
                )
                result = pool.apply_async(analyze_func, args=(serializable_construct,))
                async_results.append((construct, result))  # Keep original construct as key

            # Collect results with progress tracking
            results = {}
            completed = 0

            for construct, async_result in async_results:
                try:
                    # future.result() will raise an exception if the worker failed.
                    _processed_construct, references = future.result()
                    # It's important to use the original_construct object as the key,
                    # as the one returned from the worker might be a copy.
                    results[original_construct] = references
                except Exception as e:
                    logger.error(f"Error processing construct {original_construct.full_name} in parallel worker: {e}")
                    results[original_construct] = []  # Ensure entry for failed constructs

        logger.info(f"Parallel analysis of {len(constructs)} constructs completed.")
        return results

    def _analyze_construct(self, construct: Construct, reference_files: list[Path]) -> list[Reference]:
        """
        Worker function to analyze a single construct.

        This method is called by worker processes in the pool.

        Args:
            construct: The construct to analyze
            reference_files: List of files to search in

        Returns:
            List of references to the construct

        """
        try:
            # Note: The analyzer instance is recreated in each worker process
            # This ensures thread safety but may impact performance
            return self.analyzer.find_usages(construct, reference_files)
        except Exception as e:
            logger.error(f"Worker error analyzing {construct.name}: {e}")
            return []
