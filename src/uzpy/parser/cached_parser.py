# this_file: src/uzpy/parser/cached_parser.py

"""
Caching layer for parsers to improve performance.

This module provides a caching wrapper that can be applied to any parser
to cache parsed constructs, significantly improving performance for
repeated parsing of the same files.
"""

import hashlib
from pathlib import Path
from typing import Any, Optional, Union

import diskcache
from loguru import logger

from uzpy.types import Construct


class CachedParser:
    """
    Caching wrapper for any parser implementation.

    This class wraps an existing parser and adds persistent caching
    using diskcache. It caches parsed constructs and invalidates
    cache entries when files are modified.
    """

    def __init__(self, parser: Any, cache_dir: Path | None = None):
        """
        Initialize cached parser with an underlying parser.

        Args:
            parser: The underlying parser to wrap
            cache_dir: Directory for cache storage (defaults to ~/.uzpy/cache)
        """
        self.parser = parser
        if cache_dir is None:
            cache_dir = Path.home() / ".uzpy" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize disk cache
        self.cache = diskcache.Cache(str(cache_dir))
        logger.debug(f"Initialized parser cache at {cache_dir}")

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

    def parse_file(self, file_path: Path) -> list[Construct]:
        """
        Parse a Python file with caching.

        This method checks the cache first and only calls the underlying
        parser if no cached result is found or if the file has been modified.

        Args:
            file_path: Path to the Python file to parse

        Returns:
            List of constructs found in the file
        """
        # Create cache key from file hash
        cache_key = f"parse:{self.get_file_hash(file_path)}"

        # Check cache
        if cache_key in self.cache:
            logger.debug(f"Parser cache hit for {file_path}")
            return self.cache[cache_key]

        logger.debug(f"Parser cache miss for {file_path}, parsing...")

        # Call underlying parser
        try:
            constructs = self.parser.parse_file(file_path)
            # Create cacheable versions without tree-sitter Node objects
            cacheable_constructs = []
            for construct in constructs:
                # Create construct without the node field (which can't be pickled)
                cacheable_construct = Construct(
                    name=construct.name,
                    type=construct.type,
                    file_path=construct.file_path,
                    line_number=construct.line_number,
                    docstring=construct.docstring,
                    full_name=construct.full_name,
                    node=None,  # Don't cache the unpickleable Node object
                )
                cacheable_constructs.append(cacheable_construct)
            
            # Cache the cacheable results
            self.cache[cache_key] = cacheable_constructs
            return constructs  # Return original constructs with nodes
        except Exception as e:
            logger.error(f"Parsing failed for {file_path}: {e}")
            # Don't cache errors
            raise

    def clear_cache(self):
        """Clear all cached parse results."""
        # Clear only parse-related cache entries
        keys_to_delete = [k for k in self.cache if k.startswith("parse:")]
        for key in keys_to_delete:
            del self.cache[key]
        logger.info(f"Parser cache cleared ({len(keys_to_delete)} entries)")

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get parser cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        parse_keys = [k for k in self.cache if k.startswith("parse:")]
        return {
            "parse_entries": len(parse_keys),
            "total_size": len(self.cache),
            "volume": self.cache.volume(),
        }
