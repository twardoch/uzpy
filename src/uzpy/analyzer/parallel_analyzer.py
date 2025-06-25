# this_file: src/uzpy/analyzer/parallel_analyzer.py

"""
Parallel analyzer for uzpy.

This module provides a ParallelAnalyzer class that wraps another analyzer
to distribute the analysis of constructs across multiple processes using
the `multiprocessing` module. It aims to speed up analysis on multi-core
systems. It also integrates `multiprocessing-logging` for better log handling
from child processes.
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

    It distributes the workload of analyzing multiple constructs across a pool of worker processes.
    Note: The wrapped analyzer (and its components) must be picklable to be passed to child processes.
    If not, the worker function (_analyze_construct_worker) would need to reconstruct the analyzer.
    """

    def __init__(self, analyzer: Any, num_workers: int | None = None):
        """
        Initialize the ParallelAnalyzer.

        Args:
            analyzer: The analyzer instance to wrap and parallelize. Must be picklable.
            num_workers: The number of worker processes to use. Defaults to `multiprocessing.cpu_count()`.
        """
        self.analyzer = analyzer
        self.num_workers = num_workers if num_workers is not None else multiprocessing.cpu_count()
        # Ensure num_workers is at least 1
        if self.num_workers < 1:
            logger.warning(f"num_workers corrected from {self.num_workers} to 1.")
            self.num_workers = 1

        logger.info(f"ParallelAnalyzer initialized with {self.num_workers} worker(s).")

    def analyze_batch(self, constructs: list[Construct], search_paths: list[Path]) -> dict[Construct, list[Reference]]:
        """
        Analyze a batch of constructs in parallel.

        Args:
            constructs: A list of constructs to analyze.
            search_paths: A list of paths to search for references.

        Returns:
            A dictionary mapping constructs to their list of references.
        """
        if not constructs:
            logger.debug("analyze_batch called with no constructs.")
            return {}

        # If batch size is too small or parallelism is disabled, run sequentially.
        if len(constructs) < self.num_workers or self.num_workers <= 1:
            logger.info(
                f"Batch size ({len(constructs)}) is less than num_workers ({self.num_workers}), "
                f"or num_workers is 1. Running sequentially."
            )
            # Check if the underlying analyzer has its own batch processing
            if hasattr(self.analyzer, "analyze_batch") and callable(self.analyzer.analyze_batch):
                return self.analyzer.analyze_batch(constructs, search_paths)
            # Fallback to individual calls if no batch method on wrapped analyzer
            results_sequential = {}
            for construct_item in constructs:
                if hasattr(self.analyzer, "find_usages") and callable(self.analyzer.find_usages):
                    results_sequential[construct_item] = self.analyzer.find_usages(construct_item, search_paths)
                else:
                    logger.error(f"Wrapped analyzer {type(self.analyzer)} has no find_usages method.")
                    results_sequential[construct_item] = []
            return results_sequential

        logger.info(f"Starting parallel analysis of {len(constructs)} constructs using {self.num_workers} workers.")

        results: dict[Construct, list[Reference]] = {}

        # Using ProcessPoolExecutor for managing the process pool.
        # The context manager ensures the pool is properly shut down.
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit tasks to the executor.
            # _analyze_construct_worker is the target function.
            # self.analyzer is passed as the first argument to the worker.
            # This requires self.analyzer to be picklable.
            futures_map = {
                executor.submit(_analyze_construct_worker, self.analyzer, c, search_paths): c for c in constructs
            }

            for future in concurrent.futures.as_completed(futures_map):
                original_construct = futures_map[future]
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

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the wrapped analyzer if not found in ParallelAnalyzer."""
        if hasattr(self.analyzer, name):
            return getattr(self.analyzer, name)
        msg = (
            f"'{type(self).__name__}' object and its wrapped analyzer "
            f"'{type(self.analyzer).__name__}' have no attribute '{name}'"
        )
        raise AttributeError(msg)

    def close(self) -> None:
        """Close or clean up resources if the underlying analyzer requires it."""
        if hasattr(self.analyzer, "close") and callable(self.analyzer.close):
            try:
                self.analyzer.close()
                logger.debug("Called close() on wrapped analyzer.")
            except Exception as e:
                logger.error(f"Error calling close() on wrapped analyzer: {e}")
        logger.info("ParallelAnalyzer closed (if underlying analyzer had a close method).")

    def __del__(self) -> None:
        """Attempt to close resources when the ParallelAnalyzer is deleted."""
        self.close()
