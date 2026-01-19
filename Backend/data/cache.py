"""
In-memory TTL cache for data adapters.

This cache:
- Stores data with time-to-live (TTL)
- Automatically expires old entries
- Uses simple dictionary storage
- Thread-safe for basic operations
"""

import time
from threading import Lock
from typing import Any, Dict, Optional, Tuple


class TTLCache:
    """
    Simple in-memory cache with time-to-live expiration.

    Usage:
        cache = TTLCache()
        cache.set("key", data, ttl_seconds=300)
        value = cache.get("key")  # Returns None if expired or missing
    """

    def __init__(self):
        """Initialize empty cache with thread lock."""
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if missing/expired
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry_time = self._cache[key]

            # Check if expired
            if time.time() > expiry_time:
                # Remove expired entry
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        with self._lock:
            expiry_time = time.time() + ttl_seconds
            self._cache[key] = (value, expiry_time)

    def is_expired(self, key: str) -> bool:
        """
        Check if cache entry is expired (or missing).

        Args:
            key: Cache key

        Returns:
            True if expired or missing, False if valid
        """
        with self._lock:
            if key not in self._cache:
                return True

            _, expiry_time = self._cache[key]
            return time.time() > expiry_time

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Return number of entries in cache (including expired)."""
        with self._lock:
            return len(self._cache)

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self._cache.items() if current_time > expiry
            ]

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)


# Global cache instance (singleton pattern)
_global_cache = TTLCache()


def get_cache() -> TTLCache:
    """Get the global cache instance."""
    return _global_cache


def build_cache_key(ticker: str, start_date: str, end_date: str) -> str:
    """
    Build deterministic cache key.

    Args:
        ticker: Stock/crypto ticker
        start_date: Start date as string (YYYY-MM-DD)
        end_date: End date as string (YYYY-MM-DD)

    Returns:
        Cache key in format: ticker|start_date|end_date
    """
    return f"{ticker.upper()}|{start_date}|{end_date}"
