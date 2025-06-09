# this_file: src/uzpy/analyzer/parallel_analyzer.py

"""
Parallel analyzer for concurrent analysis of multiple constructs.

This module provides a parallel processing wrapper that can be applied to any
analyzer to analyze multiple constructs concurrently using multiprocessing,
significantly improving performance for large codebases.
"""

import multiprocessing as mp
from functools import partial
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from uzpy.types import Construct, Reference


class ParallelAnalyzer:
    """
    Parallel processing wrapper for any analyzer implementation.
    
    This class wraps an existing analyzer and adds multiprocessing support
    to analyze multiple constructs concurrently, significantly improving
    performance for large numbers of constructs.
    """
    
    def __init__(self, analyzer: Any, max_workers: Optional[int] = None):
        """
        Initialize parallel analyzer with an underlying analyzer.
        
        Args:
            analyzer: The underlying analyzer to wrap
            max_workers: Maximum number of worker processes (defaults to CPU count)
        """
        self.analyzer = analyzer
        self.max_workers = max_workers or mp.cpu_count()
        logger.debug(f"Initialized parallel analyzer with {self.max_workers} workers")
    
    def find_usages(
        self, 
        construct: Construct, 
        reference_files: list[Path]
    ) -> list[Reference]:
        """
        Find usages of a single construct (for compatibility).
        
        This method is provided for compatibility with the standard analyzer
        interface. For parallel processing, use find_usages_batch instead.
        
        Args:
            construct: The construct to find usages for
            reference_files: List of files to search in
            
        Returns:
            List of references to the construct
        """
        return self.analyzer.find_usages(construct, reference_files)
    
    def find_usages_batch(
        self,
        constructs: list[Construct],
        reference_files: list[Path],
        progress_callback: Optional[callable] = None
    ) -> dict[Construct, list[Reference]]:
        """
        Find usages of multiple constructs in parallel.
        
        This method analyzes multiple constructs concurrently using
        multiprocessing, significantly improving performance.
        
        Args:
            constructs: List of constructs to analyze
            reference_files: List of files to search in
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary mapping constructs to their references
        """
        if not constructs:
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
            
            # Submit all tasks
            async_results = []
            for construct in constructs:
                result = pool.apply_async(analyze_func, args=(construct,))
                async_results.append((construct, result))
            
            # Collect results with progress tracking
            results = {}
            completed = 0
            
            for construct, async_result in async_results:
                try:
                    references = async_result.get(timeout=60)  # 60 second timeout per construct
                    results[construct] = references
                except mp.TimeoutError:
                    logger.warning(f"Timeout analyzing {construct.name}")
                    results[construct] = []
                except Exception as e:
                    logger.error(f"Error analyzing {construct.name}: {e}")
                    results[construct] = []
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(constructs))
        
        logger.info(f"Parallel analysis complete: {len(results)} constructs analyzed")
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