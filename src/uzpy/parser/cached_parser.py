# this_file: src/uzpy/parser/cached_parser.py

"""
Cached parser decorator for uzpy.

This module provides a caching wrapper that can be applied to any parser
to cache parsed constructs, significantly improving performance for
repeated parsing of the same files.

"""

import hashlib
from pathlib import Path
from typing import Any

import diskcache
from loguru import logger

from uzpy.types import Construct


class CachedParser:
    """
    A wrapper class that adds caching functionality to an underlying parser.

    This class wraps an existing parser and adds persistent caching
    using diskcache. It caches parsed constructs and invalidates
    cache entries when files are modified.

    Used in:
    - src/uzpy/parser/__init__.py
    - src/uzpy/pipeline.py
    """

    def __init__(self, parser: Any, cache_dir: Path, cache_name: str = "parser_cache"):
        """
        Initialize the CachedParser.

        Args:
            parser: The underlying parser to wrap
            cache_dir: Directory for cache storage (defaults to ~/.uzpy/cache)

        """
        self.parser = parser
        self.cache_path = cache_dir / cache_name
        self.cache = diskcache.Cache(str(self.cache_path))  # Ensure cache_path is string
        logger.info(f"CachedParser initialized. Cache location: {self.cache_path}")

    def _get_file_hash(self, file_path: Path) -> str:
        """
        Generate a hash for a file based on its content and modification time.

        Args:
            file_path: The path to the file.

        Returns:
            Hash string combining content hash and mtime

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
            return f"nonexistent-{file_path.name}"
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return f"error-{file_path.name}"

    def _get_parse_cache_key(self, file_path: Path) -> str:
        """
        Generate a cache key for parsing a specific file.

        Args:
            file_path: The Path object of the file to be parsed.

        Returns:
            List of constructs found in the file

        Used in:
        - src/uzpy/pipeline.py
        """
        file_hash = self._get_file_hash(file_path)
        # Using a tuple for the key components before joining
        key_parts = (
            "parse_file",
            str(file_path.name),  # Use name for key component
            file_hash,
        )
        return ":".join(key_parts)

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
        """Clear all cached parse results.

"""
        # Clear only parse-related cache entries
        keys_to_delete = [k for k in self.cache if k.startswith("parse:")]
        for key in keys_to_delete:
            del self.cache[key]
        logger.info(f"Parser cache cleared ({len(keys_to_delete)} entries)")

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Parse a file, using the cache if possible.

        Args:
            file_path: The path to the file to parse.

        Returns:
            Dictionary with cache statistics

        """
        cache_key = self._get_parse_cache_key(file_path)

        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for parsing {file_path} (key: {cache_key})")
            # Tree-sitter nodes in Construct objects are not directly serializable by default with pickle.
            # If Construct objects are stored with Nodes, they need to be handled.
            # For this implementation, we assume that if Constructs are cached,
            # their 'node' attribute is either None or handled during serialization/deserialization.
            # A common practice is to set node=None before caching if the node is not needed later.
            # If 'node' is essential, a custom (de)serializer for diskcache or for Construct would be required.
            # For now, returning the cached result as is.
            return cached_result

        logger.debug(f"Cache miss for parsing {file_path} (key: {cache_key}). Parsing...")
        if not hasattr(self.parser, "parse_file") or not callable(self.parser.parse_file):
            logger.error(f"Wrapped parser {type(self.parser)} does not have a callable 'parse_file' method.")
            return []

        result = self.parser.parse_file(file_path)

        # Potentially strip or handle non-serializable parts of Construct before caching
        # For example, if construct.node (Tree-sitter node) is problematic:
        # result_to_cache = [dataclasses.replace(c, node=None) for c in result]
        # self.cache.set(cache_key, result_to_cache)
        # For now, caching as is.
        self.cache.set(cache_key, result)

        logger.debug(f"Stored parsing result for {file_path} in cache (key: {cache_key})")
        return result

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
        """Delegate attribute access to the wrapped parser if not found in CachedParser."""
        if hasattr(self.parser, name):
            return getattr(self.parser, name)
        msg = (
            f"'{type(self).__name__}' object and its wrapped parser "
            f"'{type(self.parser).__name__}' have no attribute '{name}'"
        )
        raise AttributeError(msg)
