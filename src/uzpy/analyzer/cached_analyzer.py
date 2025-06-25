# this_file: src/uzpy/analyzer/cached_analyzer.py

"""
Cached analyzer decorator for uzpy.

This module provides a CachedAnalyzer class that can wrap any uzpy analyzer
to add a persistent caching layer using diskcache. This helps to speed up
repeated analysis runs by caching results of file parsing and construct analysis.
"""

import hashlib
from pathlib import Path
from typing import Any

import diskcache
from loguru import logger

from uzpy.types import Construct, Reference


class CachedAnalyzer:
    """
    A wrapper class that adds caching functionality to an underlying analyzer.

    Uses diskcache to store and retrieve analysis results, reducing redundant
    computation for unchanged files or constructs.
    """

    def __init__(self, analyzer: Any, cache_dir: Path, cache_name: str = "analyzer_cache"):
        """
        Initialize the CachedAnalyzer.

        Args:
            analyzer: The analyzer instance to wrap (e.g., HybridAnalyzer, RuffAnalyzer).
            cache_dir: The directory where the cache will be stored.
            cache_name: The name of the cache subdirectory.
        """
        self.analyzer = analyzer
        self.cache_path = cache_dir / cache_name
        self.cache = diskcache.Cache(str(self.cache_path))  # Ensure cache_path is string
        logger.info(f"CachedAnalyzer initialized. Cache location: {self.cache_path}")

    def _get_file_hash(self, file_path: Path) -> str:
        """
        Generate a hash for a file based on its content and modification time.

        Args:
            file_path: The path to the file.

        Returns:
            A string hash representing the file's state.
        """
        try:
            stat = file_path.stat()
            # Read file in chunks to handle large files efficiently
            hasher = hashlib.md5()
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):  # 8KB chunks
                    hasher.update(chunk)
            content_hash = hasher.hexdigest()
            return f"{content_hash}-{stat.st_mtime_ns}"
        except FileNotFoundError:
            logger.warning(f"File not found for hashing: {file_path}")
            return f"nonexistent-{file_path.name}"  # Consistent hash for nonexistent files
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return f"error-{file_path.name}"  # Consistent hash for error state

    def _get_construct_cache_key(self, construct: Construct, search_paths_hash: str) -> str:
        """
        Generate a cache key for a specific construct analysis.

        Args:
            construct: The Construct object.
            search_paths_hash: A hash representing the state of all search paths.

        Returns:
            A string cache key.
        """
        file_hash = self._get_file_hash(construct.file_path)
        # Using a tuple for the key components before joining, for clarity
        key_parts = (
            "construct_analysis",
            construct.full_name,
            str(construct.file_path.name),  # Use relative path or name for better key stability
            file_hash,
            str(construct.line_number),
            search_paths_hash,
        )
        return ":".join(key_parts)

    def _get_search_paths_hash(self, search_paths: list[Path]) -> str:
        """
        Generate a hash representing the state of all files in search_paths.
        This is important because changes in reference files can invalidate
        cached analysis results for a construct.
        """
        path_hashes = []
        # Sort paths to ensure consistent hash order
        for p_item in sorted(search_paths, key=lambda x: str(x)):
            if p_item.is_file():
                path_hashes.append(self._get_file_hash(p_item))
            elif p_item.is_dir():
                # For directories, hash the sorted list of (filename, filehash) tuples
                # This is more robust than just hashing file hashes.
                # Consider limiting recursion depth for very large directories if performance becomes an issue.
                dir_file_details = []
                try:
                    for f_item in sorted(p_item.rglob("*"), key=lambda x: str(x)):  # Recursive glob
                        if f_item.is_file():
                            dir_file_details.append(f"{f_item.name}:{self._get_file_hash(f_item)}")
                except Exception as e:
                    logger.warning(f"Could not fully hash directory {p_item}: {e}")

                path_hashes.append(hashlib.md5("".join(dir_file_details).encode("utf-8")).hexdigest())
        return hashlib.md5("".join(path_hashes).encode("utf-8")).hexdigest()

    def find_usages(self, construct: Construct, search_paths: list[Path]) -> list[Reference]:
        """
        Find usages for a construct, using the cache if possible.

        Args:
            construct: The construct to find usages for.
            search_paths: A list of paths to search for references.

        Returns:
            A list of Reference objects.
        """
        search_paths_hash = self._get_search_paths_hash(search_paths)
        cache_key = self._get_construct_cache_key(construct, search_paths_hash)

        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for {construct.full_name} (key: {cache_key})")
            return cached_result

        logger.debug(f"Cache miss for {construct.full_name} (key: {cache_key}). Analyzing...")
        if not hasattr(self.analyzer, "find_usages") or not callable(self.analyzer.find_usages):
            logger.error(f"Wrapped analyzer {type(self.analyzer)} does not have a callable 'find_usages' method.")
            return []

        result = self.analyzer.find_usages(construct, search_paths)
        self.cache.set(cache_key, result)
        logger.debug(f"Stored analysis result for {construct.full_name} in cache (key: {cache_key})")
        return result

    def analyze_batch(self, constructs: list[Construct], search_paths: list[Path]) -> dict[Construct, list[Reference]]:
        """
        Analyze a batch of constructs, utilizing the cache for each.

        Args:
            constructs: A list of constructs to analyze.
            search_paths: A list of paths to search for references.

        Returns:
            A dictionary mapping constructs to their list of references.
        """
        results = {}
        search_paths_hash = self._get_search_paths_hash(search_paths)

        missed_constructs_map = {}  # Store original construct object for cache key

        for construct in constructs:
            cache_key = self._get_construct_cache_key(construct, search_paths_hash)
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Batch cache hit for {construct.full_name} (key: {cache_key})")
                results[construct] = cached_result
            else:
                logger.debug(f"Batch cache miss for {construct.full_name} (key: {cache_key})")
                # Add to a list of constructs that need to be analyzed
                missed_constructs_map[construct.full_name] = construct  # Use full_name as key temporarily

        missed_constructs_list = list(missed_constructs_map.values())

        if missed_constructs_list:
            logger.info(f"Analyzing batch of {len(missed_constructs_list)} cache-missed constructs.")
            if hasattr(self.analyzer, "analyze_batch") and callable(self.analyzer.analyze_batch):
                batch_results = self.analyzer.analyze_batch(missed_constructs_list, search_paths)
                for analyzed_construct, references in batch_results.items():
                    original_construct = missed_constructs_map[analyzed_construct.full_name]
                    results[original_construct] = references
                    cache_key = self._get_construct_cache_key(original_construct, search_paths_hash)
                    self.cache.set(cache_key, references)
                    logger.debug(
                        f"Stored batch analysis result for {original_construct.full_name} in cache (key: {cache_key})"
                    )
            else:  # Fallback to individual analysis for missed constructs
                for original_construct in missed_constructs_list:
                    # This will use individual caching via self.find_usages
                    references = self.find_usages(original_construct, search_paths)
                    results[original_construct] = references
        return results

    def clear(self) -> None:
        """Clear the entire cache."""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cache cleared. {count} items removed from {self.cache_path}.")

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        volume = self.cache.volume()
        count = len(self.cache)
        logger.info(f"Cache stats: {count} items, disk usage: {volume} bytes.")
        return {"item_count": count, "disk_usage_bytes": volume}

    def close(self) -> None:
        """Close the cache."""
        self.cache.close()
        logger.info(f"Cache closed: {self.cache_path}")

    def __del__(self) -> None:
        """Ensure cache is closed when the object is deleted."""
        self.close()

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the wrapped analyzer if not found in CachedAnalyzer."""
        if hasattr(self.analyzer, name):
            return getattr(self.analyzer, name)
        msg = (
            f"'{type(self).__name__}' object and its wrapped analyzer "
            f"'{type(self.analyzer).__name__}' have no attribute '{name}'"
        )
        raise AttributeError(msg)
