"""
Tests for newly enhanced features including:
- CLI override and transport options
- Unified cache system
- Enhanced template manager
- CLI integration improvements
"""

import tempfile
from pathlib import Path

import pytest

from mcp_template.core.cache import CacheManager


@pytest.mark.unit
class TestCacheManager:
    """Test the unified cache system functionality."""

    def test_cache_manager_initialization(self):
        """Test cache manager initializes correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(cache_dir=Path(temp_dir), max_age_hours=14.0)
            assert cache_manager.cache_dir == Path(temp_dir)
            assert cache_manager.max_age_hours == 14.0  # Default cache hours

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(cache_dir=Path(temp_dir))

            test_data = {"key": "value", "number": 42}
            cache_manager.set("test_key", test_data)

            retrieved_data = cache_manager.get("test_key")
            assert retrieved_data is not None
            assert "data" in retrieved_data
            assert "timestamp" in retrieved_data
            assert "cache_key" in retrieved_data
            assert retrieved_data["data"]["key"] == "value"
            assert retrieved_data["data"]["number"] == 42

    def test_cache_delete_alias(self):
        """Test that delete method is an alias for remove."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(cache_dir=Path(temp_dir))

            test_data = {"key": "value"}
            cache_manager.set("test_key", test_data)

            # Verify it exists
            assert cache_manager.get("test_key") is not None

            # Delete using delete method
            result = cache_manager.delete("test_key")
            assert result is True

            # Verify it's gone
            assert cache_manager.get("test_key") is None

    def test_cache_expiration(self):
        """Test cache expiration functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(
                cache_dir=Path(temp_dir), max_age_hours=0.0001
            )  # Very short TTL

            test_data = {"key": "value"}
            cache_manager.set("test_key", test_data)

            # Should be available immediately
            assert cache_manager.get("test_key") is not None

            # Wait for expiration
            import time

            time.sleep(0.5)

            # Should be None now (expired)
            assert cache_manager.get("test_key") is None
