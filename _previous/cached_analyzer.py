# this_file: src/uzpy/analyzer/cached_analyzer.py

"""
Caching layer for analyzers to improve performance.

This module provides a caching wrapper that can be applied to any analyzer
to cache parsed constructs and analysis results, significantly improving
performance for repeated operations on the same files.
"""

import hashlib
from pathlib import Path
from typing import Any, Optional, Union

import diskcache
from loguru import logger

from uzpy.types import Construct, Reference


class CachedAnalyzer:
    """
    Caching wrapper for any analyzer implementation.

    This class wraps an existing analyzer and adds persistent caching
    using diskcache. It caches both parsed constructs and analysis results,
    invalidating cache entries when files are modified.
    """

    def __init__(self, analyzer: Any, cache_dir: Path | None = None):
        """
        Initialize cached analyzer with an underlying analyzer.

        Args:
            analyzer: The underlying analyzer to wrap
            cache_dir: Directory for cache storage (defaults to ~/.uzpy/cache)
        """
        self.analyzer = analyzer
        if cache_dir is None:
            cache_dir = Path.home() / ".uzpy" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize disk cache
        self.cache = diskcache.Cache(str(cache_dir))
        logger.debug(f"Initialized cache at {cache_dir}")

    def get_file_hash(self, file_path: Path) -> str:
        """
        Generate a hash for a file based on content and modification time.

        This hash is used as part of the cache key to ensure cache invalidation
        when files are modified.

        Args:
            file_path: Path to the file

        Returns:
            Hash string combining content hash and mtime
        """
        try:
            stat = file_path.stat()
            content_hash = hashlib.md5(file_path.read_bytes()).hexdigest()
            return f"{content_hash}:{stat.st_mtime}"
        except Exception as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
            # Return unique hash on error to avoid caching
            return f"error:{id(file_path)}:{hash(str(e))}"

    def find_usages(self, construct: Construct, reference_files: list[Path]) -> list[Reference]:
        """
        Find usages of a construct with caching.

        This method checks the cache first and only calls the underlying
        analyzer if no cached result is found or if any of the reference
        files have been modified.

        Args:
            construct: The construct to find usages for
            reference_files: List of files to search in

        Returns:
            List of references to the construct
        """
        # Create cache key from construct and file hashes
        ref_hashes = [self.get_file_hash(f) for f in reference_files]
        cache_key = f"usages:{construct.name}:{construct.file_path}:{','.join(ref_hashes)}"

        # Check cache
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {construct.name}")
            return self.cache[cache_key]

        logger.debug(f"Cache miss for {construct.name}, analyzing...")

        # Call underlying analyzer
        try:
            references = self.analyzer.find_usages(construct, reference_files)
            # Cache the result
            self.cache[cache_key] = references
            return references
        except Exception as e:
            logger.error(f"Analysis failed for {construct.name}: {e}")
            # Don't cache errors
            raise

    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        logger.info("Cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "size": len(self.cache),
            "volume": self.cache.volume(),
            "hits": self.cache.stats(enable=True).hits,
            "misses": self.cache.stats(enable=True).misses,
        }
