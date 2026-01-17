"""Redis caching layer for Bible RAG.

Provides caching for search results and query embeddings.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional

import redis

from config import get_settings

settings = get_settings()


class CacheClient:
    """Redis cache client for Bible RAG."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize the cache client.

        Args:
            redis_url: Redis connection URL. Uses settings if not provided.
        """
        self.redis_url = redis_url or settings.redis_url
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        """Lazy initialization of Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=True,
            )
        return self._client

    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        try:
            return self.client.ping()
        except (redis.ConnectionError, redis.TimeoutError):
            return False

    def generate_cache_key(
        self,
        query: str,
        translations: list[str],
        filters: Optional[dict] = None,
    ) -> str:
        """Generate a cache key from query parameters.

        Args:
            query: Search query text
            translations: List of translation abbreviations
            filters: Optional filter parameters

        Returns:
            MD5 hash string for use as cache key
        """
        # Normalize inputs
        query_normalized = query.strip().lower()
        translations_sorted = sorted(translations)
        filters_normalized = json.dumps(filters or {}, sort_keys=True)

        # Create hash input
        hash_input = f"{query_normalized}|{','.join(translations_sorted)}|{filters_normalized}"

        # Generate MD5 hash
        return hashlib.md5(hash_input.encode()).hexdigest()

    def get_cached_results(self, cache_key: str) -> Optional[dict]:
        """Get cached search results.

        Args:
            cache_key: Cache key (MD5 hash)

        Returns:
            Cached results dictionary or None if not found
        """
        try:
            cached = self.client.get(f"search:{cache_key}")
            if cached:
                # Update hit count
                self.client.hincrby(f"stats:{cache_key}", "hits", 1)
                return json.loads(cached)
        except (redis.ConnectionError, redis.TimeoutError, json.JSONDecodeError):
            pass
        return None

    def cache_results(
        self,
        cache_key: str,
        results: dict,
        query_text: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache search results.

        Args:
            cache_key: Cache key (MD5 hash)
            results: Results dictionary to cache
            query_text: Original query text (for analytics)
            ttl: Time-to-live in seconds. Uses settings default if not provided.

        Returns:
            True if cached successfully, False otherwise
        """
        try:
            ttl = ttl or settings.cache_ttl

            # Store results
            self.client.setex(
                f"search:{cache_key}",
                ttl,
                json.dumps(results),
            )

            # Store metadata for analytics
            self.client.hset(
                f"stats:{cache_key}",
                mapping={
                    "query": query_text,
                    "created_at": datetime.utcnow().isoformat(),
                    "hits": 0,
                },
            )
            self.client.expire(f"stats:{cache_key}", ttl)

            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False

    def get_cached_embedding(self, text: str) -> Optional[list[float]]:
        """Get cached embedding for a text string.

        Args:
            text: Text to get embedding for

        Returns:
            List of floats (embedding) or None if not cached
        """
        try:
            cache_key = hashlib.md5(text.encode()).hexdigest()
            cached = self.client.get(f"embedding:{cache_key}")
            if cached:
                return json.loads(cached)
        except (redis.ConnectionError, redis.TimeoutError, json.JSONDecodeError):
            pass
        return None

    def cache_embedding(
        self,
        text: str,
        embedding: list[float],
        ttl: int = 86400 * 7,  # 7 days
    ) -> bool:
        """Cache an embedding.

        Args:
            text: Text the embedding was generated from
            embedding: List of floats (embedding vector)
            ttl: Time-to-live in seconds

        Returns:
            True if cached successfully
        """
        try:
            cache_key = hashlib.md5(text.encode()).hexdigest()
            self.client.setex(
                f"embedding:{cache_key}",
                ttl,
                json.dumps(embedding),
            )
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            info = self.client.info()
            keys = self.client.keys("search:*")

            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "total_keys": info.get("db0", {}).get("keys", 0),
                "cached_searches": len(keys),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
        except (redis.ConnectionError, redis.TimeoutError):
            return {
                "connected": False,
                "error": "Redis connection failed",
            }

    def clear_search_cache(self) -> int:
        """Clear all cached search results.

        Returns:
            Number of keys deleted
        """
        try:
            keys = self.client.keys("search:*")
            stats_keys = self.client.keys("stats:*")
            all_keys = keys + stats_keys

            if all_keys:
                return self.client.delete(*all_keys)
            return 0
        except (redis.ConnectionError, redis.TimeoutError):
            return 0

    def clear_embedding_cache(self) -> int:
        """Clear all cached embeddings.

        Returns:
            Number of keys deleted
        """
        try:
            keys = self.client.keys("embedding:*")
            if keys:
                return self.client.delete(*keys)
            return 0
        except (redis.ConnectionError, redis.TimeoutError):
            return 0

    def generate_verse_cache_key(
        self,
        book: str,
        chapter: int,
        verse: int,
        translations: Optional[list[str]] = None,
        include_original: bool = False,
        include_cross_refs: bool = True,
    ) -> str:
        """Generate a cache key for verse lookups.

        Args:
            book: Book name or abbreviation
            chapter: Chapter number
            verse: Verse number
            translations: List of translation abbreviations
            include_original: Include original language data
            include_cross_refs: Include cross-references

        Returns:
            MD5 hash string for use as cache key
        """
        # Normalize inputs
        book_normalized = book.strip().lower()
        translations_sorted = sorted(translations) if translations else []

        # Create hash input
        hash_input = (
            f"verse:{book_normalized}:{chapter}:{verse}:"
            f"{','.join(translations_sorted)}:{include_original}:{include_cross_refs}"
        )

        # Generate MD5 hash
        return hashlib.md5(hash_input.encode()).hexdigest()

    def get_cached_verse(self, cache_key: str) -> Optional[dict]:
        """Get cached verse data.

        Args:
            cache_key: Cache key (MD5 hash)

        Returns:
            Cached verse dictionary or None if not found
        """
        try:
            cached = self.client.get(f"verse:{cache_key}")
            if cached:
                # Update hit count
                self.client.hincrby(f"verse_stats:{cache_key}", "hits", 1)
                return json.loads(cached)
        except (redis.ConnectionError, redis.TimeoutError, json.JSONDecodeError):
            pass
        return None

    def cache_verse(
        self,
        cache_key: str,
        verse_data: dict,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache verse data.

        Args:
            cache_key: Cache key (MD5 hash)
            verse_data: Verse data dictionary to cache
            ttl: Time-to-live in seconds. Uses settings default if not provided.

        Returns:
            True if cached successfully, False otherwise
        """
        try:
            ttl = ttl or settings.cache_ttl

            # Store verse data
            self.client.setex(
                f"verse:{cache_key}",
                ttl,
                json.dumps(verse_data),
            )

            # Store metadata for analytics
            self.client.hset(
                f"verse_stats:{cache_key}",
                mapping={
                    "reference": f"{verse_data.get('reference', {}).get('book', '')} "
                                f"{verse_data.get('reference', {}).get('chapter', '')}:"
                                f"{verse_data.get('reference', {}).get('verse', '')}",
                    "created_at": datetime.utcnow().isoformat(),
                    "hits": 0,
                },
            )
            self.client.expire(f"verse_stats:{cache_key}", ttl)

            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False


# Global cache client instance
_cache_client: Optional[CacheClient] = None


def get_cache() -> CacheClient:
    """Get the global cache client instance."""
    global _cache_client
    if _cache_client is None:
        _cache_client = CacheClient()
    return _cache_client
