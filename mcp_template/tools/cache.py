"""
Cache management module for tool discovery results.

This module handles caching of discovered tools with timestamp-based invalidation
and cache management utilities.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_CACHE_MAX_AGE_HOURS = 6
CACHE_FILE_PATTERN = "*.tools.json"


class CacheManager:
    """
    Manages caching of tool discovery results.

    Features:
    - Timestamp-based cache invalidation
    - Configurable cache duration
    - Cache cleanup utilities
    - Safe file operations
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_age_hours: float = DEFAULT_CACHE_MAX_AGE_HOURS,
    ):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files (defaults to ~/.mcp/cache)
            max_age_hours: Maximum age of cache entries in hours
        """
        self.cache_dir = cache_dir or Path.home() / ".mcp" / "cache"
        self.max_age_hours = max_age_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data for a key.

        Args:
            key: Cache key (usually template name)

        Returns:
            Cached data if valid and not expired, None otherwise
        """
        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            logger.debug("Cache miss for key: %s", key)
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)

            # Validate cache structure
            if not isinstance(cached_data, dict) or "timestamp" not in cached_data:
                logger.warning("Invalid cache format for key: %s", key)
                self._remove_cache_file(cache_file)
                return None

            # Check if cache is expired
            cache_age_hours = (time.time() - cached_data["timestamp"]) / 3600
            if cache_age_hours > self.max_age_hours:
                logger.debug(
                    "Cache expired for key %s (age: %.1fh)", key, cache_age_hours
                )
                self._remove_cache_file(cache_file)
                return None

            logger.debug("Cache hit for key: %s", key)
            return cached_data

        except (json.JSONDecodeError, OSError, KeyError) as e:
            logger.warning("Failed to load cache for key %s: %s", key, e)
            self._remove_cache_file(cache_file)
            return None

    def set(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Store data in cache.

        Args:
            key: Cache key (usually template name)
            data: Data to cache (must be JSON-serializable)

        Returns:
            True if successfully cached, False otherwise
        """
        cache_file = self._get_cache_file(key)

        try:
            # Ensure timestamp is included
            cache_data = data.copy()
            cache_data["timestamp"] = time.time()
            cache_data["cache_key"] = key

            # Write to temporary file first, then rename for atomicity
            temp_file = cache_file.with_suffix(f"{cache_file.suffix}.tmp")

            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, default=str)

            # Atomic rename
            temp_file.rename(cache_file)

            logger.debug("Cached data for key: %s", key)
            return True

        except (OSError, TypeError) as e:
            logger.warning("Failed to cache data for key %s: %s", key, e)
            # Clean up temp file if it exists
            temp_file = cache_file.with_suffix(f"{cache_file.suffix}.tmp")
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            return False

    def remove(self, key: str) -> bool:
        """
        Remove cached data for a key.

        Args:
            key: Cache key to remove

        Returns:
            True if removed or didn't exist, False on error
        """
        cache_file = self._get_cache_file(key)
        return self._remove_cache_file(cache_file)

    def clear_all(self) -> int:
        """
        Clear all cached data.

        Returns:
            Number of files removed
        """
        removed_count = 0

        try:
            for cache_file in self.cache_dir.glob(CACHE_FILE_PATTERN):
                if self._remove_cache_file(cache_file):
                    removed_count += 1

            logger.info("Cleared %d cache files", removed_count)
            return removed_count

        except OSError as e:
            logger.error("Error clearing cache: %s", e)
            return removed_count

    def clear_expired(self) -> int:
        """
        Clear expired cache entries.

        Returns:
            Number of expired files removed
        """
        removed_count = 0
        current_time = time.time()

        try:
            for cache_file in self.cache_dir.glob(CACHE_FILE_PATTERN):
                if self._is_cache_expired(cache_file, current_time):
                    if self._remove_cache_file(cache_file):
                        removed_count += 1
                        logger.debug("Removed expired cache: %s", cache_file.name)

            if removed_count > 0:
                logger.info("Cleared %d expired cache files", removed_count)

            return removed_count

        except OSError as e:
            logger.error("Error clearing expired cache: %s", e)
            return removed_count

    def _is_cache_expired(self, cache_file: Path, current_time: float) -> bool:
        """Check if a cache file is expired or corrupted."""
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)

            # Check if expired
            if "timestamp" in cached_data:
                cache_age_hours = (current_time - cached_data["timestamp"]) / 3600
                return cache_age_hours > self.max_age_hours
            else:
                # Treat files without timestamp as expired
                return True

        except (json.JSONDecodeError, OSError, KeyError):
            # Treat corrupted files as expired
            return True

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the cache.

        Returns:
            Dictionary with cache statistics
        """
        try:
            cache_files = list(self.cache_dir.glob(CACHE_FILE_PATTERN))
            total_files = len(cache_files)

            if total_files == 0:
                return {
                    "total_files": 0,
                    "expired_files": 0,
                    "valid_files": 0,
                    "cache_dir": str(self.cache_dir),
                    "max_age_hours": self.max_age_hours,
                }

            expired_count = 0
            current_time = time.time()

            for cache_file in cache_files:
                if self._is_cache_expired(cache_file, current_time):
                    expired_count += 1

            valid_count = total_files - expired_count

            return {
                "total_files": total_files,
                "expired_files": expired_count,
                "valid_files": valid_count,
                "cache_dir": str(self.cache_dir),
                "max_age_hours": self.max_age_hours,
            }

        except OSError as e:
            logger.error("Error getting cache info: %s", e)
            return {
                "error": str(e),
                "cache_dir": str(self.cache_dir),
                "max_age_hours": self.max_age_hours,
            }

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for a key."""
        # Sanitize key for filename
        safe_key = "".join(c for c in key if c.isalnum() or c in "._-")
        return self.cache_dir / f"{safe_key}.tools.json"

    def _remove_cache_file(self, cache_file: Path) -> bool:
        """Safely remove a cache file."""
        try:
            if cache_file.exists():
                cache_file.unlink()
                logger.debug("Removed cache file: %s", cache_file.name)
            return True

        except OSError as e:
            logger.warning("Failed to remove cache file %s: %s", cache_file.name, e)
            return False
